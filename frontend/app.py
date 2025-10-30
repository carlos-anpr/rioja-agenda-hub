from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import streamlit as st
from streamlit.components.v1 import html as st_html

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "eventos_por_dia.json"
TEMPLATE_PATH = PROJECT_ROOT / "frontend" / "templates" / "agenda.html"

SOURCE_META = {
    "agenda_larioja": {"label": "Agenda La Rioja", "color": "#667eea", "order": 0},
    "larioja_lalistilla": {"label": "La Listilla", "color": "#764ba2", "order": 1},
    "logrono_agenda": {"label": "Ayuntamiento", "color": "#fbbf24", "order": 2},
    "planeta_rioja_planes": {"label": "Planeta Rioja", "color": "#4ade80", "order": 3},
    "elbalcon_mateo": {"label": "El Balcón de Mateo", "color": "#ef4444", "order": 4},
}

CATEGORY_COLORS = {
    "música clásica": "#6E59A5",
    "conciertos": "#CE5A83",
    "exposiciones": "#D29B3D",
    "planes con niños": "#2FA37A",
    "visitas guiadas": "#4A86D4",
    "espectáculos": "#D46464",
    "cineclub": "#5F66D6",
    "teatro": "#6E59A5",
    "planes": "#2BA9A2",
    "literario": "#D27A42",
    "sin clasificar": "#6B7280",
}
DEFAULT_CATEGORY_COLOR = "#667eea"


def build_html_payload(
    eventos_por_dia: dict[str, list[dict]],
    default_date: str,
    today: str,
) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    data_json = json.dumps(eventos_por_dia, ensure_ascii=False)
    source_json = json.dumps(SOURCE_META, ensure_ascii=False)
    palette_json = json.dumps({key.lower(): value for key, value in CATEGORY_COLORS.items()}, ensure_ascii=False)

    safe_data_json = data_json.replace("</", "<\\/")
    safe_source_json = source_json.replace("</", "<\\/")
    safe_palette_json = palette_json.replace("</", "<\\/")

    replacements = {
        "__DATA__": safe_data_json,
        "__SOURCE_META__": safe_source_json,
        "__CATEGORY_PALETTE__": safe_palette_json,
        "__DEFAULT_DATE__": default_date,
        "__TODAY__": today,
        "__DEFAULT_COLOR__": DEFAULT_CATEGORY_COLOR,
    }

    for token, value in replacements.items():
        template = template.replace(token, value)

    return template


def main() -> None:
    st.set_page_config(
        page_title="🎭 Agenda Cultural La Rioja",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown(
        """
        <style>
            header, footer, [data-testid="stToolbar"] { display: none !important; }
                html, body, [data-testid="stAppViewContainer"] { padding: 0 !important; overflow: auto !important; height: auto !important; }
            .block-container { padding: 0 !important; }
            .stApp { background: transparent; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if not DATA_PATH.exists():
        st.error(
            "⚠️ No se encontró data procesada. Ejecuta `python -m process.clean_and_merge` y vuelve a intentarlo."
        )
        return

    with DATA_PATH.open("r", encoding="utf-8") as file:
        eventos_por_dia: dict[str, list[dict]] = json.load(file)

    if not eventos_por_dia:
        st.info("🎪 Aún no hay eventos cargados. Lanza el crawler para poblar la base de datos.")
        return

    today = dt.date.today().isoformat()
    fechas = sorted(eventos_por_dia.keys())
    default_date = today if today in eventos_por_dia else (fechas[0] if fechas else today)

    html_content = build_html_payload(
        eventos_por_dia=eventos_por_dia,
        default_date=default_date,
        today=today,
    )

    # Stable dual-scroll setup: iframe manages its own scroll while keeping the page chrome hidden
    st_html(html_content, height=800, scrolling=True)


if __name__ == "__main__":
    main()
