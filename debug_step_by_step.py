#!/usr/bin/env python3
"""Debug step by step el proceso del crawler"""

import asyncio
import json
import yaml
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, JsonCssExtractionStrategy
from bs4 import BeautifulSoup

async def debug_crawler_step_by_step():
    # 1. Cargar la configuración de test
    config_path = Path("crawl_configs/elbalcon_mateo_test.yaml")
    with config_path.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    
    print("=== 1. Configuración cargada ===")
    print(f"Schema: {cfg.get('schema', {}).get('name')}")
    
    # 2. Generar URLs (solo la primera para debug)
    url = "https://www.elbalcondemateo.es/category/agenda/?f_inicio=2025-10-30&f_fin=2025-10-30"
    print(f"\n=== 2. URL de prueba ===")
    print(f"URL: {url}")
    
    # 3. Configurar la extracción CSS
    schema = cfg.get("schema")
    if schema:
        # Normalizar schema
        normalized_schema = dict(schema)
        base_selector = normalized_schema.pop("base_selector", normalized_schema.pop("base-selector", None))
        if base_selector and "baseSelector" not in normalized_schema:
            normalized_schema["baseSelector"] = base_selector
        
        extraction = JsonCssExtractionStrategy(normalized_schema, verbose=True)
        print(f"\n=== 3. Extracción CSS configurada ===")
        print(f"Base selector: {normalized_schema.get('baseSelector')}")
    
    # 4. Configurar el crawler
    from crawl4ai import CacheMode
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=extraction,
        delay_before_return_html=0.4,
    )
    
    browser_config = BrowserConfig(headless=True, verbose=True)
    
    # 5. Ejecutar crawler
    print(f"\n=== 4. Ejecutando crawler ===")
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url, config=run_config)
        
        print(f"Status: {result.success}")
        print(f"HTML length: {len(result.html) if result.html else 0}")
        
        # 6. Procesar resultado CSS
        payload_items = []
        if getattr(result, "extracted_content", None):
            try:
                payload_items = json.loads(result.extracted_content) or []
                print(f"Items extraídos por CSS: {len(payload_items)}")
                if payload_items:
                    print("Primer item CSS:")
                    print(f"  Title: {payload_items[0].get('title', 'NO TITLE')[:100]}...")
                    print(f"  Link: {payload_items[0].get('link', 'NO LINK')}")
            except json.JSONDecodeError as e:
                print(f"Error parsing CSS result: {e}")
        
        # 7. Agregar parámetros de fecha
        parsed = urlparse(url)
        q = parse_qs(parsed.query)
        f_inicio = (q.get("f_inicio") or q.get("from") or q.get("start"))
        f_fin = (q.get("f_fin") or q.get("to") or q.get("end"))
        start_str = f_inicio[0] if f_inicio else None
        end_str = f_fin[0] if f_fin else None
        
        print(f"\n=== 5. Parámetros de fecha ===")
        print(f"start_str: {start_str}")
        print(f"end_str: {end_str}")
        
        if (start_str or end_str) and isinstance(payload_items, list):
            for it in payload_items:
                if isinstance(it, dict):
                    if start_str and not it.get("date_start"):
                        it["date_start"] = start_str
                    if end_str and not it.get("date_end"):
                        it["date_end"] = end_str
        
        print(f"Items después de agregar fechas: {len(payload_items)}")
        if payload_items:
            print("Primer item después de fechas:")
            print(f"  Title: {payload_items[0].get('title', 'NO TITLE')[:100]}...")
            print(f"  Link: {payload_items[0].get('link', 'NO LINK')}")
            print(f"  Date start: {payload_items[0].get('date_start', 'NO DATE')}")
        
        # 8. Comparar HTML del navegador vs HTTP directo
        print(f"\n=== 6A. HTML del navegador ===")
        soup_browser = BeautifulSoup(result.html, "html.parser")
        browser_links = soup_browser.select('a[href]')
        print(f"Enlaces en HTML del navegador: {len(browser_links)}")
        
        print(f"\n=== 6B. HTTP directo ===")
        try:
            req = Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            })
            with urlopen(req, timeout=20) as resp:
                raw_html = resp.read().decode("utf-8", errors="ignore")
            
            soup_http = BeautifulSoup(raw_html, "html.parser")
            http_links = soup_http.select('a[href]')
            print(f"Enlaces en HTML directo: {len(http_links)}")
            
            # Usar el HTML directo para la extracción
            soup2 = soup_http
        except Exception as e:
            print(f"Error en HTTP directo: {e}")
            soup2 = soup_browser
        
        print(f"\n=== 6C. Extracción con HTML correcto ===")
        if True:  # Siempre ejecutar para elbalcon_mateo
            try:
                # Buscar en todo el documento primero
                all_headings_doc = soup2.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
                print(f"Total headings en documento: {len(all_headings_doc)}")
                
                # Buscar heading de eventos en todo el documento
                heading2 = None
                for h in all_headings_doc:
                    htxt = (h.get_text(" ", strip=True) or "").lower()
                    if "eventos para el" in htxt or "eventos para" in htxt:
                        heading2 = h
                        print(f"✓ Encontrado heading de eventos: {h.get_text(' ', strip=True)}")
                        break
                
                container2 = None
                if heading2 is not None:
                    print("Buscando container después del heading...")
                    for sib in heading2.next_siblings:
                        if getattr(sib, "name", None) in {"div", "section", "article"}:
                            container2 = sib
                            print(f"✓ Container encontrado: {sib.name} con clases {sib.get('class', [])}")
                            break
                
                if container2 is None:
                    print("No se encontró container específico, usando todo el documento")
                    container2 = soup2
                
                print(f"Container2 found: {container2.name if hasattr(container2, 'name') else 'document'}")
                
                # Debug: contar todos los enlaces en el container
                all_links_in_container = container2.select('a[href]')
                print(f"Total enlaces en container2: {len(all_links_in_container)}")
                
                # Ver algunos ejemplos de enlaces
                print("Primeros 5 enlaces en container2:")
                for i, link in enumerate(all_links_in_container[:5]):
                    text = link.get_text(" ", strip=True)
                    href = link.get("href")
                    print(f"  {i+1}. Text: {text[:50]}... | Href: {href}")
                
                # Buscar enlaces de eventos
                anchors2 = []
                markers = ("cuándo", "cuando", "dónde", "donde", "hora", "edad", "precio")
                
                print(f"\nBuscando enlaces con marcadores: {markers}")
                
                for a in container2.select('a[href]'):
                    href = a.get("href")
                    if not href:
                        continue
                    text = a.get_text(" ", strip=True)
                    if not text:
                        continue
                    low = text.lower()
                    
                    # Debug: mostrar si el enlace tiene marcadores
                    has_markers = [m for m in markers if m in low] 
                    if has_markers:
                        print(f"  ✓ Enlace con marcadores {has_markers}: {text[:50]}...")
                    
                    if not any(m in low for m in markers):
                        continue
                    
                    # Limpiar título
                    title_part = text
                    import re
                    m = re.search(r"(?i)\bcu[aá]ndo\b\s*:\s*", text)
                    if m:
                        title_part = text[:m.start()].strip()
                    
                    item2 = {
                        "title": title_part[:200],
                        "link": href,
                        "description": text,
                    }
                    if start_str and not item2.get("date_start"):
                        item2["date_start"] = start_str
                    if end_str and not item2.get("date_end"):
                        item2["date_end"] = end_str
                    anchors2.append(item2)
                
                print(f"HTTP anchors encontrados: {len(anchors2)}")
                if anchors2:
                    print("Primer item HTTP:")
                    print(f"  Title: {anchors2[0].get('title', 'NO TITLE')}")
                    print(f"  Link: {anchors2[0].get('link', 'NO LINK')}")
                    print(f"  Date start: {anchors2[0].get('date_start', 'NO DATE')}")
                
                # Combinar datos
                print(f"\n=== 7. Combinando datos ===")
                print(f"Items CSS antes: {len(payload_items)}")
                print(f"Items HTTP: {len(anchors2)}")
                
                # Reemplazar items CSS con items HTTP que tienen mejores datos
                if anchors2:
                    # Crear un mapa de enlaces de HTTP
                    http_links = {item.get('link'): item for item in anchors2 if item.get('link')}
                    
                    # Reemplazar o mejorar items existentes
                    for i, css_item in enumerate(payload_items):
                        if isinstance(css_item, dict):
                            css_link = css_item.get('link')
                            if css_link in http_links:
                                # Reemplazar con datos HTTP
                                payload_items[i] = http_links[css_link]
                                print(f"Reemplazado item {i} con datos HTTP")
                            elif not css_item.get('date_start') and start_str:
                                css_item['date_start'] = start_str
                                css_item['date_end'] = end_str
                    
                    # Agregar items HTTP que no están en CSS
                    existing_links = {item.get('link') for item in payload_items if isinstance(item, dict)}
                    for http_item in anchors2:
                        if http_item.get('link') not in existing_links:
                            payload_items.append(http_item)
                            print(f"Agregado nuevo item HTTP: {http_item.get('title', 'NO TITLE')[:50]}...")
                
                print(f"Items después de combinar: {len(payload_items)}")
                
            except Exception as e:
                print(f"Error en HTTP fallback: {e}")
        
        # 9. Resultado final
        print(f"\n=== 8. Resultado final ===")
        print(f"Total items: {len(payload_items)}")
        if payload_items:
            for i, item in enumerate(payload_items[:3]):
                print(f"{i+1}. Title: {item.get('title', 'NO TITLE')[:50]}...")
                print(f"   Link: {item.get('link', 'NO LINK')}")
                print(f"   Date: {item.get('date_start', 'NO DATE')}")
                print()

if __name__ == "__main__":
    asyncio.run(debug_crawler_step_by_step())