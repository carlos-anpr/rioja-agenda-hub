#!/usr/bin/env python3
"""Script para probar solo JavaScript sin CSS extraction"""

import asyncio
import json
from pathlib import Path
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def test_js_only():
    url = "https://www.elbalcondemateo.es/category/agenda/?f_inicio=2025-10-30&f_fin=2025-10-30"
    
    browser_config = BrowserConfig(headless=True, verbose=True)
    
    js_code = """
    () => {
      console.log('JS code starting...');
      const params = new URLSearchParams(window.location.search || "");
      const fi = params.get('f_inicio') || params.get('from') || params.get('start');
      const ff = params.get('f_fin') || params.get('to') || params.get('end');
      console.log('Parámetros URL:', fi, ff);
      
      const scope = document.querySelector('main, .site-main, #content, .elementor-widget-container') || document;
      console.log('Scope selected:', scope.tagName, scope.className);
      
      // Try to find a heading that contains the daily section title
      const headings = Array.from(scope.querySelectorAll('h1, h2, h3, h4, h5, h6'));
      console.log('Headings found:', headings.length);
      
      let heading = headings.find(h => /eventos\\s+para/i.test(h.textContent || '')) || null;
      console.log('Event heading found:', heading ? heading.textContent : 'none');
      
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
      
      console.log('Container selected:', container.tagName, container.className);
      
      const allLinks = Array.from(container.querySelectorAll('a[href]'));
      console.log('All links found:', allLinks.length);
      
      const markers = ['cuándo', 'cuando', 'dónde', 'donde', 'hora', 'edad', 'precio'];
      const isEventLike = (txt) => {
        const low = (txt || '').toLowerCase();
        return markers.some(m => low.includes(m));
      };
      
      const eventLinks = allLinks
        .filter(a => a.href && (a.href.includes('elbalcondemateo.es') || a.getAttribute('href').startsWith('/')))
        .filter(a => isEventLike(a.textContent || ''));
        
      console.log('Event-like links found:', eventLinks.length);
      
      const anchors = eventLinks.map(a => {
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
      
      console.log('Final anchors:', anchors.length);
      return anchors;
    }
    """
    
    # Sin CSS extraction, solo JavaScript
    run_config = CrawlerRunConfig(
        delay_before_return_html=5.0,
        page_timeout=20000,
        js_code=js_code
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        print("=== Probando solo JavaScript ===")
        result = await crawler.arun(url, config=run_config)
        
        print(f"JS result: {result.js_result if hasattr(result, 'js_result') else 'No JS result'}")
        
        if hasattr(result, 'js_result') and result.js_result:
            try:
                js_data = json.loads(result.js_result)
                print(f"\n=== JS devolvió {len(js_data) if isinstance(js_data, list) else 1} items ===")
                if isinstance(js_data, list):
                    for i, item in enumerate(js_data[:3]):
                        print(f"{i+1}. Título: {item.get('title', 'Sin título')}")
                        print(f"   Link: {item.get('link', 'Sin link')}")
                        print(f"   Descripción: {item.get('description', 'Sin descripción')[:100]}...")
                        print()
            except Exception as e:
                print(f"Error parsing JS result: {e}")
                print(f"Raw JS result: {result.js_result}")

if __name__ == "__main__":
    asyncio.run(test_js_only())