#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建数据库表结构
"""

from app.database import engine, Base
from app.models import apikey, workflow, prompt, model_parameter, chat_log
import os
from dotenv import load_dotenv

def init_database():
    """初始化数据库表"""
    load_dotenv()
    
    print("正在创建数据库表...")
    
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("数据库表创建成功！")
        
        # 显示创建的表
        print("\n已创建的表:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
            
    except Exception as e:
        print(f"数据库表创建失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    init_database()
