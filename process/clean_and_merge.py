"""Normaliza los JSON crudos y genera archivos consolidados."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
import re
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Tuple
import unicodedata
import hashlib
import urllib.request

from dateutil import parser
from urllib.parse import parse_qs, urljoin, urlparse, unquote
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "eventos_raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
IMAGES_DIR = PROJECT_ROOT / "frontend" / "static" / "images"
OUT_ALL = PROCESSED_DIR / "eventos.json"
OUT_BY_DAY = PROCESSED_DIR / "eventos_por_dia.json"


def fetch_elbalcon_day_raw(date_iso: str) -> list[dict[str, Any]]:
    """Fallback de emergencia: extrae anclas con 'Cuándo/Dónde/Hora…' del día dado.

    Devuelve items crudos con title/link/description y date_start/date_end=fecha.
    """
    try:
        url = f"https://www.elbalcondemateo.es/category/agenda/?f_inicio={date_iso}&f_fin={date_iso}"
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        html = urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'ignore')
        soup = BeautifulSoup(html, 'html.parser')
        markers = ("cuándo", "cuando", "dónde", "donde", "hora", "edad", "precio")
        items: list[dict[str, Any]] = []
        def get_first_plausible_img(node) -> str | None:
            # Buscar imágenes en el nodo con varias estrategias comunes de lazy-load
            if not node:
                return None
            def extract_src(img_tag) -> str | None:
                if not img_tag:
                    return None
                for attr in ("src", "data-src", "data-lazy", "data-original", "data-srcset", "srcset"):
                    val = img_tag.get(attr)
                    if val:
                        val = val.strip()
                        # Si es srcset, usar el primer candidato
                        if attr.endswith("srcset") and "," in val:
                            val = val.split(",")[0].strip().split(" ")[0]
                        return val
                return None

            # Revisar imágenes en el propio nodo
            for img in node.select("img"):
                cand = extract_src(img)
                if cand and is_plausible_lalistilla_image(cand):  # reutilizamos heurística de extensión
                    return urljoin("https://www.elbalcondemateo.es/", cand)

            # Mirar imágenes cercanas en padres inmediatos
            parent = getattr(node, 'parent', None)
            hops = 0
            while parent is not None and hops < 3:
                for img in parent.select("img"):
                    cand = extract_src(img)
                    if cand and is_plausible_lalistilla_image(cand):
                        return urljoin("https://www.elbalcondemateo.es/", cand)
                parent = getattr(parent, 'parent', None)
                hops += 1
            return None

        # 1) Anclas con texto tipo evento
        for a in soup.select('a[href]'):
            href = a.get('href')
            if not href:
                continue
            text = a.get_text(' ', strip=True)
            if not text:
                continue
            low = text.lower()
            if not any(m in low for m in markers):
                continue
            # Título hasta 'Cuándo'
            import re as _re
            title = text
            m = _re.search(r"(?i)\bcu[aá]ndo\b\s*:\s*", text)
            if m:
                title = text[: m.start()].strip()
            item = {
                'title': title[:200],
                'link': href,
                'description': text,
                'date_start': date_iso,
                'date_end': date_iso,
            }
            # Intentar imagen desde el contexto del anchor
            img_url = get_first_plausible_img(a)
            if not img_url and href.startswith("http"):
                # Fallback og:image en la página del evento
                og = fetch_og_image(href)
                if og and is_plausible_lalistilla_image(og):
                    img_url = og
            if img_url:
                item['image'] = img_url
            items.append(item)
        # 2) Bloques de tarjetas/artículos
        selectors = [
            'article', '.post', '.elementor-post', '.listing-item', '.event-item',
            '.plan-item', '.cd_item', '.cd_item--inner', '.cd_item-border--yellow'
        ]
        for sel in selectors:
            for node in soup.select(sel):
                a = node.select_one('a[href]')
                if not a:
                    continue
                href = a.get('href')
                if not href:
                    continue
                text = a.get_text(' ', strip=True) or node.get_text(' ', strip=True)
                if not text:
                    continue
                title = text[:200]
                # Evitar duplicados por enlace
                if any(it.get('link') == href for it in items):
                    continue
                item = {
                    'title': title,
                    'link': href,
                    'description': node.get_text(' ', strip=True)[:500],
                    'date_start': date_iso,
                    'date_end': date_iso,
                }
                # Imagen preferentemente del propio nodo
                img_url = get_first_plausible_img(node)
                if not img_url and href.startswith("http"):
                    og = fetch_og_image(href)
                    if og and is_plausible_lalistilla_image(og):
                        img_url = og
                if img_url:
                    item['image'] = img_url
                items.append(item)
        return items
    except Exception:
        return []


@dataclass(frozen=True)
class SourceFilters:
    strip_prefix_hooks: Tuple[Callable[[str], str], ...] = ()
    normalize_display_hooks: Tuple[Callable[[str], str], ...] = ()
    date_text_hooks: Tuple[Callable[[str], str], ...] = ()


def _fix_colon_spacing(text: str) -> str:
    return re.sub(r":\s+(?=\d)", ":", text)


DEFAULT_FILTERS = SourceFilters()
SOURCE_FILTERS: Dict[str, SourceFilters] = {
    "agenda_larioja": SourceFilters(strip_prefix_hooks=(_fix_colon_spacing,)),
    "larioja_lalistilla": SourceFilters(),
    "planeta_rioja_planes": SourceFilters(),
    "logrono_agenda": SourceFilters(),
}


def download_lalistilla_image(image_url: str) -> str | None:
    """Descarga una imagen de La Listilla usando User-Agent y la guarda localmente."""
    try:
        # Crear el directorio si no existe
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        
        # Crear nombre único basado en la URL
        url_hash = hashlib.md5(image_url.encode()).hexdigest()
        image_extension = image_url.split('.')[-1].split('?')[0] if '.' in image_url else 'jpg'
        local_filename = f"lalistilla_{url_hash}.{image_extension}"
        local_path = IMAGES_DIR / local_filename
        
        # Si ya existe la imagen, devolver la URL local
        if local_path.exists():
            return f"./frontend/static/images/{local_filename}"
        
        # Crear request con User-Agent
        req = urllib.request.Request(
            image_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        # Descargar la imagen
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.read())
                return f"./frontend/static/images/{local_filename}"
        
        return None
        
    except Exception as e:
        print(f"⚠️  Error descargando imagen de La Listilla {image_url}: {e}")
        return None


def is_plausible_lalistilla_image(url: str) -> bool:
    """Heurística conservadora: aceptar solo imágenes que parezcan del evento.

    - Extensiones permitidas: .jpg/.jpeg/.png/.webp
    - Rechazar si contiene palabras comúnmente de iconos/logos/placeholders
    - Preferir dominios de La Listilla pero permitir absolutos válidos
    """
    if not isinstance(url, str) or not url:
        return False
    u = url.lower()
    # Extensiones válidas
    if not any(u.split('?')[0].endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp")):
        return False
    # Palabras a evitar (iconos, logos, favicons, sprites, placeholders, emojis)
    blacklist = (
        "logo", "favicon", "sprite", "icon", "placeholder", "default",
        "/twf-", "emoji", "/wp-includes/", "/themes/", "/assets/",
        "1x1", "pixel",
    )
    if any(b in u for b in blacklist):
        return False
    return True


def fetch_og_image(page_url: str, timeout: int = 10) -> str | None:
    """Obtiene og:image o twitter:image de una página con User-Agent.

    Devuelve URL absoluta si existe; si no, None.
    """
    try:
        req = urllib.request.Request(
            page_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            html = resp.read().decode(errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        for prop in ("og:image", "twitter:image", "og:image:url"):
            tag = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
            if tag and tag.get("content"):
                return urljoin(page_url, tag["content"].strip())
    except Exception:
        return None
    return None


def _coerce_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None
        try:
            parsed = datetime.fromisoformat(candidate)
            return parsed.date()
        except ValueError:
            try:
                parsed = parser.parse(candidate, fuzzy=True)
                if parsed.year < 1900 or parsed.year > 2100:
                    return None
                return parsed.date()
            except (ValueError, TypeError):
                return None
    return None


def expand_event_days(event: Dict[str, Any], today: date) -> List[str]:
    start_date = _coerce_date(event.get("date_start")) or _coerce_date(event.get("date"))
    end_date = _coerce_date(event.get("date_end")) or _coerce_date(event.get("date_start")) or start_date

    if not start_date:
        base = event.get("date")
        return [base] if isinstance(base, str) else []

    if not end_date or end_date < start_date:
        end_date = start_date

    start_range = max(start_date, today)
    if end_date < start_range:
        return []

    max_span_days = 366
    if (end_date - start_range).days > max_span_days:
        end_date = start_range + timedelta(days=max_span_days)

    current = start_range
    days: List[str] = []
    while current <= end_date:
        days.append(current.isoformat())
        current += timedelta(days=1)
    return days


def load_payloads() -> Iterable[Dict[str, Any]]:
    for path in RAW_DIR.glob("*.json"):
        with path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
            payload.setdefault("name", path.stem)
            yield payload


def clean_category(value: Any) -> str:
    if not value:
        return "Sin clasificar"
    text = str(value).replace("-", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return "Sin clasificar"
    return text.title()


def reference_today(meta: Dict[str, Any]) -> date:
    tz_name = meta.get("timezone") if isinstance(meta, dict) else None
    if tz_name:
        try:
            return datetime.now(ZoneInfo(tz_name)).date()
        except Exception:  # noqa: BLE001
            pass
    return datetime.now().date()


def extract_anchor(header_id: Any) -> str | None:
    if not header_id:
        return None
    match = re.search(r"(\d+)$", str(header_id))
    if match:
        return match.group(1)
    return None


def decode_lalistilla_link(raw_link: str) -> str | None:
    parsed = urlparse(raw_link)
    query = parse_qs(parsed.query)
    for key in ("text", "body"):
        for value in query.get(key, []):
            decoded = unquote(value)
            match = re.search(r"https://larioja\.lalistilla\.com/#(\d+)", decoded)
            if match:
                return f"https://larioja.lalistilla.com/#{match.group(1)}"
    return None


def _infer_category_elbalcon(title: str, summary: str | None, link: str | None) -> str | None:
    text = f"{title} {(summary or '')} {(link or '')}".lower()
    # Heuristic mapping for El Balcón de Mateo
    mapping = [
        (r"\bcuentacuent|cuento|narraci[óo]n|storytime", "Actividades Infantiles"),
        (r"\bniñ[oa]s?|familia|infantil|peques|ludoteca|ludotecas|payas|magia|titir|títer|clown", "Actividades Infantiles"),
        (r"\btaller|manualidad|workshop|aprende|formaci[óo]n", "Formación Y Talleres"),
        (r"\bconciert|m[uú]sic|jazz|rock|pop|band|orquesta|coro|canta", "Conciertos"),
        (r"\bteatro|escen[aá]|mon[óo]logo|drama|comed", "Teatro"),
        (r"\bexpo|muestra|galer[ií]a|museo|fotograf|pintur|arte", "Exposiciones"),
        (r"\bvisita|ruta|paseo|recorrido|gu[ií]a", "Visitas Guiadas"),
        (r"\bcharla|presentaci[óo]n de libro|libro|lectura|cuenta|poes[ií]a", "Charlas Y Libros"),
        (r"\bgastronom[ií]a|degustaci[óo]n|cata|p[ií]cnic|vino|tapa", "Gastronomia"),
        (r"\bpatrimonio|monasterio|castillo|iglesia|ermita|museo|historia", "Patrimonio"),
        (r"\bferia|festival|jornadas|ciclo|programaci[óo]n", "Evento Cultural"),
        (r"\bcine|pel[ií]cul|filmoteca|proyecci[óo]n", "Teatro"),
    ]
    import re

    for pattern, cat in mapping:
        if re.search(pattern, text):
            return cat
    return None


def derive_category_and_title(raw: Dict[str, Any], payload: Dict[str, Any]) -> tuple[str, str]:
    title_source = raw.get("title") or raw.get("heading_text") or raw.get("name") or "Sin título"
    title = str(title_source).strip()
    raw_category = raw.get("category")

    if isinstance(raw_category, list):
        raw_category = " ".join(str(part) for part in raw_category)

    extracted: str | None = None
    if isinstance(raw_category, str):
        category_matches = re.findall(r"category-([\w-]+)", raw_category, re.IGNORECASE)
        if category_matches:
            preferred = next(
                (token for token in category_matches if token.lower() not in {"agenda", "planes"}),
                None,
            )
            extracted = preferred or category_matches[0]
        if not extracted:
            for pattern in (
                r"body-plan-([\w-]+)",
                r"heading-([\w-]+)",
                r"module-acordeon-([\w-]+)",
            ):
                match = re.search(pattern, raw_category, re.IGNORECASE)
                if match:
                    extracted = match.group(1)
                    break
        if not extracted and raw_category.strip():
            extracted = raw_category

    clean_title = title
    # Avoid inferring category from title prefix for sources like elbalcon_mateo
    source_name = payload.get("name") if isinstance(payload, dict) else None
    if ":" in title:
        prefix, rest = title.split(":", 1)
        if rest.strip():
            if not extracted and source_name not in {"elbalcon_mateo"}:
                extracted = prefix.strip()
            clean_title = rest.strip()

    category = clean_category(extracted)
    # Heuristic fallback for specific sources when category is missing
    if category.lower() == "sin clasificar":
        if source_name == "elbalcon_mateo":
            guess = _infer_category_elbalcon(title, raw.get("description"), raw.get("link"))
            if guess:
                category = guess
    return category, clean_title


def build_link(raw: Dict[str, Any], payload: Dict[str, Any], anchor: str | None) -> str | None:
    source_url = payload.get("source_url", "")
    raw_link = raw.get("link") or raw.get("url")
    if isinstance(raw_link, str) and raw_link.strip():
        link = raw_link.strip()
        if "api.whatsapp.com" in link:
            decoded = decode_lalistilla_link(link)
            if decoded:
                return decoded
        if "@" in link and not urlparse(link).scheme:
            return f"mailto:{link}"
        if link.startswith("/"):
            return urljoin(source_url, link)
        return link
    if anchor:
        return urljoin(source_url, f"#{anchor}")
    return None


def prepare_date_text(raw: Any) -> str | None:
    if raw is None:
        return None
    import re
    # Preserve ISO date strings like YYYY-MM-DD intact
    if isinstance(raw, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw.strip()):
        return raw.strip()
    text = " ".join(str(raw).replace("\u2014", "–").replace("\u2013", "–").replace("\u2012", "–").split())
    if not text:
        return None
    text = re.sub(r"(?i)^(del|de|desde|hasta|al|a|el|la|los|las)\s+", "", text).strip()
    text = text.split("|", 1)[0].strip()
    # Only split on dashes when it's a human range '12 oct - 14 oct',
    # avoid breaking ISO dates already handled above
    text = re.split(r"\s*[–-]\s*", text, maxsplit=1)[0]
    text = re.sub(r"\.(?=\d)", " ", text)
    text = re.sub(r"([A-Za-z])\.", r"\1", text)
    text = re.sub(r"(\d{4})(\d{4})", r"\1 \2", text)
    text = re.sub(r"\s+", " ", text).strip()
    tokens = text.split()
    while len(tokens) >= 2 and tokens[-1] == tokens[-2]:
        tokens = tokens[:-1]
    text = " ".join(tokens)

    month_map = {
        "enero": "january",
        "febrero": "february",
        "marzo": "march",
        "abril": "april",
        "mayo": "may",
        "junio": "june",
        "julio": "july",
        "agosto": "august",
        "septiembre": "september",
        "setiembre": "september",
        "octubre": "october",
        "noviembre": "november",
        "diciembre": "december",
    }
    for es, en in month_map.items():
        text = re.sub(rf"(?i)\b{es}\b", en, text)

    weekday_map = {
        "lunes": "monday",
        "martes": "tuesday",
        "miércoles": "wednesday",
        "miercoles": "wednesday",
        "jueves": "thursday",
        "viernes": "friday",
        "sábado": "saturday",
        "sabado": "saturday",
        "domingo": "sunday",
    }
    for es, en in weekday_map.items():
        text = re.sub(rf"(?i)\b{es}\b", en, text)

    return text


def parse_date(text: Any, meta: Dict[str, Any]) -> datetime | None:
    cleaned = prepare_date_text(text)
    if not cleaned:
        return None
    hint = meta.get("date_format_hint") if isinstance(meta, dict) else None
    tz_name = meta.get("timezone") if isinstance(meta, dict) else None
    default_dt = datetime.now(ZoneInfo(tz_name)) if tz_name else datetime.now()
    try:
        if hint:
            dt = datetime.strptime(cleaned, hint)
        else:
            dt = parser.parse(cleaned, default=default_dt)
    except (ValueError, TypeError):
        try:
            dt = parser.parse(cleaned, dayfirst=False, fuzzy=True, default=default_dt)
        except (ValueError, TypeError):
            return None
    if tz_name:
        try:
            dt = dt.replace(tzinfo=ZoneInfo(tz_name))
        except Exception:  # noqa: BLE001
            pass
    return dt


def normalize_event(raw: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any] | None:
    metadata = payload.get("metadata") or {}
    postprocess = metadata.get("postprocess") or {}
    source_name = payload.get("name")
    filters = SOURCE_FILTERS.get(source_name or "", DEFAULT_FILTERS)

    date_text_raw = raw.get("date")
    date_start_raw = raw.get("date_start")
    date_end_raw = raw.get("date_end")
    date_text = date_text_raw
    time_text = raw.get("time")
    if isinstance(time_text, str) and time_text.strip():
        if date_text:
            date_text = f"{date_text} {time_text}"
        else:
            date_text = time_text

    today = reference_today(postprocess)

    start_dt: datetime | None = None
    end_dt: datetime | None = None
    start_text: str | None = None
    end_text: str | None = None

    def strip_prefix(value: str) -> str:
        cleaned = unicodedata.normalize("NFKC", str(value))
        cleaned = cleaned.replace("\xa0", " ")
        cleaned = re.sub(r"(?i)(desde|hasta)(el)", r"\1 el", cleaned)
        cleaned = re.sub(r"(?i)(dia)(\d)", r"\1 \2", cleaned)
        cleaned = re.sub(r"(?i)(día)(\d)", r"\1 \2", cleaned)
        cleaned = re.sub(r"(?<=[A-Za-zÁÉÍÓÚÜáéíóúü])(?=\d)", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        for hook in filters.strip_prefix_hooks:
            cleaned = hook(cleaned)
        prefix_pattern = re.compile(r"(?i)^(del|de|desde|hasta|al|a|el|la|los|las)\b\s*")
        while True:
            match = prefix_pattern.match(cleaned)
            if not match:
                break
            cleaned = cleaned[match.end():].lstrip()
        return cleaned.strip()

    if isinstance(date_text, str):
        normalized = date_text.replace("\u2014", "–").replace("\u2013", "–")
        normalized = normalized.replace("-", " – ")
        normalized = re.sub(r"\s+", " ", normalized).strip()
        lower = normalized.lower()
        for hook in filters.date_text_hooks:
            normalized = hook(normalized)

        start_text = strip_prefix(normalized) if normalized else None
        end_text = None

        if "hasta" in lower:
            parts = re.split(r"(?i)\bhasta\b", normalized, maxsplit=1)
            if len(parts) == 2:
                start_text = strip_prefix(parts[0]) or None
                end_text = strip_prefix(parts[1]) or None
        elif re.match(r"(?i)^del\s+.+\s+al\s+.+", normalized):
            parts = re.split(r"(?i)\s+al\s+", normalized, maxsplit=1)
            if len(parts) == 2:
                start_text = strip_prefix(parts[0]) or None
                end_text = strip_prefix(parts[1]) or None
        elif re.match(r"(?i)^de\s+.+\s+a\s+.+", normalized):
            parts = re.split(r"(?i)\s+a\s+", normalized, maxsplit=1)
            if len(parts) == 2:
                start_text = strip_prefix(parts[0]) or None
                end_text = strip_prefix(parts[1]) or None
        elif "–" in normalized:
            parts = normalized.split("–", 1)
            if len(parts) == 2:
                start_text = strip_prefix(parts[0]) or None
                end_text = strip_prefix(parts[1]) or None

        start_dt = parse_date(start_text, postprocess) if start_text else None
        end_dt = parse_date(end_text, postprocess) if end_text else None
    else:
        start_dt = parse_date(date_text, postprocess)

    if isinstance(date_start_raw, str) and date_start_raw.strip():
        start_text = strip_prefix(date_start_raw)
        start_dt = parse_date(start_text, postprocess) if start_text else start_dt

    if isinstance(date_end_raw, str) and date_end_raw.strip():
        end_text = strip_prefix(date_end_raw)
        end_dt = parse_date(end_text, postprocess) if end_text else end_dt

    if start_dt and start_dt.year < 1900:
        start_dt = None
    if end_dt and end_dt.year < 1900:
        end_dt = None
    if start_dt and end_dt and end_dt < start_dt:
        end_dt = start_dt

    def combine_with_today(source: datetime | None) -> datetime:
        if source is None:
            return datetime.combine(today, time())
        base_time = source.timetz() if source.tzinfo else source.time()
        return datetime.combine(today, base_time)

    event_dt: datetime | None = None
    if start_dt and start_dt.date() >= today:
        event_dt = start_dt
    elif end_dt and end_dt.date() >= today:
        tz_source = start_dt or end_dt
        event_dt = combine_with_today(tz_source)
        if tz_source and tz_source.tzinfo:
            event_dt = event_dt.replace(tzinfo=tz_source.tzinfo)
    else:
        event_dt = start_dt or end_dt

    if not event_dt:
        return None

    if event_dt.date() < today and (not end_dt or end_dt.date() < today):
        return None

    anchor = extract_anchor(raw.get("anchor_id"))
    category, title = derive_category_and_title(raw, payload)
    if category.lower() == "sin clasificar" and payload.get("name") == "planeta_rioja_planes":
        category = "Planes"
    link = build_link(raw, payload, anchor)

    normalized_link: str | None = None
    if link:
        parsed = urlparse(link)
        if parsed.scheme or link.startswith("#"):
            normalized_link = link
        else:
            normalized_link = urljoin(payload.get("source_url", ""), link)

    def normalize_display(value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        text = unicodedata.normalize("NFKC", value)
        text = text.replace("\xa0", " ")
        text = re.sub(r"\s+", " ", text).strip()
        text = text.replace("Desdeel", "Desde el").replace("Hastael", "Hasta el")
        text = text.replace("Desdela", "Desde la").replace("Hastala", "Hasta la")
        text = text.replace("Desdelos", "Desde los").replace("Hastalos", "Hasta los")
        text = text.replace("Desdeles", "Desde les").replace("Hastales", "Hasta les")
        text = text.replace("D?a", "Día").replace("Dia", "Día")
        text = re.sub(r"(?<=\D)(?=\d)", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        for hook in filters.normalize_display_hooks:
            text = hook(text)
        return text or None

    date_display: str | None = normalize_display(date_text_raw)
    if not date_display and any(isinstance(value, str) and value.strip() for value in (date_start_raw, date_end_raw)):
        parts = []
        start_display = normalize_display(date_start_raw)
        end_display = normalize_display(date_end_raw)
        if start_display:
            parts.append(start_display)
        if end_display:
            parts.append(end_display)
        if parts:
            date_display = " | ".join(parts)

    # Procesar imagen
    raw_image = raw.get("image")
    normalized_image = None
    try:
        # Si es una URL relativa, convertirla a absoluta basada en la fuente
        source_url = payload.get("source_url", "")
        if isinstance(raw_image, str) and raw_image:
            if raw_image.startswith("/"):
                # URL relativa, necesita el dominio
                if "logrono.es" in source_url:
                    normalized_image = f"https://logrono.es{raw_image}"
                elif "elbalcondemateo.es" in source_url:
                    normalized_image = f"https://www.elbalcondemateo.es{raw_image}"
                elif "agenda.larioja.com" in source_url:
                    normalized_image = f"https://agenda.larioja.com{raw_image}"
                else:
                    # Extraer dominio genéricamente
                    parsed = urlparse(source_url)
                    if parsed.netloc:
                        normalized_image = f"{parsed.scheme}://{parsed.netloc}{raw_image}"
            elif raw_image.startswith("//"):
                # URL protocolo-relativa
                normalized_image = f"https:{raw_image}"
            elif raw_image.startswith("http"):
                # URL ya absoluta
                normalized_image = raw_image

        # Reglas específicas para La Listilla: solo usar imagen si es segura
        if payload.get("name") == "larioja_lalistilla":
            candidate_url: str | None = None
            # 1) Probar a obtener og:image de la página del evento si hay link
            if normalized_link and isinstance(normalized_link, str) and normalized_link.startswith("http"):
                og = fetch_og_image(normalized_link)
                if og and is_plausible_lalistilla_image(og):
                    candidate_url = og

            # 2) Si no hay og:image válida, usar la extraída solo si es plausible
            if not candidate_url and normalized_image and is_plausible_lalistilla_image(normalized_image):
                candidate_url = normalized_image

            # 3) Si no hay ninguna candidata clara, no usar imagen
            if candidate_url:
                local_image = download_lalistilla_image(candidate_url)
                normalized_image = local_image if local_image else None
            else:
                normalized_image = None

    except Exception:
        # En caso de error, no incluir imagen
        normalized_image = None

    normalized: Dict[str, Any] = {
        "title": str(title).strip(),
        "date": event_dt.date().isoformat(),
        "date_display": date_display or event_dt.strftime("%Y-%m-%d"),
        "location": raw.get("location") or raw.get("place"),
        "category": category,
        "source": payload.get("name"),
        "source_url": payload.get("source_url"),
        "link": normalized_link,
        "summary": raw.get("description") or raw.get("summary"),
        "image": normalized_image,
        "raw": raw,
    }

    if start_dt:
        normalized["date_start"] = start_dt.date().isoformat()
    if end_dt:
        normalized["date_end"] = end_dt.date().isoformat()

    return normalized


def group_by_day(events: Iterable[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    today = datetime.now().date()
    for event in events:
        day_keys = expand_event_days(event, today)
        if not day_keys:
            day_keys = [event["date"]]
        for day_key in day_keys:
            event_copy = dict(event)
            event_copy["date"] = day_key
            grouped[day_key].append(event_copy)
    for date_key, items in grouped.items():
        grouped[date_key] = sorted(items, key=lambda ev: ev["title"].lower())
    return dict(sorted(grouped.items()))


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    normalized: List[Dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()

    raw_payloads = list(load_payloads())
    for payload in raw_payloads:
        for raw_event in payload.get("items", []):
            event = normalize_event(raw_event, payload)
            if event:
                key = (
                    event["title"].strip().lower(),
                    event["date"],
                    (event.get("location") or "").strip().lower(),
                    (event.get("link") or "").strip().lower(),
                )
                if key in seen:
                    continue
                seen.add(key)
                normalized.append(event)

    # Backfill: si hoy no hay eventos de El Balcón de Mateo, intentar extraerlos directamente
    # para un mejor UX. Se aplica sólo al día actual.
    today = datetime.now().date().isoformat()
    has_elbalcon_today = any(ev.get("source") == "elbalcon_mateo" and ev.get("date") == today for ev in normalized)
    if not has_elbalcon_today:
        fallback_items = fetch_elbalcon_day_raw(today)
        if fallback_items:
            synthetic_payload = {
                "name": "elbalcon_mateo",
                "source_url": f"https://www.elbalcondemateo.es/category/agenda/?f_inicio={today}&f_fin={today}",
                "metadata": {"postprocess": {"timezone": "Europe/Madrid"}},
            }
            for raw_event in fallback_items:
                event = normalize_event(raw_event, synthetic_payload)
                if not event:
                    continue
                key = (
                    event["title"].strip().lower(),
                    event["date"],
                    (event.get("location") or "").strip().lower(),
                    (event.get("link") or "").strip().lower(),
                )
                if key in seen:
                    continue
                seen.add(key)
                normalized.append(event)

    normalized.sort(key=lambda ev: (ev["date"], ev["title"].lower()))
    with OUT_ALL.open("w", encoding="utf-8") as fh:
        json.dump(normalized, fh, ensure_ascii=False, indent=2)

    grouped = group_by_day(normalized)
    with OUT_BY_DAY.open("w", encoding="utf-8") as fh:
        json.dump(grouped, fh, ensure_ascii=False, indent=2)

    print(f"Eventos normalizados: {len(normalized)}")
    print(f"Agrupados por día: {len(grouped)}")


if __name__ == "__main__":
    main()
