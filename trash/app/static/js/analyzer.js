// Global variables
let currentPage = 1;
let currentPerPage = 25;
let currentFileFilter = 'all';
let availableFiles = [];
let chronoData = {};

// Initialize the analyzer when the page loads
document.addEventListener('DOMContentLoaded', function() {
    loadSummaryData();
    loadAvailableFiles();
    loadChronologicalData();
    
    // Set up event listeners
    setupEventListeners();
});

function setupEventListeners() {
    // File filter change
    document.getElementById('fileFilter').addEventListener('change', function() {
        currentFileFilter = this.value;
        currentPage = 1; // Reset to first page
        loadChronologicalData();
    });
    
    // Items per page change
    document.getElementById('itemsPerPage').addEventListener('change', function() {
        currentPerPage = parseInt(this.value);
        currentPage = 1; // Reset to first page
        loadChronologicalData();
    });
    
    // Export button
    document.getElementById('exportBtn').addEventListener('click', exportCurrentView);
    
    // Legacy export button (if it exists)
    const exportAllBtn = document.getElementById('exportAllBtn');
    if (exportAllBtn) {
        exportAllBtn.addEventListener('click', exportAllData);
    }
}

async function loadSummaryData() {
    try {
        const response = await fetch('/api/summary');
        const data = await response.json();
        
        if (response.ok) {
            displaySummaryCards(data);
            createCharts(data);
        } else {
            console.error('Error loading summary data:', data.error);
        }
    } catch (error) {
        console.error('Error loading summary data:', error);
    }
}

async function loadAvailableFiles() {
    try {
        const response = await fetch('/api/files');
        const data = await response.json();
        
        if (response.ok) {
            availableFiles = data.files;
            populateFileFilter();
        } else {
            console.error('Error loading files:', data.error);
        }
    } catch (error) {
        console.error('Error loading files:', error);
    }
}

function populateFileFilter() {
    const fileFilter = document.getElementById('fileFilter');
    
    // Clear existing options except "All files"
    fileFilter.innerHTML = '<option value="all">Todos los archivos</option>';
    
    // Add individual file options
    availableFiles.forEach(filename => {
        const option = document.createElement('option');
        option.value = filename;
        option.textContent = filename;
        fileFilter.appendChild(option);
    });
}

async function loadChronologicalData(page = 1) {
    const loading = document.getElementById('chronoLoading');
    const table = document.getElementById('chronoTable');
    
    loading.classList.remove('d-none');
    
    try {
        const params = new URLSearchParams({
            page: page,
            per_page: currentPerPage,
            file_filter: currentFileFilter
        });
        
        const response = await fetch(`/api/chronological?${params}`);
        const data = await response.json();
        
        if (response.ok) {
            chronoData = data;
            currentPage = data.pagination.page;
            displayChronologicalTable(data.events);
            displayPagination(data.pagination);
        } else {
            console.error('Error loading chronological data:', data.error);
            showError('Error cargando datos cronológicos: ' + data.error);
        }
    } catch (error) {
        console.error('Error loading chronological data:', error);
        showError('Error de conexión al cargar datos cronológicos');
    } finally {
        loading.classList.add('d-none');
    }
}

function displaySummaryCards(data) {
    const summaryCards = document.getElementById('summaryCards');
    
    summaryCards.innerHTML = `
        <div class="col-md-2">
            <div class="card text-center">
                <div class="card-body">
                    <h5 class="text-primary">${data.total_calls}</h5>
                    <p class="card-text small">Llamadas</p>
                </div>
            </div>
        </div>
        <div class="col-md-2">
            <div class="card text-center">
                <div class="card-body">
                    <h5 class="text-success">${data.total_messages}</h5>
                    <p class="card-text small">Mensajes</p>
                </div>
            </div>
        </div>
        <div class="col-md-2">
            <div class="card text-center">
                <div class="card-body">
                    <h5 class="text-info">${data.total_data_records}</h5>
                    <p class="card-text small">Uso de Datos</p>
                </div>
            </div>
        </div>
        <div class="col-md-2">
            <div class="card text-center">
                <div class="card-body">
                    <h5 class="text-warning">${data.total_call_minutes}</h5>
                    <p class="card-text small">Minutos</p>
                </div>
            </div>
        </div>
        <div class="col-md-2">
            <div class="card text-center">
                <div class="card-body">
                    <h5 class="text-secondary">${data.total_mb_used}</h5>
                    <p class="card-text small">MB Usados</p>
                </div>
            </div>
        </div>
        <div class="col-md-2">
            <div class="card text-center">
                <div class="card-body">
                    <h5 class="text-primary">${data.unique_files}</h5>
                    <p class="card-text small">Archivos</p>
                </div>
            </div>
        </div>
    `;
}

