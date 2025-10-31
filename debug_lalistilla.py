#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

# Verificar La Listilla en datos procesados
with open('data/processed/eventos_por_dia.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

lalistilla_events = [event for events in data.values() for event in events if event.get('source') == 'larioja_lalistilla']
events_with_images = [e for e in lalistilla_events if e.get('image')]

print("🔍 LA LISTILLA - ANÁLISIS DE IMÁGENES")
print("="*50)
print(f"Eventos totales: {len(lalistilla_events)}")
print(f"Eventos con imagen: {len(events_with_images)}")
print(f"Porcentaje: {len(events_with_images)/len(lalistilla_events)*100:.1f}%")

print("\n📸 EJEMPLOS DE IMÁGENES:")
for i, event in enumerate(events_with_images[:3]):
    print(f"{i+1}. {event['title'][:50]}...")
    print(f"   Imagen: {event['image']}")
    print()

print("\n📝 PROBLEMA DE DESCRIPCIONES:")
long_descriptions = [e for e in lalistilla_events if e.get('summary') and len(e.get('summary', '')) > 200]
print(f"Eventos con descripción > 200 chars: {len(long_descriptions)}")

if long_descriptions:
    print("\nEjemplo de descripción larga:")
    desc = long_descriptions[0].get('summary', '')
    print(f"Título: {long_descriptions[0]['title'][:50]}...")
    print(f"Descripción ({len(desc)} chars): {desc[:300]}...")
    print()

print("🛠️ ACCIONES NECESARIAS:")
print("1. Verificar si las URLs de imagen son correctas")
print("2. Implementar truncado de descripciones en el frontend")
print("3. Agregar límite de caracteres para La Listilla específicamente")