"""
为所有MySQL表添加软删除字段和更新时间字段的迁移脚本
专门解决MySQL数据库的兼容性问题
"""
import logging
import pymysql
from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_mysql_connection():
    """创建MySQL数据库连接"""
    # 从DATABASE_URI解析连接信息
    # 格式: mysql+pymysql://user:password@host:port/dbname
    db_uri = settings.DATABASE_URI
    
    # 提取用户名、密码、主机、端口和数据库名
    if 'mysql+pymysql://' in db_uri:
        db_uri = db_uri.replace('mysql+pymysql://', '')
    elif 'mysql://' in db_uri:
        db_uri = db_uri.replace('mysql://', '')
    
    # 分离用户认证和主机部分
    auth_host_db = db_uri.split('@')
    if len(auth_host_db) != 2:
        raise ValueError(f"数据库URI格式无效: {db_uri}")
    
    # 提取用户名和密码
    auth_part = auth_host_db[0]
    user_pass = auth_part.split(':')
    username = user_pass[0]
    password = user_pass[1] if len(user_pass) > 1 else ''
    
    # 提取主机、端口和数据库名
    host_db_part = auth_host_db[1]
    host_port_db = host_db_part.split('/')
    if len(host_port_db) < 2:
        raise ValueError(f"数据库URI中缺少数据库名: {db_uri}")
    
    host_port = host_port_db[0].split(':')
    host = host_port[0]
    port = int(host_port[1]) if len(host_port) > 1 else 3306
    database = host_port_db[1]
    
    # 移除URI参数(如果有)
    if '?' in database:
        database = database.split('?')[0]
    
    # 创建连接
    logger.info(f"连接到MySQL数据库: {username}@{host}:{port}/{database}")
    return pymysql.connect(
        host=host,
        user=username,
        password=password,
        database=database,
        port=port,
        charset='utf8mb4'
    )


def migrate_database():
    """为所有表添加软删除字段和updated_at字段"""
    try:
        # 创建数据库连接
        conn = create_mysql_connection()
        cursor = conn.cursor()
        
        try:
            # 获取所有用户表
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            logger.info(f"找到表: {', '.join(table_names)}")
            
            success_count = 0
            error_count = 0
            already_exists_deleted = 0
            already_exists_updated = 0
            
            for table_name in table_names:
                modified = False
                try:
                    # 检查表是否已有is_deleted列
                    cursor.execute(f"SHOW COLUMNS FROM `{table_name}` LIKE 'is_deleted'")
                    is_deleted_exists = cursor.fetchone() is not None
                    
                    # 检查表是否已有updated_at列
                    cursor.execute(f"SHOW COLUMNS FROM `{table_name}` LIKE 'updated_at'")
                    updated_at_exists = cursor.fetchone() is not None
                    
                    if is_deleted_exists and updated_at_exists:
                        logger.info(f"表 `{table_name}` 已有所需的所有列")
                        already_exists_deleted += 1
                        already_exists_updated += 1
                        continue
                    
                    logger.info(f"正在处理表: `{table_name}`")
                    
                    # 添加is_deleted列（如果需要）
                    if not is_deleted_exists:
                        logger.info(f"  添加 is_deleted 列到 `{table_name}`")
                        cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN `is_deleted` BOOLEAN NOT NULL DEFAULT FALSE")
                        cursor.execute(f"CREATE INDEX `idx_{table_name}_is_deleted` ON `{table_name}` (`is_deleted`)")
                        modified = True
                    else:
                        already_exists_deleted += 1
                        logger.info(f"  表 `{table_name}` 已有 is_deleted 列")
                    
                    # 添加updated_at列（如果需要）
                    if not updated_at_exists:
                        logger.info(f"  添加 updated_at 列到 `{table_name}`")
                        # 设置默认值为当前时间，与created_at保持一致
                        cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
                        modified = True
                    else:
                        already_exists_updated += 1
                        logger.info(f"  表 `{table_name}` 已有 updated_at 列")
                    
                    # 如果表被修改，标记成功
                    if modified:
                        success_count += 1
                        logger.info(f"✅ 表 `{table_name}` 处理成功")
                    
                    # 提交当前表的更改
                    conn.commit()
                
                except Exception as e:
                    error_count += 1
                    logger.error(f"❌ 表 `{table_name}` 处理失败: {str(e)}")
                    # 继续处理下一个表
                    conn.rollback()
                    continue
            
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
        
        finally:
            cursor.close()
            conn.close()
    
    except Exception as e:
        logger.error(f"执行迁移脚本失败: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        migrate_database()
    except Exception as e:
        logger.error(f"执行迁移脚本失败: {str(e)}")
        import sys
        sys.exit(1) 