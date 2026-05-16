"""
Pydantic模型（请求/响应校验）
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class KeywordBase(BaseModel):
    """主题词基础模型"""
    keyword: str


class KeywordCreate(KeywordBase):
    """创建主题词"""
    pass


class KeywordUpdate(KeywordBase):
    """更新主题词"""
    pass


class KeywordResponse(KeywordBase):
    """主题词响应"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CrawlRecordResponse(BaseModel):
    """爬取记录响应"""
    id: int
    keyword: str
    file_path: str
    file_size: int
    skill_count: int
    crawl_time: datetime
    status: str

    class Config:
        from_attributes = True


class SchedulerSettings(BaseModel):
    """定时任务设置"""
    crawl_interval_hours: int
    is_scheduler_enabled: bool
    ms_token: Optional[str] = ""
    a_bogus: Optional[str] = ""


class SchedulerStatus(BaseModel):
    """定时任务状态"""
    is_enabled: bool
    interval_hours: int
    next_run_time: Optional[str]
    is_running: bool


class CrawlProgress(BaseModel):
    """爬取进度"""
    is_running: bool
    current_keyword: Optional[str]
    current_page: int
    total_pages: Optional[int]
    skills_found: int
    logs: List[str]


class FileNode(BaseModel):
    """文件节点"""
    name: str
    type: str  # folder/file
    path: Optional[str] = None
    children: Optional[List["FileNode"]] = None
    size: Optional[int] = None
    modified_time: Optional[str] = None


FileNode.model_rebuild()
