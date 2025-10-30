#!/usr/bin/env python3
"""Inspeccionar el HTML real de la página"""

from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import re

def inspect_html():
    url = "https://www.elbalcondemateo.es/category/agenda/?f_inicio=2025-10-30&f_fin=2025-10-30"
    
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    })
    
    with urlopen(req, timeout=20) as resp:
        raw_html = resp.read().decode("utf-8", errors="ignore")
    
    print(f"HTML length: {len(raw_html)}")
    
    soup = BeautifulSoup(raw_html, "html.parser")
    
    # Buscar el heading de eventos
    headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    for h in headings:
        text = h.get_text(strip=True).lower()
        if "eventos para" in text:
            print(f"Encontrado heading: {h.get_text(strip=True)}")
            
            # Buscar el contenedor después del heading
            container = None
            for sib in h.next_siblings:
                if getattr(sib, "name", None) in {"div", "section", "article"}:
                    container = sib
                    break
            
            if container:
                print(f"Container encontrado: {container.name} con clase {container.get('class', [])}")
                
                # Buscar enlaces en el container
                links = container.select('a[href]')
                print(f"Enlaces en container: {len(links)}")
                
                markers = ["cuándo", "cuando", "dónde", "donde", "hora", "edad", "precio"]
                event_links = []
                
                for link in links:
                    text = link.get_text(" ", strip=True)
                    if text and any(marker in text.lower() for marker in markers):
                        href = link.get('href')
                        if href:
                            # Extraer título cortando antes de "Cuándo"
                            m = re.search(r"(?i)\bcu[aá]ndo\b\s*:\s*", text)
                            title = text[:m.start()].strip() if m else text
                            
                            event_links.append({
                                'title': title[:100] + "..." if len(title) > 100 else title,
                                'link': href,
                                'full_text': text[:200] + "..." if len(text) > 200 else text
                            })
                
                print(f"Enlaces de eventos encontrados: {len(event_links)}")
                for i, event in enumerate(event_links[:3]):
                    print(f"{i+1}. Título: {event['title']}")
                    print(f"   Link: {event['link']}")
                    print(f"   Texto completo: {event['full_text']}")
                    print()
            break
    
    # También buscar directamente en el documento si no encontramos el container
    if not locals().get('event_links'):
        print("\nBuscando enlaces en todo el documento...")
        main = soup.select_one("main, .site-main, #content, .elementor-widget-container") or soup
        all_links = main.select('a[href]')
        print(f"Total enlaces en main: {len(all_links)}")
        
        markers = ["cuándo", "cuando", "dónde", "donde", "hora", "edad", "precio"]
        event_links = []
        
        for link in all_links:
            text = link.get_text(" ", strip=True)
            if text and any(marker in text.lower() for marker in markers):
                href = link.get('href')
                if href and ('elbalcondemateo.es' in href or href.startswith('/')):
                    m = re.search(r"(?i)\bcu[aá]ndo\b\s*:\s*", text)
                    title = text[:m.start()].strip() if m else text
                    
                    event_links.append({
                        'title': title[:100] + "..." if len(title) > 100 else title,
                        'link': href,
                        'full_text': text[:200] + "..." if len(text) > 200 else text
                    })
        
        print(f"Enlaces de eventos encontrados en todo el documento: {len(event_links)}")
        for i, event in enumerate(event_links[:3]):
            print(f"{i+1}. Título: {event['title']}")
            print(f"   Link: {event['link']}")  
            print(f"   Texto completo: {event['full_text']}")
            print()

if __name__ == "__main__":
    inspect_html()