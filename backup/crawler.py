"""
爬虫模块 - 基于 Playwright 浏览器自动化
"""
import os
import json
import time
import datetime
from typing import List, Dict, Optional, Callable, Any
import pandas as pd
from playwright.sync_api import sync_playwright, Page, Response


class CozeSkillCrawler:
    """扣子Skill商店爬虫类 - Playwright 版本"""

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
    ):
        """
        初始化爬虫

        Args:
            request_interval: 请求间隔时间（秒）
            progress_callback: 进度回调函数
        """
        self.request_interval = request_interval
        self.progress_callback = progress_callback

        # 默认提取核心字段
        self.fields = [
            'name', 'developer', 'user_count', 'heat', 'description',
            'case_name_1', 'category', 'show_version', 'favorite_count',
            'is_free', 'is_official', 'listed_at', 'price_amount', 'labels'
        ]

        self.skills_data = []
        self.current_page = 0
        self.total_pages = None
        self.is_running = False
        self.logs = []
        self._current_keyword = ""

        # Playwright 相关
        self._playwright = None
        self._browser = None
        self._page = None
        self._api_responses = []

    def log(self, message: str):
        """记录日志"""
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        self.logs.append(log_msg)
        if self.progress_callback:
            self.progress_callback(log_msg)
        print(log_msg)

    def _handle_response(self, response: Response):
        """拦截 API 响应"""
        if "product/list" in response.url and response.status == 200:
            try:
                data = response.json()
                self._api_responses.append(data)
            except:
                pass

    def _start_browser(self):
        """启动浏览器"""
        self.log("🚀 启动浏览器...")
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )

        context = self._browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )

        self._page = context.new_page()
        self._page.on("response", self._handle_response)

        self.log("✅ 浏览器已启动")

    def _close_browser(self):
        """关闭浏览器"""
        if self._page:
            self._page.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        self.log("🔒 浏览器已关闭")

    def _extract_all_fields_from_item(self, item: Dict) -> Optional[Dict]:
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
            cases = skill_extra.get('cases', [])

            introduction = meta_info.get('introduction', {})

            skill = {
                'name': meta_info.get('name', ''),
                'description': meta_info.get('description', ''),
                'entity_id': meta_info.get('entity_id', ''),
                'draft_id': meta_info.get('draft_id', ''),
                'id': meta_info.get('id', ''),
                'entity_type': meta_info.get('entity_type', ''),
                'entity_version': meta_info.get('entity_version', ''),
                'status': meta_info.get('status', ''),
                'category': category.get('name', ''),
                'category_id': category.get('id', ''),
                'category_index': category.get('index', ''),
                'category_count': category.get('count', ''),
                'heat': meta_info.get('heat', 0),
                'favorite_count': meta_info.get('favorite_count', 0),
                'is_free': meta_info.get('is_free', False),
                'is_official': meta_info.get('is_official', False),
                'is_professional': meta_info.get('is_professional', False),
                'is_template': meta_info.get('is_template', False),
                'is_favorited': meta_info.get('is_favorited', False),
                'listed_at': meta_info.get('listed_at', ''),
                'icon_url': meta_info.get('icon_url', ''),
                'medium_icon_url': meta_info.get('medium_icon_url', ''),
                'origin_icon_url': meta_info.get('origin_icon_url', ''),
                'readme': meta_info.get('readme', ''),
                'introduction_format': introduction.get('format', '') if isinstance(introduction, dict) else '',
                'introduction_content': introduction.get('introduction', '') if isinstance(introduction, dict) else str(
                    introduction),
                'seller_id': seller.get('id', ''),
                'seller_name': seller.get('name', ''),
                'seller_avatar': seller.get('avatar_url', ''),
                'developer': user_info.get('name', ''),
                'user_id': user_info.get('user_id', ''),
                'user_name': user_info.get('user_name', ''),
                'user_avatar': user_info.get('avatar_url', ''),
                'show_version': skill_extra.get('show_version', ''),
                'publish_mode': skill_extra.get('publish_mode', ''),
                'installer_count': skill_extra.get('installer_count', 0),
                'user_count': skill_extra.get('installer_count', 0),
                'has_installed': skill_extra.get('has_installed', False),
                'has_enabled': skill_extra.get('has_enabled', False),
                'is_reach_max_enabled_limit': skill_extra.get('is_reach_max_enabled_limit', False),
                'support_build_leads': build_setting.get('support_build_leads', False),
                'commercial_type': commercial_setting.get('commercial_type', 0),
                'labels': ','.join(meta_info.get('labels', [])) if meta_info.get('labels') else '',
                'tags': ','.join(meta_info.get('tags', [])) if meta_info.get('tags') else '',
            }

            # 提取案例
            for i, case in enumerate(cases[:3], 1):
                skill[f'case_name_{i}'] = case.get('name', '')
                skill[f'case_url_{i}'] = case.get('task_url', '')
                skill[f'case_image_{i}'] = case.get('image_url', '')

            # 提取价格
            if skus:
                sku = skus[0]
                price = sku.get('price', [])
                if price:
                    skill['sku_id'] = sku.get('id', '')
                    skill['sku_description'] = sku.get('description', '')
                    skill['sku_price_type'] = sku.get('price_type', '')
                    price_info = price[0] if isinstance(price, list) and price else {}
                    skill['price_amount'] = price_info.get('amount', 0)
                    skill['price_currency'] = price_info.get('currency', '')
                    skill['price_decimal_num'] = price_info.get('decimal_num', 2)

            return skill

        except Exception as e:
            self.log(f"⚠️  解析item失败: {e}")
            return None

    def crawl_keyword(
            self,
            keyword: str = "",
            max_pages: Optional[int] = None
    ) -> List[Dict]:
        """
        爬取关键词相关的技能

        Args:
            keyword: 搜索关键词，空字符串表示不搜索
            max_pages: 最大爬取页数，None则爬取所有

        Returns:
            技能数据列表
        """
        self.is_running = True
        self._current_keyword = keyword
        self.skills_data = []
        self._api_responses = []

        try:
            self._start_browser()

            # 访问技能商店
            self.log(f"🌐 访问扣子技能商店...")
            self._page.goto("https://www.coze.cn/skills", wait_until="networkidle")
            time.sleep(2)

            # 如果有关键词，执行搜索
            if keyword:
                self.log(f"🔍 搜索关键词: '{keyword}'")
                try:
                    # 找到搜索框
                    search_input = self._page.get_by_placeholder("搜索更多技能")
                    search_input.fill(keyword)
                    search_input.press("Enter")
                    time.sleep(3)
                except Exception as e:
                    self.log(f"⚠️  搜索框操作失败: {e}")
                    # 尝试其他方式定位搜索框
                    pass
            else:
                self.log("📋 不搜索，直接浏览全部")
                time.sleep(2)

            # 收集第一页数据
            page_count = 1
            seen_ids = set()

            while True:
                time.sleep(self.request_interval)

                # 处理收集到的 API 响应
                while self._api_responses:
                    data = self._api_responses.pop(0)

                    code = data.get('code')
                    if code != 0:
                        self.log(f"⚠️  API返回错误码: {code}")
                        continue

                    products = data.get('data', {}).get('products', [])
                    has_more = data.get('data', {}).get('has_more', False)
                    total = data.get('data', {}).get('total', 0)

                    self.log(f"📄 第 {page_count} 页: {len(products)} 个技能，总计 {total} 个")

                    for product in products:
                        skill = self._extract_all_fields_from_item(product)
                        if skill and skill['id'] and skill['id'] not in seen_ids:
                            seen_ids.add(skill['id'])
                            self.skills_data.append(skill)

                    if not has_more:
                        self.log("✅ 没有更多页面了")
                        break

                # 检查是否继续
                if max_pages and page_count >= max_pages:
                    self.log(f"✅ 已达到最大页数 {max_pages}")
                    break

                # 尝试滚动加载下一页
                try:
                    self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)
                except:
                    break

                # 如果没有新的响应，结束
                if not self._api_responses:
                    break

                page_count += 1

            self.log(f"🎉 爬取完成，共获取 {len(self.skills_data)} 个唯一技能")
            return self.skills_data

        except Exception as e:
            self.log(f"❌ 爬取失败: {e}")
            import traceback
            self.log(traceback.format_exc())
            return []
        finally:
            self._close_browser()
            self.is_running = False

    def save_to_excel(self, filepath: str):
        """
        保存到Excel文件

        Args:
            filepath: 文件路径
        """
        if not self.skills_data:
            self.log("⚠️  没有数据可保存")
            return

        try:
            df = pd.DataFrame(self.skills_data)

            # 只保留配置的字段
            if self.fields:
                existing_fields = [f for f in self.fields if f in df.columns]
                df = df[existing_fields]

            # 创建目录
            os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)

            df.to_excel(filepath, index=False, engine='openpyxl')
            self.log(f"💾 数据已保存到: {filepath}")
            self.log(f"📊 共 {len(df)} 行，{len(df.columns)} 列")

        except Exception as e:
            self.log(f"❌ 保存Excel失败: {e}")