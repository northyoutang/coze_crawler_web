# 扣子技能爬取管理系统

基于 FastAPI + APScheduler + SQLite 的扣子商店技能爬虫 Web 管理系统。

## 功能特性

### 1. 主题词管理
- 管理爬取的关键词列表
- 支持新增、编辑、删除操作
- 默认关键词：即梦、足球、image2、图、童年

### 2. 文件浏览与下载
- 树形目录展示爬取的文件
- 按关键词、日期分类存储
- 支持点击下载 Excel 文件

### 3. 定时任务设置
- 自定义爬取间隔（1-24小时）
- 启用/禁用定时任务
- 显示下次执行时间
- 实时运行状态

### 4. 登录认证
- 固定账号密码登录
- Session 会话管理
- 未登录自动跳转

### 5. 手动爬取
- 一键触发手动爬取
- 实时进度条展示
- 实时日志输出
- 支持全量或单个关键词爬取

### 6. 🔐 msToken 自动续期
- ✅ **自动心跳刷新**：每30分钟发送一次心跳，保持Token活跃
- ✅ **完整Cookie保存**：登录时保存所有Cookie，提高恢复成功率
- ✅ **状态实时监控**：页面显示Token状态、有效性、最后刷新时间
- ✅ **交互式获取**：一键启动浏览器手动登录获取Token（需要Playwright支持）
- ✅ **Token持久化**：Token和Cookie自动保存到 `data/token_data.json`
- ✅ **启动自动恢复**：服务启动时自动加载保存的Token并启动守护

## 技术栈

- **后端框架**: FastAPI
- **任务调度**: APScheduler
- **数据库**: SQLite + SQLAlchemy
- **前端**: HTML + Tailwind CSS + JavaScript
- **爬虫**: requests + pandas + openpyxl
- **浏览器自动化**: Playwright（可选，用于交互式获取Token）

## 解压说明

### 方式一：使用命令行解压

```bash
# Linux/macOS
unzip coze_crawler_web.zip

# Windows (PowerShell)
Expand-Archive -Path coze_crawler_web.zip -DestinationPath .
```

### 方式二：使用图形界面工具

- Windows: 右键 -> 提取全部
- macOS: 双击自动解压
- Linux: 使用归档管理器

## 快速开始

### 1. 安装依赖

```bash
cd coze_crawler_web
pip install -r requirements.txt
```

**可选**：如需使用交互式获取Token功能，安装Playwright：
```bash
pip install playwright
playwright install chromium
```

### 2. 启动服务

```bash
python main.py
```

或使用 uvicorn 直接启动：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 访问系统

打开浏览器访问: http://localhost:8000

- 登录页面: http://localhost:8000/login
- 主页面: http://localhost:8000

### 4. 默认账号

- 用户名: `northyoutang`
- 密码: `northyoutang@gmail`

## 配置说明

### msToken 获取方法

msToken 是访问 Coze 商店 API 的必要参数，请按以下步骤获取：

#### 方法一：交互式获取（推荐）

1. 登录系统后，进入「定时设置」页面
2. 在「msToken 自动续期管理」卡片中点击「🚀 交互式获取Token」按钮
3. 在弹出的浏览器中完成 Coze 账号登录
4. 登录成功后浏览器自动关闭，Token 自动保存到系统中
5. 系统自动启动守护进程，每30分钟刷新一次Token

**注意**：此方法需要安装 Playwright 依赖。

#### 方法二：通过浏览器开发者工具

1. 打开 Chrome/Edge 浏览器，访问 https://www.coze.cn/store
2. **登录你的 Coze 账号**（必须先登录）
3. 按 `F12` 或右键选择「检查」打开开发者工具
4. 切换到 `Network`（网络）标签页
5. 在筛选框中输入 `list` 或 `product`
6. 刷新页面或在搜索框中输入任意关键词进行搜索
7. 在请求列表中找到名称包含 `list` 的请求
8. 点击该请求，在 `Headers`（请求头）选项卡中
9. 向下滚动找到 `Query String Parameters` 部分
10. 复制 `msToken` 字段的值（通常是一长串字符）
11. 在系统「定时设置」页面的「手动输入Token」框中粘贴并保存

#### 方法三：通过 Cookie 获取

1. 登录 Coze 商店后按 F12 打开开发者工具
2. 切换到 `Application`（应用）标签页
3. 左侧选择 `Cookies` -> `https://www.coze.cn`
4. 找到名为 `msToken` 的 Cookie 值
5. 复制该值到系统「手动输入Token」框中保存

