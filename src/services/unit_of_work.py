import typing as tp
from abc import ABC
from abc import abstractmethod

from sqlalchemy import orm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from src import settings
from src.services.repo import AbstractRepo
from src.services.repo.alchemy.repository import SQLAlchemyRepo
from src.services.repo.in_memory.repository import InMemoryRepo


class AbstractUnitOfWork(ABC):
    repo: AbstractRepo

    async def __aenter__(self) -> "AbstractUnitOfWork":
        return self

    async def __aexit__(
        self, exn_type: tp.Any, exn_value: tp.Any, traceback: tp.Any
    ) -> None:
        if exn_type is None:
            await self._commit()
        else:
            await self.rollback()
            raise exn_type(exn_value)

    async def commit(self) -> None:
        await self._commit()

    @abstractmethod
    async def _commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError


class InMemoryUnitOfWork(AbstractUnitOfWork):
    def __init__(self) -> None:
        self.repo: InMemoryRepo = InMemoryRepo()

    async def _commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass


class SQLAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self) -> None:
        self.engine = create_async_engine(settings.ENGINE_STRING)  # , echo=True

    def create_session(self) -> tp.Any:
        async_session = orm.sessionmaker(  # type: ignore
            bind=self.engine, expire_on_commit=False, class_=AsyncSession
        )
        return async_session

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        async_session = self.create_session()
        session = async_session()
        self.repo = SQLAlchemyRepo(session=session)
        return self

    async def __aexit__(
        self, exn_type: tp.Any, exn_value: tp.Any, traceback: tp.Any
    ) -> None:
        if exn_type is None:
            await self._commit()
        else:
            print(exn_type)
            print(exn_value)
            print(traceback.print_exc())
            print("UoW error")
            await self.rollback()
        await self.repo.session.close()  # type: ignore
        self.repo.session = None  # type: ignore

    async def _commit(self) -> None:
        await self.repo.session.commit()  # type: ignore  # noqa

    async def rollback(self) -> None:
        await self.repo.session.rollback()  # type: ignore  # noqa
