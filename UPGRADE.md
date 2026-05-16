# 扣子技能爬取系统 v2.0 升级说明

## 主要变化

### 1. 爬虫核心重构
- **移除 msToken 依赖**：不再需要手动配置 msToken 或 Cookie
- **采用 Playwright 浏览器自动化**：直接使用浏览器访问技能商店，自动捕获 API 响应
- **更稳定的数据获取**：通过真实浏览器环境模拟用户操作，避免反爬限制

### 2. 文件变更

#### 核心文件
- `crawler.py` - 完全重写，使用 Playwright 替代 requests
- `scheduler.py` - 移除 msToken 相关参数传递
- `main.py` - 移除 token_keeper 相关 API
- `models.py` - Setting 模型移除 ms_token 和 a_bogus 字段
- `schemas.py` - 相应简化数据模型
- `templates/index.html` - 移除 Token 设置界面
- `static/js/app.js` - 移除 Token 管理功能

#### 新增文件
- `UPGRADE.md` - 本文档

### 3. 新增依赖
```
playwright>=1.40.0
```

## 安装步骤

### 1. 安装 Python 依赖
```bash
pip install -r requirements.txt
```

### 2. 安装 Playwright 浏览器
```bash
playwright install chromium
```

### 3. 启动系统
```bash
python main.py
```

## 使用变化

### 定时设置页面
- 不再需要填写 msToken 和 a_bogus 字段
- 新增浏览器自动化说明提示
- 配置更简单，只需要设置爬取间隔和启用状态

### 爬取过程
- 系统会自动启动无头浏览器
- 访问扣子技能商店并搜索关键词
- 自动捕获 API 响应数据
- 分页滚动获取完整数据

## 注意事项

### 1. 首次运行
- 首次运行需要下载 Chromium 浏览器（约 100MB）
- 确保网络环境可以访问 `https://www.coze.cn`

### 2. 数据库迁移
- Setting 表结构已变化，建议删除旧的数据库文件让系统自动重建
- 或者手动执行 SQL 迁移：
```sql
ALTER TABLE settings DROP COLUMN ms_token;
ALTER TABLE settings DROP COLUMN a_bogus;
```

### 3. 性能考虑
- Playwright 会占用一定内存（每个浏览器实例约 100-200MB）
- 爬取速度取决于网络和页面加载速度
- 建议爬取间隔不小于 1 小时

## 优势对比

| 特性 | v1.0 (requests) | v2.0 (Playwright) |
|------|-----------------|-------------------|
| msToken 配置 | 需要手动获取 | **无需配置** |
| 反爬应对 | 容易被限制 | 模拟真实浏览器，更稳定 |
| 维护成本 | 需要频繁更新签名算法 | **零维护** |
| 数据完整性 | 依赖 API 稳定性 | 直接捕获真实响应 |
| 部署难度 | 高 | **低** |

## 故障排查

### 1. 浏览器启动失败
```bash
# 重新安装浏览器
playwright install --force chromium

# 检查依赖
playwright install-deps chromium
```

### 2. 页面加载超时
- 检查网络连接
- 确认可以访问 `https://www.coze.cn`
- 考虑增加请求间隔时间

### 3. 数据获取为空
- 检查浏览器日志输出
- 确认搜索关键词是否正确
- 尝试手动访问页面确认是否有数据

## 回滚方案

如需回滚到 v1.0 版本：
1. 从 backup 目录恢复原始文件
2. 恢复 requirements.txt（移除 playwright）
3. 恢复数据库表结构（添加 ms_token 和 a_bogus 字段）
