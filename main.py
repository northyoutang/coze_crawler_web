"""
FastAPI 主程序 - 扣子技能爬取管理系统（简化版，无需 msToken）
"""
import os
import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import threading

from database import engine, get_db, Base
from models import Keyword, CrawlRecord, Setting
from schemas import (
    LoginRequest, KeywordCreate, KeywordUpdate, KeywordResponse,
    CrawlRecordResponse, SchedulerSettings, SchedulerStatus,
    CrawlProgress, FileNode
)
from auth import (
    verify_credentials, create_session, destroy_session,
    is_session_valid, require_auth, get_session_from_request
)
from scheduler import (
    init_scheduler, update_scheduler_settings, get_next_run_time,
    manual_crawl_task, get_crawl_progress, crawl_status
)

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="扣子技能爬取管理系统", version="2.0.0")

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件和模板
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 修复 Jinja2 兼容性问题
from jinja2 import Environment, FileSystemLoader
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True
)

def render_template(template_name: str, context: dict):
    """渲染模板"""
    template = jinja_env.get_template(template_name)
    return HTMLResponse(template.render(context))

# 初始化默认关键词和设置
def init_default_data():
    """初始化默认数据"""
    db = next(get_db())
    try:
        # 检查是否有关键词
        keyword_count = db.query(Keyword).count()
        if keyword_count == 0:
            default_keywords = ["即梦", "足球", "image2", "图", "童年"]
            for kw in default_keywords:
                db.add(Keyword(keyword=kw))
            db.commit()
            print(f"已初始化默认关键词: {default_keywords}")

        # 检查是否有设置
        setting_count = db.query(Setting).count()
        if setting_count == 0:
            db.add(Setting(
                crawl_interval_hours=1,
                is_scheduler_enabled=True,
            ))
            db.commit()
            print("已初始化默认设置")

    except Exception as e:
        print(f"初始化数据失败: {str(e)}")
    finally:
        db.close()


# 启动时初始化
@app.on_event("startup")
async def startup_event():
    """启动事件"""
    init_default_data()
    init_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    from scheduler import shutdown_scheduler
    shutdown_scheduler()


# ==================== 页面路由 ====================

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """登录页面"""
    session_token = await get_session_from_request(request)
    if is_session_valid(session_token):
        return Response(status_code=302, headers={"Location": "/"})
    return render_template("login.html", {"request": request})


@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    """主页面"""
    session_token = await get_session_from_request(request)
    if not is_session_valid(session_token):
        return Response(status_code=302, headers={"Location": "/login"})
    return render_template("index.html", {"request": request})


# ==================== 认证接口 ====================

@app.post("/api/login")
async def login(request: LoginRequest, response: Response):
    """登录接口"""
    if verify_credentials(request.username, request.password):
        session_token = create_session()
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            max_age=86400 * 7,  # 7天
            path="/"
        )
        return {"success": True, "message": "登录成功", "token": session_token}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )


@app.post("/api/logout")
async def logout(request: Request, response: Response):
    """登出接口"""
    session_token = await get_session_from_request(request)
    if session_token:
        destroy_session(session_token)
    response.delete_cookie("session_token")
    return {"success": True, "message": "已登出"}


@app.get("/api/auth/status")
async def auth_status(request: Request):
    """检查登录状态"""
    session_token = await get_session_from_request(request)
    return {"is_logged_in": is_session_valid(session_token)}


# ==================== 主题词管理接口 ====================

@app.get("/api/keywords", response_model=List[KeywordResponse])
async def get_keywords(db: Session = Depends(get_db), auth: bool = Depends(require_auth)):
    """获取所有主题词"""
    keywords = db.query(Keyword).order_by(Keyword.created_at.desc()).all()
    return keywords


@app.post("/api/keywords", response_model=KeywordResponse)
async def create_keyword(keyword: KeywordCreate, db: Session = Depends(get_db), auth: bool = Depends(require_auth)):
    """新增主题词"""
    existing = db.query(Keyword).filter(Keyword.keyword == keyword.keyword).first()
    if existing:
        raise HTTPException(status_code=400, detail="该主题词已存在")

    db_keyword = Keyword(keyword=keyword.keyword)
    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)
    return db_keyword


@app.put("/api/keywords/{keyword_id}", response_model=KeywordResponse)
async def update_keyword(keyword_id: int, keyword: KeywordUpdate, db: Session = Depends(get_db), auth: bool = Depends(require_auth)):
    """更新主题词"""
    db_keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not db_keyword:
        raise HTTPException(status_code=404, detail="主题词不存在")

    existing = db.query(Keyword).filter(Keyword.keyword == keyword.keyword, Keyword.id != keyword_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="该主题词已存在")

    db_keyword.keyword = keyword.keyword
    db_keyword.updated_at = datetime.datetime.now()
    db.commit()
    db.refresh(db_keyword)
    return db_keyword


@app.delete("/api/keywords/{keyword_id}")
async def delete_keyword(keyword_id: int, db: Session = Depends(get_db), auth: bool = Depends(require_auth)):
    """删除主题词"""
    db_keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not db_keyword:
        raise HTTPException(status_code=404, detail="主题词不存在")

    db.delete(db_keyword)
    db.commit()
    return {"success": True, "message": "删除成功"}


