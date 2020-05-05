import typing
from abc import ABCMeta, abstractmethod

backendsRegistry = {}


class ParserNotFoundException(Exception):
	"""Means that not all parser components have been found"""


class IParsingBackendMeta(ABCMeta):
	__slots__ = ()

	def __new__(cls: typing.Type["TemplateMeta"], className: str, parents: typing.Tuple[typing.Type, ...], attrs: typing.Dict[str, typing.Any]) -> "Template":  # pylint:disable=arguments-differ
		res = super().__new__(cls, className, parents, attrs)

		parserFactoryClass = attrs.get("PARSER", None)
		if parserFactoryClass is not None:
			parserClass = getattr(parserFactoryClass, "PARSER_CLASS", None)
			if parserClass is not None and parserFactoryClass.META is not None:
				backendsRegistry[parserFactoryClass.META.product.name] = res

		return res


class IParsingBackend(metaclass=IParsingBackendMeta):
	"""A class commanding the parsing. Calls the generated parser and postprocesses its output"""

	__slots__ = ("parser",)

	PARSER = None

	@property
	@classmethod
	def NAME(cls):
		return cls.PARSER.NAME

	EX_CLASS = Exception
	ITER_INTROSPECTION = True
	CAP_INTROSPECTION = True

	def __init__(self, grammarResources: "InMemoryGrammarResources") -> None:
		self.parser = self.__class__.PARSER().fromBundle(grammarResources)

	def _getSubTreeText(self, lst: typing.Any) -> typing.Iterator[str]:
		if self.isCollection(lst):
			for t in self.iterateCollection(lst):
				yield from self._getSubTreeText(t)
		elif self.isTerminal(lst):
			yield self.terminalNodeToStr(lst)
		else:
			for t in self.iterateChildren(lst):
				yield from self._getSubTreeText(t)

	def getSubTreeText(self, node: typing.Any) -> str:
		"""Merges a tree of text tokens into a single string"""
		return "".join(self._getSubTreeText(node))

	@abstractmethod
	def iterateCollection(self, lst):
		raise NotImplementedError()

	@abstractmethod
	def iterateChildren(self, node):
		raise NotImplementedError()

	@abstractmethod
	def isTerminal(self, node):
		raise NotImplementedError()

	@abstractmethod
	def isCollection(self, lst):
		raise NotImplementedError()

	def preprocessAST(self, ast: typing.Any) -> typing.Any:
		return ast

	def parse(self, s: str) -> typing.Any:
		return self.parser(s)

	def terminalNodeToStr(self, token: typing.Optional[typing.Any]) -> typing.Optional[typing.Any]:
		return token
