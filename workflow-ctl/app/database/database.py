from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 确保 data 目录存在
data_dir = Path(__file__).parent.parent.parent / "data"
data_dir.mkdir(exist_ok=True)

# 数据库配置：优先从环境变量读取，否则使用 SQLite
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data/workflow.db"
)

# 根据数据库类型设置连接参数
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # MySQL 或其他数据库
    connect_args = {
        "charset": "utf8mb4",
        "use_unicode": True
    }

# 根据数据库类型设置引擎参数
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args=connect_args,
        echo=False
    )
else:
    # MySQL 或其他数据库
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=10,
        max_overflow=20,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """数据库会话依赖"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)

