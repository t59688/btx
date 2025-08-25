"""
为所有表添加软删除字段和更新时间字段的迁移脚本
"""
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy import inspect
import logging
import sqlalchemy
import re

from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建引擎
engine = create_engine(settings.DATABASE_URI, echo=False)
metadata = MetaData()

# 检查SQLAlchemy版本
SQLALCHEMY_VERSION = sqlalchemy.__version__
logger.info(f"SQLAlchemy版本: {SQLALCHEMY_VERSION}")
MAJOR_VERSION = int(SQLALCHEMY_VERSION.split('.')[0])


def migrate_database():
    """添加is_deleted和updated_at字段到所有表"""
    # 使用新API获取inspector
    inspector = inspect(engine)
    
    # 检测数据库类型
    db_type = engine.dialect.name
    logger.info(f"检测到数据库类型: {db_type}")
    
    # 获取所有表名并过滤系统表
    all_tables = inspector.get_table_names()
    schema_tables = []
    
    # 过滤系统表
    table_names = []
    for t in all_tables:
        # 排除可能的系统表
        if not (t.startswith('sqlite_') or t.startswith('pg_') or t.startswith('information_schema') or t == 'alembic_version'):
            table_names.append(t)
    
    logger.info(f"找到用户表: {', '.join(table_names)}")
    
    success_count = 0
    error_count = 0
    already_exists_deleted = 0
    already_exists_updated = 0
    
    # 开始执行SQL
    with engine.connect() as conn:
        # 对于MySQL，处理表名的特殊引用
        if db_type == 'mysql':
            quote_char = "`"
        else:
            quote_char = '"'
        
        for table_name in table_names:
            # 检查表结构
            columns = inspector.get_columns(table_name)
            column_names = [column['name'] for column in columns]
            
            # 检查表是否已有所需的列
            is_deleted_exists = 'is_deleted' in column_names
            updated_at_exists = 'updated_at' in column_names
            
            if is_deleted_exists and updated_at_exists:
                logger.info(f"表 {table_name} 已有所需的所有列")
                already_exists_deleted += 1
                already_exists_updated += 1
                continue
                
            logger.info(f"正在处理表: {table_name}")
            modified = False
            
            # 根据不同数据库类型使用不同的SQL语法
            try:
                # 开始事务
                trans = conn.begin()
                
                try:
                    # 添加is_deleted列（如果需要）
                    if not is_deleted_exists:
                        logger.info(f"  添加 is_deleted 列到 {table_name}")
                        
                        if db_type == 'mysql':
                            # MySQL语法
                            quoted_table = f"{quote_char}{table_name}{quote_char}"
                            add_column_sql = text(f"ALTER TABLE {quoted_table} ADD COLUMN {quote_char}is_deleted{quote_char} BOOLEAN NOT NULL DEFAULT FALSE")
                            conn.execute(add_column_sql)
                            
                            index_name = f"idx_{table_name}_is_deleted"
                            create_index_sql = text(f"CREATE INDEX {quote_char}{index_name}{quote_char} ON {quoted_table} ({quote_char}is_deleted{quote_char})")
                            conn.execute(create_index_sql)
                        
                        elif db_type == 'postgresql':
                            # PostgreSQL语法
                            quoted_table = f'{quote_char}{table_name}{quote_char}'
                            add_column_sql = text(f"ALTER TABLE {quoted_table} ADD COLUMN {quote_char}is_deleted{quote_char} BOOLEAN NOT NULL DEFAULT FALSE")
                            conn.execute(add_column_sql)
                            
                            index_name = f"idx_{table_name}_is_deleted"
                            create_index_sql = text(f"CREATE INDEX {quote_char}{index_name}{quote_char} ON {quoted_table} ({quote_char}is_deleted{quote_char})")
                            conn.execute(create_index_sql)
                        
                        elif db_type == 'sqlite':
                            # SQLite语法 - 注意SQLite的ALTER TABLE限制
                            quoted_table = f'{quote_char}{table_name}{quote_char}'
                            add_column_sql = text(f"ALTER TABLE {quoted_table} ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT 0")
                            conn.execute(add_column_sql)
                            
                            # SQLite中添加完列后创建索引
                            index_name = f"idx_{table_name}_is_deleted"
                            create_index_sql = text(f"CREATE INDEX {quote_char}{index_name}{quote_char} ON {quoted_table} (is_deleted)")
                            conn.execute(create_index_sql)
                        
                        else:
                            # 通用语法尝试
                            quoted_table = f'{quote_char}{table_name}{quote_char}'
                            add_column_sql = text(f"ALTER TABLE {quoted_table} ADD COLUMN {quote_char}is_deleted{quote_char} BOOLEAN NOT NULL DEFAULT FALSE")
                            conn.execute(add_column_sql)
                            
                            index_name = f"idx_{table_name}_is_deleted"
                            create_index_sql = text(f"CREATE INDEX {quote_char}{index_name}{quote_char} ON {quoted_table} ({quote_char}is_deleted{quote_char})")
                            conn.execute(create_index_sql)
                        
                        modified = True
                    else:
                        already_exists_deleted += 1
                        logger.info(f"  表 {table_name} 已有 is_deleted 列")
                    
                    # 添加updated_at列（如果需要）
                    if not updated_at_exists:
                        logger.info(f"  添加 updated_at 列到 {table_name}")
                        
                        if db_type == 'mysql':
                            # MySQL语法 - 使用ON UPDATE特性
                            quoted_table = f"{quote_char}{table_name}{quote_char}"
                            add_column_sql = text(f"ALTER TABLE {quoted_table} ADD COLUMN {quote_char}updated_at{quote_char} DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
                            conn.execute(add_column_sql)
                        
                        elif db_type == 'postgresql':
                            # PostgreSQL语法 - 需要创建触发器来实现自动更新
                            quoted_table = f'{quote_char}{table_name}{quote_char}'
                            
                            # 添加列
                            add_column_sql = text(f"ALTER TABLE {quoted_table} ADD COLUMN {quote_char}updated_at{quote_char} TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP")
                            conn.execute(add_column_sql)
                            
                            # 创建自动更新触发器函数(如果不存在)
                            trigger_function_sql = text("""
                                CREATE OR REPLACE FUNCTION update_timestamp()
                                RETURNS TRIGGER AS $$
                                BEGIN
                                    NEW.updated_at = CURRENT_TIMESTAMP;
                                    RETURN NEW;
                                END;
                                $$ LANGUAGE plpgsql;
                            """)
                            conn.execute(trigger_function_sql)
                            
                            # 创建触发器
                            trigger_name = f"trg_upd_{table_name}"
                            create_trigger_sql = text(f"""
                                DROP TRIGGER IF EXISTS {quote_char}{trigger_name}{quote_char} ON {quoted_table};
                                CREATE TRIGGER {quote_char}{trigger_name}{quote_char}
                                BEFORE UPDATE ON {quoted_table}
                                FOR EACH ROW EXECUTE PROCEDURE update_timestamp();
                            """)
                            conn.execute(create_trigger_sql)
                        
                        elif db_type == 'sqlite':
                            # SQLite不支持ON UPDATE，使用普通的列
                            quoted_table = f'{quote_char}{table_name}{quote_char}'
                            add_column_sql = text(f"ALTER TABLE {quoted_table} ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP")
                            conn.execute(add_column_sql)
                            
                            # 注意：SQLite需要通过触发器或应用代码实现自动更新
                            # 这里为简化只设置默认值
                        
                        else:
                            # 通用语法尝试
                            quoted_table = f'{quote_char}{table_name}{quote_char}'
                            add_column_sql = text(f"ALTER TABLE {quoted_table} ADD COLUMN {quote_char}updated_at{quote_char} TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP")
                            conn.execute(add_column_sql)
                        
                        modified = True
                    else:
                        already_exists_updated += 1
                        logger.info(f"  表 {table_name} 已有 updated_at 列")
                    
                    # 如果表被修改，计数
                    if modified:
                        success_count += 1
                        logger.info(f"✅ 表 {table_name} 处理成功")
                    
                    # 提交事务
                    trans.commit()
                
                except Exception as e:
                    # 回滚事务
                    trans.rollback()
                    error_count += 1
                    logger.error(f"❌ 表 {table_name} 处理失败: {str(e)}")
            
            except Exception as outer_e:
                error_count += 1
                logger.error(f"❌❌ 处理表 {table_name} 时发生严重错误: {str(outer_e)}")
    
    # 汇总结果
    logger.info(f"\n迁移完成! 结果统计:\n"
                f"成功修改的表: {success_count}\n"
                f"已有is_deleted列的表: {already_exists_deleted}\n"
                f"已有updated_at列的表: {already_exists_updated}\n"
                f"处理失败的表: {error_count}\n"
                f"总表数: {len(table_names)}")
    
    if error_count > 0:
        logger.warning("某些表未能成功修改，请查看日志了解详情。")
    else:
        logger.info("所有表都已成功处理！")


if __name__ == "__main__":
    try:
        migrate_database()
    except Exception as e:
        logger.error(f"执行迁移脚本失败: {str(e)}")
        import sys
        sys.exit(1) 