**关于 Token 有效期：**
- msToken 会随时间过期，通常有效期为几小时到几天
- 使用自动续期功能后，系统每30分钟自动发送心跳刷新Token
- 如遇爬取失败，请先查看 Token 状态（定时设置页面底部）
- 状态显示「已过期」时，需要重新获取新的 Token

### a_bogus（可选）

如果 API 调用失败，可以额外配置 `a_bogus` 参数，获取方式同 msToken。
通常情况下，仅配置 msToken 即可正常使用。

## 目录结构说明

```
coze_crawler_web/                 # 项目根目录
├── main.py                       # FastAPI 主程序入口
├── models.py                     # SQLAlchemy 数据库模型定义
├── schemas.py                    # Pydantic 请求/响应模型
├── crawler.py                    # 爬虫核心模块（CozeSkillCrawler 类）
├── scheduler.py                  # APScheduler 定时任务调度
├── auth.py                       # 用户认证与会话管理
├── database.py                   # SQLite 数据库连接配置
├── token_keeper.py               # ✨ msToken 自动续期守护模块（新增）
├── requirements.txt              # Python 依赖包清单
├── start.sh                      # Linux/macOS 启动脚本
├── start.bat                     # Windows 启动脚本
├── static/                       # 静态资源目录
│   ├── css/
│   │   └── style.css             # 自定义样式文件
│   └── js/
│       └── app.js                # 前端交互逻辑（含Token管理）
├── templates/                    # HTML 模板目录
│   ├── index.html                # 主页面（含Token管理界面）
│   └── login.html                # 登录页面
├── data/                         # 爬取数据存储目录（自动创建）
│   ├── token_data.json           # ✨ Token和Cookie持久化文件（新增）
│   ├── 即梦/                      # 按关键词分类的子目录
│   │   ├── 20240516/             # 按日期分类的子目录
│   │   │   └── 即梦-20240516-12-30-45.xlsx
│   │   └── 20240517/
│   ├── 足球/
│   ├── image2/
│   └── ...
├── crawler.db                    # SQLite 数据库文件（自动创建）
└── README.md                     # 本说明文档
```

### 文件命名格式

**新格式（精确到秒）：**
```
{主题词}-{YYYYMMDD}-{HH}-{MM}-{SS}.xlsx
```

**示例：**
- `即梦-20260516-12-00-00.xlsx`
- `足球-20260516-14-30-25.xlsx`

**存储目录结构：**
```
data/
├── 即梦/
│   ├── 20260516/
│   │   ├── 即梦-20260516-12-00-00.xlsx
│   │   └── 即梦-20260516-18-30-45.xlsx
│   └── 20260517/
│       └── 即梦-20260517-08-00-00.xlsx
├── 足球/
├── image2/
└── ...
```

## API 接口

### 认证接口
- `POST /api/login` - 用户登录
- `POST /api/logout` - 用户登出
- `GET /api/auth/status` - 登录状态检查

### 主题词接口
- `GET /api/keywords` - 获取所有主题词
- `POST /api/keywords` - 新增主题词
- `PUT /api/keywords/{id}` - 更新主题词
- `DELETE /api/keywords/{id}` - 删除主题词

### 定时任务接口
- `GET /api/scheduler/settings` - 获取定时设置
- `POST /api/scheduler/settings` - 更新定时设置
- `GET /api/scheduler/status` - 任务状态

### ✨ Token 管理接口（新增）
- `GET /api/token/status` - 获取Token状态（状态、预览、有效性、最后刷新时间）
- `POST /api/token/refresh` - 手动触发Token刷新（发送心跳）
- `POST /api/token/interactive` - 启动浏览器交互式获取Token
- `POST /api/token/set` - 手动设置msToken

### 爬取接口
- `POST /api/crawl/manual` - 手动触发爬取
- `GET /api/crawl/progress` - 爬取进度
- `GET /api/crawl/history` - 爬取历史

### 文件接口
- `GET /api/files/tree` - 文件目录树
- `GET /api/files/download` - 下载文件

## 爬虫模块说明

### CozeSkillCrawler 类

```python
# 初始化爬虫
crawler = CozeSkillCrawler(
    ms_token="your_ms_token",      # 可选：Coze API Token
    a_bogus="your_a_bogus",        # 可选：签名参数
    request_interval=2.0,          # 请求间隔（秒）
    progress_callback=log_func     # 进度回调函数
)

# 爬取关键词
skills = crawler.crawl_keyword(
    keyword="即梦",
    max_pages=None,                # None=爬取所有页
    page_size=50,
    progress_callback=progress_func  # (current, total, message)
)

# 保存到 Excel（新格式）
filepath, count = crawler.save_to_excel(skills, keyword="即梦")
# filepath: "data/即梦/20260516/即梦-20260516-12-00-00.xlsx"

# ✨ 交互式获取 msToken（新增方法）
ms_token = crawler.get_ms_token_interactive()
# 启动浏览器，用户登录后自动获取Token并保存
```

