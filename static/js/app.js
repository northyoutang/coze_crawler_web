// 全局变量
let currentSection = 'keywords';
let progressInterval = null;

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname === '/') {
        loadKeywords();
        loadSchedulerSettings();
        loadSchedulerStatus();
        loadFileTree();
        updateStatusInfo();
        
        // 每30秒更新一次状态
        setInterval(updateStatusInfo, 30000);
    }
});

// ==================== 导航功能 ====================

function showSection(section) {
    // 隐藏所有section
    document.querySelectorAll('.section-content').forEach(el => {
        el.classList.add('hidden');
    });
    
    // 显示选中的section
    document.getElementById(section + '-section').classList.remove('hidden');
    
    // 更新菜单激活状态
    document.querySelectorAll('.menu-btn').forEach(btn => {
        btn.classList.remove('bg-indigo-50', 'text-indigo-600');
        btn.classList.add('hover:bg-gray-100', 'text-gray-700');
    });
    
    const activeBtn = document.querySelector(`.menu-btn[data-section="${section}"]`);
    if (activeBtn) {
        activeBtn.classList.remove('hover:bg-gray-100', 'text-gray-700');
        activeBtn.classList.add('bg-indigo-50', 'text-indigo-600');
    }
    
    currentSection = section;
    
    // 如果切换到爬取页面，加载关键词选项
    if (section === 'crawl') {
        loadCrawlKeywords();
    }
    
    // 如果切换到文件浏览，重新加载文件树
    if (section === 'files') {
        loadFileTree();
    }
}

// ==================== 登录功能 ====================

async function logout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
        window.location.href = '/login';
    } catch (error) {
        console.error('登出失败:', error);
    }
}

// ==================== Toast 提示 ====================

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg transform transition-all duration-300 z-50 ${
        type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
    }`;
    
    toast.classList.remove('translate-y-20', 'opacity-0');
    
    setTimeout(() => {
        toast.classList.add('translate-y-20', 'opacity-0');
    }, 3000);
}

// ==================== 主题词管理 ====================

async function loadKeywords() {
    try {
        const response = await fetch('/api/keywords');
        const keywords = await response.json();
        
        const tableBody = document.getElementById('keywordsTable');
        tableBody.innerHTML = '';
        
        keywords.forEach(kw => {
            const createdDate = new Date(kw.created_at).toLocaleString('zh-CN');
            tableBody.innerHTML += `
                <tr>
                    <td class="px-4 py-3 text-gray-800">${kw.id}</td>
                    <td class="px-4 py-3 text-gray-800 font-medium">${kw.keyword}</td>
                    <td class="px-4 py-3 text-gray-600">${createdDate}</td>
                    <td class="px-4 py-3">
                        <button onclick="editKeyword(${kw.id}, '${kw.keyword}')" class="text-blue-600 hover:text-blue-800 mr-3">
                            编辑
                        </button>
                        <button onclick="deleteKeyword(${kw.id})" class="text-red-600 hover:text-red-800">
                            删除
                        </button>
                    </td>
                </tr>
            `;
        });
    } catch (error) {
        console.error('加载关键词失败:', error);
    }
}

function showAddKeywordModal() {
    document.getElementById('modalTitle').textContent = '添加主题词';
    document.getElementById('editKeywordId').value = '';
    document.getElementById('keywordInput').value = '';
    document.getElementById('keywordModal').classList.remove('hidden');
}

function editKeyword(id, keyword) {
    document.getElementById('modalTitle').textContent = '编辑主题词';
    document.getElementById('editKeywordId').value = id;
    document.getElementById('keywordInput').value = keyword;
    document.getElementById('keywordModal').classList.remove('hidden');
}

function closeKeywordModal() {
    document.getElementById('keywordModal').classList.add('hidden');
}

document.getElementById('keywordForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const keywordId = document.getElementById('editKeywordId').value;
    const keyword = document.getElementById('keywordInput').value.trim();
    
    if (!keyword) {
        showToast('请输入主题词', 'error');
        return;
    }
    
    try {
        let response;
        if (keywordId) {
            // 编辑
            response = await fetch(`/api/keywords/${keywordId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keyword })
            });
        } else {
            // 添加
            response = await fetch('/api/keywords', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keyword })
            });
        }
        
        if (response.ok) {
            showToast(keywordId ? '修改成功' : '添加成功');
            closeKeywordModal();
            loadKeywords();
        } else {
            const data = await response.json();
            showToast(data.detail || '操作失败', 'error');
        }
    } catch (error) {
        console.error('操作失败:', error);
        showToast('操作失败', 'error');
    }
});

