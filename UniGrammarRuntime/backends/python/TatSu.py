import typing
import ast
from pathlib import Path

from UniGrammarRuntimeCore.IParser import IParser

from ...grammarClasses import PEG
from ...ToolMetadata import ToolMetadata, Product
from ...DSLMetadata import DSLMetadata

from ...IParser import IParserFactoryFromPrecompiled, IParserFactoryFromPrecompiledOrSource, IParserFactoryFromSource
from ...IParsingBackend import IParsingBackend

tatsu = None

toolGitRepo = "https://github.com/neogeny/TatSu"


def ensureInitialized():
	global tatsu
	if tatsu is None:
		import tatsu  # pylint:disable=import-outside-toplevel,redefined-outer-name


class TatSuParser(IParser):
	__slots__ = ("parser",)
	NAME = "TatSu"

	def __init__(self, parser):
		super().__init__()
		self.parser = parser

	def __call__(self, s: str):
		return self.parser.parse(s, getattr(self.parser, "_MAIN_PRODUCTION_NAME", None))


class TatSuParserFactoryFromPrecompiled(IParserFactoryFromPrecompiled):
	__slots__ = ()

	PARSER_CLASS = TatSuParser

	def __init__(self):
		ensureInitialized()
		super().__init__()

	def getSource(self, grammarResources: "InMemoryGrammarResources"):
		parserAST = super().getSource(grammarResources)
		parserClassNode = _getParserClass(parserAST, grammarResources.name)
		firstRuleName = _getFirstRuleNameFromCompiled(parserClassNode)
		parserClassNode.body.append(ast.Assign(
			targets=[ast.Name(
				"_MAIN_PRODUCTION_NAME", ctx=ast.Store(),
				lineno=-1,
				col_offset=-1
			)],
			value=ast.Str(firstRuleName,
				lineno=-1,
				col_offset=-1
			),
			type_comment=None,
			lineno=-1,
			col_offset=-1
		))
		return parserAST

	ensureInitialized = ensureInitialized

	def processEvaledGlobals(self, globalz: dict, grammarName: str):
		return globalz[grammarName + "Parser"]


class TatSuParserFactoryFromSource(IParserFactoryFromSource):
	__slots__ = ()

	PARSER_CLASS = TatSuParser
	FORMAT = DSLMetadata(
		officialLibraryRepo=toolGitRepo + "/tree/master/examples",
		grammarExtensions=("ebnf",),
	)

	def __init__(self):
		ensureInitialized()
		super().__init__()

	def compileStr(self, grammarText: str, target: str = None, fileName: Path = None):
		return tatsu.compile(grammarText, None, filename=(str(fileName) if fileName else None))


class TatSuParserFactory(IParserFactoryFromPrecompiledOrSource):
	PRECOMPILED = TatSuParserFactoryFromPrecompiled
	SOURCE = TatSuParserFactoryFromSource
	PARSER_CLASS = TatSuParser

	META = ToolMetadata(
		Product(
			name="TatSu",
			website=toolGitRepo,
		),
		runtimeLib={
			"python": toolGitRepo,
		},
		grammarClasses=(PEG,),
		buildsTree=True
	)


def _getParserClass(m: ast.Module, grammarName: str):
	"""TaTsu has a bug: to call a python-compiled grammar one needs to explicitly provide first rule name (for ga grammar created from source he doesn't), but it is not availablei n it in machine-readable form. Fortunately it is the first func in the class."""
	className = grammarName + "Parser"

	for n in m.body:
		if isinstance(n, ast.ClassDef) and n.name == className:
			return n
	raise Exception("Parser class has not been found")


def _getFirstRuleNameFromCompiled(classNode: ast.ClassDef) -> str:
	for cn in classNode.body:
		if isinstance(cn, ast.FunctionDef) and cn.decorator_list:
			firstDecorator = cn.decorator_list[0]
			if isinstance(firstDecorator, ast.Call) and firstDecorator.func.id == "tatsumasu":
				return cn.name[1:-1]
	raise Exception("No productions has been found")


class TatSuParsingBackend(IParsingBackend):
	__slots__ = ()
	PARSER = TatSuParserFactory

	def iterateCollection(self, lst) -> typing.Any:
		return lst

	def isCollection(self, lst: typing.Any) -> bool:
		return isinstance(lst, list)

	def iterateChildren(self, node):
		#return node.children
		raise NotImplementedError

	def isTerminal(self, node):
		return isinstance(node, str)

	def terminalNodeToStr(self, token) -> typing.Optional[str]:
		return token
