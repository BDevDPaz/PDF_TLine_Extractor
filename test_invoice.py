#!/usr/bin/env python3
"""
Script para crear un PDF de factura telefónica de prueba
"""
import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def create_test_invoice():
    filename = "backend/uploads/factura_test.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "FACTURA TELEFÓNICA - PRUEBA")
    
    # Información de la línea
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, "Línea Principal: (555) 123-4567")
    
    # Eventos de llamadas
    y_pos = height - 150
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y_pos, "FECHA")
    c.drawString(120, y_pos, "HORA")
    c.drawString(180, y_pos, "EVENTO")
    c.drawString(240, y_pos, "TIPO")
    c.drawString(300, y_pos, "CONTACTO")
    c.drawString(400, y_pos, "DURACIÓN")
    
    # Datos de ejemplo
    events = [
        ("15/Jul/2024", "09:30", "Llamada", "SALIENTE", "(555) 987-6543", "5:23"),
        ("15/Jul/2024", "10:45", "Mensaje", "ENTRANTE", "(555) 111-2222", "1"),
        ("15/Jul/2024", "14:20", "Llamada", "ENTRANTE", "(555) 333-4444", "12:45"),
        ("16/Jul/2024", "08:15", "Datos", "CONSUMO", "Internet", "25.5 MB"),
        ("16/Jul/2024", "11:30", "Mensaje", "SALIENTE", "(555) 555-6666", "1"),
    ]
    
    c.setFont("Helvetica", 9)
    y_pos -= 20
    
    for event in events:
        c.drawString(50, y_pos, event[0])
        c.drawString(120, y_pos, event[1])
        c.drawString(180, y_pos, event[2])
        c.drawString(240, y_pos, event[3])
        c.drawString(300, y_pos, event[4])
        c.drawString(400, y_pos, event[5])
        y_pos -= 15
    
    c.save()
    print(f"PDF de prueba creado: {filename}")
    return filename

if __name__ == "__main__":
    try:
        filename = create_test_invoice()
        print("✅ PDF de prueba creado exitosamente")
    except Exception as e:
        print(f"❌ Error creando PDF: {e}")
        sys.exit(1)