#!/usr/bin/env python3
"""Script de debug para inspeccionar la extracción de elbalcon_mateo"""

import asyncio
import json
from pathlib import Path
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, JsonCssExtractionStrategy
from bs4 import BeautifulSoup

async def debug_elbalcon():
    url = "https://www.elbalcondemateo.es/category/agenda/?f_inicio=2025-10-30&f_fin=2025-10-30"
    
    # Test con JS del YAML
    browser_config = BrowserConfig(headless=True, verbose=True)
    
    js_code = """
    () => {
      const params = new URLSearchParams(window.location.search || "");
      const fi = params.get('f_inicio') || params.get('from') || params.get('start');
      const ff = params.get('f_fin') || params.get('to') || params.get('end');
      const scope = document.querySelector('main, .site-main, #content, .elementor-widget-container') || document;
      // Try to find a heading that contains the daily section title
      const headings = Array.from(scope.querySelectorAll('h1, h2, h3, h4, h5, h6'));
      let heading = headings.find(h => /eventos\\s+para/i.test(h.textContent || '')) || null;
      let container = null;
      if (heading) {
        // Prefer the next block-level element after the heading
        let sib = heading.nextElementSibling;
        while (sib && !['DIV','SECTION','ARTICLE','UL','OL'].includes(sib.tagName)) {
          sib = sib.nextElementSibling;
        }
        container = sib || heading.parentElement || scope;
      } else {
        container = scope;
      }
      const markers = ['cuándo', 'cuando', 'dónde', 'donde', 'hora', 'edad', 'precio'];
      const isEventLike = (txt) => {
        const low = (txt || '').toLowerCase();
        return markers.some(m => low.includes(m));
      };
      const anchors = Array.from(container.querySelectorAll('a[href]'))
        .filter(a => a.href && (a.href.includes('elbalcondemateo.es') || a.getAttribute('href').startsWith('/')))
        .filter(a => isEventLike(a.textContent || ''))
        .map(a => {
          const text = (a.textContent || '').replace(/\\s+/g,' ').trim();
          const idx = text.toLowerCase().indexOf('cuándo');
          const title = idx > 0 ? text.slice(0, idx).trim() : text.slice(0, 200).trim();
          return {
            title: title,
            link: a.href,
            description: text,
            date_start: fi || undefined,
            date_end: ff || undefined,
          };
        });
      return anchors;
    }
    """
    
    run_config = CrawlerRunConfig(
        delay_before_return_html=2.0,
        js_code=js_code
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        print("=== Obteniendo HTML con JS ===")
        result = await crawler.arun(url, config=run_config)
        
        print(f"HTML length: {len(result.html) if result.html else 0}")
        print(f"JS result: {result.js_result if hasattr(result, 'js_result') else 'No JS result'}")
        
        if hasattr(result, 'js_result') and result.js_result:
            try:
                js_data = json.loads(result.js_result)
                print(f"\n=== JS devolvió {len(js_data) if isinstance(js_data, list) else 1} items ===")
                if isinstance(js_data, list):
                    for i, item in enumerate(js_data[:5]):
                        print(f"{i+1}. Título: {item.get('title', 'Sin título')}")
                        print(f"   Link: {item.get('link', 'Sin link')}")
                        print(f"   Descripción: {item.get('description', 'Sin descripción')[:200]}...")
                        print()
            except Exception as e:
                print(f"Error parsing JS result: {e}")
                print(f"Raw JS result: {result.js_result}")
        
        if result.html:
            soup = BeautifulSoup(result.html, "html.parser")
            
            # Buscar el heading de eventos
            headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
            for h in headings:
                text = h.get_text(strip=True).lower()
                if "eventos para" in text:
                    print(f"Encontrado heading: {h.get_text(strip=True)}")
                    
            # Buscar enlaces con marcadores de evento como fallback
            main = soup.select_one("main, .site-main, #content, .elementor-widget-container") or soup
            print(f"Usando contenedor: {main.name if main and hasattr(main, 'name') else 'document'}")
            
            # Analizar todos los enlaces para debug
            all_links = main.select('a[href]')
            print(f"Total de enlaces encontrados: {len(all_links)}")
            
            # Ver algunos enlaces para debug
            print("\n=== Primeros 10 enlaces (para debug) ===")
            for i, link in enumerate(all_links[:10]):
                text = link.get_text(" ", strip=True)
                href = link.get('href')
                print(f"{i+1}. Texto: {text[:100]}...")
                print(f"   Href: {href}")
                print()
            
            links = main.select('a[href]')
            event_links = []
            
            markers = ["cuándo", "cuando", "dónde", "donde", "hora", "edad", "precio"]
            for link in links:
                text = link.get_text(" ", strip=True)
                if text and any(marker in text.lower() for marker in markers):
                    href = link.get('href')
                    if href and ('elbalcondemateo.es' in href or href.startswith('/')):
                        # Extraer título cortando antes de "Cuándo"
                        title = text
                        import re
                        m = re.search(r"(?i)\bcu[aá]ndo\b\s*:\s*", text)
                        if m:
                            title = text[:m.start()].strip()
                        
                        event_links.append({
                            'title': title[:100] + "..." if len(title) > 100 else title,
                            'link': href,
                            'full_text': text[:200] + "..." if len(text) > 200 else text
                        })
            
            print(f"\n=== HTML encontró {len(event_links)} enlaces de eventos ===")
            for i, event in enumerate(event_links[:5]):
                print(f"{i+1}. Título: {event['title']}")
                print(f"   Link: {event['link']}")
                print(f"   Texto completo: {event['full_text']}")
                print()

if __name__ == "__main__":
    asyncio.run(debug_elbalcon())