#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

# Verificar larioja_lalistilla
with open('data/eventos_raw/larioja_lalistilla.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

items_with_images = [item for item in data['items'] if item.get('image')]
print(f"larioja_lalistilla - Items con imágenes: {len(items_with_images)} de {len(data['items'])}")

if items_with_images:
    print("\nEjemplos:")
    for item in items_with_images[:3]:
        title = item.get('title', item.get('heading_text', 'N/A'))
        print(f"- {title[:50]}...")
        print(f"  Imagen: {item.get('image', 'N/A')[:100]}...")
        print()
else:
    print("No se encontraron imágenes en larioja_lalistilla")
    
print(f"\nTotal items: {len(data['items'])}")
print(f"Items con imagen: {len(items_with_images)}")
print(f"Porcentaje: {len(items_with_images)/len(data['items'])*100:.1f}%")