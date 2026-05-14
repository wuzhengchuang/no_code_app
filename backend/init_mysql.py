#!/usr/bin/env python3
"""初始化MySQL数据库表"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.db.session import Base, engine

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")

engine.dispose()