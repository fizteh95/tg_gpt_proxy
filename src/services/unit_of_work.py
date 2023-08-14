import asyncio
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
from src.settings import logger


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


# class SQLAlchemyUnitOfWork(AbstractUnitOfWork):
#     def __init__(self) -> None:
#         self.engine = create_async_engine(settings.ENGINE_STRING)  # , echo=True
#
#     def create_session(self) -> tp.Any:
#         async_session = orm.sessionmaker(  # type: ignore
#             bind=self.engine, expire_on_commit=False, class_=AsyncSession
#         )
#         return async_session
#
#     async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
#         async_session = self.create_session()
#         session = async_session()
#         self.repo = SQLAlchemyRepo(session=session)
#         return self
#
#     async def __aexit__(
#         self, exn_type: tp.Any, exn_value: tp.Any, traceback: tp.Any
#     ) -> None:
#         if exn_type is None:
#             await self._commit()
#         else:
#             logger.error("UoW error")
#             logger.error(exn_type)
#             logger.error(exn_value)
#             logger.error(traceback)
#             await self.rollback()
#         await self.repo.session.close()  # type: ignore
#         self.repo.session = None  # type: ignore
#
#     async def _commit(self) -> None:
#         await self.repo.session.commit()  # type: ignore  # noqa
#
#     async def rollback(self) -> None:
#         await self.repo.session.rollback()  # type: ignore  # noqa


class SQLAlchemyUnitOfWorkInner(AbstractUnitOfWork):
    def __init__(self) -> None:
        self.engine = create_async_engine(
            settings.ENGINE_STRING,
            # echo=True,
            pool_pre_ping=True,
            # poolclass=NullPool
            pool_recycle=600,
            pool_size=20,
            max_overflow=10,
        )
        self.session_factory = self.create_session()

    def create_session(self) -> tp.Any:
        async_session = orm.sessionmaker(  # type: ignore
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
        return async_session

    async def __aenter__(self) -> "SQLAlchemyUnitOfWorkInner":
        async_session = self.session_factory()
        self.session = async_session
        self.repo = SQLAlchemyRepo(session=self.session)
        return self

    async def __aexit__(
        self, exn_type: tp.Any, exn_value: tp.Any, traceback: tp.Any
    ) -> None:
        try:
            if exn_type is None:
                await self.session.commit()
            else:
                await self.session.rollback()
                raise exn_type(exn_value)
        except Exception as e:
            logger.warning(f"Exception in aexit: {e}")
        finally:
            if self.session is None:
                logger.warning("Session is None on aexit")
            else:
                logger.debug("Closing session")
                await asyncio.shield(self.session.close())

    async def _commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()


class SQLAlchemyUnitOfWork:
    async def __aenter__(self) -> AbstractUnitOfWork:
        self.uow = SQLAlchemyUnitOfWorkInner()
        await self.uow.__aenter__()
        return self.uow

    async def __aexit__(
        self, exc_type: tp.Any, exc_val: tp.Any, exc_tb: tp.Any
    ) -> None:
        await self.uow.__aexit__(exc_type, exc_val, exc_tb)