async function deleteKeyword(id) {
    if (!confirm('确定要删除这个主题词吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/keywords/${id}`, { method: 'DELETE' });
        
        if (response.ok) {
            showToast('删除成功');
            loadKeywords();
        } else {
            showToast('删除失败', 'error');
        }
    } catch (error) {
        console.error('删除失败:', error);
        showToast('删除失败', 'error');
    }
}

// ==================== 定时任务设置 ====================

async function loadSchedulerSettings() {
    try {
        const response = await fetch('/api/scheduler/settings');
        const settings = await response.json();
        
        document.getElementById('intervalHours').value = settings.crawl_interval_hours || 1;
        document.getElementById('schedulerEnabled').checked = settings.is_scheduler_enabled;
        
        updateSchedulerStatusText();
    } catch (error) {
        console.error('加载设置失败:', error);
    }
}

async function loadSchedulerStatus() {
    try {
        const response = await fetch('/api/scheduler/status');
        const status = await response.json();
        
        if (status.next_run_time) {
            const nextRun = new Date(status.next_run_time).toLocaleString('zh-CN');
            document.getElementById('nextRunTime').textContent = nextRun;
        } else {
            document.getElementById('nextRunTime').textContent = '未启用定时任务';
        }
    } catch (error) {
        console.error('加载状态失败:', error);
    }
}

function updateSchedulerStatusText() {
    const enabled = document.getElementById('schedulerEnabled').checked;
    document.getElementById('schedulerStatusText').textContent = enabled ? '已启用' : '已禁用';
}

document.getElementById('schedulerEnabled').addEventListener('change', updateSchedulerStatusText);

document.getElementById('schedulerForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const settings = {
        crawl_interval_hours: parseInt(document.getElementById('intervalHours').value),
        is_scheduler_enabled: document.getElementById('schedulerEnabled').checked
    };
    
    try {
        const response = await fetch('/api/scheduler/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        
        if (response.ok) {
            showToast('设置已保存');
            loadSchedulerStatus();
        } else {
            showToast('保存失败', 'error');
        }
    } catch (error) {
        console.error('保存设置失败:', error);
        showToast('保存失败', 'error');
    }
});

// ==================== 爬取功能 ====================

async function loadCrawlKeywords() {
    try {
        const response = await fetch('/api/keywords');
        const keywords = await response.json();
        
        const select = document.getElementById('crawlKeyword');
        select.innerHTML = '<option value="">全部关键词</option>';
        
        keywords.forEach(kw => {
            select.innerHTML += `<option value="${kw.keyword}">${kw.keyword}</option>`;
        });
    } catch (error) {
        console.error('加载爬取关键词失败:', error);
    }
}

async function startCrawl() {
    const keyword = document.getElementById('crawlKeyword').value;
    const startBtn = document.getElementById('startCrawlBtn');
    
    try {
        const url = keyword ? `/api/crawl/manual?keyword=${encodeURIComponent(keyword)}` : '/api/crawl/manual';
        const response = await fetch(url, { method: 'POST' });
        
        if (response.ok) {
            showToast('爬取任务已启动');
            startBtn.disabled = true;
            startBtn.classList.add('opacity-50', 'cursor-not-allowed');
            
            // 开始监听进度
            if (progressInterval) {
                clearInterval(progressInterval);
            }
            progressInterval = setInterval(updateCrawlProgress, 1000);
        } else {
            const data = await response.json();
            showToast(data.detail || '启动失败', 'error');
        }
    } catch (error) {
        console.error('启动爬取失败:', error);
        showToast('启动失败', 'error');
    }
}

async function updateCrawlProgress() {
    try {
        const response = await fetch('/api/crawl/progress');
        const progress = await response.json();
        
        // 更新状态
        document.getElementById('crawlStatus').textContent = progress.is_running ? '爬取中...' : '等待开始';
        document.getElementById('crawlKeywordName').textContent = progress.current_keyword || '';
        document.getElementById('skillCount').textContent = progress.skills_found;
        document.getElementById('currentPage').textContent = progress.current_page;
        document.getElementById('crawlRunning').textContent = progress.is_running ? '运行中' : '未运行';
        document.getElementById('crawlRunning').className = `text-2xl font-bold ${progress.is_running ? 'text-green-600' : 'text-purple-600'}`;
        
        // 更新进度条
        const progressBar = document.getElementById('progressBar');
        if (progress.is_running) {
            progressBar.classList.add('progress-animated');
        } else {
            progressBar.classList.remove('progress-animated');
        }
        
        // 更新日志
        const logsContainer = document.getElementById('crawlLogs');
        if (progress.logs && progress.logs.length > 0) {
            logsContainer.innerHTML = progress.logs.map(log => `<div>${log}</div>`).join('');
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }
        
        // 如果爬取完成，停止轮询
        if (!progress.is_running) {
            if (progressInterval) {
                clearInterval(progressInterval);
                progressInterval = null;
            }
            
            const startBtn = document.getElementById('startCrawlBtn');
            startBtn.disabled = false;
            startBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            
            // 重新加载文件树
            loadFileTree();
        }
    } catch (error) {
        console.error('获取进度失败:', error);
    }
}

// ==================== 文件浏览 ====================

async function loadFileTree() {
    try {
        const response = await fetch('/api/files/tree');
        const files = await response.json();
        
        const fileTree = document.getElementById('fileTree');
        
        if (!files || files.length === 0) {
            fileTree.innerHTML = '<div class="text-gray-500 text-center py-8">暂无文件，请先执行爬取</div>';
            return;
        }
        
        fileTree.innerHTML = renderFileTree(files);
    } catch (error) {
        console.error('加载文件树失败:', error);
    }
}

