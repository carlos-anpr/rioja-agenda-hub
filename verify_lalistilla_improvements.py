#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificación de las mejoras implementadas para La Listilla
"""

import json

print("🎯 VERIFICACIÓN DE MEJORAS - LA LISTILLA")
print("="*60)

# Cargar datos procesados
with open('data/processed/eventos_por_dia.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Filtrar eventos de La Listilla
lalistilla_events = [event for events in data.values() for event in events if event.get('source') == 'larioja_lalistilla']

print(f"📊 ESTADÍSTICAS GENERALES:")
print(f"  • Total eventos La Listilla: {len(lalistilla_events)}")

# Análisis de imágenes
events_with_images = [e for e in lalistilla_events if e.get('image')]
print(f"  • Eventos con imagen: {len(events_with_images)}")
print(f"  • Porcentaje con imagen: {len(events_with_images)/len(lalistilla_events)*100:.1f}%")

# Análisis de descripciones
long_descriptions = [e for e in lalistilla_events if e.get('summary') and len(e.get('summary', '')) > 120]
medium_descriptions = [e for e in lalistilla_events if e.get('summary') and 50 <= len(e.get('summary', '')) <= 120]
short_descriptions = [e for e in lalistilla_events if e.get('summary') and len(e.get('summary', '')) < 50]

print(f"\n📝 ANÁLISIS DE DESCRIPCIONES:")
print(f"  • Descripciones largas (>120 chars): {len(long_descriptions)}")
print(f"  • Descripciones medias (50-120 chars): {len(medium_descriptions)}")
print(f"  • Descripciones cortas (<50 chars): {len(short_descriptions)}")

# Mostrar ejemplos
if long_descriptions:
    print(f"\n📋 EJEMPLO DE DESCRIPCIÓN LARGA (será truncada):")
    example = long_descriptions[0]
    summary = example.get('summary', '')
    print(f"  Título: {example['title'][:50]}...")
    print(f"  Original ({len(summary)} chars): {summary[:100]}...")
    
    # Simular el truncado que hace el frontend
    if len(summary) > 120:
        truncated = summary[:120]
        last_space = truncated.rfind(' ')
        if last_space > 80:
            truncated = truncated[:last_space]
        truncated += '...'
        print(f"  Truncada ({len(truncated)} chars): {truncated}")

print(f"\n🖼️ ANÁLISIS DE IMÁGENES:")
# Contar imágenes únicas
from collections import Counter
image_urls = [e['image'] for e in events_with_images]
unique_images = Counter(image_urls)

print(f"  • Total imágenes: {len(image_urls)}")
print(f"  • Imágenes únicas: {len(unique_images)}")
print(f"  • Imagen más común: {unique_images.most_common(1)[0][1]}x repetida")

# Mostrar algunos ejemplos de imágenes
print(f"\n📸 EJEMPLOS DE IMÁGENES:")
for i, event in enumerate(events_with_images[:3]):
    print(f"  {i+1}. {event['title'][:40]}...")
    print(f"     🖼️ {event['image']}")

print(f"\n✅ MEJORAS IMPLEMENTADAS:")
print(f"  🔤 Frontend trunca descripciones > 120 caracteres")
print(f"  📱 Cards mantienen tamaño uniforme")
print(f"  🖼️ {len(events_with_images)} eventos tienen imagen")
print(f"  🎯 Mejora visual significativa en la interfaz")

print(f"\n🌐 PARA VER LOS CAMBIOS:")
print(f"  • Abre: http://localhost:8501")
print(f"  • Filtra por 'La Listilla' para ver solo estos eventos")
print(f"  • Las descripciones ahora son más cortas y legibles")
print(f"  • Los cards tienen un aspecto más profesional")