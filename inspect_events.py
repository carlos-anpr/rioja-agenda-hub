#!/usr/bin/env python3
"""Inspeccionar los eventos extraídos"""

import json

def inspect_events():
    filename = 'data/eventos_raw/elbalcon_mateo_test.json'
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Total items: {len(data['items'])}")
    print(f"URLs visitadas: {len(data['metadata']['visited_urls'])}")
    print(f"Primera URL visitada: {data['metadata']['visited_urls'][0] if data['metadata']['visited_urls'] else 'None'}")
    
    # Buscar eventos por fecha
    oct30_events = [item for item in data['items'] if item.get('date_start') == '2025-10-30']
    oct31_events = [item for item in data['items'] if item.get('date_start') == '2025-10-31']
    print(f"\nEventos con date_start = '2025-10-30': {len(oct30_events)}")
    print(f"Eventos con date_start = '2025-10-31': {len(oct31_events)}")
    
    print("\nPrimeros 5 eventos:")
    for i, item in enumerate(data['items'][:5]):
        print(f"{i+1}. Title: {item.get('title', 'NO TITLE')[:100]}...")
        print(f"   Link: {item.get('link', 'NO LINK')}")
        print(f"   Date start: {item.get('date_start', 'NO DATE')}")
        print()
    
    if oct31_events:
        print("\nPrimeros 3 eventos del 31 de octubre:")
        for i, item in enumerate(oct31_events[:3]):
            print(f"{i+1}. Title: {item.get('title', 'NO TITLE')[:60]}...")
            print(f"   Link: {item.get('link', 'NO LINK')}")
            print(f"   Date start: {item.get('date_start', 'NO DATE')}")
            print()

if __name__ == "__main__":
    inspect_events()