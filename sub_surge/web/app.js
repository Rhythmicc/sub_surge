// Surge 订阅配置管理 - 前端逻辑

// 配置数据
let globalConfig = null;
let analysisResult = null;  // 存储分析结果
let aiModelsCache = null;  // AI模型列表缓存
let isEditingAirport = false;  // 是否处于编辑机场模式
let editingAirportName = null;  // 当前编辑的机场名称

// API基础URL（根据实际情况修改）
const API_BASE = 'http://localhost:8000';

// 工具函数
function showAlert(message, type = 'success') {
    const container = document.getElementById('alert-container');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    container.appendChild(alert);
    
    setTimeout(() => {
        alert.remove();
    }, 3000);
}

// 加载AI模型列表
async function loadAIModels() {
    console.log('loadAIModels 被调用');
    if (aiModelsCache) {
        console.log('使用缓存的模型列表', aiModelsCache.length);
        populateModelSelect(aiModelsCache);
        return;
    }
    
    try {
        console.log('从API获取模型列表');
        const response = await fetch(`${API_BASE}/api/ai-models`);
        const models = await response.json();
        console.log('获取到模型数量:', models.length);
        aiModelsCache = models;
        populateModelSelect(models);
    } catch (error) {
        console.error('加载AI模型列表失败:', error);
        showAlert('加载AI模型列表失败，使用默认列表', 'warning');
    }
}

// 填充模型下拉列表
function populateModelSelect(models, sortBy = 'default', searchQuery = '') {
    console.log('populateModelSelect 被调用', {modelCount: models.length, sortBy, searchQuery});
    const select = document.getElementById('ai_model');
    if (!select) {
        console.error('找不到 ai_model 元素');
        return;
    }
    const currentValue = select.value;
    
    // 过滤模型
    let filteredModels = models;
    if (searchQuery) {
        const query = searchQuery.toLowerCase();
        filteredModels = models.filter(m => 
            m.name.toLowerCase().includes(query) || 
            m.id.toLowerCase().includes(query) ||
            (m.description && m.description.toLowerCase().includes(query))
        );
    }
    
    // 排序模型
    let sortedModels = [...filteredModels];
    switch(sortBy) {
        case 'price-asc':
            sortedModels.sort((a, b) => {
                const priceA = parseFloat(a.pricing.prompt) + parseFloat(a.pricing.completion);
                const priceB = parseFloat(b.pricing.prompt) + parseFloat(b.pricing.completion);
                return priceA - priceB;
            });
            break;
        case 'price-desc':
            sortedModels.sort((a, b) => {
                const priceA = parseFloat(a.pricing.prompt) + parseFloat(a.pricing.completion);
                const priceB = parseFloat(b.pricing.prompt) + parseFloat(b.pricing.completion);
                return priceB - priceA;
            });
            break;
        case 'name':
            sortedModels.sort((a, b) => a.name.localeCompare(b.name));
            break;
        case 'free-first':
            sortedModels.sort((a, b) => {
                if (a.is_free && !b.is_free) return -1;
                if (!a.is_free && b.is_free) return 1;
                return a.name.localeCompare(b.name);
            });
            break;
        case 'vendor':
            sortedModels.sort((a, b) => {
                const vendorCompare = (a.vendor || '').localeCompare(b.vendor || '');
                if (vendorCompare !== 0) return vendorCompare;
                return a.name.localeCompare(b.name);
            });
            break;
    }
    
    // 清空现有选项
    select.innerHTML = '';
    
    // 添加所有模型
    sortedModels.forEach(model => {
        const option = document.createElement('option');
        option.value = model.id;
        option.dataset.modelData = JSON.stringify(model);
        
        // 格式化显示文本
        const icon = model.is_free ? '🆓' : '💎';
        const promptPrice = parseFloat(model.pricing.prompt) * 1000000;
        const completionPrice = parseFloat(model.pricing.completion) * 1000000;
        
        if (model.is_free) {
            option.textContent = `${icon} ${model.name} (免费)`;
        } else {
            option.textContent = `${icon} ${model.name} ($${promptPrice.toFixed(3)}/$${completionPrice.toFixed(3)})`;
        }
        
        select.appendChild(option);
    });
    
    // 更新计数
    const countSpan = document.getElementById('model-count');
    if (countSpan) {
        countSpan.textContent = `(共 ${sortedModels.length} 个模型)`;
    }
    
    // 恢复之前选中的值
    if (currentValue) {
        select.value = currentValue;
    }
}

