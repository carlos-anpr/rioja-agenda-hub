#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

# Verificar URLs de imágenes procesadas
with open('data/processed/eventos_por_dia.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

events_with_images = [event for events in data.values() for event in events if event.get('image')]

print("MUESTRAS DE IMÁGENES PROCESADAS:")
print("="*60)

# Mostrar ejemplos por fuente
sources = {}
for event in events_with_images:
    source = event['source']
    if source not in sources:
        sources[source] = []
    if len(sources[source]) < 3:
        sources[source].append(event)

for source, events in sources.items():
    print(f"\n--- {source.upper()} ---")
    for i, event in enumerate(events):
        print(f"{i+1}. {event['title'][:50]}...")
        print(f"   Imagen: {event['image']}")
        print()