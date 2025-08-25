from sqlalchemy.orm import Query
from sqlalchemy import inspect
from typing import Type, Any, Optional

from app.models.base_model import BaseModel


def filter_deleted(query: Query, model_class: Type[Any]) -> Query:
    """
    过滤已删除的记录
    如果模型继承了BaseModel，添加is_deleted=False过滤条件
    """
    if hasattr(model_class, 'is_deleted'):
        query = query.filter(model_class.is_deleted == False)
    return query


def get_base_query(db_session, model_class: Type[Any]) -> Query:
    """
    获取基础查询，自动过滤已删除的记录
    """
    query = db_session.query(model_class)
    return filter_deleted(query, model_class)


def soft_delete(db_session, model_instance: BaseModel) -> bool:
    """
    软删除记录
    """
    if not hasattr(model_instance, 'is_deleted'):
        # 如果模型不支持软删除，则返回False
        return False
    
    model_instance.is_deleted = True
    db_session.commit()
    return True 