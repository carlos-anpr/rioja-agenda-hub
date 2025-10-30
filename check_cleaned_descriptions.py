#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

# Leer datos de prueba
with open('data/eventos_raw/elbalcon_mateo_test.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("DESCRIPCIONES DESPUÉS DE LA LIMPIEZA:")
print("="*80)

items_with_desc = [item for item in data['items'] if item.get('description')]
print(f"Items con descripción: {len(items_with_desc)}")

for i, item in enumerate(items_with_desc[:5]):
    desc = item.get('description', '')
    title = item.get('title', 'N/A')
    print(f"\n--- EJEMPLO {i+1} ---")
    print(f"Título: {title}")
    print(f"Descripción ({len(desc)} chars): {desc}")

print("\n" + "="*80)
print("ESTADÍSTICAS:")
print("="*80)

lengths = [len(item.get('description', '')) for item in data['items'] if item.get('description')]
if lengths:
    print(f"Descripción más corta: {min(lengths)} caracteres")
    print(f"Descripción más larga: {max(lengths)} caracteres") 
    print(f"Promedio: {sum(lengths) // len(lengths)} caracteres")
    print(f"Items con descripciones > 200 chars: {sum(1 for l in lengths if l > 200)}")
else:
    print("No hay descripciones")