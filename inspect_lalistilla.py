#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para inspeccionar La Listilla y mejorar el selector de imágenes
"""

import requests
from bs4 import BeautifulSoup

print("🔍 INSPECCIONANDO LARIOJA.LALISTILLA.COM")
print("="*50)

try:
    response = requests.get("https://larioja.lalistilla.com/", timeout=15)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Buscar contenedores de eventos
    events = soup.select('.btx-item.js-item-accordion')
    print(f"Eventos encontrados: {len(events)}")
    
    if events:
        print("\n--- ANÁLISIS DEL PRIMER EVENTO ---")
        event = events[0]
        
        # Buscar todas las imágenes en el evento
        images = event.select('img')
        print(f"Imágenes en el evento: {len(images)}")
        
        for i, img in enumerate(images):
            print(f"\nImagen {i+1}:")
            print(f"  Src: {img.get('src', 'N/A')}")
            print(f"  Alt: {img.get('alt', 'N/A')}")
            print(f"  Class: {img.get('class', 'N/A')}")
            print(f"  Parent: {img.parent.name if img.parent else 'N/A'}")
            print(f"  Parent class: {img.parent.get('class', 'N/A') if img.parent else 'N/A'}")

        # Verificar estructura del evento
        print(f"\n--- ESTRUCTURA DEL EVENTO ---")
        print("Clases del contenedor:", event.get('class', 'N/A'))
        
        # Buscar específicamente imágenes de planes
        plan_images = event.select('.btx-item.js-item-html img')
        print(f"\nImágenes con selector '.btx-item.js-item-html img': {len(plan_images)}")
        
        for img in plan_images:
            print(f"  - {img.get('src', 'N/A')}")

except Exception as e:
    print(f"Error al inspeccionar: {e}")
    
print("\n🛠️ RECOMENDACIONES:")
print("- Selector actual: '.btx-item.js-item-html img'")
print("- Posibles mejoras:")
print("  • 'img[src*=\"plan\"]' (solo imágenes de planes)")
print("  • '.btx-item img:not([src*=\"bolanos\"])' (excluir placeholder)")
print("  • 'img[src*=\"gestion.lalistilla\"], img[src*=\"admin.lalistilla\"]'")