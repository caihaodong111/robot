// 主应用文件

// 页面路由
function navigateTo(pageId) {
    // 隐藏所有页面
    document.querySelectorAll('.page-section').forEach(section => {
        section.style.display = 'none';
    });

    // 显示目标页面
    const targetSection = document.getElementById(pageId);
    if (targetSection) {
        targetSection.style.display = 'block';
    }

    // 更新导航激活状态
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });

    const activeLink = document.querySelector(`.nav-link[href="/#${pageId}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }

    if (pageId === 'devops') {
        const devopsFrame = document.getElementById('devopsFrame');
        if (devopsFrame && !devopsFrame.src) {
            devopsFrame.src = devopsFrame.dataset.src || '';
        }
    }
}

// 初始化页面路由
document.addEventListener('DOMContentLoaded', () => {
    // 根据URL hash导航到对应页面
    const hash = window.location.hash || '#dashboard';
    navigateTo(hash.substring(1));

    // 监听hash变化
    window.addEventListener('hashchange', () => {
        const pageId = window.location.hash.substring(1) || 'dashboard';
        navigateTo(pageId);
    });

    // 导航链接点击事件
    document.querySelectorAll('.nav-link[href^="/#"]').forEach(link => {
        link.addEventListener('click', (e) => {
            const pageId = link.getAttribute('href').substring(2);
            navigateTo(pageId);
        });
    });
});

// 登录表单处理
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const result = await authAPI.login(username, password);
        authToken = result.token;
        localStorage.setItem('authToken', result.token);

        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));
        modal.hide();

        // 更新UI
        updateAuthUI();
        showNotification('登录成功！', 'success');

        // 重新加载当前页面数据
        location.reload();
    } catch (error) {
        showNotification(error.message, 'danger');
    }
});

// 登出函数
function logout() {
    authAPI.logout().then(() => {
        localStorage.removeItem('authToken');
        authToken = null;
        updateAuthUI();
        showNotification('已退出登录', 'success');
        window.location.hash = '#dashboard';
    }).catch(() => {
        localStorage.removeItem('authToken');
        authToken = null;
        updateAuthUI();
        window.location.hash = '#dashboard';
    });
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 如果已登录，加载仪表盘数据
    if (isLoggedIn()) {
        loadDashboardData();
    }
});

// 加载仪表盘数据
async function loadDashboardData() {
    try {
        // 加载设备统计
        const devices = await devicesAPI.list();
        document.getElementById('totalDevices').textContent = devices.length;
        document.getElementById('onlineDevices').textContent =
            devices.filter(d => d.status === 'online').length;

        // 加载报警统计
        const alertStats = await alertsAPI.statistics('24h');
        document.getElementById('pendingAlerts').textContent =
            alertStats.total_stats.pending || 0;

        // 加载最新数据
        const latestData = await monitoringAPI.latestAll();
        document.getElementById('todayDataPoints').textContent = latestData.length;

        // 更新最新数据表格
        updateLatestDataTable(latestData);

        // 加载图表数据
        loadCharts(latestData);
    } catch (error) {
        console.error('加载仪表盘数据失败:', error);
    }
}

// 更新最新数据表格
function updateLatestDataTable(data) {
    const tbody = document.getElementById('latestDataTable');
    if (!data || data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">暂无数据</td></tr>';
        return;
    }

    tbody.innerHTML = data.map(item => `
        <tr>
            <td>${item.device_name}</td>
            <td>${formatValue(item.temperature, '℃')}</td>
            <td>${formatValue(item.humidity, '%')}</td>
            <td>${formatValue(item.pm25, 'μg/m³')}</td>
            <td>${formatValue(item.co2, 'ppm')}</td>
            <td>${formatDateTime(item.timestamp)}</td>
        </tr>
    `).join('');
}

// 图表实例
let tempChart = null;
let humidityChart = null;

// 加载图表
function loadCharts(data) {
    const labels = data.map(item => {
        const date = new Date(item.timestamp);
        return date.toLocaleTimeString('zh-CN');
    });

    const tempData = data.map(item => item.temperature);
    const humidityData = data.map(item => item.humidity);

    // 温度图表
    const tempCtx = document.getElementById('tempChart').getContext('2d');
    if (tempChart) tempChart.destroy();
    tempChart = new Chart(tempCtx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '温度 (℃)',
                data: tempData,
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });

    // 湿度图表
    const humidityCtx = document.getElementById('humidityChart').getContext('2d');
    if (humidityChart) humidityChart.destroy();
    humidityChart = new Chart(humidityCtx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '湿度 (%)',
                data: humidityData,
                borderColor: 'rgb(54, 162, 235)',
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}
