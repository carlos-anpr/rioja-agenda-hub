#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

# Leer datos raw de elbalcon_mateo
with open('data/eventos_raw/elbalcon_mateo.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Buscar items con descripciones largas
items_with_long_desc = []
for item in data['items']:
    desc = item.get('description', '')
    if desc and len(desc) > 100:
        items_with_long_desc.append(item)

print(f"Items con descripciones largas: {len(items_with_long_desc)}")
print(f"Total items: {len(data['items'])}")

print("\n" + "="*80)
print("EJEMPLOS DE DESCRIPCIONES LARGAS:")
print("="*80)

for i, item in enumerate(items_with_long_desc[:3]):
    desc = item.get('description', '')
    print(f"\n--- EJEMPLO {i+1} ---")
    print(f"Título: {item.get('title', 'N/A')}")
    print(f"Descripción ({len(desc)} caracteres):")
    print(desc[:400] + "..." if len(desc) > 400 else desc)

print("\n" + "="*80)
print("ANÁLISIS DE LONGITUD:")
print("="*80)

# Estadísticas de longitud
lengths = [len(item.get('description', '')) for item in data['items'] if item.get('description')]
if lengths:
    print(f"Descripción más corta: {min(lengths)} caracteres")
    print(f"Descripción más larga: {max(lengths)} caracteres")
    print(f"Promedio: {sum(lengths) // len(lengths)} caracteres")
    print(f"Items con descripciones > 200 chars: {sum(1 for l in lengths if l > 200)}")
    print(f"Items con descripciones > 500 chars: {sum(1 for l in lengths if l > 500)}")