// 搜索模型
function filterModels() {
    console.log('filterModels 被调用');
    if (!aiModelsCache) {
        console.warn('模型缓存为空');
        return;
    }
    
    const searchQuery = document.getElementById('model-search').value;
    const sortBy = document.getElementById('model-sort').value;
    console.log('搜索:', searchQuery, '排序:', sortBy);
    populateModelSelect(aiModelsCache, sortBy, searchQuery);
}

// 排序模型
function sortModels() {
    console.log('sortModels 被调用');
    if (!aiModelsCache) {
        console.warn('模型缓存为空');
        return;
    }
    
    const searchQuery = document.getElementById('model-search').value;
    const sortBy = document.getElementById('model-sort').value;
    console.log('搜索:', searchQuery, '排序:', sortBy);
    populateModelSelect(aiModelsCache, sortBy, searchQuery);
}

// 切换标签页
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        // 移除所有active类
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        // 添加active类到当前标签
        tab.classList.add('active');
        const tabId = tab.dataset.tab;
        document.getElementById(tabId).classList.add('active');
        
        // 如果切换到机场管理页，刷新列表
        if (tabId === 'airports') {
            loadAirports();
        } else if (tabId === 'export-import') {
            loadConfigPreview();
        } else if (tabId === 'global-config') {
            // 切换到全局配置时先加载AI模型列表，再加载配置
            loadAIModels().then(() => {
                loadGlobalConfig();
            });
        } else if (tabId === 'logs') {
            // 切换到日志页，加载日志
            loadLogs();
        }
    });
});

// 新增：添加机场按钮事件
document.getElementById('btn-add-airport-trigger')?.addEventListener('click', () => {
    isEditingAirport = false;
    editingAirportName = null;
    
    // 重置页面标题和按钮
    document.querySelector('#add-airport h2').textContent = '添加新机场';
    const submitBtn = document.querySelector('#add-airport-form button[type="submit"]');
    submitBtn.textContent = '添加机场';
    submitBtn.className = 'btn btn-primary';
    
    // 重置表单
    const form = document.getElementById('add-airport-form');
    form.reset();
    document.getElementById('name').disabled = false;
    
    // 切换到添加机场标签页（触发隐藏的标签点击）
    document.querySelector('.tab[data-tab="add-airport"]').click();
});

// 加载机场列表
async function loadAirports() {
    try {
        const response = await fetch(`${API_BASE}/api/airports`);
        const data = await response.json();
        globalConfig = data;
        
        const container = document.getElementById('airport-list');
        container.innerHTML = '';
        
        if (Object.keys(data.airports).length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #666; padding: 40px;">暂无机场配置，请添加</p>';
            return;
        }
        
        const airportNames = [];
        Object.values(data.airports).forEach(airport => {
            const card = createAirportCard(airport);
            container.appendChild(card);
            airportNames.push(airport.name);
        });
        
        // 自动检测连通性
        if (airportNames.length > 0) {
            checkAirportsHealth(airportNames);
        }
    } catch (error) {
        showAlert('加载机场列表失败: ' + error.message, 'error');
    }
}

// 创建机场卡片
function createAirportCard(airport) {
    const card = document.createElement('div');
    card.className = 'airport-card';
    
    // 构造腾讯云链接
    const txcosUrl = globalConfig.txcos_domain 
        ? `${globalConfig.txcos_domain.replace(/\/$/, '')}/${airport.key}`
        : '';
    
    card.innerHTML = `
        <input type="checkbox" class="airport-select" value="${airport.name}" onchange="updateBatchActionState()">
        <h3 style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
            <span style="display: flex; align-items: center; gap: 8px;">
                <span class="status-dot" id="status-${airport.name}" title="未检测"></span>
                ${airport.name}
            </span>
            ${txcosUrl ? `<button class="btn btn-sm" onclick="copyToClipboard('${txcosUrl}')" style="padding: 4px 8px; font-size: 12px; background: #667eea; color: white; border: none; border-radius: 4px; cursor: pointer;" title="复制腾讯云链接">📋 复制</button>` : ''}
        </h3>
        <p style="font-size: 12px; color: #888;"><strong>订阅链接:</strong> <span style="display: inline-block; max-width: 75%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; vertical-align: middle;" title="${airport.url}">${airport.url}</span></p>
        ${txcosUrl ? `<p style="font-size: 12px; color: #888;"><strong>腾讯云链接:</strong> <span style="display: inline-block; max-width: 75%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; vertical-align: middle;" title="${txcosUrl}">${txcosUrl}</span></p>` : '<p style="font-size: 12px; color: #ccc; font-style: italic;">（未配置腾讯云域名）</p>'}
        <p><strong>存储路径:</strong> ${airport.key}</p>
        <p><strong>重置周期:</strong> ${airport.reset_day}天</p>
        <div class="actions">
            <button class="btn btn-primary btn-sm" onclick="updateAirport('${airport.name}')">
                更新
            </button>
            <button class="btn btn-secondary btn-sm" onclick="editAirport('${airport.name}')">
                编辑
            </button>
            <button class="btn btn-danger btn-sm" onclick="deleteAirport('${airport.name}')">
                删除
            </button>
        </div>
    `;
    
    return card;
}

