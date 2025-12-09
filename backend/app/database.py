from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://xuanfeng_dev:xuanfengkeji2025%25@rm-bp1jldp727lmxq1m57o.mysql.rds.aliyuncs.com:3306/xinhua_dev?charset=utf8mb4")

# 创建数据库引擎 - 使用MySQL
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    echo=False,
    connect_args={
        "charset": "utf8mb4",
        "use_unicode": True
    }
)

# 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
