import time
import json
import threading
import requests
from datetime import datetime
from typing import Optional
from pathlib import Path

class TokenKeeper:
    """msToken 自动续期守护类"""
    
    def __init__(self, token_file: str = "data/token_data.json"):
        self.token_file = token_file
        self.current_token = None
        self.cookies = []
        self.daemon_thread = None
        self.running = False
        self.check_interval = 1800  # 30分钟
        self.last_refresh = None
        self.status = "stopped"  # running, stopped, expired
        
        # 确保目录存在
        Path(token_file).parent.mkdir(parents=True, exist_ok=True)
        self._load_saved_data()
    
    def _load_saved_data(self):
        """加载保存的Token和Cookie"""
        try:
            if Path(self.token_file).exists():
                with open(self.token_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.current_token = data.get('ms_token')
                    self.cookies = data.get('cookies', [])
                    self.last_refresh = datetime.fromisoformat(
                        data.get('last_refresh')
                    ) if data.get('last_refresh') else None
                print(f"已加载保存的Token: {self.current_token[:20]}..." if self.current_token else "无保存的Token")
        except Exception as e:
            print(f"加载Token数据失败: {e}")
    
    def _save_data(self):
        """保存Token和Cookie到文件"""
        data = {
            'ms_token': self.current_token,
            'cookies': self.cookies,
            'last_refresh': datetime.now().isoformat() if self.last_refresh else None,
            'status': self.status
        }
        with open(self.token_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def set_token(self, ms_token: str, cookies: list = None):
        """设置新的Token和Cookie"""
        self.current_token = ms_token
        if cookies:
            self.cookies = cookies
        self.last_refresh = datetime.now()
        self._save_data()
        print(f"Token已更新: {ms_token[:20]}...")
    
    def check_token_valid(self) -> bool:
        """检查Token是否有效"""
        if not self.current_token:
            return False
        
        try:
            # 调用一个轻量级API测试Token有效性
            response = requests.get(
                "https://www.coze.cn/api/user/info",
                headers={
                    "Cookie": f"msToken={self.current_token}",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                timeout=10
            )
            
            # 如果返回200且没有登录错误提示
            if response.status_code == 200:
                result = response.json()
                return result.get('code') == 0
            
            return False
        except Exception as e:
            print(f"Token检查失败: {e}")
            return False
    
    def heartbeat(self) -> bool:
        """发送心跳刷新Token"""
        if not self.current_token:
            self.status = "expired"
            return False
        
        try:
            session = requests.Session()
            
            # 设置保存的Cookie
            for cookie in self.cookies:
                session.cookies.set(cookie['name'], cookie['value'])
            
            # 同时设置header中的msToken
            headers = {"Cookie": f"msToken={self.current_token}"}
            
            # 调用API
            response = session.get(
                "https://www.coze.cn/api/user/info",
                headers=headers,
                timeout=10
            )
            
            # 检查响应中的Set-Cookie，获取新的Token
            for cookie in session.cookies:
                if cookie.name == 'msToken' and cookie.value != self.current_token:
                    self.current_token = cookie.value
                    print(f"Token已自动刷新: {self.current_token[:20]}...")
                    self._save_data()
                    break
            
            self.last_refresh = datetime.now()
            self.status = "running"
            return True
            
        except Exception as e:
            print(f"心跳失败: {e}")
            self.status = "error"
            return False
    
    def _daemon_loop(self):
        """守护循环"""
        while self.running:
            try:
                self.heartbeat()
            except Exception as e:
                print(f"守护循环异常: {e}")
            
            # 等待下次检查
            for _ in range(self.check_interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def start(self):
        """启动守护线程"""
        if self.running:
            print("守护已在运行中")
            return
        
        self.running = True
        self.daemon_thread = threading.Thread(target=self._daemon_loop, daemon=True)
        self.daemon_thread.start()
        self.status = "running"
        print("Token守护已启动")
    
    def stop(self):
        """停止守护"""
        self.running = False
        self.status = "stopped"
        print("Token守护已停止")
    
    def get_status(self) -> dict:
        """获取当前状态"""
        return {
            "status": self.status,
            "has_token": self.current_token is not None,
            "token_preview": self.current_token[:20] + "..." if self.current_token else None,
            "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
            "check_interval": self.check_interval,
            "is_valid": self.check_token_valid() if self.current_token else False
        }

# 全局单例
token_keeper = TokenKeeper()