function createCharts(data) {
    // Type distribution chart
    const typeCtx = document.getElementById('typeChart').getContext('2d');
    new Chart(typeCtx, {
        type: 'pie',
        data: {
            labels: ['Llamadas', 'Mensajes', 'Uso de Datos'],
            datasets: [{
                data: [data.total_calls, data.total_messages, data.total_data_records],
                backgroundColor: [
                    'rgba(13, 110, 253, 0.8)',
                    'rgba(25, 135, 84, 0.8)',
                    'rgba(13, 202, 240, 0.8)'
                ],
                borderColor: [
                    'rgba(13, 110, 253, 1)',
                    'rgba(25, 135, 84, 1)',
                    'rgba(13, 202, 240, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#ffffff'
                    }
                }
            }
        }
    });
    
    // Note: Time chart would require additional data processing
    // For now, we'll create a placeholder
    const timeCtx = document.getElementById('timeChart').getContext('2d');
    new Chart(timeCtx, {
        type: 'bar',
        data: {
            labels: ['Actividad Total'],
            datasets: [{
                label: 'Eventos Procesados',
                data: [data.total_calls + data.total_messages + data.total_data_records],
                backgroundColor: 'rgba(13, 110, 253, 0.8)',
                borderColor: 'rgba(13, 110, 253, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#ffffff'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#ffffff'
                    }
                },
                x: {
                    ticks: {
                        color: '#ffffff'
                    }
                }
            }
        }
    });
}

function displayChronologicalTable(events) {
    const table = document.getElementById('chronoTable');
    
    if (!events || events.length === 0) {
        table.innerHTML = `
            <div class="text-center py-4">
                <p class="text-muted">No se encontraron eventos para mostrar.</p>
            </div>
        `;
        return;
    }
    
    const tableHTML = `
        <table class="table table-striped table-hover">
            <thead>
                <tr>
                    <th>Fecha y Hora</th>
                    <th>Tipo</th>
                    <th>Detalle</th>
                    <th>Contacto/Info</th>
                    <th>Descripción</th>
                    <th>Valor</th>
                    <th>Archivo</th>
                </tr>
            </thead>
            <tbody>
                ${events.map(event => {
                    const timestamp = new Date(event.timestamp);
                    const formattedDate = timestamp.toLocaleDateString('es-ES');
                    const formattedTime = timestamp.toLocaleTimeString('es-ES');
                    
                    let badgeClass = '';
                    switch (event.event_type) {
                        case 'call':
                            badgeClass = 'bg-primary';
                            break;
                        case 'message':
                            badgeClass = 'bg-success';
                            break;
                        case 'data_usage':
                            badgeClass = 'bg-info';
                            break;
                    }
                    
                    let valueDisplay = '';
                    if (event.event_type === 'call' && event.numeric_value) {
                        valueDisplay = `${event.numeric_value} min`;
                    } else if (event.event_type === 'data_usage' && event.numeric_value) {
                        valueDisplay = `${event.numeric_value} ${event.format_info}`;
                    } else if (event.format_info) {
                        valueDisplay = event.format_info;
                    }
                    
                    return `
                        <tr>
                            <td>
                                <div class="small">
                                    <div><strong>${formattedDate}</strong></div>
                                    <div class="text-muted">${formattedTime}</div>
                                </div>
                            </td>
                            <td>
                                <span class="badge ${badgeClass}">${getEventTypeLabel(event.event_type)}</span>
                            </td>
                            <td>${event.type_detail || '-'}</td>
                            <td>${event.contact_info || '-'}</td>
                            <td>${event.description || '-'}</td>
                            <td>${valueDisplay || '-'}</td>
                            <td>
                                <small class="text-muted">${event.source_file}</small>
                            </td>
                        </tr>
                    `;
                }).join('')}
            </tbody>
        </table>
    `;
    
    table.innerHTML = tableHTML;
}

