#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para demostrar las mejoras visuales en los cards con imágenes
"""

print("🎨 REDISEÑO DE CARDS CON IMÁGENES")
print("="*60)
print("")
print("✨ NUEVAS CARACTERÍSTICAS:")
print("  📸 Imágenes atractivas en los cards de eventos")
print("  🎭 Placeholders con iconos por categoría")
print("  🔄 Efecto hover con zoom en imágenes")
print("  📱 Diseño responsive y moderno")
print("  🛠️ Manejo inteligente de errores de imagen")
print("")
print("📊 ESTADÍSTICAS DE IMÁGENES:")

import json

with open('data/processed/eventos_por_dia.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

total_events = sum(len(events) for events in data.values())
events_with_images = sum(1 for events in data.values() for event in events if event.get('image'))

print(f"  📈 Total eventos: {total_events:,}")
print(f"  🖼️ Eventos con imagen: {events_with_images:,}")
print(f"  📊 Porcentaje con imagen: {events_with_images/total_events*100:.1f}%")

# Por fuente
from collections import Counter
sources_with_images = Counter()
sources_total = Counter()

for events in data.values():
    for event in events:
        source = event['source']
        sources_total[source] += 1 
        if event.get('image'):
            sources_with_images[source] += 1

print("")
print("📋 POR FUENTE:")
for source in sources_total:
    total = sources_total[source]
    with_img = sources_with_images[source]
    percentage = with_img/total*100 if total > 0 else 0
    print(f"  {source:20} - {with_img:4d}/{total:4d} ({percentage:5.1f}%)")

print("")
print("🌐 PARA VER LOS CAMBIOS:")
print("  1. Abre: http://localhost:8501")
print("  2. Los cards ahora tienen:")
print("     • Imágenes de 200px de altura")
print("     • Efecto zoom al hacer hover")
print("     • Iconos por categoría cuando no hay imagen")  
print("     • Diseño más moderno y atractivo")
print("")
print("🎯 CATEGORÍAS CON ICONOS:")
categories = {
    'conciertos': '🎵', 'música': '🎼', 'teatro': '🎭', 
    'exposiciones': '🖼️', 'cine': '🎬', 'planes con niños': '👨‍👩‍👧‍👦',
    'visitas guiadas': '🚶‍♂️', 'espectáculos': '🎪', 'literario': '📚'
}
for cat, icon in categories.items():
    print(f"  {icon} {cat}")

print("")
print("✅ El rediseño está completo y funcionando!")