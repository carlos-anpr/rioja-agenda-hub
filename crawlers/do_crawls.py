"""Ejecutor simple de crawls definidos en YAML usando Crawl4AI."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

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
    if isinstance(base, str):
        push(base)
    elif isinstance(base, list):
        for item in base:
            push(item)

    extra = cfg.get("urls")
    if isinstance(extra, list):
        for item in extra:
            push(item)

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
            if isinstance(payload_items, list):
                aggregated.extend(payload_items)

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
