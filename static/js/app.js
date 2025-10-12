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
    $$('.tab').forEach(tab => tab.classList.remove('tab--active'));
    $(`#tab-${tabName}`).classList.add('tab--active');
    
    // Update nav buttons
    $$('.tabbar-btn').forEach(btn => btn.classList.remove('tabbar-btn--active'));
    $(`.tabbar-btn[data-tab="${tabName}"]`).classList.add('tabbar-btn--active');
    
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
    list.hidden = true;
    empty.hidden = true;
    
    try {
        const tasks = await api('/tasks/');
        loading.style.display = 'none';
        
        if (tasks.length === 0) {
            empty.hidden = false;
            return;
        }
        
        list.hidden = false;
        list.innerHTML = tasks.map(task => `
            <li>
                <div class="card">
                    <h3>${escapeHtml(task.name)}</h3>
                    ${task.description ? `<p>${escapeHtml(task.description)}</p>` : ''}
                    <div class="card-meta">
                        <span>Every ${task.frequency_days} days</span>
                        <span>Due ${formatDate(task.next_due_date)}</span>
                    </div>
                </div>
            </li>
        `).join('');
    } catch (error) {
        loading.style.display = 'none';
        showToast('Failed to load tasks');
    }
}

// Inventory
async function loadInventory() {
    const loading = $('#invLoading');
    const list = $('#inventoryList');
    const empty = $('#inventoryEmpty');
    
    loading.style.display = 'flex';
    list.innerHTML = '';
    list.hidden = true;
    empty.hidden = true;
    
    try {
        const items = await api('/inventory/');
        loading.style.display = 'none';
        
        if (items.length === 0) {
            empty.hidden = false;
            return;
        }
        
        list.hidden = false;
        list.innerHTML = items.map(item => {
            const isLow = item.quantity_on_hand <= item.reorder_threshold;
            return `
                <li>
                    <div class="card">
                        <h3>${escapeHtml(item.name)}</h3>
                        <div class="card-meta">
                            <span style="color: ${isLow ? 'var(--danger)' : 'var(--success)'}">
                                ${item.quantity_on_hand} ${item.unit}
                            </span>
                            <span>Reorder at ${item.reorder_threshold}</span>
                        </div>
                    </div>
                </li>
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
    
    const typeInfo = readingTypes.find(t => t.slug === slug) || {};
    
    if (currentChart) {
        currentChart.destroy();
    }
    
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

// Health check
async function checkHealth() {
    try {
        await api('/health');
        $('#apiStatus').textContent = 'Connected';
        $('#onlineBadge').className = 'badge badge--ok';
        $('#onlineBadge').textContent = '● online';
    } catch (error) {
        $('#apiStatus').textContent = 'Disconnected';
        $('#onlineBadge').className = 'badge badge--err';
        $('#onlineBadge').textContent = '● offline';
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Navigation
    $$('.tabbar-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            switchTab(btn.dataset.tab);
        });
    });
    
    // Task modal
    const taskDialog = $('#taskDialog');
    const taskForm = $('#taskForm');
    
    $('#btnAddTask')?.addEventListener('click', () => {
        taskDialog.showModal();
        taskForm.querySelector('[name="next_due_date"]').value = getNextDueDate(7);
    });
    
    $('#btnAddTaskEmpty')?.addEventListener('click', () => {
        taskDialog.showModal();
        taskForm.querySelector('[name="next_due_date"]').value = getNextDueDate(7);
    });
    
    $('#taskCancel')?.addEventListener('click', () => {
        taskDialog.close();
        taskForm.reset();
    });
    
    taskForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        
        const data = {
            name: formData.get('name'),
            description: formData.get('description') || null,
            frequency_days: parseInt(formData.get('frequency_days')),
            next_due_date: formData.get('next_due_date')
        };
        
        try {
            await api('/tasks/', { method: 'POST', body: JSON.stringify(data) });
            showToast('Task created');
            taskDialog.close();
            taskForm.reset();
            loadTasks();
        } catch (error) {
            showToast('Failed to create task');
        }
    });
    
    // Update due date when frequency changes
    taskForm?.querySelector('[name="frequency_days"]')?.addEventListener('input', (e) => {
        taskForm.querySelector('[name="next_due_date"]').value = getNextDueDate(parseInt(e.target.value) || 7);
    });
    
    // Inventory modal
    const inventoryDialog = $('#inventoryDialog');
    const inventoryForm = $('#inventoryForm');
    
    $('#btnAddInventory')?.addEventListener('click', () => {
        inventoryDialog.showModal();
        $('#invName').focus();
    });
    
    $('#btnAddInventoryEmpty')?.addEventListener('click', () => {
        inventoryDialog.showModal();
        $('#invName').focus();
    });
    
    $('#inventoryCancel')?.addEventListener('click', () => {
        inventoryDialog.close();
        inventoryForm.reset();
    });
    
    inventoryForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const data = {
            name: $('#invName').value.trim(),
            quantity_on_hand: parseFloat($('#invQuantity').value),
            unit: $('#invUnit').value.trim(),
            reorder_threshold: parseFloat($('#invThreshold').value)
        };
        
        try {
            await api('/inventory/', { method: 'POST', body: JSON.stringify(data) });
            showToast('Inventory item added');
            inventoryDialog.close();
            inventoryForm.reset();
            loadInventory();
        } catch (error) {
            showToast('Failed to add item');
            console.error(error);
        }
    });
    
    // Reading form
    $('#readingType')?.addEventListener('change', () => {
        updateReadingUnit();
        loadReadings();
    });
    
    const readingDate = $('#readingDate');
    if (readingDate) {
        readingDate.value = new Date().toISOString().split('T')[0];
    }
    
    $('#readingForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const data = {
            reading_type_slug: $('#readingType').value,
            reading_value: parseFloat($('#readingValue').value),
            reading_date: $('#readingDate').value
        };
        
        try {
            await api('/readings/', { method: 'POST', body: JSON.stringify(data) });
            showToast('Reading saved');
            loadReadings();
            $('#readingValue').value = '';
        } catch (error) {
            showToast('Failed to save reading');
        }
    });
    
    // Initialize
    checkHealth();
    loadReadingTypes().then(() => loadReadings());
    switchTab('tasks');
});