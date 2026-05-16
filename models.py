"""
数据库模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from database import Base
import datetime


class Keyword(Base):
    """主题词表"""
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)


class CrawlRecord(Base):
    """爬取记录表"""
    __tablename__ = "crawl_records"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), index=True)
    file_path = Column(String(512))
    file_size = Column(Integer, default=0)
    skill_count = Column(Integer, default=0)
    status = Column(String(20))  # success, failed
    crawl_time = Column(DateTime, default=datetime.datetime.now)


class Setting(Base):
    """系统设置表 - 简化版（无需 msToken）"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    crawl_interval_hours = Column(Integer, default=1)  # 爬取间隔（小时）
    is_scheduler_enabled = Column(Boolean, default=True)  # 是否启用定时任务
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
