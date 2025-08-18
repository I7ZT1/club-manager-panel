from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

# Создание асинхронного движка SQLAlchemy
engine = create_async_engine(
    settings.DB_URL,
    echo=False,  # Для логирования SQL-запросов
)

# Создание фабрики сессий
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Базовый класс для моделей ORM
from sqlalchemy.ext.declarative import as_declarative, declared_attr

@as_declarative()
class Base:
    id: any
    __name__: str

    # Генерация имени таблицы на основе имени класса, если не указано явно
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

# Функция для получения сессии
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
