#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

# Verificar imágenes en logrono_agenda
with open('data/eventos_raw/logrono_agenda.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

items_with_images = [item for item in data['items'] if item.get('image')]
print(f"Items con imágenes: {len(items_with_images)} de {len(data['items'])}")

print("\n" + "="*60)
print("EJEMPLOS DE IMÁGENES:")
print("="*60)

for i, item in enumerate(items_with_images[:5]):
    print(f"\n--- EJEMPLO {i+1} ---")
    print(f"Título: {item.get('title', 'N/A')}")
    print(f"Imagen: {item.get('image', 'N/A')}")

# También verificar todos los crawlers
print("\n" + "="*60)
print("RESUMEN POR FUENTE:")
print("="*60)

import glob
import os

for json_file in glob.glob('data/eventos_raw/*.json'):
    source_name = os.path.basename(json_file).replace('.json', '')
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
        
        total_items = len(source_data['items'])
        items_with_images = len([item for item in source_data['items'] if item.get('image')])
        
        print(f"{source_name:20} - {items_with_images:3d}/{total_items:3d} items con imagen")
        
        # Mostrar un ejemplo de imagen si existe
        if items_with_images > 0:
            example_image = next(item.get('image') for item in source_data['items'] if item.get('image'))
            print(f"                     Ejemplo: {example_image[:80]}...")
        print()
        
    except Exception as e:
        print(f"{source_name:20} - Error: {e}")