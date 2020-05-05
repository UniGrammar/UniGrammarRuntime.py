import typing
from collections import OrderedDict
from pathlib import Path

from UniGrammarRuntimeCore.IParser import IParser

from ...grammarClasses import PEG
from ...ToolMetadata import ToolMetadata, Product
from ...DSLMetadata import DSLMetadata

from ...IParser import IParserFactoryFromSource
from ...IParsingBackend import IParsingBackend
from ...utils import ListLikeDict, NodeWithAttrChildrenMixin, ListNodesMixin

parsimonious = None
NodeWithAttrChildren = None
ListNodes = None


toolGitRepo = "https://github.com/erikrose/parsimonious"

class ParsimoniousParser(IParser):
	__slots__ = ("parser",)

	def __init__(self, parser: "parsimonious.grammar.Grammar") -> None:
		super().__init__()
		self.parser = parser

	def __call__(self, s: str) -> "parsimonious.nodes.Node":
		return self.parser.parse(s)


class ParsimoniousParserFactory(IParserFactoryFromSource):
	__slots__ = ()
	PARSER_CLASS = ParsimoniousParser

	FORMAT = DSLMetadata(
		officialLibraryRepo=None,
		grammarExtensions=None
	)

	META = ToolMetadata(
		Product(
			name="parsimonious",
			website=toolGitRepo,
		),
		runtimeLib={
			"python": toolGitRepo,
		},
		grammarClasses=(PEG,),
		buildsTree=None
	)

	def __init__(self) -> None:
		global parsimonious

		if parsimonious is None:
			import parsimonious  # pylint:disable=import-outside-toplevel,redefined-outer-name

		super().__init__()

	def compileStr(self, grammarText: str, target=None, fileName: Path = None) -> "parsimonious.grammar.Grammar":
		return parsimonious.Grammar(grammarText)

	def fromInternal(self, internalRepr: str, target: str = None) -> typing.Any:
		return self.__class__.PARSER_CLASS(self.compileStr(internalRepr, target))


def _transformParsimoniousAST(node: typing.Union["parsimonious.nodes.Node", "parsimonious.nodes.RegexNode"], capSchema: typing.Dict[str, typing.Dict[str, str]]) -> None:
	"""Walks parsimonious AST to make it more friendly for our processing:
		1. Replaces lists of children with `ListLikeDict`s, using `expr_name`s as keys
		2. Adds `__getattr__` to the nodes looking up attrs in the dicts of children

		All of this is needed because our postprocessing is attr-based.
	"""

	if not isinstance(node, parsimonious.nodes.RegexNode):
		if not isinstance(node.expr, (parsimonious.expressions.OneOrMore, parsimonious.expressions.ZeroOrMore)):
			newChildren = OrderedDict()
			for child in node.children:
				childProdName = child.expr_name
				_transformParsimoniousAST(child, capSchema)
				nameToUse = None
				if node.expr_name in capSchema:
					thisElMapping = capSchema[node.expr_name]

					if childProdName in thisElMapping:
						nameToUse = thisElMapping[childProdName]  # recovered name

				if nameToUse is None:
					# we have to insert something
					nameToUse = childProdName
				newChildren[nameToUse] = child
			node.children = ListLikeDict(newChildren)
			node.__class__ = NodeWithAttrChildren
		else:
			for child in node.children:
				_transformParsimoniousAST(child, capSchema)
			node.__class__ = ListNodes


class ParsimoniousParsingBackend(IParsingBackend):
	__slots__ = ("parser", "capSchema")
	ITER_INTROSPECTION = True
	CAP_INTROSPECTION = False
	PARSER = ParsimoniousParserFactory

	def __init__(self, grammarResources: "InMemoryGrammarResources") -> None:
		global NodeWithAttrChildren, ListNodes

		super().__init__(grammarResources)
		self.capSchema = grammarResources.capSchema

		if NodeWithAttrChildren is None:

			class NodeWithAttrChildren(parsimonious.nodes.Node, NodeWithAttrChildrenMixin):  # pylint:disable=redefined-outer-name
				__slots__ = ()

			class ListNodes(parsimonious.nodes.Node, ListNodesMixin):  # pylint:disable=redefined-outer-name,unused-variable
				__slots__ = ()

	def iterateChildren(self, node):
		return node.children

	def isTerminal(self, node):
		return isinstance(node, parsimonious.nodes.RegexNode)

	def iterateCollection(self, lst) -> typing.Any:
		return lst.children

	def isCollection(self, lst: typing.Any) -> bool:
		return isinstance(lst.expr, (parsimonious.expressions.ZeroOrMore, parsimonious.expressions.OneOrMore))

	def preprocessAST(self, ast):
		_transformParsimoniousAST(ast, self.capSchema)
		return ast

	def terminalNodeToStr(self, token: "parsimonious.nodes.RegexNode") -> typing.Optional[str]:
		return token.text

	def getSubTreeText(self, node: "parsimonious.nodes.Node") -> str:
		"""Merges a tree of text tokens into a single string"""
		return node.text
