"""
定时任务调度模块 - 简化版（无需 msToken）
"""
import os
import datetime
from typing import Optional, List
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Keyword, CrawlRecord, Setting
from crawler import CozeSkillCrawler

# 全局调度器实例
scheduler: Optional[BackgroundScheduler] = None

# 爬取任务状态
crawl_status = {
    "is_running": False,
    "current_keyword": None,
    "current_page": 0,
    "total_pages": None,
    "skills_found": 0,
    "logs": [],
}


def log_crawl(message: str):
    """记录爬取日志"""
    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    log_msg = f"[{timestamp}] {message}"
    crawl_status["logs"].append(log_msg)
    # 保留最近100条日志
    if len(crawl_status["logs"]) > 100:
        crawl_status["logs"] = crawl_status["logs"][-100:]
    print(log_msg)


def crawl_keyword_task(keyword: str):
    """
    爬取单个关键词的任务

    Args:
        keyword: 关键词
    """
    db = SessionLocal()
    try:
        crawl_status["current_keyword"] = keyword
        crawl_status["logs"] = []

        # 创建爬虫实例（无需 msToken）
        def progress_callback(log_msg):
            log_crawl(log_msg)

        crawler = CozeSkillCrawler(
            request_interval=2.0,
            progress_callback=progress_callback,
            headless=True,
        )

        # 执行爬取
        log_crawl(f"开始爬取关键词: {keyword}")
        skills = crawler.crawl_keyword(keyword=keyword, max_scroll=15)

        crawl_status["skills_found"] = len(skills)
        log_crawl(f"关键词 '{keyword}' 爬取完成，共获取 {len(skills)} 个技能")

        # 使用新的保存方法
        output_path, skill_count = crawler.save_to_excel(skills, keyword)

        if output_path and skill_count > 0:
            file_size = os.path.getsize(output_path)

            # 记录爬取记录
            record = CrawlRecord(
                keyword=keyword,
                file_path=output_path,
                file_size=file_size,
                skill_count=skill_count,
                status="success",
            )
            db.add(record)
            db.commit()

            log_crawl(f"文件已保存: {output_path}")
        else:
            # 记录失败记录
            record = CrawlRecord(
                keyword=keyword,
                file_path="",
                file_size=0,
                skill_count=0,
                status="failed",
            )
            db.add(record)
            db.commit()

            log_crawl("保存失败或无数据")

    except Exception as e:
        log_crawl(f"爬取异常: {str(e)}")
        import traceback
        traceback.print_exc()

        # 记录失败记录
        try:
            record = CrawlRecord(
                keyword=keyword,
                file_path="",
                file_size=0,
                skill_count=0,
                status="failed",
            )
            db.add(record)
            db.commit()
        except:
            pass
    finally:
        db.close()


def scheduled_crawl_task():
    """定时爬取任务 - 爬取所有关键词"""
    if crawl_status["is_running"]:
        log_crawl("已有爬取任务在运行，跳过本次定时任务")
        return

    crawl_status["is_running"] = True
    crawl_status["current_keyword"] = None
    crawl_status["current_page"] = 0
    crawl_status["skills_found"] = 0
    crawl_status["logs"] = []

    db = SessionLocal()
    try:
        # 获取所有关键词
        keywords = db.query(Keyword).all()
        if not keywords:
            log_crawl("没有配置关键词，跳过爬取")
            return

        log_crawl(f"定时爬取任务开始，共 {len(keywords)} 个关键词")

        # 逐个爬取
        for kw in keywords:
            crawl_keyword_task(kw.keyword)

        log_crawl("定时爬取任务完成")

    except Exception as e:
        log_crawl(f"定时任务异常: {str(e)}")
    finally:
        crawl_status["is_running"] = False
        db.close()


def manual_crawl_task(keyword: Optional[str] = None) -> bool:
    """
    手动触发爬取任务

    Args:
        keyword: 指定关键词，None 表示爬取所有关键词

    Returns:
        是否成功启动
    """
    if crawl_status["is_running"]:
        return False

    crawl_status["is_running"] = True
    crawl_status["current_keyword"] = None
    crawl_status["current_page"] = 0
    crawl_status["skills_found"] = 0
    crawl_status["logs"] = []

    db = SessionLocal()
    try:
        # 获取关键词列表
        if keyword:
            keywords = [keyword]
        else:
            keywords = [kw.keyword for kw in db.query(Keyword).all()]

        if not keywords:
            log_crawl("没有配置关键词")
            crawl_status["is_running"] = False
            return False

        log_crawl(f"手动爬取任务开始，共 {len(keywords)} 个关键词")

        # 逐个爬取
        for kw in keywords:
            crawl_keyword_task(kw)

        log_crawl("手动爬取任务完成")

    except Exception as e:
        log_crawl(f"手动爬取异常: {str(e)}")
    finally:
        crawl_status["is_running"] = False
        db.close()

    return True


def init_scheduler():
    """初始化调度器"""
    global scheduler

    if scheduler is not None:
        return

    scheduler = BackgroundScheduler()

    db = SessionLocal()
    try:
        # 获取设置
        setting = db.query(Setting).first()
        if not setting:
            # 创建默认设置
            setting = Setting(
                crawl_interval_hours=1,
                is_scheduler_enabled=True,
            )
            db.add(setting)
            db.commit()

        interval_hours = setting.crawl_interval_hours
        is_enabled = setting.is_scheduler_enabled

        if is_enabled:
            # 添加定时任务 - 每 interval_hours 小时执行一次，整点开始
            scheduler.add_job(
                scheduled_crawl_task,
                trigger=CronTrigger(hour=f'*/{interval_hours}', minute=0),
                id='crawl_task',
                name='定时爬取任务',
                replace_existing=True,
            )
            scheduler.start()
            print(f"定时任务已启动，每 {interval_hours} 小时执行一次")
        else:
            print("定时任务未启用")

    except Exception as e:
        print(f"初始化调度器失败: {str(e)}")
    finally:
        db.close()


def update_scheduler_settings(interval_hours: int, is_enabled: bool):
    """更新调度器设置"""
    global scheduler

    if scheduler is None:
        scheduler = BackgroundScheduler()

    # 移除现有任务
    if scheduler.get_job('crawl_task'):
        scheduler.remove_job('crawl_task')

    if is_enabled:
        # 添加新任务
        scheduler.add_job(
            scheduled_crawl_task,
            trigger=CronTrigger(hour=f'*/{interval_hours}', minute=0),
            id='crawl_task',
            name='定时爬取任务',
            replace_existing=True,
        )
        if not scheduler.running:
            scheduler.start()
        print(f"定时任务已更新，每 {interval_hours} 小时执行一次")
    else:
        if scheduler.running:
            scheduler.shutdown(wait=False)
        print("定时任务已禁用")


def get_next_run_time() -> Optional[str]:
    """获取下一次执行时间"""
    global scheduler
    if scheduler and scheduler.running:
        job = scheduler.get_job('crawl_task')
        if job and job.next_run_time:
            return job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
    return None


def get_crawl_progress() -> dict:
    """获取爬取进度"""
    return crawl_status.copy()


def shutdown_scheduler():
    """关闭调度器"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        print("调度器已关闭")
