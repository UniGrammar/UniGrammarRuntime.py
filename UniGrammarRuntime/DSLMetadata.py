import typing
import warnings

from .ToolMetadata import Product
from .FormatMetadata import FormatMetadata

class DSLMetadata(FormatMetadata):
	__slots__ = ("officialLibraryRepo",)

	def __init__(self, officialLibraryRepo: typing.Optional[str] = None, grammarExtensions: typing.Optional[typing.Union[typing.Tuple[str, str], typing.Tuple[str]]] = None, product: typing.Optional[Product] = None) -> None:
		super().__init__(grammarExtensions, product)
		self.officialLibraryRepo = officialLibraryRepo
