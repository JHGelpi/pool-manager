// API base URL
const API_BASE = '';

// Global state
let currentTab = 'tasks';
let readingTypes = [];
let currentChart = null;

// Utility functions
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

function showToast(message, duration = 3000) {
    const toast = $('#toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), duration);
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const target = new Date(date);
    target.setHours(0, 0, 0, 0);
    
    const diffDays = Math.round((target - today) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'today';
    if (diffDays === 1) return 'tomorrow';
    if (diffDays === -1) return 'yesterday';
    if (diffDays > 0) return `in ${diffDays} days`;
    return `${Math.abs(diffDays)} days ago`;
}

// API functions
async function api(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        if (response.status === 204) return null;
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Tab switching
function switchTab(tabName) {
    currentTab = tabName;
    
    // Update tab visibility
    $$('.tab').forEach(tab => tab.classList.remove('active'));
    $(`#tab-${tabName}`).classList.add('active');
    
    // Update nav buttons
    $$('.nav-btn').forEach(btn => btn.classList.remove('active'));
    $(`.nav-btn[data-tab="${tabName}"]`).classList.add('active');
    
    // Load tab data
    switch(tabName) {
        case 'tasks': loadTasks(); break;
        case 'inventory': loadInventory(); break;
        case 'readings': loadReadings(); break;
        case 'settings': checkHealth(); break;
    }
}

// Tasks
async function loadTasks() {
    const loading = $('#tasksLoading');
    const list = $('#tasksList');
    const empty = $('#tasksEmpty');
    
    loading.style.display = 'flex';
    list.innerHTML = '';
    empty.hidden = true;
    
    try {
        const tasks = await api('/tasks/');
        loading.style.display = 'none';
        
        if (tasks.length === 0) {
            empty.hidden = false;
            return;
        }
        
        list.innerHTML = tasks.map(task => `
            <div class="card">
                <h3>${escapeHtml(task.name)}</h3>
                ${task.description ? `<p>${escapeHtml(task.description)}</p>` : ''}
                <div class="card-meta">
                    <span>Every ${task.frequency_days} days</span>
                    <span>Due ${formatDate(task.next_due_date)}</span>
                </div>
            </div>
        `).join('');
    } catch (error) {
        loading.style.display = 'none';
        showToast('Failed to load tasks');
    }
}

async function createTask(data) {
    try {
        await api('/tasks/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        showToast('Task created');
        loadTasks();
        return true;
    } catch (error) {
        showToast('Failed to create task');
        return false;
    }
}

// Inventory
async function loadInventory() {
    const loading = $('#inventoryLoading');
    const list = $('#inventoryList');
    const empty = $('#inventoryEmpty');
    
    loading.style.display = 'flex';
    list.innerHTML = '';
    empty.hidden = true;
    
    try {
        const items = await api('/inventory/');
        loading.style.display = 'none';
        
        if (items.length === 0) {
            empty.hidden = false;
            return;
        }
        
        list.innerHTML = items.map(item => {
            const isLow = item.quantity_on_hand <= item.reorder_threshold;
            return `
                <div class="card">
                    <h3>${escapeHtml(item.name)}</h3>
                    <div class="card-meta">
                        <span style="color: ${isLow ? 'var(--danger)' : 'var(--success)'}">
                            ${item.quantity_on_hand} ${item.unit}
                        </span>
                        <span>Reorder at ${item.reorder_threshold}</span>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        loading.style.display = 'none';
        showToast('Failed to load inventory');
    }
}

// Readings
async function loadReadingTypes() {
    try {
        readingTypes = await api('/readings/types');
        const select = $('#readingType');
        select.innerHTML = readingTypes.map(type => 
            `<option value="${type.slug}" data-unit="${type.unit || ''}">${type.name}</option>`
        ).join('');
        updateReadingUnit();
    } catch (error) {
        showToast('Failed to load reading types');
    }
}

function updateReadingUnit() {
    const select = $('#readingType');
    const unit = select.selectedOptions[0]?.dataset.unit || '';
    $('#readingUnit').textContent = unit ? `(${unit})` : '';
}

async function loadReadings() {
    const slug = $('#readingType').value;
    if (!slug) return;
    
    try {
        const readings = await api(`/readings/?slug=${slug}&days=90`);
        renderChart(slug, readings);
    } catch (error) {
        console.error('Failed to load readings:', error);
    }
}

function renderChart(slug, readings) {
    const canvas = $('#readingChart');
    const ctx = canvas.getContext('2d');
    
    // Find reading type info
    const typeInfo = readingTypes.find(t => t.slug === slug) || {};
    
    // Destroy existing chart
    if (currentChart) {
        currentChart.destroy();
    }
    
    // Create new chart
    currentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: readings.map(r => r.reading_date),
            datasets: [{
                label: `${typeInfo.name || slug} ${typeInfo.unit ? '(' + typeInfo.unit + ')' : ''}`,
                data: readings.map(r => r.reading_value),
                borderColor: '#4f8cff',
                backgroundColor: 'rgba(79, 140, 255, 0.1)',
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#e5ecff' }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#a3acc2' },
                    grid: { color: 'rgba(255, 255, 255, 0.06)' }
                },
                y: {
                    ticks: { color: '#a3acc2' },
                    grid: { color: 'rgba(255, 255, 255, 0.06)' }
                }
            }
        }
    });
}

async function createReading(data) {
    try {
        await api('/readings/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        showToast('Reading saved');
        loadReadings();
        return true;
    } catch (error) {
        showToast('Failed to save reading');
        return false;
    }
}

// Health check
async function checkHealth() {
    try {
        await api('/health');
        $('#apiStatus').textContent = 'Connected';
        $('#statusBadge').className = 'badge badge-ok';
        $('#statusBadge').textContent = '● online';
        
        await api('/readyz');
        $('#dbStatus').textContent = 'Connected';
    } catch (error) {
        $('#apiStatus').textContent = 'Disconnected';
        $('#dbStatus').textContent = 'Disconnected';
        $('#statusBadge').className = 'badge badge-error';
        $('#statusBadge').textContent = '● offline';
    }
}

// Utility
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getNextDueDate(frequencyDays) {
    const date = new Date();
    date.setDate(date.getDate() + frequencyDays);
    return date.toISOString().split('T')[0];
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Navigation
    $$('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            switchTab(btn.dataset.tab);
        });
    });
    
    // Task modal
    $('#btnAddTask').addEventListener('click', () => {
        $('#taskModal').showModal();
        $('#taskDue').value = getNextDueDate(7);
    });
    
    $('#btnAddTaskEmpty').addEventListener('click', () => {
        $('#taskModal').showModal();
        $('#taskDue').value = getNextDueDate(7);
    });
    
    $('#btnCancelTask').addEventListener('click', () => {
        $('#taskModal').close();
        $('#taskForm').reset();
    });
    
    $('#taskForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        
        const data = {
            name: formData.get('taskName') || $('#taskName').value,
            description: formData.get('taskDesc') || $('#taskDesc').value || null,
            frequency_days: parseInt(formData.get('taskFreq') || $('#taskFreq').value),
            next_due_date: formData.get('taskDue') || $('#taskDue').value
        };
        
        const success = await createTask(data);
        if (success) {
            $('#taskModal').close();
            $('#taskForm').reset();
        }
    });
    
    // Update due date when frequency changes
    $('#taskFreq').addEventListener('input', (e) => {
        $('#taskDue').value = getNextDueDate(parseInt(e.target.value) || 7);
    });
    
    // Reading form
    $('#readingType').addEventListener('change', () => {
        updateReadingUnit();
        loadReadings();
    });
    
    $('#readingDate').value = new Date().toISOString().split('T')[0];
    
    $('#readingForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const data = {
            reading_type_slug: $('#readingType').value,
            reading_value: parseFloat($('#readingValue').value),
            reading_date: $('#readingDate').value
        };
        
        const success = await createReading(data);
        if (success) {
            $('#readingValue').value = '';
        }
    });
    
    // Initialize
    checkHealth();
    loadReadingTypes().then(() => loadReadings());
    switchTab('tasks');
});