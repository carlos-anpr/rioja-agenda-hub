"""Ejecutor simple de crawls definidos en YAML usando Crawl4AI."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen

import yaml
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    JsonCssExtractionStrategy,
)

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - dependency optional at runtime
    BeautifulSoup = None

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "crawl_configs"
RAW_DATA_DIR = PROJECT_ROOT / "data" / "eventos_raw"


def discover_configs() -> Dict[str, Path]:
    configs: Dict[str, Path] = {}
    for cfg_path in CONFIG_DIR.glob("*.yaml"):
        configs[cfg_path.stem] = cfg_path
    return configs


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def normalize_schema(raw_schema: Dict[str, Any]) -> Dict[str, Any]:
    schema = dict(raw_schema)
    base_selector = schema.pop("base_selector", schema.pop("base-selector", None))
    if base_selector and "baseSelector" not in schema:
        schema["baseSelector"] = base_selector

    for field in schema.get("fields", []):
        if "selector" not in field:
            raise ValueError("Cada campo del schema debe incluir 'selector'.")
        field["type"] = field.get("type", "text")
    return schema


def build_run_config(cfg: Dict[str, Any]) -> CrawlerRunConfig:
    schema = cfg.get("schema")
    extraction = None
    if schema:
        extraction = JsonCssExtractionStrategy(normalize_schema(schema), verbose=False)
    run_config = cfg.get("run_config") or {}
    allowed_run_keys = {
        "wait_for",
        "wait_for_timeout",
        "wait_until",
        "page_timeout",
        "delay_before_return_html",
        "scan_full_page",
        "process_iframes",
        "js_code",
        "mean_delay",
        "max_range",
        "semaphore_count",
    }
    run_kwargs = {key: run_config[key] for key in allowed_run_keys if key in run_config}
    return CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=extraction,
        **run_kwargs,
    )


def collect_target_urls(cfg: Dict[str, Any], cfg_path: Path) -> List[str]:
    urls: List[str] = []
    seen: set[str] = set()

    def push(candidate: Any) -> None:
        if isinstance(candidate, str):
            trimmed = candidate.strip()
            if trimmed and trimmed not in seen:
                urls.append(trimmed)
                seen.add(trimmed)

    base = cfg.get("url")
    # Determine whether to include base URL when date_range is present
    date_range = cfg.get("date_range")
    include_base = True
    if isinstance(date_range, dict):
        include_base = bool(date_range.get("include_base", False))

    if include_base:
        if isinstance(base, str):
            push(base)
        elif isinstance(base, list):
            for item in base:
                push(item)

    extra = cfg.get("urls")
    if isinstance(extra, list):
        for item in extra:
            push(item)

    # Dynamic date-range URL generation (optional)
    if isinstance(date_range, dict):
        pattern = (
            date_range.get("url_pattern")
            or date_range.get("pattern")
            or date_range.get("template")
        )
        if pattern:
            try:
                days_ahead = int(date_range.get("days_ahead", 90))
            except (TypeError, ValueError):
                days_ahead = 90
            try:
                chunk_days = int(date_range.get("chunk_days", 7))
            except (TypeError, ValueError):
                chunk_days = 7
            single_day = bool(date_range.get("single_day", False))
            inclusive = bool(date_range.get("inclusive", False))
            try:
                start_days_back = int(date_range.get("start_days_back", 0))
            except (TypeError, ValueError):
                start_days_back = 0
            date_format = date_range.get("date_format", "%Y-%m-%d")

            # Respect timezone if provided in postprocess metadata
            tz_name = None
            postprocess = cfg.get("postprocess")
            if isinstance(postprocess, dict):
                tz_name = postprocess.get("timezone")
            now = datetime.now(ZoneInfo(tz_name)) if tz_name else datetime.now()

            start_date = now.date() - timedelta(days=start_days_back)
            end_date = start_date + timedelta(days=days_ahead)

            current = start_date
            while current < end_date:
                chunk_end = min(current + timedelta(days=chunk_days), end_date)
                # Determine end date string according to settings
                effective_end = chunk_end
                if single_day:
                    effective_end = current
                elif inclusive:
                    # Use inclusive end (subtract one day) but never before current
                    effective_end = max(current, chunk_end - timedelta(days=1))

                start_str = current.strftime(date_format)
                end_str = effective_end.strftime(date_format)
                try:
                    candidate = pattern.format(
                        start=start_str,
                        end=end_str,
                        start_date=start_str,
                        end_date=end_str,
                    )
                except Exception:
                    candidate = None
                if candidate:
                    push(candidate)
                current = chunk_end

    pagination = cfg.get("pagination")
    if isinstance(pagination, dict):
        template = pagination.get("template") or pagination.get("pattern")
        start = pagination.get("start", 1)
        end = pagination.get("end")
        step = pagination.get("step", 1)
        if template and end is not None:
            try:
                step_value = int(step) if step else 1
            except (TypeError, ValueError):
                step_value = 1
            for page in range(int(start), int(end) + 1, max(step_value, 1)):
                try:
                    candidate = template.format(page=page)
                except Exception:
                    continue
                push(candidate)

    if not urls:
        raise ValueError(f"El archivo {cfg_path} debe definir 'url' o proporcionar 'urls'.")
    return urls


async def crawl_config(name: str, cfg_path: Path) -> Dict[str, Any]:
    cfg = load_yaml(cfg_path)
    urls = collect_target_urls(cfg, cfg_path)

    run_config = build_run_config(cfg)
    browser_config = BrowserConfig(headless=True, verbose=False)

    aggregated: List[Dict[str, Any]] = []
    visited: List[str] = []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for target in urls:
            try:
                result = await crawler.arun(target, config=run_config)
            except Exception:  # noqa: BLE001
                continue
            visited.append(target)
            if getattr(result, "extracted_content", None):
                try:
                    payload_items = json.loads(result.extracted_content) or []
                except json.JSONDecodeError:
                    payload_items = []
            else:
                payload_items = []

            # If target URL contains date query parameters, propagate them into items when missing
            try:
                parsed = urlparse(target)
                q = parse_qs(parsed.query)
                f_inicio = (q.get("f_inicio") or q.get("from") or q.get("start"))
                f_fin = (q.get("f_fin") or q.get("to") or q.get("end"))
                start_str = f_inicio[0] if f_inicio else None
                end_str = f_fin[0] if f_fin else None
                if (start_str or end_str) and isinstance(payload_items, list):
                    for it in payload_items:
                        if isinstance(it, dict):
                            if start_str and not it.get("date_start"):
                                it["date_start"] = start_str
                            if end_str and not it.get("date_end"):
                                it["date_end"] = end_str
                # Heurística específica: si es 'elbalcon_mateo' y la extracción por CSS falla o es escasa,
                # intentar una extracción usando petición HTTP directa ya que el contenido puede cargarse dinámicamente.
                if (
                    name.startswith("elbalcon_mateo")
                    and BeautifulSoup
                ):
                    few_items = not payload_items or (isinstance(payload_items, list) and len(payload_items) < 3)
                    # Detectar si es una URL de día concreto (f_inicio == f_fin)
                    is_daily = bool(start_str and end_str and start_str == end_str)
                    # Para elbalcon_mateo, siempre intentar extracción adicional ya que el contenido se carga dinámicamente
                    if True:
                        try:
                            import re as _re
                            soup = BeautifulSoup(result.html, "html.parser")
                            anchors: list[dict[str, Any]] = []
                            main = soup.select_one("main, .site-main, #content, .elementor-widget-container")
                            scope = main or soup
                            # Buscar el encabezado "Eventos para el" y recoger los enlaces posteriores hasta el siguiente encabezado relevante
                            heading = None
                            for h in scope.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
                                htxt = (h.get_text(" ", strip=True) or "").lower()
                                if "eventos para el" in htxt or "eventos para" in htxt:
                                    heading = h
                                    break
                            # Buscar bloque de contenido inmediatamente después del encabezado
                            content_block = None
                            if heading is not None:
                                for sib in heading.next_siblings:
                                    if getattr(sib, "name", None) in {"div", "section", "article"}:
                                        content_block = sib
                                        break
                            start_node = content_block or heading or scope
                            for el in start_node.select('a[href]'):
                                    href = el.get("href")
                                    if not href:
                                        continue
                                    text = el.get_text(" ", strip=True)
                                    if not text:
                                        continue
                                    # Saltar enlaces fuera del contenido principal (nav/footer/aside/header)
                                    if el.find_parent(["nav", "footer", "aside", "header"]):
                                        continue
                                    # Mantener solo anclas que parecen un bloque de evento (palabras clave típicas)
                                    tnorm = text.lower()
                                    event_markers = ("cuándo", "cuando", "dónde", "donde", "hora", "edad", "precio")
                                    if not any(marker in tnorm for marker in event_markers):
                                        continue
                                    # Evitar enlaces de navegación o publicidad comunes
                                    tlow = text.lower()
                                    if any(key in tlow for key in ("suscríbete", "newsletter", "soy publi", "+ planes", "lo más visto")):
                                        continue
                                    # Evitar duplicados
                                    if any(it.get("link") == href for it in payload_items if isinstance(it, dict)):
                                        continue
                                    # Construir título: si aparece 'Cuándo' recortar antes, si no usar texto
                                    title_part = text
                                    m = _re.search(r"(?i)\bcu[aá]ndo\b\s*:\s*", text)
                                    if m:
                                        title_part = text[: m.start()].strip()
                                    item = {
                                        "title": title_part[:200],
                                        "link": href,
                                        "description": text,
                                    }
                                    if start_str and not item.get("date_start"):
                                        item["date_start"] = start_str
                                    if end_str and not item.get("date_end"):
                                        item["date_end"] = end_str
                                    anchors.append(item)
                            # Además, buscar bloques de artículo/listado que contengan el evento
                            # (captura eventos que no tienen un ancla con la palabra 'Cuándo')
                            try:
                                article_selectors = [
                                    "article",
                                    ".post",
                                    ".elementor-post",
                                    ".listing-item",
                                    ".event-item",
                                    ".plan-item",
                                    ".cd_item",
                                    ".cd_item--inner",
                                    ".cd_item-border--yellow",
                                ]
                                for sel in article_selectors:
                                    for node in start_node.select(sel):
                                        # Tomar el primer enlace interno significativo
                                        a = node.select_one('a[href]')
                                        if not a:
                                            continue
                                        href = a.get('href')
                                        if not href:
                                            continue
                                        # Evitar duplicados
                                        if any(it.get('link') == href for it in payload_items if isinstance(it, dict)):
                                            continue
                                        # Extraer un título razonable
                                        text = a.get_text(' ', strip=True) or node.get_text(' ', strip=True)
                                        if not text:
                                            continue
                                        title_part = text
                                        # Construir item y añadir contexto de fecha
                                        item = {
                                            'title': title_part[:200],
                                            'link': href,
                                            'description': node.get_text(' ', strip=True)[:500],
                                        }
                                        if start_str and not item.get('date_start'):
                                            item['date_start'] = start_str
                                        if end_str and not item.get('date_end'):
                                            item['date_end'] = end_str
                                        # Evitar añadir si ya presente en anchors
                                        if not any(a.get('link') == href for a in anchors):
                                            anchors.append(item)
                            except Exception:
                                pass
                            if anchors:
                                if not isinstance(payload_items, list):
                                    payload_items = []
                                payload_items.extend(anchors)
                        except Exception:  # noqa: BLE001
                            pass
            except Exception:  # noqa: BLE001
                pass

            if BeautifulSoup and getattr(result, "html", None):
                try:
                    soup = BeautifulSoup(result.html, "html.parser")
                    cards = soup.select('div[data-elementor-type="loop-item"]')
                    for idx, item in enumerate(payload_items):
                        if idx >= len(cards):
                            break
                        classes = cards[idx].get("class") or []
                        categories = [cls for cls in classes if cls.startswith("category-")]
                        if categories and "category" not in item:
                            item["category"] = " ".join(categories)
                except Exception:  # noqa: BLE001
                    pass

            # Segunda pasada para 'elbalcon_mateo' usando petición HTTP directa para obtener contenido completo
            try:
                if name.startswith("elbalcon_mateo") and BeautifulSoup:
                    parsed = urlparse(target)
                    q = parse_qs(parsed.query)
                    f_inicio = (q.get("f_inicio") or q.get("from") or q.get("start"))
                    f_fin = (q.get("f_fin") or q.get("to") or q.get("end"))
                    start_str = f_inicio[0] if f_inicio else None
                    end_str = f_fin[0] if f_fin else None
                    is_daily = bool(start_str and end_str and start_str == end_str)
                    # Siempre intentar petición HTTP directa para elbalcon_mateo
                    # ya que el contenido puede estar en HTML estático que el navegador no procesa bien

                    if True:
                        try:
                            req = Request(target, headers={
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
                                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                            })
                            with urlopen(req, timeout=20) as resp:  # noqa: S310
                                raw_html = resp.read().decode("utf-8", errors="ignore")
                            soup2 = BeautifulSoup(raw_html, "html.parser")
                            anchors2: list[dict[str, Any]] = []
                            # Buscar sección por encabezado en todo el documento
                            heading2 = None
                            for h in soup2.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
                                htxt = (h.get_text(" ", strip=True) or "").lower()
                                if "eventos para el" in htxt or "eventos para" in htxt:
                                    heading2 = h
                                    break
                            container2 = None
                            if heading2 is not None:
                                sib = heading2.next_element
                                # Tomar el siguiente bloque contenedor cercano
                                for sib in heading2.next_siblings:
                                    if getattr(sib, "name", None) in {"div", "section", "article"}:
                                        container2 = sib
                                        break
                            if container2 is None:
                                container2 = soup2
                            markers = ("cuándo", "cuando", "dónde", "donde", "hora", "edad", "precio")
                            for a in container2.select('a[href]'):
                                href = a.get("href")
                                if not href:
                                    continue
                                text = a.get_text(" ", strip=True)
                                if not text:
                                    continue
                                low = text.lower()
                                if not any(m in low for m in markers):
                                    continue
                                # NO deduplicar aquí - queremos que los datos HTTP reemplacen a los CSS si son mejores
                                title_part = text
                                import re as _re
                                m = _re.search(r"(?i)\bcu[aá]ndo\b\s*:\s*", text)
                                if m:
                                    title_part = text[: m.start()].strip()
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
                            # También intentar capturar mediante bloques de artículo/listado
                            try:
                                article_selectors = [
                                    "article",
                                    ".post",
                                    ".elementor-post",
                                    ".listing-item",
                                    ".event-item",
                                    ".plan-item",
                                    ".cd_item",
                                    ".cd_item--inner",
                                    ".cd_item-border--yellow",
                                ]
                                for sel in article_selectors:
                                    for node in container2.select(sel):
                                        a = node.select_one('a[href]')
                                        if not a:
                                            continue
                                        href = a.get('href')
                                        if not href:
                                            continue
                                        if any(it.get('link') == href for it in payload_items if isinstance(it, dict)):
                                            continue
                                        text = a.get_text(' ', strip=True) or node.get_text(' ', strip=True)
                                        if not text:
                                            continue
                                        title_part = text
                                        item2 = {
                                            'title': title_part[:200],
                                            'link': href,
                                            'description': node.get_text(' ', strip=True)[:500],
                                        }
                                        if start_str and not item2.get('date_start'):
                                            item2['date_start'] = start_str
                                        if end_str and not item2.get('date_end'):
                                            item2['date_end'] = end_str
                                        if not any(a.get('link') == href for a in anchors2):
                                            anchors2.append(item2)
                            except Exception:
                                pass
                            if anchors2:
                                if not isinstance(payload_items, list):
                                    payload_items = []
                                payload_items.extend(anchors2)
                        except Exception:  # noqa: BLE001
                            pass
            except Exception:  # noqa: BLE001
                pass
            # Para elbalcon_mateo, filtrar y limpiar los datos antes de agregar
            if isinstance(payload_items, list):
                if name.startswith("elbalcon_mateo"):
                    # Obtener parámetros de fecha del URL
                    try:
                        parsed = urlparse(target)
                        q = parse_qs(parsed.query)
                        f_inicio = (q.get("f_inicio") or q.get("from") or q.get("start"))
                        f_fin = (q.get("f_fin") or q.get("to") or q.get("end"))
                        target_start_str = f_inicio[0] if f_inicio else None
                        target_end_str = f_fin[0] if f_fin else None
                    except Exception:
                        target_start_str = None
                        target_end_str = None
                    
                    # Dar prioridad a items con enlaces válidos y limpiar duplicados
                    good_items = []
                    seen_links = set()
                    
                    # Primero agregar items con enlaces válidos
                    for item in payload_items:
                        if isinstance(item, dict) and item.get('link'):
                            link = item['link']
                            if link not in seen_links and 'elbalcondemateo.es' in link:
                                seen_links.add(link)
                                # Limpiar el título si es necesario
                                title = item.get('title', '')
                                if title and 'Cuándo:' in title:
                                    import re
                                    m = re.search(r"(?i)\bcu[aá]ndo\b\s*:\s*", title)
                                    if m:
                                        title = title[:m.start()].strip()
                                
                                # Quitar el prefijo "Agenda" si está presente
                                if title.startswith('Agenda '):
                                    title = title[7:].strip()
                                
                                item['title'] = title
                                
                                # Limpiar y acortar la descripción
                                description = item.get('description', '')
                                if description:
                                    import re
                                    
                                    # Quitar prefijo "Agenda" al inicio
                                    if description.startswith('Agenda '):
                                        description = description[7:].strip()
                                    
                                    # Buscar la descripción real después de los metadatos
                                    # Patrón: buscar después de fechas, precios, etc.
                                    desc_patterns = [
                                        r'\d{1,2}\s+de\s+\w+\.\s+([A-Z].*)',  # "1 de noviembre. Descripción..."
                                        r'Precio:\s*[^.]+\.\s+([A-Z].*)',      # "Precio: X€. Descripción..."
                                        r'gratis\)\s+[^.]*\.\s+([A-Z].*)',     # "gratis) info. Descripción..."
                                        r'Requiere\s+[^.]+\.\s+([A-Z].*)',     # "Requiere reserva. Descripción..."
                                        r'\.\s+([A-Z][a-z]+(?:\s+[a-z]+)*\s+[A-Z].*)', # Patrón general con mayúscula
                                    ]
                                    
                                    clean_desc = None
                                    for pattern in desc_patterns:
                                        match = re.search(pattern, description)
                                        if match:
                                            clean_desc = match.group(1).strip()
                                            break
                                    
                                    # Si no encontramos un patrón claro, buscar la primera oración descriptiva
                                    if not clean_desc:
                                        # Buscar después de precio/fecha la primera oración que empiece con mayúscula
                                        sentences = re.split(r'\.\s+', description)
                                        for sentence in sentences:
                                            sentence = sentence.strip()
                                            # Descartar metadatos (hora, edad, precio, etc.)
                                            if (sentence and 
                                                len(sentence) > 20 and
                                                not re.match(r'^(Hora|Edad|Precio|Dónde|Cuándo|Del|Desde|Hasta)', sentence) and
                                                re.match(r'^[A-Z]', sentence)):
                                                clean_desc = sentence
                                                break
                                    
                                    if clean_desc:
                                        description = clean_desc
                                    
                                    # Limitar a 150 caracteres máximo para que sea más conciso
                                    if len(description) > 150:
                                        description = description[:150]
                                        # Cortar en la última palabra completa
                                        last_space = description.rfind(' ')
                                        if last_space > 80:  # Solo si no corta demasiado
                                            description = description[:last_space]
                                        description = description.rstrip('.,;:') + '...'
                                    
                                    item['description'] = description
                                # Asegurar que tiene fechas del URL
                                if target_start_str and not item.get("date_start"):
                                    item["date_start"] = target_start_str
                                if target_end_str and not item.get("date_end"):
                                    item["date_end"] = target_end_str
                                good_items.append(item)
                    
                    # Si no hay suficientes items con enlaces, agregar los que no tienen enlaces
                    if len(good_items) < 3:
                        for item in payload_items:
                            if isinstance(item, dict) and not item.get('link'):
                                # También asegurar fechas para estos items
                                if target_start_str and not item.get("date_start"):
                                    item["date_start"] = target_start_str
                                if target_end_str and not item.get("date_end"):
                                    item["date_end"] = target_end_str
                                good_items.append(item)
                    
                    aggregated.extend(good_items)
                else:
                    aggregated.extend(payload_items)

            # Fallback: rellenar títulos faltantes usando la descripción o la ruta del enlace
            try:
                import re
                from urllib.parse import urlparse
                for it in aggregated:
                    if not isinstance(it, dict):
                        continue
                    title = (it.get('title') or '').strip()
                    if title:
                        continue
                    desc = (it.get('description') or '').strip()
                    # Intentar tomar la parte antes de 'Cuándo' si existe
                    if desc:
                        parts = re.split(r"(?i)\bcu[aá]ndo\b[:\s]", desc, maxsplit=1)
                        candidate = parts[0].strip() if parts else ''
                        if candidate:
                            it['title'] = candidate[:200]
                            continue
                    # Si no hay descripción útil, derivar título de la URL
                    link = it.get('link') or ''
                    if link:
                        try:
                            path = urlparse(link).path.rstrip('/')
                            slug = path.split('/')[-1] if path else link
                            it['title'] = (slug.replace('-', ' ').replace('_', ' ') or link)[:200]
                        except Exception:
                            it['title'] = (link or '')[:200]
                    else:
                        it['title'] = None
            except Exception:  # noqa: BLE001
                pass

    data = {
        "name": name,
        "source_url": urls[0],
        "items": aggregated,
        "metadata": {
            "schema": cfg.get("schema"),
            "description": cfg.get("description"),
            "postprocess": cfg.get("postprocess"),
            "visited_urls": visited,
        },
    }
    return data


def persist_payload(name: str, payload: Dict[str, Any]) -> Path:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DATA_DIR / f"{name}.json"
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    return out_path


async def main(selected: Iterable[str] | None = None) -> None:
    configs = discover_configs()
    if not configs:
        raise SystemExit("No se encontraron YAML en crawl_configs/")

    if selected:
        missing = [name for name in selected if name not in configs]
        if missing:
            raise SystemExit(f"Config no encontrada: {', '.join(missing)}")
        targets = {name: configs[name] for name in selected}
    else:
        targets = configs

    for name, cfg_path in targets.items():
        print(f">>> {name}: iniciando crawl")
        try:
            payload = await crawl_config(name, cfg_path)
        except Exception as exc:  # noqa: BLE001
            print(f"xxx {name}: error -> {exc}")
            continue
        out_path = persist_payload(name, payload)
        print(f"✔✔ {name}: {len(payload['items'])} items guardados en {out_path.relative_to(PROJECT_ROOT)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ejecuta crawls definidos por YAML.")
    parser.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="Lista opcional de nombres (stem del YAML) a ejecutar",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args.only))
