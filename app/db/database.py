from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.settings import settings


class DBDependency:
    """Класс для управления зависимостями базы данных, используя SQLAlchemy."""

    def __init__(self):
        """
        Инициализирует экземпляр класса,
        отвечающего за взаимодействие с асинхронной базой данных.
        """
        self._engine: AsyncEngine = create_async_engine(
            url=settings.db_settings.async_db_url,
            echo=settings.db_settings.db_echo,
        )
        self._session_factory: async_sessionmaker[AsyncSession] = (
            async_sessionmaker(
                bind=self._engine,
                expire_on_commit=False,
            )
        )

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Создает асинхронные сессии базы данных."""
        return self._session_factory

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    async def close(self) -> None:
        await self._engine.dispose()


db_dependency = DBDependency()


async def get_db_session():
    async with db_dependency.session_factory() as session:
        yield session
