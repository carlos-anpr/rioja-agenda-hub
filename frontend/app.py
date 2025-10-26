from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "eventos_por_dia.json"
CONFIG_DIR = PROJECT_ROOT / "crawl_configs"

st.set_page_config(page_title="Eventos", layout="wide")

if not DATA_PATH.exists():
    st.warning(
        "No se encontró data procesada. Ejecuta `python -m process.clean_and_merge` y vuelve a intentarlo.",
        icon="⚠️",
    )
    st.stop()

with DATA_PATH.open("r", encoding="utf-8") as fh:
    eventos_por_dia = json.load(fh)

if not eventos_por_dia:
    st.info("Aún no hay eventos cargados. Lanza el crawler para poblar la base de datos.")
    st.stop()

fechas = sorted(eventos_por_dia.keys())

hoy = dt.date.today().isoformat()
initial_index = fechas.index(hoy) if hoy in fechas else 0

col_filtro, col_stats = st.columns([2, 1])
with col_filtro:
    fecha_sel = st.selectbox("Fecha", fechas, index=initial_index)
    eventos_dia = eventos_por_dia.get(fecha_sel, [])
    if not eventos_dia:
        st.info("No hay eventos registrados para esta fecha.")
        st.stop()

    conteos_fuente: dict[str, int] = {}
    for evento in eventos_dia:
        fuente = evento.get("source", "desconocido")
        conteos_fuente[fuente] = conteos_fuente.get(fuente, 0) + 1

    opciones_fuente = sorted(conteos_fuente.items(), key=lambda item: item[0].lower())
    etiquetas_fuente = {fuente: f"{fuente} ({conteo})" for fuente, conteo in opciones_fuente}
    valores_multiselect = [etiquetas_fuente[fuente] for fuente, _ in opciones_fuente]

    seleccion_fuentes = st.multiselect(
        "Fuente",
        options=valores_multiselect,
        default=valores_multiselect,
        help="Selecciona qué fuentes mostrar",
    )

    fuentes_filtradas = {
        fuente
        for fuente, etiqueta in etiquetas_fuente.items()
        if not seleccion_fuentes or etiqueta in seleccion_fuentes
    }
    if not fuentes_filtradas:
        fuentes_filtradas = set(conteos_fuente.keys())

    eventos_filtrados_fuente = [
        evento for evento in eventos_dia if evento.get("source", "desconocido") in fuentes_filtradas
    ]

    conteos_categoria: dict[str, int] = {}
    for evento in eventos_filtrados_fuente:
        categoria = evento.get("category") or "Sin clasificar"
        conteos_categoria[categoria] = conteos_categoria.get(categoria, 0) + 1

    opciones_categoria = sorted(conteos_categoria.items(), key=lambda item: item[0].lower())
    etiquetas_categoria = {cat: f"{cat} ({conteo})" for cat, conteo in opciones_categoria}
    lista_categorias = ["Todas"] + [etiquetas_categoria[cat] for cat, _ in opciones_categoria]
    categoria_elegida = st.selectbox("Categoría", lista_categorias)

    if categoria_elegida == "Todas":
        categoria_filtrada = None
    else:
        inverso_categoria = {etiqueta: cat for cat, etiqueta in etiquetas_categoria.items()}
        categoria_filtrada = inverso_categoria.get(categoria_elegida)

with col_stats:
    eventos_visibles = [
        evt
        for evt in eventos_filtrados_fuente
        if categoria_filtrada is None
        or (evt.get("category") or "Sin clasificar") == categoria_filtrada
    ]
    st.metric("Eventos visibles", len(eventos_visibles))

if not eventos_visibles:
    st.info("No se encontraron eventos con los filtros seleccionados.")
    st.stop()

for evento in eventos_visibles:
    categoria = evento.get("category") or "Sin clasificar"
    st.markdown(f"### {evento.get('title', 'Sin título')}")
    st.write(
        f"**Fecha:** {evento.get('date_display')}  \
**Lugar:** {evento.get('location') or 'Sin especificar'}  \
**Categoría:** {categoria}"
    )

    if evento.get("summary"):
        st.write(evento["summary"])

    link = evento.get("link")
    if link:
        st.markdown(f"[Link al evento]({link})")

    st.caption(f"Fuente: {evento.get('source')} | {evento.get('source_url')}")
    st.divider()
