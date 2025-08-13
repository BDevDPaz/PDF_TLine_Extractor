#!/usr/bin/env python3
"""
Analiza el formato específico del PDF para crear patrones regex precisos
"""

import pdfplumber
import re

def analyze_call_patterns():
    """Analiza las líneas de llamadas en el PDF"""
    
    pdf_path = "attached_assets/1BillSummaryJn_1755046685947.pdf"
    call_lines = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                # Buscar líneas que contengan patrones de llamadas
                if re.search(r'(IN|OUT)\s+.*?[FGH]\s+\d+', line, re.IGNORECASE):
                    call_lines.append(f"Page {page_num}: {line}")
    
    print("🔍 LÍNEAS DE LLAMADAS DETECTADAS:")
    for line in call_lines[:10]:  # Primeras 10
        print(f"  {line}")
    
    return call_lines

def analyze_message_patterns():
    """Analiza las líneas de mensajes en el PDF"""
    
    pdf_path = "attached_assets/1BillSummaryJn_1755046685947.pdf"
    message_lines = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                # Buscar líneas que contengan patrones de mensajes
                if re.search(r'(IN|OUT)\s+.*?(TXT|PIC)', line, re.IGNORECASE):
                    message_lines.append(f"Page {page_num}: {line}")
    
    print("\n📱 LÍNEAS DE MENSAJES DETECTADAS:")
    for line in message_lines[:15]:  # Primeras 15
        print(f"  {line}")
    
    return message_lines

def analyze_data_patterns():
    """Analiza las líneas de datos en el PDF"""
    
    pdf_path = "attached_assets/1BillSummaryJn_1755046685947.pdf"
    data_lines = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                # Buscar líneas que contengan patrones de datos (MB, GB)
                if re.search(r'Mobile Internet|Web Access|\d+[\.,]\d+\s*(MB|GB)', line, re.IGNORECASE):
                    data_lines.append(f"Page {page_num}: {line}")
    
    print("\n📊 LÍNEAS DE DATOS DETECTADAS:")
    for line in data_lines:
        print(f"  {line}")
    
    return data_lines

def suggest_patterns():
    """Sugiere patrones regex mejorados basados en el análisis"""
    
    print("\n🔧 PATRONES REGEX SUGERIDOS:")
    
    # Patrón para llamadas basado en análisis
    call_pattern = r'^\s*(\d{1,2}:\d{2})\s*(AM|PM)\s+(IN|OUT)\s+(.*?)\s+([A-Z])\s+(\d+)\s*(-|\$[\d\.]+)?\s*$'
    print(f"🔥 Llamadas: {call_pattern}")
    
    # Patrón para mensajes basado en análisis  
    message_pattern = r'^\s*(\d{1,2}:\d{2})\s*(AM|PM)\s+(IN|OUT)\s+(.*?)\s+(TXT|PIC|MMS)\s*(-|\$[\d\.]+)?\s*$'
    print(f"📱 Mensajes: {message_pattern}")
    
    # Patrón para datos basado en análisis
    data_pattern = r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+(.*?)\s+(-)\s+(-)\s+([\d,\.]+)\s*(-|\$[\d\.]+)?\s*$'
    print(f"📊 Datos: {data_pattern}")

if __name__ == "__main__":
    print("🔬 ANÁLISIS DETALLADO DEL FORMATO PDF")
    print("=" * 60)
    
    call_lines = analyze_call_patterns()
    message_lines = analyze_message_patterns()
    data_lines = analyze_data_patterns()
    
    suggest_patterns()
    
    print(f"\n📋 RESUMEN:")
    print(f"  Líneas de llamadas detectadas: {len(call_lines)}")
    print(f"  Líneas de mensajes detectadas: {len(message_lines)}")
    print(f"  Líneas de datos detectadas: {len(data_lines)}")
    print(f"  Total estimado: {len(call_lines) + len(message_lines) + len(data_lines)}")