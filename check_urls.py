#!/usr/bin/env python3
"""Verificar qué URLs se están generando para elbalcon_mateo"""

import yaml
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def check_urls():
    config_path = Path("crawl_configs/elbalcon_mateo.yaml")
    with config_path.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    
    # Reproducir la lógica de collect_target_urls
    urls = []
    
    # URL base
    base = cfg.get("url")
    date_range = cfg.get("date_range")
    include_base = True
    if isinstance(date_range, dict):
        include_base = bool(date_range.get("include_base", False))
    
    if include_base and base:
        urls.append(base)
    
    # URLs de fecha
    if isinstance(date_range, dict):
        pattern = date_range.get("url_pattern")
        if pattern:
            days_ahead = int(date_range.get("days_ahead", 90))
            chunk_days = int(date_range.get("chunk_days", 7))
            single_day = bool(date_range.get("single_day", False))
            start_days_back = int(date_range.get("start_days_back", 0))
            date_format = date_range.get("date_format", "%Y-%m-%d")
            
            now = datetime.now()
            start_date = now.date() - timedelta(days=start_days_back)
            end_date = start_date + timedelta(days=days_ahead)
            
            current = start_date
            while current < end_date:
                chunk_end = min(current + timedelta(days=chunk_days), end_date)
                effective_end = current if single_day else chunk_end
                
                start_str = current.strftime(date_format)
                end_str = effective_end.strftime(date_format)
                try:
                    candidate = pattern.format(
                        start=start_str,
                        end=end_str,
                        start_date=start_str,
                        end_date=end_str,
                    )
                    urls.append(candidate)
                except Exception:
                    pass
                current = chunk_end
    
    print(f"Total URLs generadas: {len(urls)}")
    print("\nPrimeras 5 URLs:")
    for i, url in enumerate(urls[:5]):
        print(f"{i+1}. {url}")
    
    print("\nÚltimas 5 URLs:")
    for i, url in enumerate(urls[-5:]):
        print(f"{len(urls)-4+i}. {url}")

if __name__ == "__main__":
    check_urls()