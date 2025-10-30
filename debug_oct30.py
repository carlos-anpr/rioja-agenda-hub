#!/usr/bin/env python3
"""Debug específico para la URL del día 30"""

from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import re

def debug_oct30():
    url = "https://www.elbalcondemateo.es/category/agenda/?f_inicio=2025-10-30&f_fin=2025-10-30"
    
    # Extraer parámetros de fecha
    parsed = urlparse(url)
    q = parse_qs(parsed.query)
    f_inicio = (q.get("f_inicio") or q.get("from") or q.get("start"))
    f_fin = (q.get("f_fin") or q.get("to") or q.get("end"))
    start_str = f_inicio[0] if f_inicio else None
    end_str = f_fin[0] if f_fin else None
    
    print(f"URL: {url}")
    print(f"Start str: {start_str}")
    print(f"End str: {end_str}")
    
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    })
    
    with urlopen(req, timeout=20) as resp:
        raw_html = resp.read().decode("utf-8", errors="ignore")
    
    soup = BeautifulSoup(raw_html, "html.parser")
    
    # Buscar el heading de eventos
    heading = None
    for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        text = h.get_text(strip=True).lower()
        if "eventos para" in text:
            heading = h
            print(f"Encontrado heading: {h.get_text(strip=True)}")
            break
    
    if not heading:
        print("No se encontró heading de eventos")
        return
    
    # Buscar el contenedor después del heading
    container = None
    for sib in heading.next_siblings:
        if getattr(sib, "name", None) in {"div", "section", "article"}:
            container = sib
            break
    
    if not container:
        print("No se encontró contenedor")
        return
    
    print(f"Container: {container.name} con clase {container.get('class', [])}")
    
    # Buscar enlaces en el container
    links = container.select('a[href]')
    print(f"Enlaces en container: {len(links)}")
    
    markers = ["cuándo", "cuando", "dónde", "donde", "hora", "edad", "precio"]
    anchors = []
    
    for link in links:
        text = link.get_text(" ", strip=True)
        if text and any(marker in text.lower() for marker in markers):
            href = link.get('href')
            if href and ('elbalcondemateo.es' in href or href.startswith('/')):
                # Extraer título cortando antes de "Cuándo"
                m = re.search(r"(?i)\bcu[aá]ndo\b\s*:\s*", text)
                title = text[:m.start()].strip() if m else text
                
                item = {
                    'title': title,
                    'link': href,
                    'description': text,
                    'date_start': start_str,
                    'date_end': end_str,
                }
                anchors.append(item)
    
    print(f"\nEventos extraídos: {len(anchors)}")
    for i, event in enumerate(anchors[:5]):
        print(f"{i+1}. Título: {event['title'][:100]}...")
        print(f"   Link: {event['link']}")
        print(f"   Date start: {event['date_start']}")
        print()

if __name__ == "__main__":
    debug_oct30()