# ==================== 定时任务接口 ====================

@app.get("/api/scheduler/settings", response_model=SchedulerSettings)
async def get_scheduler_settings(db: Session = Depends(get_db), auth: bool = Depends(require_auth)):
    """获取定时任务设置"""
    setting = db.query(Setting).first()
    if not setting:
        setting = Setting(crawl_interval_hours=1, is_scheduler_enabled=True)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return SchedulerSettings(
        crawl_interval_hours=setting.crawl_interval_hours,
        is_scheduler_enabled=setting.is_scheduler_enabled,
    )


@app.post("/api/scheduler/settings")
async def update_settings(settings: SchedulerSettings, db: Session = Depends(get_db), auth: bool = Depends(require_auth)):
    """更新定时任务设置"""
    setting = db.query(Setting).first()
    if not setting:
        setting = Setting()
        db.add(setting)

    setting.crawl_interval_hours = settings.crawl_interval_hours
    setting.is_scheduler_enabled = settings.is_scheduler_enabled
    db.commit()

    # 更新调度器
    update_scheduler_settings(settings.crawl_interval_hours, settings.is_scheduler_enabled)

    return {"success": True, "message": "设置已更新"}


@app.get("/api/scheduler/status", response_model=SchedulerStatus)
async def get_scheduler_status(db: Session = Depends(get_db), auth: bool = Depends(require_auth)):
    """获取定时任务状态"""
    setting = db.query(Setting).first()
    next_run = get_next_run_time()

    return SchedulerStatus(
        is_enabled=setting.is_scheduler_enabled if setting else False,
        interval_hours=setting.crawl_interval_hours if setting else 1,
        next_run_time=next_run,
        is_running=crawl_status["is_running"],
    )


# ==================== 爬取接口 ====================

@app.post("/api/crawl/manual")
async def start_manual_crawl(keyword: Optional[str] = None, auth: bool = Depends(require_auth)):
    """手动触发爬取"""
    if crawl_status["is_running"]:
        raise HTTPException(status_code=400, detail="已有爬取任务正在运行")

    # 在后台线程中执行爬取
    thread = threading.Thread(target=manual_crawl_task, args=(keyword,))
    thread.daemon = True
    thread.start()

    return {"success": True, "message": "爬取任务已启动"}


@app.get("/api/crawl/progress", response_model=CrawlProgress)
async def get_crawl_status(auth: bool = Depends(require_auth)):
    """获取爬取进度"""
    progress = get_crawl_progress()
    return CrawlProgress(
        is_running=progress["is_running"],
        current_keyword=progress["current_keyword"],
        current_page=progress["current_page"],
        total_pages=progress["total_pages"],
        skills_found=progress["skills_found"],
        logs=progress["logs"][-50:],  # 返回最近50条日志
    )


@app.get("/api/crawl/history", response_model=List[CrawlRecordResponse])
async def get_crawl_history(limit: int = 20, db: Session = Depends(get_db), auth: bool = Depends(require_auth)):
    """获取爬取历史"""
    records = db.query(CrawlRecord).order_by(CrawlRecord.crawl_time.desc()).limit(limit).all()
    return records


# ==================== 文件管理接口 ====================

def scan_directory(path: str, relative_path: str = ""):
    """递归扫描目录并构建文件树"""
    children = []
    try:
        for item in sorted(os.listdir(path)):
            item_path = os.path.join(path, item)
            # 构建相对路径，确保使用正斜杠 / 用于 URL
            if relative_path:
                item_relative = relative_path + "/" + item
            else:
                item_relative = item

            if os.path.isdir(item_path):
                children.append(FileNode(
                    name=item,
                    type="folder",
                    children=scan_directory(item_path, item_relative)
                ))
            elif item.endswith('.xlsx'):
                stat = os.stat(item_path)
                children.append(FileNode(
                    name=item,
                    type="file",
                    path=item_relative,
                    size=stat.st_size,
                    modified_time=datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                ))
    except Exception as e:
        print(f"扫描目录失败 {path}: {e}")

    return children


@app.get("/api/files/tree", response_model=List[FileNode])
async def get_file_tree(auth: bool = Depends(require_auth)):
    """获取文件目录树"""
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        return []

    return scan_directory(data_dir)


@app.get("/api/files/download")
async def download_file(path: str, auth: bool = Depends(require_auth)):
    """下载文件"""
    # 将 URL 路径的正斜杠转换为系统路径
    normalized_path = path.replace('/', os.sep)
    file_path = os.path.join("data", normalized_path) if not normalized_path.startswith("data") else normalized_path

    print(f"下载请求 - path参数: {path}")
    print(f"下载请求 - 文件路径: {file_path}")
    
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        print(f"错误: 文件不存在 {file_path}")
        raise HTTPException(status_code=404, detail=f"文件不存在: {path}")

    if not file_path.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="仅支持下载 Excel 文件")

    filename = os.path.basename(file_path)
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
