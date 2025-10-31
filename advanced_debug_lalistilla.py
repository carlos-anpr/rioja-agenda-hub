#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debugging avanzado de imágenes de La Listilla con diferentes configuraciones
"""

import requests
import json
from urllib.parse import urlparse

print("🕵️ DEBUG AVANZADO - IMÁGENES LA LISTILLA")
print("="*60)

# Cargar algunos ejemplos de URLs
with open('data/processed/eventos_por_dia.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

lalistilla_images = []
for events in data.values():
    for event in events:
        if (event.get('source') == 'larioja_lalistilla' and 
            event.get('image') and 
            len(lalistilla_images) < 5):
            lalistilla_images.append(event['image'])

print(f"🔗 Probando {len(lalistilla_images)} URLs diferentes:")

# Diferentes configuraciones de headers
test_configs = [
    {
        'name': 'Sin headers',
        'headers': {}
    },
    {
        'name': 'User-Agent básico',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    },
    {
        'name': 'Headers completos',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    },
    {
        'name': 'Con Referer',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://larioja.lalistilla.com/',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        }
    }
]

success_count = 0
total_tests = 0

for i, url in enumerate(lalistilla_images):
    print(f"\n--- URL {i+1}: {url[:50]}... ---")
    
    for config in test_configs:
        total_tests += 1
        print(f"\n  🧪 {config['name']}:")
        
        try:
            response = requests.get(
                url, 
                headers=config['headers'],
                timeout=5,
                stream=True,
                allow_redirects=True
            )
            
            print(f"    Status: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = response.headers.get('content-length', '0')
                print(f"    ✅ Éxito - {content_type} ({content_length} bytes)")
                success_count += 1
                break  # Si funciona con esta config, pasar a la siguiente URL
            else:
                print(f"    ❌ Error HTTP: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"    ⏱️ Timeout")
        except requests.exceptions.ConnectionError as e:
            print(f"    🔌 Error conexión: {str(e)[:50]}...")
        except Exception as e:
            print(f"    💥 Error: {str(e)[:50]}...")

print(f"\n📊 RESUMEN:")
print(f"URLs exitosas: {success_count}/{len(lalistilla_images)}")
print(f"Total pruebas: {total_tests}")

if success_count > 0:
    print(f"\n✅ ¡Algunas URLs funcionan! El problema puede ser:")
    print("1. Configuración específica de headers necesaria")
    print("2. Rate limiting del servidor")
    print("3. Carga demasiado rápida en el navegador")
else:
    print(f"\n❌ Ninguna URL funciona desde Python")
    print("Pero funcionan desde navegador → Problema de User-Agent/CORS")

print(f"\n🛠️ SOLUCIONES POSIBLES:")
print("1. Implementar lazy loading más lento")
print("2. Agregar User-Agent correcto en el frontend")
print("3. Usar proxy/CORS bypass")
print("4. Pre-cargar imágenes con delay")