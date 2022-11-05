from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Literal,
    Protocol,
    TypeAlias,
    TypeVar,
    cast,
    overload,
)

from sqlalchemy import Column, ForeignKey, Integer, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from .config import settings

engine = create_async_engine(settings.get_database_url())
SessionLocal = cast(
    Callable[[], AsyncSession],
    sessionmaker(
        autocommit=False, autoflush=False, bind=engine, class_=cast(Any, AsyncSession)
    ),
)

T = TypeVar("T")
Default = TypeVar("Default")
B_co = TypeVar("B_co", covariant=True)
T_co = TypeVar("T_co", covariant=True)


class SQLType(Protocol[T_co]):
    @property
    def python_type(self) -> T_co:
        ...


class BaseC(Protocol[B_co, T]):
    @overload
    def __get__(self, instance: None, owner: type[Any]) -> B_co:
        ...

    @overload
    def __get__(self, instance: Any, owner: type[Any]) -> T:
        ...

    def __set__(self, instance: Any, value: T) -> None:
        ...


C: TypeAlias = BaseC[Column, T]
R: TypeAlias = BaseC[relationship, T]


@overload
def col(
    typ: type[SQLType[T]], *args, default: None, primary_key: Literal[True], **kwargs
) -> C[T]:
    ...


@overload
def col(
    typ: type[SQLType[T]], *args, default: Default | Callable[[], Default], **kwargs
) -> C[T | Default]:
    ...


@overload
def col(typ: type[SQLType[T]], *args, **kwargs) -> C[T]:
    ...


def col(typ: type[SQLType[Any]], *args, **kwargs) -> C[Any]:
    """Column"""
    return Column(typ, *args, **kwargs)  # type: ignore


def rel(*args, default: str | None = None, **kwargs) -> R:
    """relationship"""
    return relationship(*args, **kwargs)


def pk(*, default: None, **kwargs) -> C[int]:
    """Primary key"""
    return Column(Integer, primary_key=True, **kwargs)  # type: ignore


@overload
def fk(ref: str, *, nullable: Literal[True], default: None, **kwargs) -> C[int | None]:
    ...


@overload
def fk(ref: str, *, nullable: Literal[False], default: None, **kwargs) -> C[int]:
    ...


def fk(ref: str, **kwargs) -> Any:
    """Foreign key"""
    return Column(Integer, ForeignKey(ref), **kwargs)


if TYPE_CHECKING:
    from sqlalchemy.ext.declarative import DeclarativeMeta as _DeclarativeMeta
    from typing_extensions import dataclass_transform

    @dataclass_transform(
        kw_only_default=True,
        field_specifiers=(col, rel, fk),
    )
    class Base(metaclass=_DeclarativeMeta):
        metadata: ClassVar[MetaData]

else:
    Base = declarative_base()
