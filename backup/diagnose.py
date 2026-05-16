#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统诊断脚本 - 快速定位启动问题
"""

import sys
import os

print("=" * 60)
print("🔍 Coze Crawler Web 系统诊断")
print("=" * 60)

# -----------------------------------------------------------------------------
# 1. 检查Python版本
# -----------------------------------------------------------------------------
print("\n📌 1. Python版本检查")
print(f"   当前版本: {sys.version}")
if sys.version_info >= (3, 8):
    print("   ✅ Python版本符合要求 (>=3.8)")
else:
    print("   ❌ Python版本过低，需要3.8+")

# -----------------------------------------------------------------------------
# 2. 检查依赖是否安装
# -----------------------------------------------------------------------------
print("\n📌 2. 依赖包检查")
required_packages = [
    ("fastapi", "FastAPI"),
    ("uvicorn", "Uvicorn"),
    ("sqlalchemy", "SQLAlchemy"),
    ("playwright", "Playwright"),
    ("pandas", "Pandas"),
    ("openpyxl", "OpenPyXL"),
    ("apscheduler", "APScheduler"),
    ("python-multipart", "Python-Multipart"),
    ("requests", "Requests"),
]

missing_packages = []
for pkg_name, display_name in required_packages:
    try:
        __import__(pkg_name.replace("-", "_"))
        print(f"   ✅ {display_name}")
    except ImportError:
        print(f"   ❌ {display_name} - 未安装")
        missing_packages.append(display_name)

if missing_packages:
    print(f"\n   ⚠️  缺少 {len(missing_packages)} 个依赖包")
    print(f"   请执行: pip install {' '.join(missing_packages)}")
else:
    print("\n   ✅ 所有依赖包已安装")

# -----------------------------------------------------------------------------
# 3. 检查文件结构
# -----------------------------------------------------------------------------
print("\n📌 3. 文件结构检查")
required_files = [
    "main.py",
    "models.py",
    "schemas.py",
    "crawler.py",
    "scheduler.py",
    "auth.py",
    "database.py",
    "token_keeper.py",
    "templates/index.html",
    "templates/login.html",
    "static/js/app.js",
    "static/css/style.css",
]

missing_files = []
for file_path in required_files:
    if os.path.exists(file_path):
        print(f"   ✅ {file_path}")
    else:
        print(f"   ❌ {file_path} - 缺失")
        missing_files.append(file_path)

if missing_files:
    print(f"\n   ⚠️  缺少 {len(missing_files)} 个文件")
else:
    print("\n   ✅ 所有必需文件存在")

# -----------------------------------------------------------------------------
# 4. 检查端口占用
# -----------------------------------------------------------------------------
print("\n📌 4. 端口检查")
import socket

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("0.0.0.0", port))
            return False
        except OSError:
            return True

for port in [8000, 8001, 8080]:
    if is_port_in_use(port):
        print(f"   ❌ 端口 {port} - 被占用")
    else:
        print(f"   ✅ 端口 {port} - 可用")

# -----------------------------------------------------------------------------
# 5. 尝试导入模块
# -----------------------------------------------------------------------------
print("\n📌 5. 模块导入测试")
test_modules = [
    ("database", "数据库模块"),
    ("models", "模型模块"),
    ("schemas", "数据校验模块"),
    ("auth", "认证模块"),
    ("crawler", "爬虫模块"),
    ("scheduler", "定时任务模块"),
    ("token_keeper", "Token守护模块"),
]

import_errors = []
for module_name, display_name in test_modules:
    try:
        __import__(module_name)
        print(f"   ✅ {display_name}")
    except Exception as e:
        print(f"   ❌ {display_name} - 导入失败: {e}")
        import_errors.append((display_name, str(e)))

# -----------------------------------------------------------------------------
# 6. 检查Playwright浏览器
# -----------------------------------------------------------------------------
print("\n📌 6. Playwright浏览器检查")
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browsers = []
        if hasattr(p, 'chromium'):
            browsers.append("Chromium")
        print(f"   ✅ Playwright可用，浏览器: {', '.join(browsers)}")
except Exception as e:
    print(f"   ❌ Playwright检查失败: {e}")
    print("   请执行: playwright install chromium")

# -----------------------------------------------------------------------------
# 总结
# -----------------------------------------------------------------------------
print("\n" + "=" * 60)
print("📊 诊断总结")
print("=" * 60)

problems = []
if missing_packages:
    problems.append(f"缺少依赖包: {', '.join(missing_packages)}")
if missing_files:
    problems.append(f"缺少文件: {len(missing_files)} 个")
if import_errors:
    problems.append(f"模块导入错误: {len(import_errors)} 个")

if not problems:
    print("\n✅ 系统检查全部通过！")
    print("\n启动命令:")
    print("   python main.py")
    print("\n如果仍然无法启动，请检查:")
    print("   1. 防火墙是否阻止了端口")
    print("   2. 是否有其他程序占用了8000端口")
    print("   3. 查看控制台输出的详细错误信息")
else:
    print("\n❌ 发现以下问题:")
    for i, problem in enumerate(problems, 1):
        print(f"   {i}. {problem}")
    
    print("\n建议修复步骤:")
    print("   1. 安装缺失的依赖包")
    print("   2. 确保所有文件都已正确解压")
    print("   3. 重新运行诊断脚本确认问题已解决")

print("\n" + "=" * 60)
