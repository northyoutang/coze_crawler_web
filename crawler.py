
"""
Coze Skill 爬虫（稳定增强版）

优化内容：
1. 精准按 keyword 过滤接口
2. 不再依赖 msToken
3. 使用 Playwright 自动浏览器
4. 修复 response.json 页面关闭问题
5. 修复 React 输入框 fill() 无效问题
6. 自动滚动加载更多
7. skill 去重
8. Excel 导出
"""

import os
import time
import datetime

from typing import List, Dict, Optional, Callable, Any
from urllib.parse import urlparse, parse_qs, unquote

import pandas as pd

from playwright.sync_api import (
    sync_playwright,
    Browser,
    Page,
    Playwright,
    Response
)


class CozeSkillCrawler:

    FIELD_NAMES_CN = {
        'name': '技能名称',
        'description': '简介',
        'developer': '开发者',
        'user_count': '用户数',
        'heat': '热度',
        'category': '分类',
        'show_version': '版本',
        'favorite_count': '收藏数',
        'is_free': '是否免费',
        'is_official': '是否官方',
        'price_amount': '价格',
        'labels': '标签',
        'listed_at': '上架时间',
    }

    def __init__(
        self,
        request_interval: float = 2.0,
        progress_callback: Optional[Callable] = None,
        headless: bool = True,
    ):

        self.request_interval = request_interval
        self.progress_callback = progress_callback
        self.headless = headless

        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

        self.logs = []

        self.current_keyword = ""

        self._api_responses: List[Response] = []

        self.seen_request_urls = set()

        self.fields = [
            'name',
            'developer',
            'user_count',
            'heat',
            'description',
            'category',
            'show_version',
            'favorite_count',
            'is_free',
            'is_official',
            'listed_at',
            'price_amount',
            'labels'
        ]

    # =========================================================
    # 日志
    # =========================================================

    def log(self, message: str):

        timestamp = datetime.datetime.now().strftime('%H:%M:%S')

        log_msg = f"[{timestamp}] {message}"

        self.logs.append(log_msg)

        if self.progress_callback:
            self.progress_callback(log_msg)

        print(log_msg)

    # =========================================================
    # 监听接口
    # =========================================================

    def _handle_api_response(self, response: Response):

        try:

            url = response.url

            # 只监听 product/list
            if 'product/list' not in url:
                return

            if response.status != 200:
                return

            # 去重
            if url in self.seen_request_urls:
                return

            self.seen_request_urls.add(url)

            parsed = urlparse(url)

            params = parse_qs(parsed.query)

            keyword = params.get("keyword", [""])[0]

            keyword = unquote(keyword).strip().lower()

            current_keyword = (
                self.current_keyword
                .strip()
                .lower()
            )

            # 只保留当前 keyword
            if keyword != current_keyword:
                return

            self._api_responses.append(response)

            self.log(
                f"✅ response.text: keyword={response.text}"
            )

        except Exception as e:

            self.log(
                f"⚠️ response监听失败: {str(e)}"
            )

    # =========================================================
    # 启动浏览器
    # =========================================================

    def start_browser(self):

        self.log("🚀 正在启动浏览器...")

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ]
        )

        context = self.browser.new_context(
            viewport={
                'width': 1920,
                'height': 1080
            },
            user_agent=(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
        )

        self.page = context.new_page()

        # 接口监听
        self.page.on(
            'response',
            self._handle_api_response
        )

        # 调试网络请求
        self.page.on(
            'request',
            lambda request: print(
                f"🌐 {request.method} {request.url[:120]}"
            )
        )

        self.log("✅ 浏览器启动成功")

    # =========================================================
    # 关闭浏览器
    # =========================================================

    def stop_browser(self):

        try:

            if self.page:
                self.page.close()

            if self.browser:
                self.browser.close()

            if self.playwright:
                self.playwright.stop()

            self.log("✅ 浏览器已关闭")

        except Exception as e:

            self.log(
                f"⚠️ 浏览器关闭失败: {str(e)}"
            )

    # =========================================================
    # skill 解析
    # =========================================================

    def extract_skill(self, item: Dict):

        try:

            meta_info = item.get('meta_info', {})

            skill_extra = item.get('skill_extra', {})

            category = meta_info.get('category', {})

            price_info = meta_info.get('price', {})

            result = {
                'name': meta_info.get('name', ''),
                'description': meta_info.get('description', ''),
                'developer': (
                    skill_extra.get('developer', '')
                    or meta_info.get('developer', '')
                ),
                'user_count': str(
                    skill_extra.get('installer_count', '')
                ),
                'heat': str(
                    meta_info.get('heat', '')
                ),
                'category': category.get('name', ''),
                'show_version': skill_extra.get(
                    'show_version',
                    ''
                ),
                'favorite_count': str(
                    meta_info.get(
                        'favorite_count',
                        ''
                    )
                ),
                'is_free': (
                    '是'
                    if meta_info.get('is_free')
                    else '否'
                ),
                'is_official': (
                    '是'
                    if meta_info.get('is_official')
                    else '否'
                ),
                'listed_at': meta_info.get(
                    'listed_at',
                    ''
                ),
                'price_amount': '',
                'labels': ', '.join(
                    meta_info.get('labels', [])
                )
            }

            if (
                price_info
                and price_info.get('amount')
            ):
                result['price_amount'] = str(
                    float(price_info['amount']) / 100
                )

            if not result['name']:
                return None

            return result

        except Exception as e:

            self.log(
                f"⚠️ skill解析失败: {str(e)}"
            )

            return None

    # =========================================================
    # JSON解析
    # =========================================================

    def parse_skills_from_json(self, data: Dict):

        skills = []

        try:

            if data.get('code') != 0:
                return skills

            products = (
                data
                .get('data', {})
                .get('products', [])
            )

            self.log(
                f"📦 当前响应包含 "
                f"{len(products)} 个 skill"
            )

            for item in products:

                skill = self.extract_skill(item)

                if skill:
                    skills.append(skill)

            return skills

        except Exception as e:

            self.log(
                f"⚠️ JSON解析失败: {str(e)}"
            )

            return skills

    # =========================================================
    # 爬取
    # =========================================================

    def crawl_keyword(
        self,
        keyword: str,
        max_scroll: int = 20
    ) -> List[Dict]:

        self.current_keyword = keyword

        self._api_responses = []

        self.seen_request_urls = set()

        all_skills = []

        try:

            self.start_browser()

            self.log(
                f"🔍 开始搜索关键词: {keyword}"
            )

            self.page.goto(
                "https://www.coze.cn/skills?tab=space",
                wait_until="domcontentloaded",
                timeout=60000
            )

            time.sleep(5)

            # 搜索框
            selectors = [
                'input[placeholder*="搜索"]',
                'input[placeholder*="skill"]',
                'input[type="search"]',
                '.search-input input',
            ]

            search_input = None

            for selector in selectors:

                try:

                    search_input = (
                        self.page.wait_for_selector(
                            selector,
                            timeout=3000
                        )
                    )

                    if search_input:

                        self.log(
                            f"✅ 找到搜索框: {selector}"
                        )

                        break

                except:
                    pass

            if not search_input:

                self.log("❌ 未找到搜索框")

                return []

            # React输入
            search_input.click()

            search_input.press("Control+A")

            search_input.press("Backspace")

            time.sleep(0.5)

            self.log(
                f"⌨️ 正在输入关键词: {keyword}"
            )

            search_input.type(
                keyword,
                delay=120
            )

            # 不要 press enter
            # Coze 是 debounce 搜索

            # 等待接口返回
            start_time = time.time()

            while time.time() - start_time < 15:

                if len(self._api_responses) > 0:
                    break

                time.sleep(0.5)

            if not self._api_responses:

                self.log(
                    "⚠️ 未捕获到API响应"
                )

            # 自动滚动
            previous_count = len(
                self._api_responses
            )

            for i in range(max_scroll):

                self.page.mouse.wheel(0, 4000)

                time.sleep(2)

                current_count = len(
                    self._api_responses
                )

                self.log(
                    f"📄 第{i+1}次滚动 "
                    f"当前响应数: {current_count}"
                )

                if current_count == previous_count:
                    break

                previous_count = current_count

            # 统一解析 response
            for response in self._api_responses:

                try:

                    data = response.json()

                    skills = (
                        self.parse_skills_from_json(
                            data
                        )
                    )

                    all_skills.extend(skills)

                except Exception as e:

                    self.log(
                        f"⚠️ response解析失败: "
                        f"{str(e)}"
                    )

            # 去重
            unique_skills = {}

            for skill in all_skills:

                name = skill.get('name')

                if name:
                    unique_skills[name] = skill

            all_skills = list(
                unique_skills.values()
            )

            self.log(
                f"✅ 最终获取 "
                f"{len(all_skills)} 个技能"
            )

        except Exception as e:

            self.log(
                f"❌ 爬取失败: {str(e)}"
            )

            import traceback

            traceback.print_exc()

        finally:

            self.stop_browser()

        return all_skills

    # =========================================================
    # Excel保存
    # =========================================================

    def save_to_excel(
        self,
        skills: List[Dict[str, Any]],
        keyword: str
    ):

        try:

            if not skills:

                self.log(
                    "⚠️ 没有数据可保存"
                )

                return None, 0

            now = datetime.datetime.now()

            date_str = now.strftime('%Y%m%d')

            time_str = now.strftime('%H-%M-%S')

            dir_path = (
                f"data/{keyword}/{date_str}"
            )

            os.makedirs(
                dir_path,
                exist_ok=True
            )

            filename = (
                f"{dir_path}/"
                f"{keyword}-{date_str}-{time_str}.xlsx"
            )

            df = pd.DataFrame(skills)

            df.rename(
                columns={
                    k: v
                    for k, v in (
                        self.FIELD_NAMES_CN.items()
                    )
                    if k in df.columns
                },
                inplace=True
            )

            df.to_excel(
                filename,
                index=False,
                engine='openpyxl'
            )

            self.log(
                f"💾 Excel已保存: {filename}"
            )

            self.log(
                f"📊 共保存 "
                f"{len(skills)} 条数据"
            )

            return filename, len(skills)

        except Exception as e:

            self.log(
                f"❌ Excel保存失败: {str(e)}"
            )

            return None, 0


# =========================================================
# 测试
# =========================================================

if __name__ == "__main__":

    crawler = CozeSkillCrawler(
        headless=False
    )

    keyword = "即梦"

    skills = crawler.crawl_keyword(
        keyword=keyword,
        max_scroll=15
    )

    print(
        f"\n最终获取 "
        f"{len(skills)} 条数据\n"
    )

    if skills:

        for i, item in enumerate(skills[:10]):

            print(
                f"{i+1}. "
                f"{item.get('name')}"
            )

        crawler.save_to_excel(
            skills,
            keyword
        )

    else:

        print("未获取到数据")

