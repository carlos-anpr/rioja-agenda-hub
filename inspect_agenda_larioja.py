#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para inspeccionar la estructura HTML de agenda.larioja.com
y encontrar los selectores correctos para las imágenes
"""

import requests
from bs4 import BeautifulSoup

print("🔍 INSPECCIONANDO AGENDA.LARIOJA.COM")
print("="*50)

try:
    response = requests.get("https://agenda.larioja.com/", timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Buscar artículos con eventos
    articles = soup.select('section article')
    print(f"Artículos encontrados: {len(articles)}")
    
    if articles:
        print("\n--- ESTRUCTURA DEL PRIMER ARTÍCULO ---")
        article = articles[0]
        print("HTML del artículo:")
        print(article.prettify()[:1000] + "...")
        
        # Buscar todas las imágenes en el artículo
        images = article.select('img')
        print(f"\nImágenes en el artículo: {len(images)}")
        
        for i, img in enumerate(images):
            print(f"  Imagen {i+1}:")
            print(f"    Tag: {img.name}")
            print(f"    Src: {img.get('src', 'N/A')}")
            print(f"    Alt: {img.get('alt', 'N/A')}")
            print(f"    Class: {img.get('class', 'N/A')}")
            print(f"    Parent: {img.parent.name if img.parent else 'N/A'}")
            print()

except Exception as e:
    print(f"Error al inspeccionar: {e}")
    
print("\n🛠️ POSIBLES SELECTORES A PROBAR:")
print("- 'img'")
print("- 'article img'")
print("- '.voc-agenda-foto img'")
print("- '.imagen img'")
print("- '[src*=\".jpg\"], [src*=\".png\"], [src*=\".jpeg\"]'")