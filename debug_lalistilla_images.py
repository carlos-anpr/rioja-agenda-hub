#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análisis detallado del problema de imágenes de La Listilla
"""

import json
import requests

print("🔍 DIAGNÓSTICO DETALLADO - IMÁGENES LA LISTILLA")
print("="*60)

# Cargar datos procesados
with open('data/processed/eventos_por_dia.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Obtener eventos de La Listilla
lalistilla_events = []
for events in data.values():
    for event in events:
        if event.get('source') == 'larioja_lalistilla' and event.get('image'):
            lalistilla_events.append(event)

print(f"📊 Eventos de La Listilla con campo imagen: {len(lalistilla_events)}")

if lalistilla_events:
    print("\n🔗 ANÁLISIS DE URLs:")
    
    # Tomar una muestra de URLs
    sample_events = lalistilla_events[:5]
    
    for i, event in enumerate(sample_events):
        url = event['image']
        print(f"\n--- EVENTO {i+1} ---")
        print(f"Título: {event['title'][:50]}...")
        print(f"URL imagen: {url}")
        
        # Verificar si la URL es accesible
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            print(f"Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"Content-Length: {response.headers.get('content-length', 'N/A')}")
            
            if response.status_code == 200:
                print("✅ URL accesible")
            else:
                print("❌ URL no accesible")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error al acceder: {str(e)[:100]}")
            
        except Exception as e:
            print(f"❌ Error inesperado: {str(e)[:100]}")

# Verificar si hay un problema de CORS o dominio
print(f"\n🌐 ANÁLISIS DE DOMINIOS:")
from collections import Counter
from urllib.parse import urlparse

domains = []
for event in lalistilla_events:
    try:
        parsed = urlparse(event['image'])
        domains.append(parsed.netloc)
    except:
        domains.append('ERROR')

domain_counter = Counter(domains)
print("Dominios de imágenes:")
for domain, count in domain_counter.items():
    print(f"  {domain}: {count} imágenes")

print(f"\n🛠️ POSIBLES PROBLEMAS:")
print("1. URLs no accesibles (404, 403, etc.)")
print("2. Problemas de CORS en el navegador")
print("3. Imágenes que requieren autenticación")
print("4. URLs malformadas")
print("5. Problema en el frontend JavaScript")

print(f"\n🔧 VERIFICAR EN NAVEGADOR:")
print("1. Abre las DevTools (F12)")
print("2. Ve a la pestaña Network")
print("3. Filtra por 'Img'")
print("4. Recarga la página")
print("5. Busca errores 404, 403 o CORS")