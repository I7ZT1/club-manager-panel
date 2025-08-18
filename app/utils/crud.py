from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, Literal
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class FilterCondition(BaseModel):
    field: str
    op: Literal[
        'eq', 'ne', 'lt', 'lte', 'gt', 'gte', 
        'in', 'not_in', 'like', 'between', 'is_null'
    ]
    value: Any
    

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]) -> None:
        self._model = model

    async def create(
        self, session: AsyncSession, obj_in: CreateSchemaType
    ) -> ModelType:
        obj_in_data = dict(obj_in)
        db_obj = self._model(**obj_in_data)
        session.add(db_obj)
        await session.commit()
        return db_obj

    def apply_filters(self, query, filters: Optional[List[FilterCondition]]) -> Any:
        if not filters:
            return query

        for cond in filters:
            attr = cond.field
            op = cond.op.lower()
            value = cond.value

            column = getattr(self._model, attr, None)
            if column is None:
                continue

            if isinstance(value, str):
                try:
                    if hasattr(column.type, 'python_type') and column.type.python_type in (datetime,):
                        value = datetime.fromisoformat(value)
                except Exception:
                    pass

            # Новая магия ✨
            if op == "eq":
                query = query.filter(column == value)
            elif op == "ne":
                query = query.filter(column != value)
            elif op in ("gt", "greater", "more"):
                query = query.filter(column > value)
            elif op in ("lt", "less"):
                query = query.filter(column < value)
            elif op in ("gte", "ge"):
                query = query.filter(column >= value)
            elif op in ("lte", "le"):
                query = query.filter(column <= value)
            elif op == "in":
                if isinstance(value, (list, tuple, set)):
                    query = query.filter(column.in_(value))
                else:
                    query = query.filter(column.in_(str(value).split(",")))
            elif op == "not_in":
                if isinstance(value, (list, tuple, set)):
                    query = query.filter(~column.in_(value))
                else:
                    query = query.filter(~column.in_(str(value).split(",")))
            elif op == "like":
                query = query.filter(column.like(value))
            elif op == "between":
                if isinstance(value, (list, tuple)) and len(value) == 2:
                    query = query.filter(column.between(value[0], value[1]))
            elif op == "is_null":
                if value is True:
                    query = query.filter(column.is_(None))
                elif value is False:
                    query = query.filter(column.is_not(None))

        return query

    def apply_order_by(self, query, order_by: Optional[list] = None) -> Any:
        if not order_by:
            return query

        order_clauses = []
        for field in order_by:
            # Преобразуем поле в строку, если это не строка
            field_str = str(field)
            
            if field_str.startswith('-'):
                # Сортировка по убыванию
                column = getattr(self._model, field_str[1:], None)
                if column is not None:
                    order_clauses.append(column.desc())
            elif field_str.startswith('+'):
                # Сортировка по возрастанию (явно указано)
                column = getattr(self._model, field_str[1:], None)
                if column is not None:
                    order_clauses.append(column.asc())
            else:
                # Сортировка по возрастанию (по умолчанию)
                column = getattr(self._model, field_str, None)
                if column is not None:
                    order_clauses.append(column.asc())

        if order_clauses:
            query = query.order_by(*order_clauses)
        return query

    async def count(self, session: AsyncSession, *args, **kwargs) -> int:
        # Преобразуем datetime объекты в naive datetime
        for key, value in kwargs.items():
            if isinstance(value, datetime) and value.tzinfo is not None:
                kwargs[key] = value.replace(tzinfo=None)
        
        query = select(func.count()).select_from(self._model).filter(*args).filter_by(**kwargs)
        result = await session.execute(query)
        return result.scalar_one()

    async def get(self, session: AsyncSession, order_by: Optional[list] = None, *args, **kwargs) -> Optional[ModelType]:
        query = select(self._model).filter(*args).filter_by(**kwargs)
        if order_by:
            query = query.order_by(*order_by)
        else:
            pass  # По умолчанию

        result = await session.execute(
            query
        )
        return result.scalars().first()

    async def get_multi(
        self, session: AsyncSession, 
        filter_list: Optional[List[FilterCondition]] = None, 
        offset: int = 0, limit: int = 90000, 
        order_by: Optional[list] = None
    ) -> List[ModelType]:
        query = select(self._model)
        query = self.apply_filters(query, filter_list)
        query = self.apply_order_by(query, order_by)
        
        result = await session.execute(
            query.offset(offset).limit(limit)
        )
        return result.scalars().all()


    async def update(
        self,
        session: AsyncSession,
        obj_id: int,
        *,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        db_obj: Optional[ModelType] = None,
        **kwargs
    ) -> Optional[ModelType]:
        # Если db_obj не передан, получаем его по id
        if db_obj is None:
            db_obj = await self.get(session, id=obj_id)
            if db_obj is None:
                return None

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
            
        for field in update_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
                
        session.add(db_obj)
        await session.commit()
        return db_obj


    async def delete(
        self, session: AsyncSession, *args, db_obj: Optional[ModelType] = None, **kwargs
    ) -> ModelType:
        db_obj = db_obj or await self.get(session, *args, **kwargs)
        await session.delete(db_obj)
        await session.commit()
        return db_obj