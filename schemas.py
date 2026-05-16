"""
Pydantic 数据模型
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


# 认证相关
class LoginRequest(BaseModel):
    username: str
    password: str


# 主题词相关
class KeywordBase(BaseModel):
    keyword: str


class KeywordCreate(KeywordBase):
    pass


class KeywordUpdate(KeywordBase):
    pass


class KeywordResponse(KeywordBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 爬取记录相关
class CrawlRecordResponse(BaseModel):
    id: int
    keyword: str
    file_path: str
    file_size: int
    skill_count: int
    status: str
    crawl_time: datetime

    class Config:
        from_attributes = True


# 调度器设置相关 - 简化版
class SchedulerSettings(BaseModel):
    crawl_interval_hours: int = 1
    is_scheduler_enabled: bool = True


# 调度器状态
class SchedulerStatus(BaseModel):
    is_enabled: bool
    interval_hours: int
    next_run_time: Optional[str] = None
    is_running: bool


# 爬取进度
class CrawlProgress(BaseModel):
    is_running: bool
    current_keyword: Optional[str] = None
    current_page: int
    total_pages: Optional[int] = None
    skills_found: int
    logs: List[str] = []


# 文件节点
class FileNode(BaseModel):
    name: str
    type: str  # 'folder' or 'file'
    children: Optional[List['FileNode']] = None
    path: Optional[str] = None
    size: Optional[int] = None
    modified_time: Optional[str] = None


FileNode.model_rebuild()
