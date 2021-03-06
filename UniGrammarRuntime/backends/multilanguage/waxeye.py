import typing
from collections import OrderedDict

from UniGrammarRuntimeCore.IParser import IParser

from ...grammarClasses import PEG
from ...ToolMetadata import ToolMetadata, Product

from ...IParser import IParserFactoryFromPrecompiled
from ...IParsingBackend import IParsingBackend
from ...utils import ListLikeDict, NodeWithAttrChildrenMixin, ListNodesMixin

waxeye = None
NodeWithAttrChildren = None
ListNodes = None
TerminalNode = None


toolGitRepo = "https://github.com/waxeye-org/waxeye"
masterBranchURI = toolGitRepo + "/tree/master"
srcURI = masterBranchURI + "/src"


def decapitalizeFirst(s: str) -> str:
	return "".join((s[0].lower(), s[1:]))


def capitalizeFirst(s: str) -> str:
	return "".join((s[0].upper(), s[1:]))


def _transformWaxeyeAST(node: "waxeye.AST", capSchema: typing.Dict[str, typing.Dict[str, str]], iterSchema: typing.List[str]) -> None:
	"""
	Fucking waxeye decapitalizes all the identifiers, destroying uniformity between backends. So we have 2 lookups instead of one. It is definitely a bug in waxeye.
	"""
	capitalizedType = capitalizeFirst(node.type)

	if node.type not in iterSchema and capitalizedType not in iterSchema:
		newChildren = OrderedDict()
		thisElMapping = None
		if node.type in capSchema:
			thisElMapping = capSchema[node.type]
		elif capitalizedType in capSchema:
			thisElMapping = capSchema[capitalizedType]

		for i, child in enumerate(node.children):
			nameToUse = str(i)  # we cannot use just ints as keys for ListLikeDict because it also supports positional indexing
			if not isinstance(child, str):
				childProdName = child.type
				_transformWaxeyeAST(child, capSchema, iterSchema)
				if thisElMapping:
					childProdNameCapitalized = capitalizeFirst(childProdName)

					if childProdName in thisElMapping:
						nameToUse = thisElMapping[childProdName]  # recovered name
					elif childProdNameCapitalized in thisElMapping:
						nameToUse = thisElMapping[childProdNameCapitalized]  # recovered name

				if isinstance(nameToUse, int):
					# we have to insert something, and in this case it's better to have prod name than just number
					nameToUse = childProdName
			newChildren[nameToUse] = child
		node.children = ListLikeDict(newChildren)

		if len(node.children) == 1 and isinstance(node.children[0], str):
			node.__class__ = TerminalNode
		else:
			node.__class__ = NodeWithAttrChildren
	else:
		for child in node.children:
			_transformWaxeyeAST(child, capSchema, iterSchema)
		node.__class__ = ListNodes


class WaxeyeParser(IParser):
	NAME = "waxeye"

	__slots__ = ("parser",)

	def __init__(self, parser):
		super().__init__()
		self.parser = parser

	def __call__(self, s: str) -> "waxeye.AST":
		print("self.parser", self.parser)
		return self.parser.parse(s)


class WaxeyeParserFactory(IParserFactoryFromPrecompiled):
	__slots__ = ()
	PARSER_CLASS = WaxeyeParser
	META = ToolMetadata(
		Product(
			name="waxeye",
			website=toolGitRepo,
		),
		runtimeLib={
			"python": srcURI + "/python",
			"js": srcURI + "/javascript",
			"java": srcURI + "/java",
			"c++": srcURI + "/c",
			"racket": srcURI + "/racket",
			"ruby": srcURI + "/ruby",
			"sml": srcURI + "/sml",
		},
		grammarClasses=(PEG,),
		buildsTree=True
	)

	def processEvaledGlobals(self, globalz: dict, grammarName: str):
		return globalz["Parser"]

	def __init__(self) -> None:
		global waxeye, NodeWithAttrChildren, ListNodes, TerminalNode
		if waxeye is None:
			import waxeye  # pylint:disable=import-outside-toplevel,redefined-outer-name

			class NodeWithAttrChildren(waxeye.AST, NodeWithAttrChildrenMixin):  # pylint:disable=redefined-outer-name,unused-variable
				__slots__ = ()

			class ListNodes(waxeye.AST, ListNodesMixin):  # pylint:disable=redefined-outer-name,unused-variable
				__slots__ = ()

			class TerminalNode(waxeye.AST, TerminalNodeMixin):  # pylint:disable=redefined-outer-name,unused-variable
				__slots__ = ()

		super().__init__()


class WaxeyeParsingBackend(IParsingBackend):
	__slots__ = ("parser", "capSchema", "iterSchema")

	PARSER = WaxeyeParserFactory
	ITER_INTROSPECTION = False
	CAP_INTROSPECTION = False

	#EX_CLASS = waxeye.ParseError # not an Exception

	def __init__(self, grammarResources: "InMemoryGrammarResources") -> None:
		super().__init__(grammarResources)

		self.capSchema = grammarResources.capSchema
		self.iterSchema = grammarResources.iterSchema

	def iterateChildren(self, node):
		return node.children

	def isTerminal(self, node):
		return isinstance(node, (str, TerminalNode))

	def iterateCollection(self, lst):
		return lst

	def isCollection(self, lst: typing.Union["waxeye.AST", str]) -> bool:
		return isinstance(lst, ListNodes)

	def parse(self, s: str) -> "waxeye.AST":
		return self.parser(s)

	def preprocessAST(self, ast):
		_transformWaxeyeAST(ast, self.capSchema, self.iterSchema)
		return ast

	def terminalNodeToStr(self, token: typing.Union[str, "waxeye.AST"]) -> str:
		return str(token)
