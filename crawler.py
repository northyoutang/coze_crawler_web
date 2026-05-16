"""
爬虫模块 - 基于已有coze_skill_crawler改编
"""
import os
import json
import time
import datetime
from typing import List, Dict, Optional, Callable, Any
import requests
import pandas as pd


class CozeSkillCrawler:
    """扣子Skill商店爬虫类"""

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
        ms_token: str = None,
        a_bogus: Optional[str] = None,
        request_interval: float = 2.0,
        progress_callback: Optional[Callable] = None,
    ):
        """
        初始化爬虫

        Args:
            ms_token: 可选的msToken参数
            a_bogus: 可选的a_bogus参数（签名）
            request_interval: 请求间隔时间（秒）
            progress_callback: 进度回调函数
        """
        self.ms_token = ms_token
        self.a_bogus = a_bogus
        self.request_interval = request_interval
        self.base_url = "https://www.coze.cn/api/marketplace/product/list"
        self.progress_callback = progress_callback

        # 默认提取核心字段
        self.fields = [
            'name', 'developer', 'user_count', 'heat', 'description',
            'case_name_1', 'category', 'show_version', 'favorite_count',
            'is_free', 'is_official', 'listed_at', 'price_amount', 'labels'
        ]

        self.session = requests.Session()

        # 模拟浏览器请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://www.coze.cn/store',
            'Origin': 'https://www.coze.cn',
        }

        self.session.headers.update(self.headers)
        self.skills_data = []
        self.current_page = 0
        self.total_pages = None
        self.is_running = False
        self.logs = []

    def log(self, message: str):
        """记录日志"""
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        self.logs.append(log_msg)
        if self.progress_callback:
            self.progress_callback(log_msg)
        print(log_msg)

    def fetch_from_api(self, page_num: int = 1, page_size: int = 50, keyword: str = "") -> Optional[Dict]:
        """
        从API获取数据
        """
        try:
            sort_type = '4' if keyword else '1'

            params = {
                'entity_type': '11',
                'sort_type': sort_type,
                'page_num': str(page_num),
                'page_size': str(page_size),
                'keyword': keyword,
            }

            if self.ms_token:
                params['msToken'] = self.ms_token

            if not keyword:
                params['source'] = '1'

            if self.a_bogus:
                params['a_bogus'] = self.a_bogus

            self.log(f"请求第 {page_num} 页...")
            if keyword:
                self.log(f"搜索关键词: '{keyword}'")

            response = self.session.get(self.base_url, params=params, timeout=30)
            self.log(f"响应状态码: {response.status_code}")

            response.raise_for_status()
            data = response.json()

            has_more = data.get('data', {}).get('has_more', False)
            self.log(f"是否还有下一页: {'是' if has_more else '否'}")

            time.sleep(self.request_interval)

            return data

        except requests.exceptions.RequestException as e:
            self.log(f"请求第 {page_num} 页失败: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            self.log(f"解析JSON响应失败: {str(e)}")
            return None

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
            cases = skill_extra.get('cases', [])
            user_label = user_info.get('user_label', {})
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
                'category': category.get('name', ''),
                'category_id': category.get('id', ''),
                'category_index': str(category.get('index', '')),
                'category_count': str(category.get('count', '')),
                'category_icon': category.get('icon_url', ''),
                'category_active_icon': category.get('active_icon_url', ''),
                'user_count': str(skill_extra.get('installer_count', 0)) if skill_extra.get('installer_count') else '',
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
                'seller_id': seller.get('id', ''),
                'seller_name': seller.get('name', ''),
                'seller_avatar': seller.get('avatar_url', ''),
                'user_id': user_info.get('user_id', ''),
                'user_name': user_info.get('user_name', ''),
                'user_avatar': user_info.get('avatar_url', ''),
                'user_label_id': user_label.get('label_id', ''),
                'user_label_name': user_label.get('label_name', ''),
                'user_label_icon': user_label.get('icon_url', '') or user_label.get('icon_uri', ''),
                'user_label_jump': user_label.get('jump_link', ''),
                'case_name_1': cases[0].get('name', '') if len(cases) > 0 else '',
                'case_url_1': cases[0].get('task_url', '') if len(cases) > 0 else '',
                'case_image_1': cases[0].get('image_url', '') if len(cases) > 0 else '',
                'case_name_2': cases[1].get('name', '') if len(cases) > 1 else '',
                'case_url_2': cases[1].get('task_url', '') if len(cases) > 1 else '',
                'case_image_2': cases[1].get('image_url', '') if len(cases) > 1 else '',
                'case_name_3': cases[2].get('name', '') if len(cases) > 2 else '',
                'case_url_3': cases[2].get('task_url', '') if len(cases) > 2 else '',
                'case_image_3': cases[2].get('image_url', '') if len(cases) > 2 else '',
                'show_version': skill_extra.get('show_version', ''),
                'publish_mode': str(skill_extra.get('publish_mode', '')),
                'has_installed': '是' if skill_extra.get('has_installed', False) else '否',
                'has_enabled': '是' if skill_extra.get('has_enabled', False) else '否',
                'is_reach_max_enabled_limit': '是' if skill_extra.get('is_reach_max_enabled_limit', False) else '否',
                'support_build_leads': '是' if build_setting.get('support_build_leads', False) else '否',
                'commercial_type': str(commercial_setting.get('commercial_type', '')),
                'sku_id': sku.get('id', ''),
                'sku_description': sku.get('description', ''),
                'sku_price_type': str(sku.get('price_type', '')),
                'price_amount': str(float(price_info.get('amount', 0)) / 100) if price_info and price_info.get('amount') else '',
                'price_currency': str(price_info.get('currency', '')) if price_info else '',
                'price_decimal_num': str(price_info.get('decimal_num', '')) if price_info else '',
                'labels': ', '.join(meta_info.get('labels', [])) if meta_info.get('labels') else '',
                'tags': ', '.join(meta_info.get('tags', [])) if meta_info.get('tags') else '',
            }

            # 提取开发者名称
            developer = (
                skill_extra.get('developer', '') or
                skill_extra.get('author', '') or
                skill_extra.get('creator', '') or
                meta_info.get('developer', '') or
                meta_info.get('author', '') or
                meta_info.get('creator', '') or
                item.get('developer', '') or
                item.get('author', '') or
                item.get('creator', '') or
                user_info.get('name', '') or
                user_info.get('nickname', '') or
                user_info.get('username', '') or
                seller.get('name', '')
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
        从API返回的JSON数据中解析skill列表
        """
        skills = []

        try:
            if data.get('code') != 0:
                self.log(f"API返回错误: code={data.get('code')}")
                return skills

            response_data = data.get('data', {})
            products = response_data.get('products', [])

            if not products:
                self.log("未在响应中找到products列表")
                return skills

            self.log(f"从API响应中找到 {len(products)} 个skill")

            for item in products:
                skill_info = self.extract_all_fields_from_item(item)
                if skill_info:
                    filtered_skill = {k: v for k, v in skill_info.items() if k in self.fields}
                    skills.append(filtered_skill)

            self.log(f"成功解析 {len(skills)} 个skill")

        except Exception as e:
            self.log(f"解析skill列表失败: {str(e)}")

        return skills

    def crawl_keyword(
        self,
        keyword: str,
        max_pages: Optional[int] = None,
        page_size: int = 50,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[Dict]:
        """
        爬取指定关键词的所有skill

        Args:
            keyword: 搜索关键词
            max_pages: 最大爬取页数，None表示爬取所有页
            page_size: 每页数量
            progress_callback: 进度回调函数(当前进度, 总数, 状态信息)

        Returns:
            所有skill信息列表
        """
        self.is_running = True
        self.current_page = 0
        all_skills = []

        page_num = 1
        while True:
            if max_pages is not None and page_num > max_pages:
                self.log(f"已达到最大页数限制: {max_pages}")
                break

            self.current_page = page_num

            # 调用进度回调
            if progress_callback:
                progress_callback(page_num, max_pages or 0, f"正在爬取第 {page_num} 页...")

            response_data = self.fetch_from_api(page_num, page_size, keyword)

            if not response_data:
                self.log(f"第 {page_num} 页获取失败，停止爬取")
                break

            skills = self.parse_skills_from_json(response_data)

            if not skills:
                self.log(f"第 {page_num} 页没有找到skill，停止爬取")
                break

            all_skills.extend(skills)
            self.log(f"第 {page_num} 页获取到 {len(skills)} 个skill，累计: {len(all_skills)} 个")

            # 检查是否还有下一页
            has_more = response_data.get('data', {}).get('has_more', False)
            if not has_more:
                self.log("所有页面爬取完成")
                break

            page_num += 1

        # 完成时调用进度回调
        if progress_callback:
            progress_callback(page_num - 1, max_pages or (page_num - 1), f"爬取完成，共获取 {len(all_skills)} 个技能")

        self.is_running = False
        return all_skills

    def save_to_excel(self, skills: List[Dict[str, Any]], keyword: str):
        """
        保存为Excel格式

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
            self.log(f"数据已保存到: {filename}")
            self.log(f"文件大小: {file_size} 字节，共 {len(skills)} 条记录")

            return filename, len(skills)

        except Exception as e:
            self.log(f"保存Excel文件失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, 0

    def get_ms_token_interactive(self) -> str:
        """
        交互式获取msToken（人工辅助登录）
        返回: 获取到的msToken
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.log("playwright未安装，请先安装: pip install playwright && playwright install chromium")
            return ""
        
        print("=" * 60)
        print("正在启动浏览器进行交互式登录...")
        print("请在浏览器中手动完成登录操作")
        print("登录成功后浏览器会自动关闭")
        print("=" * 60)
        
        with sync_playwright() as p:
            # 启动可见的浏览器
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            # 访问主页
            page.goto("https://www.coze.cn")
            
            # 等待用户登录（等待跳转到首页或工作台）
            try:
                # 等待URL变化表示登录成功
                page.wait_for_url(
                    lambda url: "home" in url or "store" in url or "workspace" in url,
                    timeout=300000  # 5分钟超时
                )
                
                # 等待一下确保Token已设置
                page.wait_for_timeout(2000)
                
                # 从LocalStorage获取msToken
                ms_token = page.evaluate("""() => {
                    return localStorage.getItem('msToken') || 
                           sessionStorage.getItem('msToken') ||
                           '';
                }""")
                
                # 同时获取完整的Cookie
                cookies = context.cookies()
                
                browser.close()
                
                if ms_token:
                    print(f"✓ 成功获取msToken")
                    print(f"Token预览: {ms_token[:30]}...")
                    print(f"获取到 {len(cookies)} 个Cookie")
                    
                    # 保存到TokenKeeper
                    from token_keeper import token_keeper
                    token_keeper.set_token(ms_token, cookies)
                    
                    return ms_token
                else:
                    print("✗ 未能获取到msToken")
                    return ""
                    
            except Exception as e:
                print(f"获取Token超时或失败: {e}")
                browser.close()
                return ""
