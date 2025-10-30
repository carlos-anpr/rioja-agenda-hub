#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

# Leer datos procesados
with open('data/processed/eventos_por_dia.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Encontrar eventos de elbalcon_mateo
elbalcon_events = []
for events in data.values():
    for event in events:
        if event.get('source') == 'elbalcon_mateo':
            elbalcon_events.append(event)

print(f"Total eventos elbalcon_mateo: {len(elbalcon_events)}")
print("\n" + "="*80)
print("PRIMEROS 3 EVENTOS:")
print("="*80)

for i, event in enumerate(elbalcon_events[:3]):
    print(f"\n--- EVENTO {i+1} ---")
    print(f"Título: {event['title']}")
    print(f"Fecha: {event['date']}")
    print(f"Lugar: {event.get('location', 'N/A')}")
    print(f"Link: {event.get('link', 'N/A')}")
    summary = event.get('summary') or 'N/A'
    print(f"Resumen: {summary[:100] if summary != 'N/A' else summary}...")
    
print("\n" + "="*80)
print("ANÁLISIS DE LINKS:")
print("="*80)

# Verificar si los links son únicos y apuntan a eventos específicos
links = [event.get('link') for event in elbalcon_events if event.get('link')]
unique_links = set(links)

print(f"Total links: {len(links)}")
print(f"Links únicos: {len(unique_links)}")
print(f"Links que apuntan a agenda general: {sum(1 for link in links if 'agenda' in link and '?' in link)}")
print(f"Links que apuntan a eventos específicos: {sum(1 for link in links if 'agenda' not in link or '?' not in link)}")

print("\nEjemplos de links:")
for i, link in enumerate(list(unique_links)[:5]):
    print(f"  {i+1}. {link}")