### TokenKeeper 类（新增）

```python
from token_keeper import TokenKeeper, token_keeper

# 设置Token
token_keeper.set_token("your_ms_token", cookies_list)

# 检查Token有效性
is_valid = token_keeper.check_token_valid()

# 发送心跳刷新
success = token_keeper.heartbeat()

# 启动守护线程
token_keeper.start()  # 后台每30分钟自动刷新

# 获取状态
status = token_keeper.get_status()
# {
#   "status": "running",        # running/stopped/expired
#   "has_token": true,
#   "token_preview": "abc123...",
#   "last_refresh": "2026-05-16T12:34:56",
#   "check_interval": 1800,
#   "is_valid": true
# }
```

## 注意事项

1. **msToken 有效期**: Coze 的 msToken 可能会过期，启用自动续期后系统每30分钟自动刷新
2. **请求频率**: 爬虫已内置延迟机制（默认 2 秒），避免频繁请求触发反爬
3. **数据存储**: 爬取的 Excel 文件存储在 `data/` 目录下，按关键词和日期分类
4. **定时任务**: 服务重启后会自动恢复定时任务配置和Token守护
5. **并发控制**: 同一时间只能运行一个爬取任务，避免重复执行
6. **数据备份**: 建议定期备份 `data/` 目录和 `crawler.db` 数据库
7. **Playwright**: 交互式获取Token功能需要安装Playwright及其浏览器驱动

## 常见问题

### Q: 启动时提示 "ModuleNotFoundError"
A: 请先执行 `pip install -r requirements.txt` 安装依赖

### Q: 爬取总是失败，提示 "API返回错误"
A: 请检查「定时设置」页面底部的Token状态：
   - 状态显示「已过期」：需要重新获取Token
   - 状态显示「无效」：Token可能已失效，请重新获取

### Q: 定时任务不执行
A: 请检查「定时设置」页面是否已启用，确认间隔小时数是否正确

### Q: 如何修改默认账号密码？
A: 编辑 `auth.py` 文件中的 `VERIFY_CREDENTIALS` 函数

### Q: Excel 文件在哪里？
A: 所有爬取数据保存在 `data/{关键词}/{日期}/` 目录下

### Q: 交互式获取Token功能无法使用？
A: 请确保已安装 Playwright 依赖：
```bash
pip install playwright
playwright install chromium
```
注意：服务器环境需要支持图形界面或使用无头模式（当前实现使用可见浏览器）

### Q: Token自动续期是如何工作的？
A: 
1. 系统启动时加载 `data/token_data.json` 中保存的Token和Cookie
2. 后台守护线程每30分钟发送一次心跳请求到 Coze API
3. 心跳请求携带保存的Cookie，尝试获取新的Token
4. 如果成功刷新，新Token自动保存到文件
5. 如果刷新失败，状态更新为「已过期」，需要用户重新登录获取

## 更新日志

### v3.0.0 (2026-05-16)
- ✨ **新增**：msToken 自动续期守护线程，每30分钟自动心跳刷新
- ✨ **新增**：交互式浏览器获取Token功能（基于Playwright）
- ✨ **新增**：Token和Cookie持久化存储，服务重启自动恢复
- ✨ **新增**：Token状态实时监控面板（状态、有效性、最后刷新时间）
- ✨ **新增**：Token管理API接口（状态查询、手动刷新、交互式获取、手动设置）
- 🎨 **改进**：前端「定时设置」页面新增「msToken 自动续期管理」卡片
- 📝 **更新**：README.md 补充Token续期功能完整说明
- 🔧 **优化**：main.py 启动事件集成Token守护自动启动
- 📦 **新增**：token_keeper.py 独立模块，Token管理与守护功能

### v2.0.0 (2026-05-16)
- ✨ 改进：Excel 文件命名格式更新为精确到秒
- ✨ 改进：目录结构按关键词/日期分层存储
- ✨ 改进：save_to_excel 方法重构，返回文件路径和数量
- ✨ 新增：msToken 支持可选参数，默认可为空
- ✨ 新增：request_interval 参数配置请求间隔
- ✨ 新增：crawl_keyword 支持进度回调函数
- 📝 更新：README.md 补充解压说明、目录结构说明、msToken 获取方法
- 🔧 优化：scheduler.py 适配新的保存方法

### v1.0.0
- 🎉 初始版本发布
- 支持基本的爬取功能
- 支持 Web 管理界面
- 支持定时任务调度
