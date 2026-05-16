"""
爬虫模块 - 使用 Playwright 浏览器自动化方式，无需 msToken
"""
import os
import time
import datetime
import asyncio
from typing import List, Dict, Optional, Callable, Any
from playwright.sync_api import sync_playwright, Page, Browser, Playwright, Response as PlaywrightResponse
import pandas as pd


class CozeSkillCrawler:
    """扣子Skill商店爬虫类 - Playwright浏览器自动化版本"""

    # 可用字段列表
    AVAILABLE_FIELDS = [
        'name', 'description', 'entity_id', 'draft_id', 'id', 'entity_type',
        'entity_version', 'status', 'category', 'category_id', 'category_index',
        'category_count', 'category_icon', 'category_active_icon', 'user_count',
        'heat', 'favorite_count', 'is_free', 'is_official', 'is_professional',
        'is_template', 'is_favorited', 'listed_at', 'icon_url', 'medium_icon_url',
        'origin_icon_url', 'readme', 'introduction_format', 'introduction_content',
        'seller_id', 'seller_name', 'seller_avatar', 'developer', 'user_id',
        'user_name', 'user_avatar', 'user_label_id', 'user_label_name',
        'user_label_icon', 'user_label_jump', 'case_name_1', 'case_url_1',
        'case_image_1', 'case_name_2', 'case_url_2', 'case_image_2', 'case_name_3',
        'case_url_3', 'case_image_3', 'show_version', 'publish_mode',
        'installer_count', 'has_installed', 'has_enabled', 'is_reach_max_enabled_limit',
        'support_build_leads', 'commercial_type', 'sku_id', 'sku_description',
        'sku_price_type', 'price_amount', 'price_currency', 'price_decimal_num',
        'labels', 'tags',
    ]

    # 中文列名映射
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
        'introduction_content': '详细介绍',
        'case_name_1': '案例1',
        'case_name_2': '案例2',
        'case_name_3': '案例3',
        'price_amount': '价格(元)',
        'labels': '标签',
        'listed_at': '上架时间',
    }

    def __init__(
        self,
        request_interval: float = 2.0,
        progress_callback: Optional[Callable] = None,
        headless: bool = True,
    ):
        """
        初始化爬虫

        Args:
            request_interval: 请求间隔时间（秒）
            progress_callback: 进度回调函数
            headless: 是否无头模式运行浏览器
        """
        self.request_interval = request_interval
        self.progress_callback = progress_callback
        self.headless = headless
        
        # 默认提取核心字段
        self.fields = [
            'name', 'developer', 'user_count', 'heat', 'description',
            'case_name_1', 'category', 'show_version', 'favorite_count',
            'is_free', 'is_official', 'listed_at', 'price_amount', 'labels'
        ]

        # Playwright 相关对象
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # 运行状态
        self.skills_data = []
        self.current_page = 0
        self.total_pages = None
        self.is_running = False
        self.logs = []
        
        # 用于捕获 API 响应的数据
        self._api_responses: List[Dict] = []

    def log(self, message: str):
        """记录日志"""
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        self.logs.append(log_msg)
        if self.progress_callback:
            self.progress_callback(log_msg)
        print(log_msg)

    def _handle_api_response(self, response: PlaywrightResponse):
        """处理 API 响应，捕获技能列表数据"""
        try:
            # 只处理包含 product/list 的请求
            if 'product/list' in response.url and response.status == 200:
                data = response.json()
                if data.get('code') == 0:
                    self._api_responses.append(data)
                    self.log(f"✅ 捕获 API 响应成功，URL: {response.url[:80]}...")
        except Exception as e:
            # 忽略解析错误，可能不是 JSON
            pass

    def start_browser(self):
        """启动浏览器"""
        try:
            self.log("🚀 正在启动浏览器...")
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                ]
            )
            
            # 创建新页面，设置用户代理
            context = self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
            )
            self.page = context.new_page()
            
            # 监听所有响应，捕获 API 数据
            self.page.on('response', self._handle_api_response)
            
            self.log("✅ 浏览器启动成功")
        except Exception as e:
            self.log(f"❌ 浏览器启动失败: {str(e)}")
            raise

    def stop_browser(self):
        """关闭浏览器"""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            self.log("✅ 浏览器已关闭")
        except Exception as e:
            self.log(f"⚠️  关闭浏览器时出错: {str(e)}")

    def extract_all_fields_from_item(self, item: Dict) -> Optional[Dict]:
        """
        从单个skill item中提取所有字段
        """
        try:
            meta_info = item.get('meta_info', {})
            skill_extra = item.get('skill_extra', {})
            commercial_setting = item.get('commercial_setting', {})
            build_setting = item.get('build_setting', {})
            skus = item.get('skus', [])
            seller = meta_info.get('seller', {})
            user_info = meta_info.get('user_info', {})
            category = meta_info.get('category', {})
            cases = skill_extra.get('cases', []) if skill_extra else []
            user_label = user_info.get('user_label', {}) if user_info else {}
            price_info = meta_info.get('price', {})

            sku = skus[0] if skus else {}

            all_fields = {
                'name': meta_info.get('name', ''),
                'description': meta_info.get('description', ''),
                'entity_id': meta_info.get('entity_id', ''),
                'draft_id': meta_info.get('draft_id', ''),
                'id': meta_info.get('id', ''),
                'entity_type': str(meta_info.get('entity_type', '')),
                'entity_version': meta_info.get('entity_version', ''),
                'status': str(meta_info.get('status', '')),
                'category': category.get('name', '') if category else '',
                'category_id': category.get('id', '') if category else '',
                'category_index': str(category.get('index', '')) if category else '',
                'category_count': str(category.get('count', '')) if category else '',
                'category_icon': category.get('icon_url', '') if category else '',
                'category_active_icon': category.get('active_icon_url', '') if category else '',
                'user_count': str(skill_extra.get('installer_count', 0)) if skill_extra and skill_extra.get('installer_count') else '',
                'heat': str(meta_info.get('heat', '')) if meta_info.get('heat') else '',
                'favorite_count': str(meta_info.get('favorite_count', 0)) if meta_info.get('favorite_count') is not None else '',
                'is_free': '是' if meta_info.get('is_free', False) else '否',
                'is_official': '是' if meta_info.get('is_official', False) else '否',
                'is_professional': '是' if meta_info.get('is_professional', False) else '否',
                'is_template': '是' if meta_info.get('is_template', False) else '否',
                'is_favorited': '是' if meta_info.get('is_favorited', False) else '否',
                'listed_at': meta_info.get('listed_at', ''),
                'icon_url': meta_info.get('icon_url', ''),
                'medium_icon_url': meta_info.get('medium_icon_url', ''),
                'origin_icon_url': meta_info.get('origin_icon_url', ''),
                'readme': meta_info.get('readme', ''),
                'introduction_format': str(meta_info.get('introduction', {}).get('format', '')),
                'introduction_content': meta_info.get('introduction', {}).get('introduction', ''),
                'seller_id': seller.get('id', '') if seller else '',
                'seller_name': seller.get('name', '') if seller else '',
                'seller_avatar': seller.get('avatar_url', '') if seller else '',
                'user_id': user_info.get('user_id', '') if user_info else '',
                'user_name': user_info.get('user_name', '') if user_info else '',
                'user_avatar': user_info.get('avatar_url', '') if user_info else '',
                'user_label_id': user_label.get('label_id', '') if user_label else '',
                'user_label_name': user_label.get('label_name', '') if user_label else '',
                'user_label_icon': (user_label.get('icon_url', '') or user_label.get('icon_uri', '')) if user_label else '',
                'user_label_jump': user_label.get('jump_link', '') if user_label else '',
                'case_name_1': cases[0].get('name', '') if len(cases) > 0 else '',
                'case_url_1': cases[0].get('task_url', '') if len(cases) > 0 else '',
                'case_image_1': cases[0].get('image_url', '') if len(cases) > 0 else '',
                'case_name_2': cases[1].get('name', '') if len(cases) > 1 else '',
                'case_url_2': cases[1].get('task_url', '') if len(cases) > 1 else '',
                'case_image_2': cases[1].get('image_url', '') if len(cases) > 1 else '',
                'case_name_3': cases[2].get('name', '') if len(cases) > 2 else '',
                'case_url_3': cases[2].get('task_url', '') if len(cases) > 2 else '',
                'case_image_3': cases[2].get('image_url', '') if len(cases) > 2 else '',
                'show_version': skill_extra.get('show_version', '') if skill_extra else '',
                'publish_mode': str(skill_extra.get('publish_mode', '')) if skill_extra else '',
                'has_installed': '是' if skill_extra.get('has_installed', False) else '否',
                'has_enabled': '是' if skill_extra.get('has_enabled', False) else '否',
                'is_reach_max_enabled_limit': '是' if skill_extra.get('is_reach_max_enabled_limit', False) else '否',
                'support_build_leads': '是' if build_setting.get('support_build_leads', False) else '否',
                'commercial_type': str(commercial_setting.get('commercial_type', '')) if commercial_setting else '',
                'sku_id': sku.get('id', '') if sku else '',
                'sku_description': sku.get('description', '') if sku else '',
                'sku_price_type': str(sku.get('price_type', '')) if sku else '',
                'price_amount': str(float(price_info.get('amount', 0)) / 100) if price_info and price_info.get('amount') else '',
                'price_currency': str(price_info.get('currency', '')) if price_info else '',
                'price_decimal_num': str(price_info.get('decimal_num', '')) if price_info else '',
                'labels': ', '.join(meta_info.get('labels', [])) if meta_info.get('labels') else '',
                'tags': ', '.join(meta_info.get('tags', [])) if meta_info.get('tags') else '',
            }

            # 提取开发者名称
            developer = (
                (skill_extra.get('developer', '') if skill_extra else '') or
                (skill_extra.get('author', '') if skill_extra else '') or
                (skill_extra.get('creator', '') if skill_extra else '') or
                meta_info.get('developer', '') or
                meta_info.get('author', '') or
                meta_info.get('creator', '') or
                item.get('developer', '') or
                item.get('author', '') or
                item.get('creator', '') or
                (user_info.get('name', '') if user_info else '') or
                (user_info.get('nickname', '') if user_info else '') or
                (user_info.get('username', '') if user_info else '') or
                (seller.get('name', '') if seller else '')
            )
            all_fields['developer'] = str(developer) if developer else ''

            if not all_fields.get('name'):
                return None

            return all_fields

        except Exception as e:
            self.log(f"提取skill信息失败: {str(e)}")
            return None

    def parse_skills_from_json(self, data: Dict) -> List[Dict]:
        """
        从 API 返回的 JSON 数据中解析 skill 列表
        """
        skills = []

        try:
            if data.get('code') != 0:
                self.log(f"API 返回错误: code={data.get('code')}")
                return skills

            response_data = data.get('data', {})
            products = response_data.get('products', [])

            if not products:
                self.log("未在响应中找到 products 列表")
                return skills

            self.log(f"从 API 响应中找到 {len(products)} 个 skill")

            for item in products:
                skill_info = self.extract_all_fields_from_item(item)
                if skill_info:
                    filtered_skill = {k: v for k, v in skill_info.items() if k in self.fields}
                    skills.append(filtered_skill)

            self.log(f"成功解析 {len(skills)} 个 skill")

        except Exception as e:
            self.log(f"解析 skill 列表失败: {str(e)}")
            import traceback
            traceback.print_exc()

        return skills

    def crawl_keyword(
        self,
        keyword: str,
        max_pages: Optional[int] = None,
    ) -> List[Dict]:
        """
        爬取指定关键词的所有 skill（使用浏览器自动化）

        Args:
            keyword: 搜索关键词
            max_pages: 最大爬取页数，None 表示爬取所有页

        Returns:
            所有 skill 信息列表
        """
        self.is_running = True
        self.current_page = 0
        all_skills = []
        self._api_responses = []
        
        try:
            self.start_browser()
            self.log(f"🔍 开始搜索关键词: {keyword}")
            
            # 访问技能商店页面
            self.log("🌐 正在访问扣子技能商店...")
            self.page.goto("https://www.coze.cn/skills?tab=space", wait_until="networkidle", timeout=60000)
            time.sleep(2)
            
            # 尝试多种可能的搜索框选择器
            search_selectors = [
                'input[placeholder*="搜索"]',
                'input[placeholder*="skill"]',
                'input[type="search"]',
                '.search-input input',
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = self.page.wait_for_selector(selector, timeout=5000)
                    if search_input:
                        self.log(f"✅ 找到搜索框，选择器: {selector}")
                        break
                except:
                    continue
            
            if not search_input:
                self.log("⚠️  未找到搜索框，尝试直接使用搜索 URL")
                # 直接跳转到搜索 URL
                encoded_keyword = keyword.replace(' ', '%20')
                search_url = f"https://www.coze.cn/skills?keyword={encoded_keyword}&tab=space"
                self.page.goto(search_url, wait_until="networkidle", timeout=60000)
                time.sleep(3)
            else:
                # 输入关键词并搜索
                self.log(f"⌨️  正在输入关键词: {keyword}")
                search_input.fill(keyword)
                time.sleep(1)
                
                # 按回车键搜索
                search_input.press("Enter")
                self.log("🔄 提交搜索请求...")
            
            # 等待搜索结果加载
            time.sleep(5)
            
            # 检查是否已经捕获到第一页数据
            if not self._api_responses:
                self.log("⚠️  等待 API 响应...")
                # 滚动页面触发更多加载
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                time.sleep(3)
            
            # 解析第一页数据
            if self._api_responses:
                data = self._api_responses[0]
                skills = self.parse_skills_from_json(data)
                all_skills.extend(skills)
                self.current_page = 1
                self.log(f"📄 第 1 页爬取完成，获得 {len(skills)} 个技能")
                
                # 检查是否有更多页面
                has_more = data.get('data', {}).get('has_more', False)
                
                # 继续翻页
                page_num = 2
                while has_more and (max_pages is None or page_num <= max_pages):
                    time.sleep(self.request_interval)
                    
                    # 滚动到页面底部触发加载更多
                    self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    
                    # 等待新的 API 响应
                    start_time = time.time()
                    got_response = False
                    
                    while time.time() - start_time < 10:  # 最多等待10秒
                        if len(self._api_responses) >= page_num:
                            got_response = True
                            break
                        time.sleep(0.5)
                    
                    if got_response:
                        data = self._api_responses[page_num - 1]
                        skills = self.parse_skills_from_json(data)
                        all_skills.extend(skills)
                        self.current_page = page_num
                        self.log(f"📄 第 {page_num} 页爬取完成，获得 {len(skills)} 个技能，累计: {len(all_skills)}")
                        has_more = data.get('data', {}).get('has_more', False)
                        page_num += 1
                    else:
                        self.log(f"⚠️  第 {page_num} 页未能获取响应，停止爬取")
                        break
            else:
                self.log("❌ 未能捕获 API 响应，尝试直接从页面提取数据")
                
                # 备用方案：尝试从页面 DOM 中提取数据
                skills = self._extract_skills_from_page()
                if skills:
                    all_skills.extend(skills)
                    self.log(f"📄 从页面提取到 {len(skills)} 个技能")
            
            self.log(f"✅ 关键词 '{keyword}' 爬取完成，共获取 {len(all_skills)} 个技能")
            
        except Exception as e:
            self.log(f"❌ 爬取过程出错: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.stop_browser()
            self.is_running = False
        
        return all_skills

    def _extract_skills_from_page(self) -> List[Dict]:
        """
        备用方法：直接从页面 DOM 中提取技能数据
        """
        skills = []
        try:
            # 查找技能卡片
            cards = self.page.query_selector_all('[class*="card"], [class*="skill"], [class*="product"]')
            self.log(f"找到 {len(cards)} 个可能的技能卡片")
            
            for card in cards[:50]:  # 限制数量避免超时
                try:
                    name = card.query_selector('h3, [class*="title"], [class*="name"]')
                    desc = card.query_selector('[class*="desc"], [class*="description"]')
                    
                    if name:
                        skill = {
                            'name': name.inner_text().strip() if name else '',
                            'description': desc.inner_text().strip() if desc else '',
                            'developer': '',
                            'user_count': '',
                            'heat': '',
                            'category': '',
                            'show_version': '',
                            'favorite_count': '',
                            'is_free': '',
                            'is_official': '',
                            'listed_at': '',
                            'price_amount': '',
                            'labels': '',
                        }
                        if skill['name']:
                            skills.append(skill)
                except:
                    continue
                    
        except Exception as e:
            self.log(f"从页面提取数据失败: {str(e)}")
        
        return skills

    def save_to_excel(self, skills: List[Dict[str, Any]], keyword: str):
        """
        保存为 Excel 格式

        文件名格式：{keyword}-{YYYYMMDD}-{HH}-{MM}-{SS}.xlsx
        存储路径：data/{keyword}/{YYYYMMDD}/

        Args:
            skills: 技能数据列表
            keyword: 关键词

        Returns:
            (文件路径, 技能数量) 元组，失败返回 (None, 0)
        """
        try:
            if not skills:
                self.log("没有数据可保存")
                return None, 0

            # 创建目录
            now = datetime.datetime.now()
            date_str = now.strftime('%Y%m%d')
            time_str = now.strftime('%H-%M-%S')

            dir_path = f"data/{keyword}/{date_str}"
            os.makedirs(dir_path, exist_ok=True)

            filename = f"{dir_path}/{keyword}-{date_str}-{time_str}.xlsx"

            df = pd.DataFrame(skills)

            # 重命名列为中文
            df.rename(columns={k: v for k, v in self.FIELD_NAMES_CN.items() if k in df.columns}, inplace=True)

            df.to_excel(filename, index=False, engine='openpyxl')

            file_size = os.path.getsize(filename)
            self.log(f"💾 数据已保存到: {filename}")
            self.log(f"📊 文件大小: {file_size} 字节，共 {len(skills)} 条记录")

            return filename, len(skills)

        except Exception as e:
            self.log(f"❌ 保存 Excel 文件失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, 0
