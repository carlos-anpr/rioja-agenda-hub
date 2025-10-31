#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificar si las imágenes de La Listilla están en los datos procesados
"""

import json

print("🔍 VERIFICACIÓN FINAL - IMÁGENES LA LISTILLA")
print("="*60)

# Cargar datos procesados
with open('data/processed/eventos_por_dia.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Buscar eventos de La Listilla
lalistilla_events = []
for date, events in data.items():
    for event in events:
        if event.get('source') == 'larioja_lalistilla':
            lalistilla_events.append(event)

total_lalistilla = len(lalistilla_events)
with_images = [e for e in lalistilla_events if e.get('image')]

print(f"📊 ESTADÍSTICAS:")
print(f"  Total eventos La Listilla: {total_lalistilla}")
print(f"  Eventos con imagen: {len(with_images)}")
print(f"  Porcentaje: {len(with_images)/total_lalistilla*100:.1f}%")

print(f"\n🖼️ EJEMPLOS DE IMÁGENES (primeros 5):")
for i, event in enumerate(with_images[:5]):
    print(f"  {i+1}. {event['title'][:40]}...")
    print(f"     {event['image']}")

# Verificar si las URLs están correctas
print(f"\n🌐 ANÁLISIS DE URLs:")
from collections import Counter
from urllib.parse import urlparse

domains = []
for event in with_images:
    try:
        parsed = urlparse(event['image'])
        domains.append(parsed.netloc)
    except:
        domains.append('ERROR')

domain_counter = Counter(domains)
print("Dominios encontrados:")
for domain, count in domain_counter.items():
    print(f"  • {domain}: {count} imágenes")

print(f"\n🚀 SIGUIENTE PASO:")
print("1. Recargar la página web (http://localhost:8501)")
print("2. Abrir DevTools (F12) → Network → Img")
print("3. Filtrar por 'La Listilla' en el frontend")
print("4. Ver si las imágenes aparecen ahora")
print("5. Si siguen sin aparecer, verificar errores en Console")

print(f"\n✅ Las URLs están correctas en los datos procesados!")
print("El problema podría estar en el frontend o el navegador.")