function displayPagination(pagination) {
    const paginationContainer = document.getElementById('chronoPagination');
    
    if (pagination.total_pages <= 1) {
        paginationContainer.innerHTML = '';
        return;
    }
    
    let paginationHTML = '<ul class="pagination justify-content-center">';
    
    // First page link
    paginationHTML += `
        <li class="page-item ${pagination.page === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="navigateToPage(1)">Primera</a>
        </li>
    `;
    
    // Previous block link
    if (pagination.has_prev_block) {
        const prevBlockEnd = pagination.block_start - 1;
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="navigateToPage(${prevBlockEnd})">...</a>
            </li>
        `;
    }
    
    // Current block pages
    for (let i = pagination.block_start; i <= pagination.block_end; i++) {
        paginationHTML += `
            <li class="page-item ${i === pagination.page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="navigateToPage(${i})">${i}</a>
            </li>
        `;
    }
    
    // Next block link
    if (pagination.has_next_block) {
        const nextBlockStart = pagination.block_end + 1;
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="navigateToPage(${nextBlockStart})">...</a>
            </li>
        `;
    }
    
    // Last page link
    paginationHTML += `
        <li class="page-item ${pagination.page === pagination.total_pages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="navigateToPage(${pagination.total_pages})">Última</a>
        </li>
    `;
    
    paginationHTML += '</ul>';
    
    // Add pagination info
    paginationHTML += `
        <div class="text-center mt-2">
            <small class="text-muted">
                Mostrando página ${pagination.page} de ${pagination.total_pages} 
                (${pagination.total_records} eventos total)
            </small>
        </div>
    `;
    
    paginationContainer.innerHTML = paginationHTML;
}

function navigateToPage(page) {
    if (page !== currentPage) {
        currentPage = page;
        loadChronologicalData(page);
    }
}

function getEventTypeLabel(eventType) {
    switch (eventType) {
        case 'call':
            return 'Llamada';
        case 'message':
            return 'Mensaje';
        case 'data_usage':
            return 'Datos';
        default:
            return eventType;
    }
}

function exportCurrentView() {
    if (!chronoData.events || chronoData.events.length === 0) {
        showError('No hay datos para exportar');
        return;
    }
    
    const csvContent = convertToCSV(chronoData.events);
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        
        const filterSuffix = currentFileFilter === 'all' ? 'todos' : currentFileFilter.replace('.pdf', '');
        link.setAttribute('download', `eventos_cronologicos_${filterSuffix}_pagina_${currentPage}.csv`);
        
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

function convertToCSV(events) {
    const headers = [
        'Fecha',
        'Hora',
        'Tipo de Evento',
        'Detalle de Tipo',
        'Contacto/Info',
        'Descripción',
        'Valor Numérico',
        'Formato/Unidad',
        'Archivo Fuente'
    ];
    
    const rows = events.map(event => {
        const timestamp = new Date(event.timestamp);
        return [
            timestamp.toLocaleDateString('es-ES'),
            timestamp.toLocaleTimeString('es-ES'),
            getEventTypeLabel(event.event_type),
            event.type_detail || '',
            event.contact_info || '',
            event.description || '',
            event.numeric_value || '',
            event.format_info || '',
            event.source_file || ''
        ];
    });
    
    const csvContent = [headers, ...rows]
        .map(row => row.map(field => `"${String(field).replace(/"/g, '""')}"`).join(','))
        .join('\n');
    
    // Add BOM for proper UTF-8 encoding in Excel
    return '\ufeff' + csvContent;
}

function exportAllData() {
    // This would export all legacy data - placeholder implementation
    console.log('Export all data functionality would be implemented here');
    showError('Funcionalidad de exportar todos los datos no implementada aún');
}

function showError(message) {
    // Simple error display - could be enhanced with better styling
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show position-fixed';
    alert.style.top = '20px';
    alert.style.right = '20px';
    alert.style.zIndex = '9999';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}