// 批量操作状态更新
function updateBatchActionState() {
    const checkboxes = document.querySelectorAll('.airport-select:checked');
    const allCheckboxes = document.querySelectorAll('.airport-select');
    const count = checkboxes.length;
    
    // Update count
    const countSpan = document.getElementById('selected-count');
    if (countSpan) countSpan.textContent = count;
    
    // Update Select All checkbox state
    const selectAllCb = document.getElementById('select-all-airports');
    if (selectAllCb) {
        selectAllCb.checked = (count > 0 && count === allCheckboxes.length);
        selectAllCb.indeterminate = (count > 0 && count < allCheckboxes.length);
    }
    
    // Enable/Disable buttons
    const btnDelete = document.getElementById('btn-batch-delete');
    
    if (count > 0) {
        if(btnDelete) { btnDelete.disabled = false; btnDelete.style.opacity = '1'; btnDelete.style.cursor = 'pointer'; }
    } else {
        if(btnDelete) { btnDelete.disabled = true; btnDelete.style.opacity = '0.6'; btnDelete.style.cursor = 'not-allowed'; }
    }
}

// 复制到剪贴板
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showAlert('已复制到剪贴板', 'success');
    }).catch(() => {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showAlert('已复制到剪贴板', 'success');
    });
}

// 全选/反选
function toggleSelectAll(source) {
    const checkboxes = document.querySelectorAll('.airport-select');
    checkboxes.forEach(cb => {
        cb.checked = source.checked;
    });
    updateBatchActionState();
}

// 批量删除
async function deleteSelectedAirports() {
    const checkboxes = document.querySelectorAll('.airport-select:checked');
    if (checkboxes.length === 0) return;
    
    if (!confirm(`确定要删除选中的 ${checkboxes.length} 个机场配置吗？`)) {
        return;
    }
    
    let successCount = 0;
    for (const checkbox of checkboxes) {
        const name = checkbox.value;
        try {
            const response = await fetch(`${API_BASE}/api/airports/${name}`, {
                method: 'DELETE'
            });
            if (response.ok) successCount++;
        } catch (error) {
            console.error(`删除 ${name} 失败:`, error);
        }
    }
    
    showAlert(`成功删除 ${successCount} 个机场`);
    loadAirports();
    updateBatchActionState(); 
}

// 批量检测连通性（现改为通用检测函数）
async function checkAirportsHealth(names) {
    if (!names || names.length === 0) return;
    
    // 设置为检测中状态
    names.forEach(name => {
        const dot = document.getElementById(`status-${name}`);
        if(dot) {
            dot.title = "检测中...";
            dot.className = "status-dot status-yellow";
        }
    });

    try {
        const response = await fetch(`${API_BASE}/api/check-availabilities`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ names: names })
        });
        
        const results = await response.json();
        
        Object.entries(results).forEach(([name, statusData]) => {
             const dot = document.getElementById(`status-${name}`);
             if (dot) {
                 if (statusData.status === 'ok') {
                     dot.className = "status-dot status-green";
                     dot.title = "正常访问";
                 } else {
                     dot.className = "status-dot status-red";
                     dot.title = `无法访问 (${statusData.code || 'Error'})`;
                 }
             }
        });
        
    } catch (e) {
        console.error('检测请求失败', e);
        // 如果失败，将状态标记为红色或重置
        names.forEach(name => {
            const dot = document.getElementById(`status-${name}`);
            if(dot && dot.className.includes("status-yellow")) {
                dot.className = "status-dot status-red";
                dot.title = "检测失败";
            }
        });
    }
}