function renderFileTree(items) {
    let html = '';
    
    items.forEach(item => {
        if (item.type === 'folder') {
            const hasChildren = item.children && item.children.length > 0;
            html += `
                <div class="tree-item py-1">
                    <div class="flex items-center px-2 py-1 rounded hover:bg-gray-100">
                        <div onclick="toggleFolder(this)" class="flex items-center flex-1">
                            <span class="tree-toggle text-gray-400">
                                ${hasChildren ? `
                                <svg class="w-4 h-4" style="transform: rotate(0deg); transition: transform 0.2s;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                                </svg>
                                ` : `<span class="w-4 inline-block"></span>`}
                            </span>
                            <span class="text-yellow-500 mr-2">
                                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"></path>
                                </svg>
                            </span>
                            <span class="font-medium text-gray-700">${item.name}</span>
                        </div>
                    </div>
                    ${hasChildren ? `<div class="tree-children ml-6" style="display: none;">${renderFileTree(item.children)}</div>` : ''}
                </div>
            `;
        } else {
            const fileSize = item.size ? (item.size / 1024).toFixed(2) + ' KB' : '';
            html += `
                <div class="tree-item py-1">
                    <div class="flex items-center px-2 py-1 rounded hover:bg-gray-100 ml-6">
                        <div onclick="downloadFile('${item.path}')" class="flex items-center flex-1 cursor-pointer">
                            <span class="text-green-500 mr-2">
                                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd"></path>
                                </svg>
                            </span>
                            <span class="text-gray-700">${item.name}</span>
                            <span class="ml-auto text-xs text-gray-400 mr-2">${fileSize}</span>
                        </div>
                        <button onclick="deleteFileOrFolder('${item.path}', 'file', event)" class="text-red-500 hover:text-red-700 p-1" title="删除文件">🗑️</button>
                    </div>
                </div>
            `;
        }
    });
    
    return html;
}

async function deleteFileOrFolder(path, type, event) {
    event.stopPropagation();
    
    const itemType = type === 'folder' ? '目录' : '文件';
    const itemName = path.split('/').pop();
    
    if (!confirm(`确定要删除${itemType} "${itemName}" 吗？${type === 'folder' ? '注意：只能删除空目录。' : ''}`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/files/delete?path=${encodeURIComponent(path)}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            const result = await response.json();
            showToast(result.message || '删除成功');
            await loadFileTree();
        } else {
            const error = await response.json();
            showToast(error.detail || '删除失败', 'error');
        }
    } catch (error) {
        console.error('删除失败:', error);
        showToast('删除失败，请重试', 'error');
    }
}

function toggleFolder(element) {
    if (!element) return;

    const svgIcon = element.querySelector('.tree-toggle svg');
    const treeItem = element.closest('.tree-item');
    if (!treeItem) return;

    const children = treeItem.querySelector('.tree-children');
    if (!children) return;

    // 🔴 用 style.display 代替 classList，不需要依赖 CSS
    if (children.style.display === 'none' || children.style.display === '') {
        children.style.display = 'block';
        if (svgIcon) svgIcon.style.transform = 'rotate(90deg)';
    } else {
        children.style.display = 'none';
        if (svgIcon) svgIcon.style.transform = 'rotate(0deg)';
    }
}

function downloadFile(path) {
    window.open(`/api/files/download?path=${encodeURIComponent(path)}`, '_blank');
}

// ==================== 系统状态 ====================

async function updateStatusInfo() {
    try {
        const [schedulerRes, crawlRes, historyRes] = await Promise.all([
            fetch('/api/scheduler/status'),
            fetch('/api/crawl/progress'),
            fetch('/api/crawl/history?limit=1')
        ]);
        
        const schedulerStatus = await schedulerRes.json();
        const crawlStatus = await crawlRes.json();
        const history = await historyRes.json();
        
        const lastCrawl = history.length > 0 ? history[0] : null;
        
        let statusHtml = `
            <div class="flex justify-between items-center">
                <span class="text-gray-600">定时任务:</span>
                <span class="px-2 py-1 rounded-full text-xs ${schedulerStatus.is_enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}">
                    ${schedulerStatus.is_enabled ? '已启用' : '已禁用'}
                </span>
            </div>
            <div class="flex justify-between items-center">
                <span class="text-gray-600">爬取状态:</span>
                <span class="px-2 py-1 rounded-full text-xs ${crawlStatus.is_running ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'}">
                    ${crawlStatus.is_running ? '运行中' : '空闲'}
                </span>
            </div>
        `;
        
        if (lastCrawl) {
            const crawlStatusClass = lastCrawl.status === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700';
            statusHtml += `
                <div class="flex justify-between items-center">
                    <span class="text-gray-600">上次爬取:</span>
                    <span class="px-2 py-1 rounded-full text-xs ${crawlStatusClass}">
                        ${lastCrawl.status === 'success' ? '成功' : '失败'}
                    </span>
                </div>
            `;
        }
        
        document.getElementById('statusInfo').innerHTML = statusHtml;
    } catch (error) {
        console.error('更新状态失败:', error);
    }
}
