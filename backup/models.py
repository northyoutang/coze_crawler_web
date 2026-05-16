"""
数据库模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger
from datetime import datetime
from database import Base


class Keyword(Base):
    """主题词表"""
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class CrawlRecord(Base):
    """爬取记录表"""
    __tablename__ = "crawl_records"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(100), index=True, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, default=0)
    skill_count = Column(Integer, default=0)
    crawl_time = Column(DateTime, default=datetime.now)
    status = Column(String(20), default="success")  # success/failed


class Setting(Base):
    """系统设置表"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    crawl_interval_hours = Column(Integer, default=1)  # 爬取间隔（小时）
    is_scheduler_enabled = Column(Boolean, default=True)  # 是否启用定时任务
    ms_token = Column(String(500), default="")  # Coze API msToken
    a_bogus = Column(String(200), default="")  # Coze API a_bogus参数
