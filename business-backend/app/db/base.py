# 导入所有模型，以便Alembic可以创建迁移
from app.db.session import Base
from app.models.user import User
from app.models.style import Style
from app.models.artwork import Artwork
from app.models.like import Like
from app.models.credit_record import CreditRecord
from app.models.system_config import SystemConfig
from app.models.admin import Admin
from app.models.product import Product
from app.models.order import Order 