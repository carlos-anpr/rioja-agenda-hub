#!/usr/bin/env python3
"""Modificar temporalmente el YAML para probar solo el día 30"""

import yaml
from pathlib import Path

def modify_yaml_for_test():
    config_path = Path("crawl_configs/elbalcon_mateo.yaml")
    backup_path = Path("crawl_configs/elbalcon_mateo.yaml.backup")
    
    # Hacer backup
    with config_path.open("r", encoding="utf-8") as f:
        original_content = f.read()
    
    with backup_path.open("w", encoding="utf-8") as f:
        f.write(original_content)
    
    # Crear configuración solo para el día 30
    test_config = {
        'description': 'Test para día 30 únicamente',
        'urls': ['https://www.elbalcondemateo.es/category/agenda/?f_inicio=2025-10-30&f_fin=2025-10-30'],
        'schema': {
            'name': 'elbalcon_mateo',
            'baseSelector': '.cd_item, article',
            'fields': [
                {'name': 'title', 'selector': 'a[href], h2 a, h3 a, .entry-title a, .cd_item a', 'type': 'text'},
                {'name': 'link', 'selector': 'a[href], h2 a, h3 a, .entry-title a, .cd_item a', 'type': 'attribute', 'attribute': 'href'},
                {'name': 'description', 'selector': '.entry-summary p, .excerpt, .post-excerpt p, .resumen, p, .cd_item--inner, .cd_item', 'type': 'text'},
            ]
        },
        'run_config': {
            'delay_before_return_html': 0.4,
        }
    }
    
    with config_path.open("w", encoding="utf-8") as f:
        yaml.dump(test_config, f)
    
    print("YAML modificado para test del día 30")
    print("Para restaurar: cp crawl_configs/elbalcon_mateo.yaml.backup crawl_configs/elbalcon_mateo.yaml")

if __name__ == "__main__":
    modify_yaml_for_test()