// 预览订阅内容
document.getElementById('preview-btn').addEventListener('click', async () => {
    const urlInput = document.getElementById('url');
    const url = urlInput.value;
    
    if (!url) {
        showAlert('请先填写订阅链接', 'error');
        return;
    }
    
    const previewBtn = document.getElementById('preview-btn');
    const originalText = previewBtn.textContent;
    previewBtn.textContent = '⏳ 下载中...';
    previewBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/api/preview`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url })
        });
        
        if (response.ok) {
            const data = await response.json();
            displaySubscriptionPreview(data);
            showAlert('订阅内容已加载');
        } else {
            const error = await response.json();
            showAlert('预览失败: ' + error.detail, 'error');
        }
    } catch (error) {
        showAlert('预览失败: ' + error.message, 'error');
    } finally {
        previewBtn.textContent = originalText;
        previewBtn.disabled = false;
    }
});

// 显示订阅内容预览
function displaySubscriptionPreview(data) {
    const previewDiv = document.getElementById('subscription-preview');
    const infoDiv = document.getElementById('preview-info');
    const contentTextarea = document.getElementById('subscription-content');
    
    infoDiv.innerHTML = `
        <span>📊 总行数: <strong>${data.line_count}</strong></span>
        <span style="margin-left: 20px;">🔐 Base64编码: <strong>${data.is_base64 ? '是' : '否'}</strong></span>
        <span style="margin-left: 20px;">👁️ 显示: <strong>前50行</strong></span>
    `;
    
    contentTextarea.value = data.content;
    contentTextarea.dataset.fullContent = data.content; // 保存完整内容
    previewDiv.style.display = 'block';
    
    // 滚动到预览区域
    previewDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// 手动编辑内容
document.getElementById('edit-content-btn').addEventListener('click', () => {
    const contentTextarea = document.getElementById('subscription-content');
    const editBtn = document.getElementById('edit-content-btn');
    
    if (contentTextarea.hasAttribute('readonly')) {
        contentTextarea.removeAttribute('readonly');
        contentTextarea.style.borderColor = '#2196F3';
        contentTextarea.style.background = '#fff';
        editBtn.textContent = '💾 保存编辑';
        showAlert('现在可以编辑订阅内容了', 'info');
    } else {
        contentTextarea.setAttribute('readonly', 'readonly');
        contentTextarea.style.borderColor = '#ddd';
        contentTextarea.style.background = '#f5f5f5';
        editBtn.textContent = '✏️ 手动编辑';
        showAlert('编辑已保存');
    }
});

// 关闭预览
document.getElementById('close-preview-btn').addEventListener('click', () => {
    document.getElementById('subscription-preview').style.display = 'none';
});

// 分析预览的内容
document.getElementById('analyze-content-btn').addEventListener('click', async () => {
    const contentTextarea = document.getElementById('subscription-content');
    const content = contentTextarea.value;
    
    if (!content) {
        showAlert('订阅内容为空', 'error');
        return;
    }
    
    const analyzeBtn = document.getElementById('analyze-content-btn');
    const originalText = analyzeBtn.textContent;
    analyzeBtn.textContent = '⏳ 分析中...';
    analyzeBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/api/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content })
        });
        
        if (response.ok) {
            analysisResult = await response.json();
            console.log('🤖 AI分析结果:', analysisResult);
            displayAnalysisResult(analysisResult);
            showAlert('分析完成！查看推荐配置');
            
            // 滚动到分析结果
            document.getElementById('analysis-result').scrollIntoView({ 
                behavior: 'smooth', 
                block: 'nearest' 
            });
        } else {
            const error = await response.json();
            showAlert('分析失败: ' + error.detail, 'error');
        }
    } catch (error) {
        showAlert('分析失败: ' + error.message, 'error');
    } finally {
        analyzeBtn.textContent = originalText;
        analyzeBtn.disabled = false;
    }
});

// 智能分析订阅链接（直接从URL分析）
document.getElementById('analyze-btn').addEventListener('click', async () => {
    const urlInput = document.getElementById('url');
    const url = urlInput.value;
    
    if (!url) {
        showAlert('请先填写订阅链接', 'error');
        return;
    }
    
    const analyzeBtn = document.getElementById('analyze-btn');
    const originalText = analyzeBtn.textContent;
    analyzeBtn.textContent = '⏳ 分析中...';
    analyzeBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/api/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url })
        });
        
        if (response.ok) {
            analysisResult = await response.json();
            console.log('🤖 AI分析结果:', analysisResult);
            displayAnalysisResult(analysisResult);
            showAlert('分析完成！查看推荐配置');
        } else {
            const error = await response.json();
            showAlert('分析失败: ' + error.detail, 'error');
        }
    } catch (error) {
        showAlert('分析失败: ' + error.message, 'error');
    } finally {
        analyzeBtn.textContent = originalText;
        analyzeBtn.disabled = false;
    }
});

// 显示分析结果
function displayAnalysisResult(result) {
    const resultDiv = document.getElementById('analysis-result');
    const contentDiv = document.getElementById('analysis-content');
    
    if (result.error) {
        contentDiv.innerHTML = `
            <p style="color: #d32f2f;">❌ ${result.error}</p>
        `;
        resultDiv.style.display = 'block';
        return;
    }
    
    const analysis = result.analysis || {};
    const suggestions = result.suggestions || {};
    const analysisMethod = result.analysis_method || 'static';
    
    // 分析方法标识
    const methodBadge = analysisMethod === 'ai' 
        ? '<span style="background: #4CAF50; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; margin-left: 8px;">🤖 AI增强</span>'
        : analysisMethod === 'static'
        ? '<span style="background: #FF9800; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; margin-left: 8px;">📊 规则分析</span>'
        : '';
    
    let html = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-bottom: 15px;">
            <div>
                <strong>节点数量:</strong> ${analysis.node_count || 0}
            </div>
            <div>
                <strong>格式类型:</strong> ${analysis.format_type || 'unknown'}
            </div>
            <div>
                <strong>置信度:</strong> ${(result.confidence * 100).toFixed(0)}% ${methodBadge}
            </div>
        </div>
    `;
    
    if (analysis.countries && analysis.countries.length > 0) {
        html += `
            <div style="margin-bottom: 10px;">
                <strong>检测到的国家/地区:</strong><br>
                <div style="margin-top: 5px; display: flex; flex-wrap: wrap; gap: 5px;">
                    ${analysis.countries.map(c => `<span style="background: #fff; padding: 3px 8px; border-radius: 4px; font-size: 12px;">${c}</span>`).join('')}
                </div>
            </div>
        `;
    }
    
    if (suggestions.name) {
        html += `
            <div style="margin-top: 10px;">
                <strong>建议机场名称:</strong> ${suggestions.name}
            </div>
        `;
    }
    
    // 显示AI特殊建议
    if (suggestions.special_notes) {
        html += `
            <div style="margin-top: 10px; padding: 10px; background: #fff3cd; border-radius: 4px;">
                <strong>💡 AI建议:</strong> ${suggestions.special_notes}
            </div>
        `;
    }
    
    // 显示AI错误（如果有）
    if (result.ai_error) {
        html += `
            <div style="margin-top: 10px; padding: 8px; background: #fff; border-radius: 4px; font-size: 12px; color: #666;">
                ⚠️ AI分析不可用（已使用规则分析）: ${result.ai_error}
            </div>
        `;
    }
    
    contentDiv.innerHTML = html;
    resultDiv.style.display = 'block';
}

// 应用推荐配置
document.getElementById('apply-suggestions').addEventListener('click', () => {
    if (!analysisResult) {
        showAlert('没有分析结果', 'error');
        return;
    }
    
    // 只在名称为空时才应用推荐的机场名称（避免覆盖已有的名称）
    if (analysisResult.suggestions.name && !document.getElementById('name').value) {
        document.getElementById('name').value = analysisResult.suggestions.name;
    }
    
    if (analysisResult.is_node_list !== undefined) {
        document.getElementById('is_node_list').checked = analysisResult.is_node_list;
    }
    
    // 应用排除关键词
    if (analysisResult.exclude_keywords && analysisResult.exclude_keywords.length > 0) {
        document.getElementById('exclude_keywords').value = analysisResult.exclude_keywords.join(', ');
    }
    
    // 应用国家映射
    if (analysisResult.country_mapping && Object.keys(analysisResult.country_mapping).length > 0) {
        document.getElementById('country_mapping').value = JSON.stringify(analysisResult.country_mapping, null, 2);
    }
    
    showAlert('已应用AI推荐配置！请检查并补充其他信息');
    
    // 滚动到机场名称输入框
    document.getElementById('name').focus();
});

// 添加机场
document.getElementById('add-airport-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {
        name: isEditingAirport ? editingAirportName : formData.get('name'),
        url: formData.get('url'),
        key: formData.get('key'),
        reset_day: parseInt(formData.get('reset_day')) || 30,
        is_node_list: formData.get('is_node_list') === 'on'
    };
    
    // 处理排除关键词
    const excludeKeywords = document.getElementById('exclude_keywords').value;
    if (excludeKeywords) {
        data.exclude_keywords = excludeKeywords.split(',').map(k => k.trim());
    }
    
    // 处理国家映射
    const countryMapping = document.getElementById('country_mapping').value;
    if (countryMapping) {
        try {
            data.country_mapping = JSON.parse(countryMapping);
        } catch (error) {
            showAlert('国家映射JSON格式错误', 'error');
            return;
        }
    }
    
    try {
        let response;
        let successMessage;
        
        // 调试：打印发送的数据
        console.log('📤 发送的机场数据:', data);
        
        if (isEditingAirport) {
            // 更新模式：调用 PUT API
            response = await fetch(`${API_BASE}/api/airports/${editingAirportName}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            successMessage = '机场配置已更新！';
        } else {
            // 添加模式：调用 POST API
            response = await fetch(`${API_BASE}/api/airports`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            successMessage = '机场添加成功！';
        }
        
        if (response.ok) {
            showAlert(successMessage);
            e.target.reset();
            
            // 重置编辑模式
            isEditingAirport = false;
            editingAirportName = null;
            document.querySelector('#add-airport h2').textContent = '添加新机场';
            const submitBtn = document.querySelector('#add-airport-form button[type="submit"]');
            submitBtn.textContent = '添加机场';
            submitBtn.className = 'btn btn-primary';
            document.getElementById('name').disabled = false;
            
            // 切换到机场管理页
            document.querySelector('.tab[data-tab="airports"]').click();
        } else {
            const error = await response.json();
            console.error('❌ 错误响应:', error);
            showAlert((isEditingAirport ? '更新' : '添加') + '失败: ' + error.detail, 'error');
        }
    } catch (error) {
        console.error('❌ 请求失败:', error);
        showAlert((isEditingAirport ? '更新' : '添加') + '失败: ' + error.message, 'error');
    }
});

// 更新机场
async function updateAirport(name) {
    try {
        const response = await fetch(`${API_BASE}/api/airports/${name}/update`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showAlert(`机场 ${name} 更新成功！`);
        } else {
            const error = await response.json();
            showAlert('更新失败: ' + error.detail, 'error');
        }
    } catch (error) {
        showAlert('更新失败: ' + error.message, 'error');
    }
}

// 编辑机场
function editAirport(name) {
    const airport = globalConfig.airports[name];
    if (!airport) return;
    
    // 设置编辑模式
    isEditingAirport = true;
    editingAirportName = name;
    
    // 切换到添加机场页
    document.querySelector('.tab[data-tab="add-airport"]').click();
    
    // 更新页面标题和按钮文本
    document.querySelector('#add-airport h2').textContent = '编辑机场配置';
    const submitBtn = document.querySelector('#add-airport-form button[type="submit"]');
    submitBtn.textContent = '更新机场';
    submitBtn.className = 'btn btn-success';  // 改变按钮颜色
    
    // 填充表单（包括订阅链接）
    document.getElementById('name').value = airport.name;
    document.getElementById('name').disabled = true; // 名称不可修改
    document.getElementById('url').value = airport.url; // 预填充订阅链接
    document.getElementById('key').value = airport.key;
    document.getElementById('reset_day').value = airport.reset_day;
    document.getElementById('is_node_list').checked = airport.is_node_list;
    
    if (airport.parser_config.exclude_keywords) {
        document.getElementById('exclude_keywords').value = 
            airport.parser_config.exclude_keywords.join(', ');
    }
    
    if (airport.parser_config.country_name_mapping) {
        document.getElementById('country_mapping').value = 
            JSON.stringify(airport.parser_config.country_name_mapping, null, 2);
    }
}

// 删除机场
async function deleteAirport(name) {
    if (!confirm(`确定要删除机场 "${name}" 吗？`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/airports/${name}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showAlert(`机场 ${name} 已删除`);
            loadAirports();
        } else {
            const error = await response.json();
            showAlert('删除失败: ' + error.detail, 'error');
        }
    } catch (error) {
        showAlert('删除失败: ' + error.message, 'error');
    }
}

// 加载全局配置
async function loadGlobalConfig() {
    try {
        const response = await fetch(`${API_BASE}/api/config`);
        const data = await response.json();
        
        document.getElementById('txcos_domain').value = data.txcos_domain || '';
        document.getElementById('interval').value = data.interval || 3600;
        document.getElementById('merge_key').value = data.merge_key || 'merge.conf';
        
        // 生成合并机场列表
        renderMergeAirportsList(data.airports || {}, data.merge_airports || []);
        
        // 加载AI配置
        document.getElementById('ai_api_key').value = data.ai_api_key || '';
        document.getElementById('ai_base_url').value = data.ai_base_url || 'https://openrouter.ai/api/v1/chat/completions';
        
        // 设置AI模型（确保在选项加载后设置）
        const modelSelect = document.getElementById('ai_model');
        const modelValue = data.ai_model || 'google/gemini-2.0-flash-exp:free';
        
        // 尝试设置值，如果选项不存在则等待
        if (modelSelect.querySelector(`option[value="${modelValue}"]`)) {
            modelSelect.value = modelValue;
        } else {
            // 如果选项还没加载，设置一个临时值
            setTimeout(() => {
                if (modelSelect.querySelector(`option[value="${modelValue}"]`)) {
                    modelSelect.value = modelValue;
                }
            }, 500);
        }
    } catch (error) {
        showAlert('加载全局配置失败: ' + error.message, 'error');
    }
}

// 生成合并机场列表
function renderMergeAirportsList(airports, selectedAirports) {
    const container = document.getElementById('merge_airports_list');
    
    if (Object.keys(airports).length === 0) {
        container.innerHTML = '<p style="color: #999; text-align: center; padding: 20px;">暂无机场</p>';
        return;
    }
    
    let html = '<div class="merge-list-grid">';
    Object.keys(airports).forEach(name => {
        const isChecked = selectedAirports.includes(name);
        html += `
            <label class="merge-item">
                <input type="checkbox" value="${name}" class="merge-airport-checkbox" ${isChecked ? 'checked' : ''}>
                <span title="${name}">${name}</span>
            </label>
        `;
    });
    html += '</div>';
    
    container.innerHTML = html;
}

// 保存全局配置
document.getElementById('global-config-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // 从多选框中获取选中的机场
    const selectedAirports = Array.from(document.querySelectorAll('.merge-airport-checkbox:checked'))
        .map(checkbox => checkbox.value);
    
    const formData = new FormData(e.target);
    const data = {
        txcos_domain: formData.get('txcos_domain'),
        interval: parseInt(formData.get('interval')),
        merge_key: formData.get('merge_key'),
        merge_airports: selectedAirports,
        ai_api_key: formData.get('ai_api_key'),
        ai_base_url: formData.get('ai_base_url'),
        ai_model: formData.get('ai_model')
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/config`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showAlert('全局配置保存成功！');
        } else {
            const error = await response.json();
            showAlert('保存失败: ' + error.detail, 'error');
        }
    } catch (error) {
        showAlert('保存失败: ' + error.message, 'error');
    }
});

