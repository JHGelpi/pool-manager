// API base URL
const API_BASE = '';

// Global state
let currentTab = 'tasks';
let readingTypes = [];
let currentChart = null;

// Utility functions - $ returns ONE element, $$ returns ALL matching elements
function $(selector) {
    return document.querySelector(selector);
}

function $$(selector) {
    return document.querySelectorAll(selector);
}

function showToast(message, duration = 3000) {
    const toast = $('#toast');
    if (!toast) return;
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
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Tomorrow';
    if (diffDays === -1) return 'Yesterday';
    if (diffDays > 0) return `In ${diffDays} days`;
    return `${Math.abs(diffDays)} days ago`;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getTodayDate() {
    return new Date().toISOString().split('T')[0];
}

function getFutureDate(days) {
    const date = new Date();
    date.setDate(date.getDate() + days);
    return date.toISOString().split('T')[0];
}

// API functions
async function api(endpoint, options = {}) {
    console.log('API call:', endpoint, options.method || 'GET');
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        console.log('API response:', response.status, response.statusText);
        
        if (!response.ok) {
            let errorMsg = `HTTP ${response.status}`;
            try {
                const errorText = await response.text();
                errorMsg += `: ${errorText}`;
            } catch (e) {
                // Ignore
            }
            throw new Error(errorMsg);
        }
        
        if (response.status === 204) return null;
        const data = await response.json();
        console.log('API data:', data);
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Tab switching
function switchTab(tabName) {
    console.log('Switching to tab:', tabName);
    currentTab = tabName;
    
    // Update tab visibility using $$() for all tabs
    const allTabs = $$('.tab');
    allTabs.forEach(tab => tab.classList.remove('active'));
    
    const targetTab = $(`#tab-${tabName}`);
    if (targetTab) {
        targetTab.classList.add('active');
    }
    
    // Update nav buttons using $$() for all buttons
    const allNavBtns = $$('.nav-btn');
    allNavBtns.forEach(btn => btn.classList.remove('active'));
    
    const targetBtn = $(`.nav-btn[data-tab="${tabName}"]`);
    if (targetBtn) {
        targetBtn.classList.add('active');
    }
    
    // Load tab data
    switch(tabName) {
        case 'tasks': 
            loadTasks(); 
            break;
        case 'inventory': 
            loadInventory(); 
            break;
        case 'readings': 
            loadReadings(); 
            break;
        case 'settings': 
            checkHealth(); 
            break;
    }
}

// Tasks
async function loadTasks() {
    console.log('Loading tasks...');
    const loading = $('#tasksLoading');
    const list = $('#tasksList');
    const empty = $('#tasksEmpty');
    
    if (!loading || !list || !empty) {
        console.error('Task elements not found');
        return;
    }
    
    loading.style.display = 'flex';
    list.innerHTML = '';
    list.style.display = 'none';
    empty.style.display = 'none';
    
    try {
        const tasks = await api('/tasks/');
        console.log('Loaded tasks:', tasks.length);
        loading.style.display = 'none';
        
        if (!tasks || tasks.length === 0) {
            empty.style.display = 'block';
            return;
        }
        
        list.style.display = 'grid';
        list.innerHTML = tasks.map(task => {
            const dueDate = new Date(task.next_due_date);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            dueDate.setHours(0, 0, 0, 0);
            
            const isOverdue = dueDate < today;
            const isDueToday = dueDate.getTime() === today.getTime();
            
            let dueBadge = '';
            if (isOverdue) {
                dueBadge = '<span style="color: var(--danger); font-weight: 600;">⚠ Overdue</span>';
            } else if (isDueToday) {
                dueBadge = '<span style="color: var(--warning); font-weight: 600;">⚡ Due today</span>';
            }
            
            return `
                <div class="card">
                    <h3>${escapeHtml(task.name)}</h3>
                    ${task.description ? `<p>${escapeHtml(task.description)}</p>` : ''}
                    <div class="card-meta">
                        <span>Every ${task.frequency_days} days</span>
                        <span>Due: ${formatDate(task.next_due_date)}</span>
                    </div>
                    ${dueBadge}
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Failed to load tasks:', error);
        loading.style.display = 'none';
        showToast('Failed to load tasks: ' + error.message);
        empty.style.display = 'block';
    }
}

// Inventory
async function loadInventory() {
    console.log('Loading inventory...');
    const loading = $('#inventoryLoading');
    const list = $('#inventoryList');
    const empty = $('#inventoryEmpty');
    
    if (!loading || !list || !empty) {
        console.error('Inventory elements not found');
        return;
    }
    
    loading.style.display = 'flex';
    list.innerHTML = '';
    list.style.display = 'none';
    empty.style.display = 'none';
    
    try {
        const items = await api('/inventory/');
        console.log('Loaded inventory items:', items.length);
        loading.style.display = 'none';
        
        if (!items || items.length === 0) {
            empty.style.display = 'block';
            return;
        }
        
        list.style.display = 'grid';
        list.innerHTML = items.map(item => {
            const isLow = item.quantity_on_hand <= item.reorder_threshold;
            const stockColor = isLow ? 'var(--danger)' : 'var(--success)';
            const stockIcon = isLow ? '⚠' : '✓';
            
            return `
                <div class="card">
                    <h3>${escapeHtml(item.name)}</h3>
                    <div class="card-meta">
                        <span style="color: ${stockColor}; font-weight: 600;">
                            ${stockIcon} ${item.quantity_on_hand} ${item.unit}
                        </span>
                        <span>Reorder at ${item.reorder_threshold}</span>
                    </div>
                    ${isLow ? '<p style="color: var(--danger); margin-top: 0.5rem;">Stock is low!</p>' : ''}
                </div>
            `;
        }).join('');
    } catch (error) {
        loading.style.display = 'none';
        showToast('Failed to load inventory');
        console.error(error);
    }
}

// Readings
async function loadReadingTypes() {
    try {
        readingTypes = await api('/readings/types');
        const select = $('#readingType');
        
        if (!select) return;
        
        select.innerHTML = '<option value="">Select type...</option>' + 
            readingTypes.map(type => 
                `<option value="${type.slug}" data-unit="${type.unit || ''}">${type.name}</option>`
            ).join('');
        
        if (readingTypes.length > 0) {
            select.value = readingTypes[0].slug;
            updateReadingUnit();
        }
    } catch (error) {
        showToast('Failed to load reading types');
        console.error(error);
    }
}

function updateReadingUnit() {
    const select = $('#readingType');
    if (!select) return;
    
    const selectedOption = select.selectedOptions[0];
    const unit = selectedOption?.dataset.unit || '';
    const unitSpan = $('#readingUnit');
    
    if (unitSpan) {
        unitSpan.textContent = unit ? `(${unit})` : '';
    }
}

async function loadReadings() {
    const select = $('#readingType');
    if (!select) return;
    
    const slug = select.value;
    if (!slug) return;
    
    try {
        const readings = await api(`/readings/?slug=${slug}&days=90`);
        renderChart(slug, readings);
    } catch (error) {
        console.error('Failed to load readings:', error);
        showToast('Failed to load readings');
    }
}

function renderChart(slug, readings) {
    const canvas = $('#readingChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const typeInfo = readingTypes.find(t => t.slug === slug) || {};
    
    if (currentChart) {
        currentChart.destroy();
    }
    
    if (readings.length === 0) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#a3acc2';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No readings yet for this type', canvas.width / 2, canvas.height / 2);
        return;
    }
    
    currentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: readings.map(r => {
                const date = new Date(r.reading_date);
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            }),
            datasets: [{
                label: `${typeInfo.name || slug} ${typeInfo.unit ? '(' + typeInfo.unit + ')' : ''}`,
                data: readings.map(r => r.reading_value),
                borderColor: '#4f8cff',
                backgroundColor: 'rgba(79, 140, 255, 0.1)',
                tension: 0.3,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { 
                        color: '#e5ecff',
                        font: { size: 12 }
                    }
                }
            },
            scales: {
                x: {
                    ticks: { 
                        color: '#a3acc2',
                        font: { size: 11 }
                    },
                    grid: { color: 'rgba(255, 255, 255, 0.06)' }
                },
                y: {
                    ticks: { 
                        color: '#a3acc2',
                        font: { size: 11 }
                    },
                    grid: { color: 'rgba(255, 255, 255, 0.06)' }
                }
            }
        }
    });
}

// Health check
async function checkHealth() {
    const apiStatus = $('#apiStatus');
    const dbStatus = $('#dbStatus');
    const statusBadge = $('#statusBadge');
    
    try {
        await api('/health');
        if (apiStatus) apiStatus.textContent = 'Connected';
        if (statusBadge) {
            statusBadge.className = 'badge badge-ok';
            statusBadge.textContent = '● Online';
        }
        
        const readyStatus = await api('/readyz');
        if (dbStatus) {
            dbStatus.textContent = readyStatus.status === 'ready' ? 'Connected' : 'Error';
        }
    } catch (error) {
        if (apiStatus) apiStatus.textContent = 'Disconnected';
        if (dbStatus) dbStatus.textContent = 'Unknown';
        if (statusBadge) {
            statusBadge.className = 'badge badge-error';
            statusBadge.textContent = '● Offline';
        }
        console.error('Health check failed:', error);
    }
}

// Event Listeners - This is where line 388 should be
document.addEventListener('DOMContentLoaded', function() {
    console.log('App initializing...');
    
    // Navigation - Use $$ to get ALL nav buttons
    const navButtons = $$('.nav-btn');
    console.log('Found nav buttons:', navButtons.length);
    
    // Now iterate over the collection
    navButtons.forEach(function(btn) {
        btn.addEventListener('click', function() {
            console.log('Switching to tab:', btn.dataset.tab);
            switchTab(btn.dataset.tab);
        });
    });
    
    // Task modal
    const taskDialog = $('#taskDialog');
    const taskForm = $('#taskForm');
    
    const btnAddTask = $('#btnAddTask');
    if (btnAddTask) {
        btnAddTask.addEventListener('click', function() {
            if (taskDialog) taskDialog.showModal();
            const freqInput = taskForm?.querySelector('[name="frequency_days"]');
            if (freqInput) {
                taskForm.querySelector('[name="next_due_date"]').value = getFutureDate(parseInt(freqInput.value) || 7);
            }
        });
    }
    
    const btnAddTaskEmpty = $('#btnAddTaskEmpty');
    if (btnAddTaskEmpty) {
        btnAddTaskEmpty.addEventListener('click', function() {
            if (taskDialog) taskDialog.showModal();
            const freqInput = taskForm?.querySelector('[name="frequency_days"]');
            if (freqInput) {
                taskForm.querySelector('[name="next_due_date"]').value = getFutureDate(parseInt(freqInput.value) || 7);
            }
        });
    }
    
    const taskCancel = $('#taskCancel');
    if (taskCancel) {
        taskCancel.addEventListener('click', function() {
            if (taskDialog) taskDialog.close();
            if (taskForm) taskForm.reset();
        });
    }
    
    // Update due date when frequency changes
    const freqInput = taskForm?.querySelector('[name="frequency_days"]');
    if (freqInput) {
        freqInput.addEventListener('input', function(e) {
            const dueDateInput = taskForm.querySelector('[name="next_due_date"]');
            if (dueDateInput) {
                dueDateInput.value = getFutureDate(parseInt(e.target.value) || 7);
            }
        });
    }
    
    if (taskForm) {
        taskForm.addEventListener('submit', async function(e) {
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
                showToast('✓ Task created successfully');
                if (taskDialog) taskDialog.close();
                if (taskForm) taskForm.reset();
                loadTasks();
            } catch (error) {
                showToast('Failed to create task');
                console.error(error);
            }
        });
    }
    
    // Inventory modal
    const inventoryDialog = $('#inventoryDialog');
    const inventoryForm = $('#inventoryForm');
    
    const btnAddInventory = $('#btnAddInventory');
    if (btnAddInventory) {
        btnAddInventory.addEventListener('click', function() {
            if (inventoryDialog) inventoryDialog.showModal();
            const invName = $('#invName');
            if (invName) invName.focus();
        });
    }
    
    const btnAddInventoryEmpty = $('#btnAddInventoryEmpty');
    if (btnAddInventoryEmpty) {
        btnAddInventoryEmpty.addEventListener('click', function() {
            if (inventoryDialog) inventoryDialog.showModal();
            const invName = $('#invName');
            if (invName) invName.focus();
        });
    }
    
    const inventoryCancel = $('#inventoryCancel');
    if (inventoryCancel) {
        inventoryCancel.addEventListener('click', function() {
            if (inventoryDialog) inventoryDialog.close();
            if (inventoryForm) inventoryForm.reset();
        });
    }
    
    if (inventoryForm) {
        inventoryForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const data = {
                name: $('#invName').value.trim(),
                quantity_on_hand: parseFloat($('#invQuantity').value),
                unit: $('#invUnit').value.trim(),
                reorder_threshold: parseFloat($('#invThreshold').value)
            };
            
            try {
                await api('/inventory/', { method: 'POST', body: JSON.stringify(data) });
                showToast('✓ Inventory item added');
                if (inventoryDialog) inventoryDialog.close();
                if (inventoryForm) inventoryForm.reset();
                loadInventory();
            } catch (error) {
                showToast('Failed to add item');
                console.error(error);
            }
        });
    }
    
    // Reading form
    const readingTypeSelect = $('#readingType');
    if (readingTypeSelect) {
        readingTypeSelect.addEventListener('change', function() {
            updateReadingUnit();
            loadReadings();
        });
    }
    
    const readingDate = $('#readingDate');
    if (readingDate) {
        readingDate.value = getTodayDate();
    }
    
    const readingForm = $('#readingForm');
    if (readingForm) {
        readingForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const typeSelect = $('#readingType');
            const valueInput = $('#readingValue');
            const dateInput = $('#readingDate');
            
            if (!typeSelect.value) {
                showToast('Please select a reading type');
                return;
            }
            
            const data = {
                reading_type_slug: typeSelect.value,
                reading_value: parseFloat(valueInput.value),
                reading_date: dateInput.value
            };
            
            try {
                await api('/readings/', { method: 'POST', body: JSON.stringify(data) });
                showToast('✓ Reading saved');
                valueInput.value = '';
                loadReadings();
            } catch (error) {
                showToast('Failed to save reading');
                console.error(error);
            }
        });
    }
    
    // Initialize
    console.log('Checking health...');
    checkHealth();
    
    console.log('Loading reading types...');
    loadReadingTypes().then(function() {
        if (currentTab === 'readings') {
            loadReadings();
        }
    });
    
    console.log('Switching to tasks tab...');
    switchTab('tasks');
});