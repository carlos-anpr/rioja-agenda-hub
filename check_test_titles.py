#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

# Leer datos de prueba
with open('data/eventos_raw/elbalcon_mateo_test.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("TÍTULOS DE EVENTOS DE PRUEBA (primeros 10):")
print("="*60)

for i, item in enumerate(data['items'][:10]):
    title = item.get('title', 'SIN TITULO')
    link = item.get('link', 'N/A')
    print(f"{i+1:2d}. {title}")
    print(f"     Link: {link[:60]}...")
    print()