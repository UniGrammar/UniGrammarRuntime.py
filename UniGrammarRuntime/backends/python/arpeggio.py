import typing
from collections import OrderedDict
from pathlib import Path

from UniGrammarRuntimeCore.IParser import IParser

from ...grammarClasses import PEG
from ...ToolMetadata import ToolMetadata, Product
from ...DSLMetadata import DSLMetadata

from ...IParser import IParserFactoryFromSource
from ...IParsingBackend import IParsingBackend
from ...utils import AttrDict, flattenDictsIntoIterable

arpeggio = None


def getFirstRuleName(grammarSrc: str) -> str:
	parser = arpeggio.ParserPython(arpeggio.peg.peggrammar, arpeggio.peg.comment, reduce_tree=False)
	parsedAST = parser.parse(grammarSrc)
	for el in parsedAST:
		if el.rule_name == "rule":
			if el[0].rule_name == "rule_name":
				return el[0].flat_str()



class ArpeggioParser(IParser):
	__slots__ = ("parser",)

	def __init__(self, parser) -> None:
		super().__init__()
		self.parser = parser

	def __call__(self, s: str):
		return self.parser.parse(s)


toolGitRepo = "https://github.com/textX/Arpeggio"

class ArpeggioParserFactory(IParserFactoryFromSource):
	__slots__ = ()
	PARSER_CLASS = ArpeggioParser
	FORMAT = DSLMetadata(
		officialLibraryRepo=toolGitRepo + "/tree/master/examples",
		grammarExtensions=("peg",)
	)
	
	META = ToolMetadata(
		Product(
			name="arpeggio",
			website=toolGitRepo,
		),
		runtimeLib={
			"python": toolGitRepo,
		},
		grammarClasses=(PEG,),
		buildsTree=None
	)

	def __init__(self) -> None:
		global arpeggio

		if arpeggio is None:
			import arpeggio  # pylint:disable=import-outside-toplevel,redefined-outer-name
			import arpeggio.peg  # pylint:disable=import-outside-toplevel,redefined-outer-name

		super().__init__()

	def compileStr(self, grammarText: str, target=None, fileName: Path = None):
		firstRuleName = getFirstRuleName(grammarText)
		return arpeggio.peg.ParserPEG(grammarText, firstRuleName, skipws=False, debug=False)


	def fromInternal(self, internalRepr: str, target: str = None) -> typing.Any:
		return self.__class__.PARSER_CLASS(self.compileStr(internalRepr, target))

TransformedASTElT = typing.Union["arpeggio.Terminal", "TransformedASTT"]
TransformedASTT = typing.Mapping[str, TransformedASTElT]


def _transformArpeggioAST(node, capSchema: typing.Dict[str, typing.Dict[str, str]], iterSchema: typing.List[str]) -> TransformedASTElT:
	if node.rule_name not in iterSchema:
		newChildren = AttrDict()
		thisElMapping = None
		if node.rule_name in capSchema:
			thisElMapping = capSchema[node.rule_name]

		if not isinstance(node, arpeggio.Terminal):
			for i, child in enumerate(node):
				nameToUse = str(i)  # we cannot use just ints as keys for ListLikeDict because it also supports positional indexing
				if not isinstance(child, str):
					childProdName = child.rule_name
					newChild = _transformArpeggioAST(child, capSchema, iterSchema)
					if thisElMapping:
						if childProdName in thisElMapping:
							nameToUse = thisElMapping[childProdName]  # recovered name

					if isinstance(nameToUse, int):
						# we have to insert something, and in this case it's better to have prod name than just number
						nameToUse = childProdName
				else:
					newChild = child
				newChildren[nameToUse] = newChild
			return newChildren
		return node.flat_str()
	else:
		return [_transformArpeggioAST(child, capSchema, iterSchema) for child in node]


class ArpeggioParsingBackend(IParsingBackend):
	__slots__ = ("parser", "capSchema", "iterSchema")
	ITER_INTROSPECTION = False
	CAP_INTROSPECTION = False
	PARSER = ArpeggioParserFactory

	def __init__(self, grammarResources: "InMemoryGrammarResources") -> None:
		global arpeggio

		super().__init__(grammarResources)
		self.capSchema = grammarResources.capSchema
		self.iterSchema = grammarResources.iterSchema

		if arpeggio is None:
			import arpeggio
			import arpeggio.peg

	def iterateChildren(self, node):
		yield from lst

	def isTerminal(self, node):
		return isinstance(node, str)

	def iterateCollection(self, lst) -> typing.Any:
		yield from lst

	def isCollection(self, lst) -> bool:
		return isinstance(lst, ListNodes)

	def preprocessAST(self, ast):
		return _transformArpeggioAST(ast, self.capSchema, self.iterSchema)

	def terminalNodeToStr(self, token) -> typing.Optional[str]:
		return "".join(flattenDictsIntoIterable(node))

	def getSubTreeText(self, node) -> str:
		"""Merges a tree of text tokens into a single string"""
		return "".join(flattenDictsIntoIterable(node))
