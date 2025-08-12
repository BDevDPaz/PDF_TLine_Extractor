#!/bin/bash
# Script Completo de Creación de Aplicación (v3)
# Este script crea una aplicación web robusta, completa y documentada en un solo paso.

echo "Iniciando la creación de la aplicación robusta y documentada (v3)..."
echo "------------------------------------------------------------------"
echo ""

# --- 1. Crear la estructura de directorios en la raíz ---
echo "PASO 1: Creando estructura de directorios..."
mkdir -p app/extractors app/db app/static/js app/templates app/services data/raw data/processed
echo "✅ Estructura de directorios creada."
echo ""

# --- 2. Crear los archivos de configuración y documentación ---
echo "PASO 2: Creando archivos de configuración y README.md..."

# Archivo README.md
cat > README.md << 'EOF'
# 🚀 Analizador de Datos PDF con IA (v3)

Este proyecto es una aplicación web completa construida con Flask que proporciona un panel de control con cuatro herramientas integradas para procesar, analizar, visualizar y tomar notas sobre datos extraídos de archivos PDF (diseñado para facturas de servicios).

La aplicación es robusta, garantiza la integridad de los datos durante las cargas y cuenta con una interfaz de usuario moderna y responsiva construida con TailwindCSS.

---

## ✨ Características Principales

1.  **Carga y Procesamiento de PDFs:**
    *   Sube múltiples archivos PDF simultáneamente.
    *   El sistema extrae de forma inteligente registros de llamadas, mensajes y uso de datos.
    *   **Integridad de Datos:** Al volver a subir un archivo, solo se actualizan los datos de ese archivo específico, sin afectar los datos de otros archivos ya procesados. Todo el proceso es transaccional.

2.  **Analizador Interactivo:**
    *   Visualiza resúmenes de datos con gráficos (Chart.js).
    *   Explora todos los registros en una tabla de datos potente y cronológica (AG-Grid).
    *   Funcionalidades de búsqueda, filtrado y ordenación avanzadas.
    *   Exporta los datos de la tabla a un archivo CSV.

3.  **Visor de PDF:**
    *   Una herramienta simple para cargar y visualizar cualquier archivo PDF directamente en el navegador.

4.  **Notas con IA (Google Gemini):**
    *   Un bloc de notas inteligente que se guarda automáticamente en el navegador.
    *   Utiliza la IA para resumir, continuar, corregir o extraer puntos de acción del texto.

---

## 🔧 Pila Tecnológica (Tech Stack)

*   **Backend:** Python 3, Flask
*   **Base de Datos:** SQLite con SQLAlchemy ORM (para una gestión de datos robusta)
*   **Procesamiento de Datos:** Pandas, pdfplumber
*   **Frontend:** HTML5, TailwindCSS, JavaScript
*   **Visualización:** Chart.js, AG-Grid Community
*   **IA Generativa:** Google Gemini API
*   **Entorno:** Configurado para Replit con Poetry

---

## 📂 Estructura del Proyecto