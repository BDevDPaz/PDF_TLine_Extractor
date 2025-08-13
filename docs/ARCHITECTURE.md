# Arquitectura del Sistema: Backend vs Frontend

## Separación Clara de Responsabilidades

### BACKEND (La Cocina y el Cerebro)
**Ubicación**: Servidor Replit (Python/Flask)
**Puerto**: 5000

#### Responsabilidades del Backend:

1. **Procesamiento Pesado**
   - Extracción PDF con sistema híbrido ultra-agresivo
   - Análisis con Google Gemini AI
   - Procesamiento de múltiples estrategias simultáneas
   - Operaciones que requieren alto CPU

2. **Lógica de Negocio**
   - Algoritmos de extracción de datos
   - Validación de información extraída
   - Categorización automática de eventos
   - Cálculos de precisión y estadísticas

3. **Persistencia de Datos**
   - Gestión de base de datos SQLite
   - Operaciones CRUD (Create, Read, Update, Delete)
   - Transacciones seguras
   - Backup y recuperación de datos

4. **Seguridad y Autenticación**
   - Validación de archivos subidos
   - Sanitización de nombres de archivo
   - Control de tamaño de archivos
   - Manejo seguro de API keys

5. **API REST**
   - Exposición de endpoints estructurados
   - Respuestas JSON consistentes
   - Manejo de errores centralizado
   - Logging detallado

#### Endpoints del Backend:

```
POST /api/upload          # Carga de archivos PDF
POST /api/process         # Procesamiento híbrido ultra-agresivo
GET  /api/get-data        # Obtener datos con filtros
GET  /api/export-csv      # Exportación a CSV
POST /api/chat            # Chat con AI
GET  /api/stats           # Estadísticas del sistema
GET  /api/system-info     # Información del sistema
```

### FRONTEND (La Fachada y la Experiencia)
**Ubicación**: Navegador del usuario
**Tecnologías**: HTML, CSS (Tailwind), JavaScript (Vanilla)

#### Responsabilidades del Frontend:

1. **Presentación Visual**
   - Renderizado de componentes UI
   - Estilos y animaciones
   - Responsive design
   - Feedback visual al usuario

2. **Interacción del Usuario**
   - Captura de eventos (click, drag & drop, etc.)
   - Formularios y validación básica
   - Navegación entre secciones
   - Experiencia de usuario fluida

3. **Gestión de Estado del Cliente**
   - Estado de carga (loading states)
   - Datos temporales en memoria
   - Preferencias de filtros
   - Estado de componentes

4. **Comunicación con Backend**
   - Llamadas fetch() a la API
   - Manejo de respuestas asíncronas
   - Error handling para el usuario
   - Progreso de operaciones largas

## Flujo de Trabajo Típico

### 1. Carga de Archivo PDF

**Frontend**:
```javascript
// Usuario selecciona archivo
const file = fileInput.files[0];

// Actualiza estado visual
setLoading(true);
showProgress("Subiendo archivo...");

// Llama al backend
const response = await fetch('/api/upload', {
    method: 'POST',
    body: formData
});
```

**Backend**:
```python
@app.route('/api/upload', methods=['POST'])
def upload_file():
    # Validación de seguridad
    file = request.files['pdfFile']
    filename = secure_filename(file.filename)
    
    # Procesamiento pesado
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Respuesta estructurada
    return jsonify({
        'success': True,
        'filename': filename,
        'file_size': os.path.getsize(filepath)
    })
```

### 2. Procesamiento con Sistema Híbrido

**Frontend**:
```javascript
// Inicia procesamiento
showProgress("Procesando con 5 estrategias...");

const result = await fetch('/api/process', {
    method: 'POST',
    body: JSON.stringify({ filename, pages })
});

// Actualiza UI con resultados
if (result.success) {
    showResults(result.processing_summary);
    loadDataTable();
}
```

**Backend**:
```python
@app.route('/api/process', methods=['POST'])
def process_file():
    # Lógica de negocio compleja
    for strategy_name, extractor_func in extraction_strategies:
        result = extractor_func(filepath, pages)
        
        # Procesamiento pesado
        if result["success"] and result["records_processed"] >= 372:
            logger.info("🏆 OBJETIVO 100% ALCANZADO")
            break
    
    # Respuesta con métricas completas
    return jsonify({
        'success': True,
        'processing_summary': {...},
        'strategy_details': [...]
    })
```

## Ventajas de esta Arquitectura

1. **Escalabilidad**: El backend puede manejar múltiples usuarios simultáneos
2. **Mantenibilidad**: Separación clara de responsabilidades
3. **Seguridad**: Toda la lógica crítica está en el servidor
4. **Performance**: Procesamiento pesado en servidor, UI responsiva en cliente
5. **Flexibilidad**: Frontend puede cambiar sin afectar backend y viceversa

## Tecnologías por Capa

### Backend Stack:
- **Python 3.11**: Lenguaje principal
- **Flask**: Framework web ligero
- **SQLAlchemy**: ORM para base de datos
- **SQLite**: Base de datos embebida
- **Google Gemini AI**: Procesamiento con IA
- **pdfplumber**: Extracción de PDF
- **Gunicorn**: Servidor WSGI

### Frontend Stack:
- **HTML5**: Estructura semántica
- **Tailwind CSS**: Framework de estilos
- **Vanilla JavaScript**: Lógica del cliente
- **Fetch API**: Comunicación con backend
- **Chart.js**: Visualizaciones de datos
- **PDF.js**: Preview de PDFs

Esta arquitectura garantiza un sistema robusto, mantenible y escalable con separación clara de responsabilidades entre el backend (procesamiento y lógica) y el frontend (presentación e interacción).