// 刷新AI模型列表
async function refreshAIModels() {
    const btn = event.target;
    const originalText = btn.textContent;
    btn.textContent = '⏳ 加载中...';
    btn.disabled = true;
    
    try {
        // 清除缓存
        aiModelsCache = null;
        
        // 重新加载
        await loadAIModels();
        showAlert('AI模型列表已更新');
    } catch (error) {
        showAlert('刷新失败: ' + error.message, 'error');
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

// 导出配置
document.getElementById('export-btn').addEventListener('click', async () => {
    try {
        const response = await fetch(`${API_BASE}/api/config/export`);
        const data = await response.json();
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { 
            type: 'application/json' 
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'sub-surge-config.json';
        a.click();
        URL.revokeObjectURL(url);
        
        showAlert('配置已导出');
    } catch (error) {
        showAlert('导出失败: ' + error.message, 'error');
    }
});

// 合并订阅
document.getElementById('merge-btn').addEventListener('click', async () => {
    // 从多选框中获取选中的机场
    const selectedAirports = Array.from(document.querySelectorAll('.merge-airport-checkbox:checked'))
        .map(checkbox => checkbox.value);
    
    if (selectedAirports.length === 0) {
        showAlert('请先选择要合并的机场', 'error');
        return;
    }
    
    const mergeBtn = document.getElementById('merge-btn');
    const originalText = mergeBtn.textContent;
    mergeBtn.textContent = '⏳ 合并中...';
    mergeBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/api/merge`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ airports: selectedAirports })
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('✅ 合并成功:', result);
            
            // 从结果中获取生成的链接
            const mergeUrl = result.result?.url || '';
            
            // 显示成功消息和复制按钮
            const alertContainer = document.getElementById('alert-container');
            const alert = document.createElement('div');
            alert.className = 'alert alert-success';
            alert.innerHTML = `
                订阅合并成功！<br>
                <span style="font-size: 12px; color: #666; margin-top: 8px; display: block;">
                    链接: ${mergeUrl}
                    <button onclick="copyToClipboard('${mergeUrl}')" style="margin-left: 8px; padding: 4px 8px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">📋 复制</button>
                </span>
            `;
            alertContainer.appendChild(alert);
            
            setTimeout(() => {
                alert.remove();
            }, 5000);
        } else {
            const error = await response.json();
            showAlert('合并失败: ' + error.detail, 'error');
        }
    } catch (error) {
        console.error('❌ 合并失败:', error);
        showAlert('合并失败: ' + error.message, 'error');
    } finally {
        mergeBtn.textContent = originalText;
        mergeBtn.disabled = false;
    }
});

// 导入配置
document.getElementById('import-btn').addEventListener('click', async () => {
    const fileInput = document.getElementById('import-file');
    const file = fileInput.files[0];
    
    if (!file) {
        showAlert('请选择文件', 'error');
        return;
    }
    
    try {
        const text = await file.text();
        const data = JSON.parse(text);
        
        const response = await fetch(`${API_BASE}/api/config/import`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showAlert('配置导入成功！');
            loadAirports();
            loadGlobalConfig();
        } else {
            const error = await response.json();
            showAlert('导入失败: ' + error.detail, 'error');
        }
    } catch (error) {
        showAlert('导入失败: ' + error.message, 'error');
    }
});

// 加载配置预览
async function loadConfigPreview() {
    try {
        const response = await fetch(`${API_BASE}/api/config`);
        const data = await response.json();
        
        const preview = document.getElementById('config-preview');
        preview.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
        const preview = document.getElementById('config-preview');
        preview.textContent = '加载失败: ' + error.message;
    }
}

// 日志相关功能
let logAutoRefreshInterval = null;

// 加载日志
async function loadLogs() {
    try {
        const lines = document.getElementById('log-lines').value;
        const response = await fetch(`${API_BASE}/api/logs?lines=${lines}`);
        const data = await response.json();
        
        const container = document.getElementById('logs-container');
        
        if (data.logs && data.logs.length > 0) {
            // 为不同级别的日志添加颜色
            const coloredLogs = data.logs.map(line => {
                if (line.includes('ERROR')) {
                    return `<span style="color: #f48771;">${line}</span>`;
                } else if (line.includes('WARNING')) {
                    return `<span style="color: #e5c07b;">${line}</span>`;
                } else if (line.includes('INFO')) {
                    return `<span style="color: #61afef;">${line}</span>`;
                } else {
                    return line;
                }
            }).join('');
            
            container.innerHTML = coloredLogs;
            // 自动滚动到底部
            container.scrollTop = container.scrollHeight;
        } else {
            container.innerHTML = '<p style="color: #888;">暂无日志</p>';
        }
    } catch (error) {
        const container = document.getElementById('logs-container');
        container.innerHTML = `<p style="color: #f48771;">加载日志失败: ${error.message}</p>`;
    }
}

// 清空日志显示
function clearLogsDisplay() {
    const container = document.getElementById('logs-container');
    container.innerHTML = '<p style="color: #888;">日志已清空，点击"刷新日志"重新加载...</p>';
}

// 监听自动刷新开关
document.addEventListener('DOMContentLoaded', () => {
    const autoRefreshCheckbox = document.getElementById('auto-refresh-logs');
    if (autoRefreshCheckbox) {
        autoRefreshCheckbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                // 开启自动刷新
                loadLogs(); // 立即加载一次
                logAutoRefreshInterval = setInterval(loadLogs, 5000);
            } else {
                // 关闭自动刷新
                if (logAutoRefreshInterval) {
                    clearInterval(logAutoRefreshInterval);
                    logAutoRefreshInterval = null;
                }
            }
        });
    }
});

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    loadAirports();
    loadGlobalConfig();
});
