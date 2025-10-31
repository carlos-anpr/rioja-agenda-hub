#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

# Verificar agenda_larioja
with open('data/eventos_raw/agenda_larioja.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

items_with_images = [item for item in data['items'] if item.get('image')]
print(f"agenda_larioja - Items con imágenes: {len(items_with_images)} de {len(data['items'])}")

if items_with_images:
    print("\nEjemplos:")
    for item in items_with_images[:3]:
        print(f"- {item.get('title', 'N/A')}")
        print(f"  Imagen: {item.get('image', 'N/A')}")
else:
    print("No se encontraron imágenes. Posibles razones:")
    print("- El selector CSS puede ser incorrecto")
    print("- Las imágenes pueden cargarse dinámicamente")
    print("- La estructura del HTML puede haber cambiado")
    
    print("\nVer contenido de un item de ejemplo:")
    if data['items']:
        import pprint
        pprint.pprint(data['items'][0])