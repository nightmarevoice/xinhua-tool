"""
初始化数据库脚本
"""
from app.database.database import engine, Base
from app.models import apikey, workflow, prompt, model_parameter

def init_database():
    """创建所有数据库表"""
    print("正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成！")

if __name__ == "__main__":
    init_database()














