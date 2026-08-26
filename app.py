# -*- coding: utf-8 -*-
"""Portafolio Óptimo · Asistente Cuantitativo (Grupo 3 / UTEC)."""

from __future__ import annotations

import base64
import importlib
import re
from pathlib import Path

import agente_chat
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

importlib.reload(agente_chat)
from agente_chat import PREGUNTAS_SUGERIDAS, ROLES_ACTIVO, responder
from datos_grupo3 import PARAMETROS_GRUPO3, cargar_resultados
from presentacion import GLOSARIO, PASOS_RECORRIDO, frase_ejecutiva, formatear_paso
from simulador import simular

APP_DIR = Path(__file__).parent
LOGO_UTEC = APP_DIR / "assets" / "logo_utec.png"
LOGO_FALLBACK = APP_DIR / "assets" / "logo_utec.svg"
HERO_CHARTS = APP_DIR / "assets" / "hero_charts.svg"

NAV_PAGES = ["Resumen", "Simulador", "Cartera", "Riesgo", "Desempeño", "El asistente"]
NAV_LABELS = {
    "Resumen": "📊  Resumen",
    "Simulador": "🧪  Simulador",
    "Cartera": "💼  Cartera",
    "Riesgo": "⚠️  Riesgo",
    "Desempeño": "📈  Desempeño",
    "El asistente": "🤖  El asistente",
}

st.set_page_config(
    page_title="Portafolio Óptimo · Grupo 3",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="expanded",
)

_TEMA_CLARO = "☀  Claro"
_TEMA_OSCURO = "🌙  Oscuro"

_tema_inicial = st.session_state.get("tema")
if _tema_inicial is None or _tema_inicial not in (_TEMA_CLARO, _TEMA_OSCURO, "Claro", "Oscuro"):
    st.session_state.tema = _TEMA_CLARO
elif _tema_inicial == "Claro":
    st.session_state.tema = _TEMA_CLARO
elif _tema_inicial == "Oscuro":
    st.session_state.tema = _TEMA_OSCURO
if "pagina" not in st.session_state:
    st.session_state.pagina = "Resumen"
if "demo_paso" not in st.session_state:
    st.session_state.demo_paso = -1

# -- Sidebar --
with st.sidebar:
    st.markdown(
        '<div class="sb-brand">'
        '<div class="sb-mark"><i></i><i></i><i></i><i></i></div>'
        '<div><div class="sb-title">PORTAFOLIO<br>ÓPTIMO</div>'
        '<div class="sb-sub">Asistente Cuantitativo<br>· Grupo 3</div></div></div>',
        unsafe_allow_html=True,
    )
    if "sidebar_nav" not in st.session_state:
        st.session_state.sidebar_nav = st.session_state.pagina
    _selected_page = st.radio(
        "Navegación",
        NAV_PAGES,
        format_func=lambda page: NAV_LABELS[page],
        key="sidebar_nav",
        label_visibility="collapsed",
    )
    if _selected_page != st.session_state.pagina:
        st.session_state.pagina = _selected_page
    pagina = st.session_state.pagina
    st.markdown(
        '<div class="sb-mode-box"><div class="sb-mode-label">MODO ACTUAL</div></div>',
        unsafe_allow_html=True,
    )
    st.segmented_control(
        "Tema",
        options=[_TEMA_CLARO, _TEMA_OSCURO],
        key="tema",
        label_visibility="collapsed",
    )
    st.markdown(
        '<div class="sb-footer"><strong>UTEC</strong><br>'
        '<span>Management Analytics S.A.</span></div>',
        unsafe_allow_html=True,
    )

if st.session_state.get("tema") not in (_TEMA_CLARO, _TEMA_OSCURO):
    st.session_state.tema = _TEMA_OSCURO if st.session_state.get("tema") == "Oscuro" else _TEMA_CLARO

ES_OSCURO = st.session_state.tema == _TEMA_OSCURO

# Paleta mockup: forest dark + coral + sage
_COLOR_TEXT = "#E8E4DC" if ES_OSCURO else "#1A231F"
_COLOR_SAGE = "#94B8A3"
_COLOR_CORAL = "#E69984"
_COLOR_TEAL = "#7A9EAE"
_COLOR_ROSE = "#D3B1AF"

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(
        color=_COLOR_TEXT,
        family="Inter, DM Sans, sans-serif",
        size=12,
    ),
    margin=dict(l=8, r=8, t=20, b=8),
)
PLOTLY_COLORS = [_COLOR_SAGE, _COLOR_CORAL, _COLOR_TEAL, _COLOR_ROSE, "#A8C69F"]

# -- Estilos --
_COMMON_CSS = """
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@500;600;700&display=swap');
  html, body { font-size: 15px !important; }
  html, body, [class*="css"] { font-family: Inter, sans-serif !important; }
  .page-title, .hero h1, .card h4, .semaforo .estado {
    font-family: 'Playfair Display', Georgia, serif !important;
  }

  /* -- Hide Streamlit UI chrome -- */
  [data-testid="stDecoration"]   { display: none !important; }
  [data-testid="collapsedControl"] { display: none !important; }
  #MainMenu { visibility: hidden; }
  header[data-testid="stHeader"] { background: transparent !important; }

  /* -- SIDEBAR -- */
  [data-testid="stSidebar"] { width: 260px !important; }
  [data-testid="stSidebar"] > div:first-child {
    padding: 1.6rem 1rem 1rem !important;
  }
  [data-testid="stSidebar"] hr { display: none !important; }

  .sb-brand {
    display: flex; align-items: center; gap: 12px;
    margin-bottom: 28px; padding: 0 4px;
  }
  .sb-mark {
    position: relative; flex: 0 0 34px; width: 34px; height: 34px;
  }
  .sb-mark i {
    position: absolute; width: 17px; height: 17px; border-radius: 5px;
    background: linear-gradient(135deg,#E69984,#94B8A3);
    box-shadow: 0 3px 10px rgba(230,153,132,.25);
  }
  .sb-mark i:nth-child(1) { left:0; top:0; }
  .sb-mark i:nth-child(2) { left:14px; top:0; opacity:.85; }
  .sb-mark i:nth-child(3) { left:0; top:14px; opacity:.75; }
  .sb-mark i:nth-child(4) { left:14px; top:14px; }
  .sb-title {
    font-size: 1rem !important; font-weight: 800 !important;
    color: #fff !important; letter-spacing: .02em; line-height: 1.15;
  }
  .sb-sub {
    font-size: .72rem !important; color: rgba(255,255,255,.55) !important;
    margin-top: 6px; line-height: 1.35;
  }

  [data-testid="stSidebar"] [role="radiogroup"] {
    display: flex; flex-direction: column; gap: 5px;
  }
  [data-testid="stSidebar"] [role="radiogroup"] label {
    min-height: 42px; padding: 0 14px !important; border-radius: 10px;
    background: transparent; transition: background .15s ease;
    cursor: pointer;
  }
  [data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(255,255,255,.08);
  }
  [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(90deg,rgba(230,153,132,.22),rgba(148,184,163,.35));
    box-shadow: inset 0 0 0 1px rgba(230,153,132,.28);
  }
  [data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {
    display: none !important;
  }
  [data-testid="stSidebar"] [role="radiogroup"] input[type="radio"] {
    position: absolute !important; opacity: 0 !important;
    width: 0 !important; height: 0 !important; pointer-events: none !important;
  }
  [data-testid="stSidebar"] [role="radiogroup"] [data-baseweb="radio"] {
    width: 100% !important;
  }
  [data-testid="stSidebar"] [role="radiogroup"] [data-baseweb="radio"] > div:first-child {
    display: none !important;
  }
  [data-testid="stSidebar"] [role="radiogroup"] [data-baseweb="radio"] > div:last-child {
    width: 100% !important; padding-left: 0 !important;
  }
  [data-testid="stSidebar"] [role="radiogroup"] label p {
    color: rgba(255,255,255,.76) !important;
    font-size: .92rem !important; font-weight: 500 !important;
    margin: 0 !important;
  }
  [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {
    color: #fff !important; font-weight: 700 !important;
  }

  .sb-mode-box { margin-top: 28px; }
  .sb-mode-label {
    font-size: 10px; font-weight: 700; letter-spacing: 0.1em;
    color: rgba(255,255,255,0.55); margin: 0 4px 10px;
  }
  .sb-footer {
    font-size: 0.78rem; color: rgba(255,255,255,0.45);
    line-height: 1.5; padding: 24px 4px 8px;
    margin-top: 20px; border-top: 1px solid rgba(255,255,255,.08);
  }
  .sb-footer strong { color: rgba(255,255,255,0.85); font-size: 0.85rem; }
  .sb-footer span { color: rgba(255,255,255,0.62) !important; }

  /* Toggle tema en sidebar */
  [data-testid="stSidebar"] [data-testid="stSegmentedControl"] {
    background: rgba(0,0,0,0.28) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 14px !important;
    padding: 6px !important; width: 100% !important;
    margin-top: -4px !important;
  }
  [data-testid="stSidebar"] [data-testid="stSegmentedControl"] > div {
    display: flex !important; flex-direction: row !important;
    width: 100% !important; gap: 6px !important;
  }
  [data-testid="stSidebar"] [data-testid="stSegmentedControl"] button {
    flex: 1 1 50% !important; min-width: 0 !important;
    height: 40px !important; border-radius: 10px !important;
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    color: rgba(255,255,255,0.88) !important;
    box-shadow: none !important;
  }
  [data-testid="stSidebar"] [data-testid="stSegmentedControl"] button p,
  [data-testid="stSidebar"] [data-testid="stSegmentedControl"] button span,
  [data-testid="stSidebar"] [data-testid="stSegmentedControl"] button div {
    color: rgba(255,255,255,0.88) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.88) !important;
    font-size: .8rem !important; font-weight: 600 !important;
    white-space: nowrap !important;
  }
  [data-testid="stSidebar"] [data-testid="stSegmentedControl"] button[aria-pressed="true"] {
    background: #E69984 !important;
    border-color: rgba(230,153,132,0.55) !important;
    box-shadow: 0 0 14px rgba(230,153,132,0.28) !important;
    color: #0D1110 !important;
  }
  [data-testid="stSidebar"] [data-testid="stSegmentedControl"] button[aria-pressed="true"] p,
  [data-testid="stSidebar"] [data-testid="stSegmentedControl"] button[aria-pressed="true"] span,
  [data-testid="stSidebar"] [data-testid="stSegmentedControl"] button[aria-pressed="true"] div {
    color: #0D1110 !important;
    -webkit-text-fill-color: #0D1110 !important;
  }

  /* -- PARAM BAR -- */
  .param-bar-head {
    display: flex; align-items: center; gap: 10px;
    margin: 0 0 12px 4px;
  }
  .param-bar-text {
    font-size: 14px; font-weight: 700; color: #8A9A95;
  }
  .param-vivo {
    background: rgba(230,153,132,0.18); color: #E69984; font-size: 10px; font-weight: 800;
    padding: 3px 9px; border-radius: 6px; letter-spacing: 0.08em;
  }
  [data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px !important;
    padding: 14px 12px 12px !important;
    margin-bottom: 18px !important;
  }
  [data-testid="stVerticalBlockBorderWrapper"] > div > [data-testid="stHorizontalBlock"] {
    gap: 10px !important;
  }
  [data-testid="stVerticalBlockBorderWrapper"] > div > [data-testid="stHorizontalBlock"] > [data-testid="column"] {
    border-right: 1px solid rgba(120,145,132,.18);
    padding: 0 10px !important;
  }
  [data-testid="stVerticalBlockBorderWrapper"] > div > [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child {
    border-right: 0;
  }
  [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stSelectbox"] label p {
    font-size: .72rem !important; font-weight: 600 !important;
    color: #648076 !important; margin-bottom: 4px !important;
  }
  [data-testid="stVerticalBlockBorderWrapper"] [data-baseweb="select"] > div {
    min-height: 38px !important; border-radius: 8px !important;
    border-color: transparent !important; background: transparent !important;
    padding-left: 0 !important;
  }
  [data-testid="stVerticalBlockBorderWrapper"] [data-baseweb="select"] span {
    font-size: .9rem !important; font-weight: 700 !important;
  }

  /* -- HERO -- */
  .hero {
    border-radius: 20px; padding: 32px 36px; margin-bottom: 18px;
    display: flex; gap: 20px; align-items: center; justify-content: space-between;
    position: relative; overflow: hidden;
  }
  .hero-copy { flex: 1; min-width: 0; }
  .hero-art  { flex: 0 0 300px; max-width: 320px; }
  .hero-art img { width: 100%; height: auto; display: block; }

  /* Force ALL text inside hero to be white */
  .hero, .hero *, .hero h1, .hero p, .hero strong, .hero div,
  .hero .kicker, .hero .kpi, .hero .kpi .v, .hero .kpi .l,
  [data-testid="stMarkdownContainer"] .hero *,
  [data-testid="stMarkdownContainer"] .hero h1,
  [data-testid="stMarkdownContainer"] .hero p {
    color: #ffffff !important;
  }
  .hero h1 {
    font-size: 1.8rem !important; font-weight: 800 !important;
    line-height: 1.2 !important; margin: 10px 0 12px !important;
  }
  .hero p { line-height: 1.6 !important; font-size: 0.95rem !important; }
  .kicker {
    font-size: 11px !important; font-weight: 700 !important;
    letter-spacing: 0.12em !important; text-transform: uppercase !important;
    color: #E69984 !important;
  }
  .hero h1 {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-weight: 600 !important;
  }

  /* -- KPI ROW -- */
  .kpi-row { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin-top: 20px; }
  .kpi {
    border-radius: 14px; padding: 14px 16px;
    border: 1px solid rgba(255,255,255,0.12);
    background: rgba(0,0,0,0.2);
    display: flex; align-items: flex-start; gap: 11px;
  }
  .kpi-icon {
    flex: 0 0 34px; width: 34px; height: 34px; border-radius: 9px;
    background: rgba(255,255,255,0.12);
    display: flex; align-items: center; justify-content: center;
  }
  .kpi-body { flex: 1; min-width: 0; }
  .kpi .v { font-size: 1.3rem !important; font-weight: 800 !important; line-height: 1.1 !important; }
  .kpi .l { font-size: 10.5px !important; margin-top: 4px !important; opacity: 0.78 !important; line-height: 1.35 !important; }

  /* -- CARDS -- */
  .card { border-radius: 18px; padding: 20px 22px; margin-bottom: 14px; }
  .card h4 { margin: 0 0 14px; font-size: 1rem; font-weight: 700; }
  .card p, .card li { font-size: 0.88rem; line-height: 1.6; }

  /* -- PILLS -- */
  .pill { display:inline-block; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }

  /* -- SEMAFORO -- */
  .semaforo { text-align: center; padding: 28px 16px; border-radius: 18px; }
  .ring {
    width: 96px; height: 96px; border-radius: 50%; margin: 0 auto 14px;
    display: flex; align-items: center; justify-content: center;
    border: 6px solid #94B8A3; font-size: 2.2rem;
    box-shadow: 0 6px 22px rgba(148,184,163,0.25);
  }
  .ring.ambar { border-color: #e6b450; box-shadow: 0 6px 22px rgba(230,180,80,0.2); }
  .ring.rojo  { border-color: #e05555; box-shadow: 0 6px 22px rgba(224,85,85,0.2); }
  .semaforo .estado { font-size: 1.2rem; font-weight: 800; }
  .semaforo .sub    { font-size: 13px; margin-top: 6px; }
  .semaforo-foot    { margin-top: 14px; padding-top: 10px; border-top: 1px solid rgba(128,160,140,0.2); font-size: 11px; opacity: 0.65; }

  /* -- REC ROWS -- */
  .rec-row   { display: flex; align-items: center; gap: 8px; padding: 5px 0; border-bottom: 1px solid rgba(128,160,140,0.12); font-size: 0.875rem; }
  .rec-ico   { flex: 0 0 18px; text-align: center; font-size: 13px; }
  .rec-label { flex: 1; opacity: 0.68; }
  .rec-val   { flex: 0 0 auto; text-align: right; }
  .rec-donut-label { font-size: 11px; opacity: 0.65; margin-bottom: 6px; }
  .rec-link  { font-size: 12px; text-decoration: none; opacity: 0.85; }
  .rec-link:hover { opacity: 1; }

  /* -- MISC -- */
  .decision { border-radius: 16px; padding: 16px 18px; margin-bottom: 14px; }
  .badge { display:inline-block; border-radius: 999px; padding: 6px 14px; font-size: 12px; font-weight: 600; }
  .page-title { font-size: 1.65rem !important; font-weight: 800 !important; margin: 0 0 4px !important; line-height: 1.2 !important; }
  .page-sub   { font-size: 0.93rem !important; margin: 0 0 16px !important; }
  .recorrido-banner { border-radius: 14px; padding: 14px 18px; margin-bottom: 14px; }
  .tab-hint { display:inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; }
  .foot { font-size: 12px; margin-top: 28px; padding-top: 12px; }

  @media (max-width: 900px) {
    .kpi-row { grid-template-columns: 1fr 1fr; }
    .hero { flex-direction: column; }
    .hero-art { max-width: 220px; }
  }
"""

_DARK_CSS = """
  .stApp { background: #0D1110 !important; color: #E8E4DC !important; }
  .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
    color: #F0EDE8 !important;
  }
  [data-testid="stSidebar"] { background: linear-gradient(170deg, #121816 0%, #0A0E0C 100%) !important; }
  [data-testid="stSidebar"] * { color: #E8E4DC !important; }
  .page-title { color: #F0EDE8 !important; }
  .page-sub   { color: #8A9A95 !important; }
  .badge { background: rgba(230,153,132,0.14); color: #E69984; border: 1px solid rgba(230,153,132,0.32); }
  .param-bar-text { color: #8A9A95; }
  .param-vivo { background: rgba(230,153,132,0.18); color: #E69984; }
  [data-testid="stVerticalBlockBorderWrapper"] {
    background: #1A231F !important; border-color: rgba(36,51,46,0.9) !important;
  }
  [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stSelectbox"] label p {
    color: #8A9A95 !important;
  }
  [data-testid="stVerticalBlockBorderWrapper"] [data-baseweb="select"] > div {
    background: rgba(255,255,255,.03) !important;
    border-color: rgba(148,184,163,.2) !important;
  }
  [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stSelectbox"] span { color: #F0EDE8 !important; }
  [data-baseweb="select"] > div,
  [data-baseweb="input"] > div,
  [data-baseweb="textarea"] > div {
    background: #16211E !important;
    border-color: rgba(148,184,163,.22) !important;
    color: #F0EDE8 !important;
  }
  [data-baseweb="select"] span,
  [data-baseweb="input"] input,
  [data-baseweb="textarea"] textarea {
    color: #F0EDE8 !important;
    -webkit-text-fill-color: #F0EDE8 !important;
  }
  [data-baseweb="popover"],
  [data-baseweb="popover"] > div,
  [role="listbox"] {
    background: #16211E !important;
    border-color: rgba(148,184,163,.25) !important;
  }
  [role="option"] { color: #E8E4DC !important; background: #16211E !important; }
  [role="option"]:hover,
  [role="option"][aria-selected="true"] {
    color: #0D1110 !important; background: #E69984 !important;
  }
  .hero { background: linear-gradient(130deg, #1F2E28 0%, #141C19 55%, #233930 100%);
          border: 1px solid rgba(230,153,132,0.12); box-shadow: 0 20px 50px rgba(0,0,0,0.45); }
  .kicker { color: #E69984 !important; }
  .card { background: #1A231F; border: 1px solid #24332E; box-shadow: 0 4px 18px rgba(0,0,0,0.28); }
  .card h4 { color: #F0EDE8 !important; }
  .card p, .card li { color: #B8C4BE !important; }
  .pill       { background: rgba(148,184,163,0.14); color: #94B8A3 !important; border: 1px solid rgba(148,184,163,0.3); }
  .pill-amber { background: rgba(230,153,132,0.14); color: #E69984 !important; border: 1px solid rgba(230,153,132,0.32); }
  .pill-red   { background: rgba(220,90,90,0.14);  color: #f0a0a0 !important; border: 1px solid rgba(220,90,90,0.32); }
  .semaforo { background: #1A231F; border: 1px solid #24332E; }
  .semaforo .estado { color: #F0EDE8 !important; }
  .semaforo .sub    { color: #8A9A95 !important; }
  .ring       { background: rgba(148,184,163,0.08); border-color: #94B8A3; }
  .ring.ambar { background: rgba(230,153,132,0.08); border-color: #E69984; }
  .ring.rojo  { background: rgba(224,85,85,0.08); }
  .decision       { background: rgba(148,184,163,0.1);  border: 1px solid rgba(148,184,163,0.28); }
  .decision-ambar { background: rgba(230,153,132,0.1);  border-color: rgba(230,153,132,0.3); }
  .decision-rojo  { background: rgba(224,85,85,0.1);   border-color: rgba(224,85,85,0.3); }
  .decision h4, .decision p, .decision li { color: #E8E4DC !important; }
  .recorrido-banner { background: #1A231F; border: 1px solid rgba(230,153,132,0.25); }
  .recorrido-banner h4 { color: #E69984 !important; }
  .recorrido-banner p  { color: #B8C4BE !important; }
  .tab-hint { background: #E69984; color: #0D1110 !important; }
  .foot { color: #8A9A95 !important; border-top: 1px solid #24332E; }
  .rec-label { color: #8A9A95 !important; }
  .rec-val   { color: #E8E4DC !important; }
  .rec-link  { color: #E69984 !important; }
  div[data-testid="stMetricValue"] { color: #E69984 !important; }
  div[data-testid="stMetricLabel"] { color: #8A9A95 !important; }
  [data-testid="stMetricDelta"] { color: #94B8A3 !important; }
  [data-testid="stChatMessage"] { background: #1A231F !important; border: 1px solid #24332E !important; border-radius: 14px !important; }
  [data-testid="stChatInput"] > div {
    background: #16211E !important; border-color: rgba(148,184,163,.25) !important;
  }
  [data-testid="stChatInput"] textarea {
    color: #F0EDE8 !important; -webkit-text-fill-color: #F0EDE8 !important;
  }
  label { color: #C5D0CA !important; font-weight: 500 !important; }
  [data-testid="stMarkdownContainer"] p,
  [data-testid="stMarkdownContainer"] span,
  [data-testid="stMarkdownContainer"] li { color: #E8E4DC !important; }
  .stExpander { border: 1px solid #24332E !important; border-radius: 12px !important; }
  .stExpander summary { color: #F0EDE8 !important; background: #1A231F !important; }
  div[data-testid="stExpander"] { background: #1A231F !important; }
  [data-testid="stCaptionContainer"],
  [data-testid="stCaptionContainer"] p,
  [data-testid="stCaptionContainer"] span { color: #8A9A95 !important; }
  [data-testid="stDataFrame"],
  [data-testid="stTable"] { color: #E8E4DC !important; }
  [data-testid="stTable"] th { background: #213028 !important; color: #F0EDE8 !important; }
  [data-testid="stTable"] td { background: #1A231F !important; color: #C5D0CA !important; }
  .stButton button,
  [data-testid="stBaseButton-secondary"] {
    background: #213028 !important; border-color: rgba(148,184,163,.3) !important;
    color: #E8E4DC !important;
  }
  .stButton button:hover,
  [data-testid="stBaseButton-secondary"]:hover {
    background: #2A3A34 !important; border-color: #E69984 !important;
  }
  [data-testid="stBaseButton-primary"] {
    background: #E69984 !important; border-color: #E69984 !important; color: #0D1110 !important;
  }
  [data-testid="stTabs"] button { color: #8A9A95 !important; }
  [data-testid="stTabs"] button[aria-selected="true"] { color: #E69984 !important; }
  [data-testid="stDownloadButton"] button { background: #213028 !important;
    border: 1px solid #24332E !important; color: #E8E4DC !important;
    border-radius: 10px !important; text-align: left !important; font-weight: 500 !important; padding: 10px 14px !important; }
  /* Hero text white — LAST rule wins */
  [data-testid="stMarkdownContainer"] .hero p,
  [data-testid="stMarkdownContainer"] .hero span,
  [data-testid="stMarkdownContainer"] .hero h1,
  [data-testid="stMarkdownContainer"] .hero strong,
  .hero p, .hero span, .hero h1, .hero strong, .hero div { color: #F0EDE8 !important; }
  [data-testid="stMarkdownContainer"] .hero .kicker { color: #E69984 !important; }
"""

_LIGHT_CSS = """
  .stApp { background: #F4F1EC !important; color: #1A231F !important; }
  .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
    color: #1A231F !important;
  }
  [data-testid="stSidebar"] { background: linear-gradient(170deg, #1A231F 0%, #0D1110 100%) !important; }
  [data-testid="stSidebar"] * { color: #E8E4DC !important; }
  .page-title { color: #1A231F !important; }
  .page-sub   { color: #5A6B64 !important; }
  .badge { background: rgba(230,153,132,0.15); color: #C46B55; border: 1px solid rgba(230,153,132,0.35); }
  .param-bar-text { color: #5A6B64; }
  .param-vivo { background: rgba(230,153,132,0.18); color: #C46B55; }
  [data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff !important;
    border: 1px solid #E0DCD4 !important;
    border-radius: 16px !important;
    padding: 14px 10px 6px !important;
    margin-bottom: 18px !important;
    box-shadow: 0 4px 18px rgba(26,35,31,0.06);
  }
  .hero { background: linear-gradient(130deg, #233930 0%, #16211E 50%, #2A4038 100%);
          box-shadow: 0 20px 50px rgba(13,17,16,0.22); }
  .kicker { color: #E69984 !important; }
  .card    { background: #ffffff; border: 1px solid #E0DCD4; box-shadow: 0 4px 22px rgba(26,35,31,0.06); }
  .card h4 { color: #1A231F !important; }
  .card p, .card li, .card b, .card strong { color: #3D4A44 !important; }
  .pill       { background: rgba(148,184,163,0.15); color: #3D6B55 !important; border: 1px solid rgba(148,184,163,0.35); }
  .pill-amber { background: rgba(230,153,132,0.15); color: #C46B55 !important; border: 1px solid rgba(230,153,132,0.35); }
  .pill-red   { background: rgba(190,50,50,0.09); color: #9e2020 !important; border: 1px solid rgba(190,50,50,0.28); }
  .semaforo { background: #fff; border: 1px solid #E0DCD4; box-shadow: 0 4px 20px rgba(26,35,31,0.05); }
  .semaforo .estado { color: #1A231F !important; }
  .semaforo .sub    { color: #5A6B64 !important; }
  .semaforo-foot    { color: #5A6B64 !important; border-top-color: rgba(26,35,31,0.1) !important; }
  .ring       { background: #EDF5F0; border-color: #94B8A3; box-shadow: 0 6px 22px rgba(148,184,163,0.2); }
  .ring.ambar { background: #FDF4F0; border-color: #E69984; box-shadow: 0 6px 22px rgba(230,153,132,0.2); }
  .ring.rojo  { background: #fdf0f0; border-color: #c83838; box-shadow: 0 6px 22px rgba(200,56,56,0.18); }
  .decision       { background: #EDF5F0; border: 1px solid #C5D9CC; }
  .decision-ambar { background: #FDF4F0; border-color: #F0D0C4; }
  .decision-rojo  { background: #fdeeee; border-color: #efbcbc; }
  .decision h4, .decision p, .decision li { color: #1A231F !important; }
  .recorrido-banner { background: #fff; border: 1px solid #E0DCD4; }
  .recorrido-banner h4 { color: #C46B55 !important; }
  .recorrido-banner p  { color: #3D4A44 !important; }
  .tab-hint { background: #E69984; color: #0D1110 !important; }
  .foot { color: #5A6B64 !important; border-top: 1px solid #E0DCD4; }
  .rec-label { color: #5A6B64 !important; }
  .rec-val   { color: #1A231F !important; }
  .rec-link  { color: #C46B55 !important; }
  div[data-testid="stMetricValue"] { color: #C46B55 !important; }
  div[data-testid="stMetricLabel"] { color: #5A6B64 !important; }
  [data-testid="stChatMessage"] { background: #fff !important; border: 1px solid #E0DCD4 !important; border-radius: 14px !important; }
  label { color: #1A231F !important; font-weight: 500 !important; }
  [data-testid="stMarkdownContainer"] p,
  [data-testid="stMarkdownContainer"] span,
  [data-testid="stMarkdownContainer"] li { color: #1A231F !important; }
  .stExpander { border: 1px solid #E0DCD4 !important; border-radius: 12px !important; background: #fff !important; }
  .stExpander summary { color: #1A231F !important; background: #fff !important; }
  [data-testid="stCaptionContainer"],
  [data-testid="stCaptionContainer"] p,
  [data-testid="stCaptionContainer"] span { color: #5A6B64 !important; }
  [data-baseweb="select"] > div,
  [data-baseweb="input"] > div,
  [data-baseweb="textarea"] > div {
    background: #fff !important; border-color: #E0DCD4 !important; color: #1A231F !important;
  }
  [data-baseweb="select"] span,
  [data-baseweb="input"] input,
  [data-baseweb="textarea"] textarea {
    color: #1A231F !important; -webkit-text-fill-color: #1A231F !important;
  }
  [data-baseweb="popover"],
  [data-baseweb="popover"] > div,
  [role="listbox"] { background: #fff !important; border-color: #E0DCD4 !important; }
  [role="option"] { color: #1A231F !important; background: #fff !important; }
  [role="option"]:hover,
  [role="option"][aria-selected="true"] { background: #FDF4F0 !important; color: #C46B55 !important; }
  [data-testid="stTable"] th { background: #EDF5F0 !important; color: #1A231F !important; }
  [data-testid="stTable"] td { background: #fff !important; color: #3D4A44 !important; }
  [data-testid="stDownloadButton"] button { background: #F7F5F1 !important; border: 1px solid #E0DCD4 !important;
    color: #1A231F !important; border-radius: 10px !important;
    text-align: left !important; font-weight: 500 !important; padding: 10px 14px !important; }
  [data-testid="stDownloadButton"] button:hover { background: #FDF4F0 !important; border-color: #E69984 !important; }
  [data-testid="stBaseButton-primary"] {
    background: #E69984 !important; border-color: #E69984 !important; color: #0D1110 !important;
  }
  /* Hero text always cream — LAST rule wins */
  [data-testid="stMarkdownContainer"] .hero p,
  [data-testid="stMarkdownContainer"] .hero span,
  [data-testid="stMarkdownContainer"] .hero h1,
  [data-testid="stMarkdownContainer"] .hero strong,
  .hero p, .hero span, .hero h1, .hero strong, .hero div { color: #F0EDE8 !important; }
  [data-testid="stMarkdownContainer"] .hero .kicker { color: #E69984 !important; }
"""

if ES_OSCURO:
    st.markdown("<style>" + _COMMON_CSS + _DARK_CSS + "</style>", unsafe_allow_html=True)
else:
    st.markdown("<style>" + _COMMON_CSS + _LIGHT_CSS + "</style>", unsafe_allow_html=True)


def money(x, moneda="S/"):
    if moneda == "US$":
        return f"US$ {x:,.0f}"
    return f"S/ {x:,.0f}"


def pct(x):
    return f"{x:.2%}"


def num(x):
    return f"{x:.2f}"


def card_open(title: str = ""):
    t = f"<h4>{title}</h4>" if title else ""
    return f'<div class="card">{t}'


def card_close():
    return "</div>"


def estado_semaforo(crit: dict) -> tuple[str, str, str]:
    n_ok = sum(1 for k in ("sharpe_ok", "vol_ok", "vs_mercado_ok") if crit[k])
    if n_ok == 3 and crit.get("clases_ok", True):
        return "verde", "ELEGIBLE", "Cumple Sharpe, volatilidad y supera al mercado."
    if n_ok == 0:
        return "rojo", "NO ELEGIBLE", "No cumple los criterios mínimos del mandato."
    return "ambar", "REVISAR", "Cumple parcialmente — el comité debe evaluar."


def fig_pesos(pesos: pd.DataFrame):
    df = pesos.copy()
    df["Peso %"] = df["Peso"] * 100
    fig = px.bar(
        df.sort_values("Peso"),
        x="Peso %",
        y="Ticker",
        color="Clase de Activo",
        orientation="h",
        hover_data={"Capital": ":,.0f", "Peso %": ":.2f", "Ticker": False},
        color_discrete_sequence=PLOTLY_COLORS,
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=max(300, 26 * len(df)), showlegend=True,
                      legend=dict(orientation="h", y=-0.18))
    grid = "rgba(0,0,0,0.06)" if not ES_OSCURO else "rgba(255,255,255,0.06)"
    fig.update_xaxes(title="Peso (%)", gridcolor=grid)
    fig.update_yaxes(title="", gridcolor=grid)
    return fig


def fig_clases(clases: pd.DataFrame):
    fig = px.pie(
        clases,
        values="Peso",
        names="Clase de Activo",
        hole=0.55,
        color_discrete_sequence=PLOTLY_COLORS,
    )
    fig.update_traces(textposition="outside", textinfo="percent",
                      textfont_size=11)
    fig.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=True,
                      legend=dict(orientation="h", y=-0.1, font=dict(size=10)))
    return fig


def fig_comparador(sims: dict[str, dict]):
    metricas = ["Retorno %", "Volatilidad %", "Sharpe", "VaR %"]
    fig = go.Figure()
    colors = {"Conservador": "#7A9EAE", "Máx. Sharpe": "#94B8A3", "Agresivo": "#E69984"}
    for nombre, s in sims.items():
        vals = [s["retorno_anual"] * 100, s["vol_anual"] * 100, s["sharpe"], s["var_anual"] * 100]
        fig.add_trace(go.Bar(
            name=nombre, x=metricas, y=vals,
            marker_color=colors.get(nombre, "#9db5aa"),
            text=[f"{v:.2f}" for v in vals], textposition="outside",
        ))
    fig.update_layout(**PLOTLY_LAYOUT, barmode="group", height=360,
                      legend=dict(orientation="h", y=1.12))
    return fig


def informe_txt(sim: dict) -> str:
    bm = sim["benchmark"]
    crit = sim["criterios"]
    luz, etiqueta, detalle = estado_semaforo(crit)
    mon = sim["moneda"]
    dec = frase_ejecutiva(sim, crit, luz, etiqueta, bm)
    lineas = [
        "INFORME DE COMITÉ · Portafolio Óptimo Grupo 3 · UTEC",
        "=" * 56,
        f"Estado: {etiqueta} ({detalle})",
        "",
        "DECISIÓN EJECUTIVA",
        dec["titulo"].replace("**", "").replace("*", ""),
    ]
    for b in dec["bullets"]:
        lineas.append(f"  • {b.replace('**', '')}")
    lineas += [
        "",
        f"Perfil: {sim['perfil']} | Activos: {sim['n_activos']} | Horizonte: {sim['horizonte_meses']} m",
        f"Capital: {money(sim['capital_m'], mon)} | VaR conf.: {int(sim['confianza']*100)}%",
        "",
        "KPIs",
        f"  Retorno anual: {pct(sim['retorno_anual'])}",
        f"  Volatilidad:   {pct(sim['vol_anual'])}",
        f"  Sharpe:        {num(sim['sharpe'])}  (S&P {num(bm['sharpe'])})",
        f"  VaR:           {pct(sim['var'])} ≈ {money(sim['var_soles'], mon)}",
        f"  CVaR:          {pct(sim['cvar'])} ≈ {money(sim['cvar_soles'], mon)}",
        f"  Ganancia esp.: {money(sim['ganancia'], mon)}",
        "",
        "Top posiciones",
    ]
    for _, row in sim["pesos"].head(10).iterrows():
        lineas.append(
            f"  {row['Ticker']:6} {row['Clase de Activo'][:28]:28} "
            f"{pct(row['Peso']):>7}  {money(row['Capital'], mon)}"
        )
    lineas += [
        "",
        "DISCLAIMER: Simulación académica. No constituye recomendación de inversión.",
    ]
    return "\n".join(lineas)


def html_decision(sim, crit, luz, etiqueta, bm) -> str:
    def _md(text: str) -> str:
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        return re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)

    dec = frase_ejecutiva(sim, crit, luz, etiqueta, bm)
    css = {"verde": "decision", "ambar": "decision decision-ambar", "rojo": "decision decision-rojo"}[luz]
    bullets = "".join(f"<li>{_md(b)}</li>" for b in dec["bullets"])
    return (
        f'<div class="{css}"><h4>Decisión del agente</h4>'
        f"<p>{_md(dec['titulo'])}</p><ul>{bullets}</ul>"
        f"<p><em>La votación final es del comité humano.</em></p></div>"
    )


# -- Parámetros VIVO --
h1, h2 = st.columns([3, 1.2])
with h1:
    st.markdown(
        '<p class="page-title">Gestión cuantitativa de patrimonio</p>'
        '<p class="page-sub">Portafolio diversificado, riesgo medible y recomendación trazable para el comité.</p>',
        unsafe_allow_html=True,
    )
with h2:
    st.markdown(
        '<div style="text-align:right;padding-top:8px">'
        '<span class="badge">Simulación académica Grupo 3 · UTEC</span></div>',
        unsafe_allow_html=True,
    )

with st.container(border=True):
    st.markdown(
        '<div class="param-bar-head">'
        '<span class="param-bar-text">Parámetros del simulador</span>'
        '<span class="param-vivo">VIVO</span>'
        "</div>",
        unsafe_allow_html=True,
    )
    _params = [
        ("◎  Capital", "Capital", ["S/ 1 MM", "S/ 2 MM", "S/ 3 MM", "S/ 5 MM"], 0, None),
        ("□  Horizonte", "Horizonte", [6, 12, 24, 36], 1, lambda m: f"{m} meses"),
        ("♙  Perfil", "Perfil", ["Conservador", "Máx. Sharpe", "Agresivo"], 1, None),
        ("◇  Confianza VaR", "Confianza VaR", ["99%", "95%"], 0, None),
        ("▥  N° activos", "N.º activos", [5, 10, 15, 20], 3, None),
        ("◉  Moneda", "Moneda", ["S/", "US$"], 0, None),
    ]
    cols = st.columns(6)
    _vals = []
    for i, (label, key_name, opts, idx, fmt) in enumerate(_params):
        with cols[i]:
            kwargs = dict(
                label=label,
                options=opts,
                index=idx,
                key=f"param_{key_name}",
            )
            if fmt is not None:
                kwargs["format_func"] = fmt
            _vals.append(st.selectbox(**kwargs))
    capital_sel, horizonte, perfil, conf_lbl, n_activos, moneda = _vals
capital_map = {"S/ 1 MM": 1_000_000, "S/ 2 MM": 2_000_000, "S/ 3 MM": 3_000_000, "S/ 5 MM": 5_000_000}
capital = capital_map[capital_sel]
confianza = 0.99 if conf_lbl.startswith("99") else 0.95

sim = simular(
    capital=capital,
    horizonte_meses=int(horizonte),
    perfil=perfil,
    confianza=confianza,
    n_activos=int(n_activos),
    moneda=moneda,
)

escenario_id = f"{perfil}|{n_activos}|{horizonte}|{confianza}|{capital}|{moneda}"
if "escenario_prev" not in st.session_state:
    st.session_state.escenario_prev = escenario_id
elif st.session_state.escenario_prev != escenario_id:
    st.session_state.escenario_prev = escenario_id
    if "chat_msgs" in st.session_state:
        st.session_state.chat_msgs.append({
            "role": "assistant",
            "content": (
                f"Escenario actualizado → **{perfil}** · {n_activos} activos · "
                f"{horizonte} m · VaR {int(confianza*100)}% · {money(sim['capital_m'], moneda)}."
            ),
        })

try:
    colab = cargar_resultados()
    graficos = colab["graficos"]
except FileNotFoundError:
    graficos = {}

bm = sim["benchmark"]
crit = sim["criterios"]
luz, etiqueta, detalle_sem = estado_semaforo(crit)
pill_cls = {"verde": "pill", "ambar": "pill pill-amber", "rojo": "pill pill-red"}[luz]
ring_cls = {"verde": "ring", "ambar": "ring ambar", "rojo": "ring rojo"}[luz]
ring_icon = {"verde": "✓", "ambar": "!", "rojo": "✕"}[luz]

# Banner recorrido
if st.session_state.demo_paso >= 0:
    paso_idx = min(st.session_state.demo_paso, len(PASOS_RECORRIDO) - 1)
    paso = formatear_paso(PASOS_RECORRIDO[paso_idx], sim, bm, etiqueta, int(confianza * 100))
    st.markdown(
        f"""
        <div class="recorrido-banner">
          <h4>Recorrido del comité · Paso {paso_idx + 1}/{len(PASOS_RECORRIDO)} — {paso['titulo']}</h4>
          <p><span class="tab-hint">Ir a: {paso['tab']}</span></p>
          <p><b>Guion:</b> {paso['guion']}</p>
          <p><b>Tip:</b> {paso['tip']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    rc1, rc2, rc3, rc4 = st.columns([1, 1, 1, 2])
    if rc1.button("◀ Anterior", key="demo_prev"):
        st.session_state.demo_paso = max(0, st.session_state.demo_paso - 1)
        st.rerun()
    if rc2.button("Siguiente ▶", key="demo_next"):
        nxt = min(len(PASOS_RECORRIDO) - 1, st.session_state.demo_paso + 1)
        st.session_state.demo_paso = nxt
        dest = PASOS_RECORRIDO[nxt]["tab"]
        st.session_state.pagina = dest
        st.session_state.sidebar_nav = dest
        st.rerun()
    if rc3.button("Terminar", key="demo_end"):
        st.session_state.demo_paso = -1
        st.rerun()
    if paso.get("chat_demo") and rc4.button("💬 Pregunta demo", key="demo_ask"):
        if "chat_msgs" not in st.session_state:
            st.session_state.chat_msgs = []
        q = paso["chat_demo"]
        st.session_state.chat_msgs.append({"role": "user", "content": q})
        st.session_state.chat_msgs.append({"role": "assistant", "content": responder(q, sim)})
        st.session_state.pagina = "El asistente"
        st.session_state.sidebar_nav = "El asistente"
        st.rerun()

pagina = st.session_state.pagina

# -- RESUMEN --
if pagina == "Resumen":
    # -- Hero banner --─
    hero_art = ""
    if HERO_CHARTS.exists():
        b64 = base64.b64encode(HERO_CHARTS.read_bytes()).decode()
        hero_art = (
            '<div class="hero-art">'
            f'<img src="data:image/svg+xml;base64,{b64}" alt="Gráficos del portafolio"/>'
            "</div>"
        )

    # Icon SVGs for KPI badges
    _ico_sharpe = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>'
    _ico_ret    = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 12h8M12 8v8"/></svg>'
    _ico_gain   = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-4 0v2"/></svg>'
    _ico_var    = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'

    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-copy">
            <div class="kicker">Gestión cuantitativa de patrimonio</div>
            <h1>Su capital, invertido con criterio,<br>disciplina y evidencia.</h1>
            <p>El asistente construye un portafolio diversificado, maximiza retorno por unidad de riesgo,
            cuantifica la pérdida potencial y entrega una recomendación trazable.<br>
            <strong style="color:#7fdfb0">La decisión final siempre es humana.</strong></p>
            <div class="kpi-row">
              <div class="kpi">
                <div class="kpi-icon" style="color:#5dffa0">{_ico_sharpe}</div>
                <div class="kpi-body">
                  <div class="v">{num(sim['sharpe'])}</div>
                  <div class="l">Ratio de Sharpe<br>(vs. {num(bm['sharpe'])} mercado)</div>
                </div>
              </div>
              <div class="kpi">
                <div class="kpi-icon" style="color:#ffc870">{_ico_ret}</div>
                <div class="kpi-body">
                  <div class="v">{pct(sim['retorno_anual'])}</div>
                  <div class="l">Retorno esperado anual</div>
                </div>
              </div>
              <div class="kpi">
                <div class="kpi-icon" style="color:#a0d8ff">{_ico_gain}</div>
                <div class="kpi-body">
                  <div class="v">{money(sim['ganancia'], moneda)}</div>
                  <div class="l">Ganancia esperada ({horizonte} m)</div>
                </div>
              </div>
              <div class="kpi">
                <div class="kpi-icon" style="color:#ffb0a0">{_ico_var}</div>
                <div class="kpi-body">
                  <div class="v">{pct(sim['var'])}</div>
                  <div class="l">VaR {int(confianza*100)}% · {horizonte} m</div>
                </div>
              </div>
            </div>
          </div>
          {hero_art}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- Glosario --─
    g1, g2, g3 = st.columns(3)
    with g1:
        with st.expander("ℹ️ Ratio de Sharpe"):
            st.markdown(GLOSARIO["Sharpe"])
    with g2:
        with st.expander(f"ℹ️ VaR {int(confianza*100)}%"):
            st.markdown(GLOSARIO["VaR"])
    with g3:
        with st.expander(f"ℹ️ CVaR {int(confianza*100)}%"):
            st.markdown(GLOSARIO["CVaR"])

    # -- Bottom 3 cards --─
    import datetime as _dt
    _ts = _dt.datetime.now().strftime("Validado el %d %b %Y · %I:%M %p").replace("AM", "a. m.").replace("PM", "p. m.")

    _ico_check = "✓" if luz == "verde" else ("!" if luz == "ambar" else "✕")
    _valid_color = {"verde": "#3dcf7a", "ambar": "#e6b450", "rojo": "#e05555"}[luz]

    s1, s2, s3 = st.columns([1, 1.4, 1.1])

    # Card 1 — Elegibilidad
    with s1:
        st.markdown(
            f"""
            <div class="semaforo">
              <div class="{ring_cls}">{ring_icon}</div>
              <div class="estado">{etiqueta}</div>
              <div class="sub">{detalle_sem}</div>
              <div class="semaforo-foot">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="{_valid_color}"
                     stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px;margin-right:4px">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
                {_ts}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Card 2 — Recomendación (usamos card_open/close para que Streamlit widgets queden dentro)
    with s2:
        _rows = [
            ("📊", "Retorno anual esperado:", f"**{pct(sim['retorno_anual'])}**"),
            ("〜", "Volatilidad:", pct(sim['vol_anual'])),
            ("◈", "Ratio de Sharpe:", num(sim['sharpe'])),
            ("⋰", "Diversificación:", "**Diversificada**"),
            ("👤", "Perfil:", f"**{perfil}**"),
            ("📋", "Activos recomendados:", f"**{n_activos} activos**"),
            ("⏱", "Horizonte:", f"**{horizonte} meses**"),
        ]
        st.markdown(card_open("Recomendación de referencia"), unsafe_allow_html=True)
        _left_r, _right_r = st.columns([1.1, 1])
        with _left_r:
            for _ico, _lbl, _val in _rows:
                st.markdown(
                    f'<div class="rec-row"><span class="rec-ico">{_ico}</span>'
                    f'<span class="rec-label">{_lbl}</span>'
                    f'<span class="rec-val">{_val}</span></div>',
                    unsafe_allow_html=True,
                )
            st.markdown('<a class="rec-link" href="#">Ver detalles de la recomendación →</a>', unsafe_allow_html=True)
        with _right_r:
            st.caption("Distribución sugerida")
            st.plotly_chart(fig_clases(sim["clases"]), use_container_width=True, key="plotly_donut_resumen")
        st.markdown(card_close(), unsafe_allow_html=True)

    # Card 3 — Exportar
    with s3:
        csv_pesos = sim["pesos"].copy()
        csv_pesos["Peso"] = csv_pesos["Peso"].map(lambda x: round(float(x), 6))
        st.markdown(card_open("Exportar para el comité"), unsafe_allow_html=True)
        st.download_button(
            "📄  Descargar cartera · Formato CSV",
            data=csv_pesos.to_csv(index=False).encode("utf-8"),
            file_name=f"cartera_grupo3_{perfil.replace(' ', '_').lower()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.download_button(
            "📝  Descargar informe · Formato TXT",
            data=informe_txt(sim).encode("utf-8"),
            file_name="informe_comite_grupo3.txt",
            mime="text/plain",
            use_container_width=True,
        )
        st.download_button(
            "📊  Descargar reporte ejecutivo · CSV",
            data=sim["pesos"].to_csv(index=False).encode("utf-8"),
            file_name=f"reporte_ejecutivo_grupo3.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.caption("Archivos listos para su presentación y análisis.")
        st.markdown(card_close(), unsafe_allow_html=True)

    # -- Recorrido del comité (al fondo) --
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🗺️  Recorrido del comité — guion de defensa (~5 min)", expanded=False):
        st.caption("Navega paso a paso durante la presentación.")
        if st.button("▶  Iniciar recorrido", type="primary", key="demo_start"):
            st.session_state.demo_paso = 0
            st.rerun()
        for i, p in enumerate(PASOS_RECORRIDO, start=1):
            pf = formatear_paso(p, sim, bm, etiqueta, int(confianza * 100))
            st.markdown(f"**{i}. {pf['tab']}** — {pf['titulo']}")

# -- SIMULADOR --
elif pagina == "Simulador":
    st.markdown('<p class="kicker">Simulador VIVO</p>', unsafe_allow_html=True)
    st.caption("Recalcula sin internet sobre métricas del modelo Grupo 3.")
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Capital", money(sim["capital_m"], moneda))
    k2.metric("Retorno", pct(sim["retorno_anual"]))
    k3.metric("Volatilidad", pct(sim["vol_anual"]))
    k4.metric("Sharpe", num(sim["sharpe"]), delta=f"vs {num(bm['sharpe'])}")
    k5.metric(f"VaR {int(confianza*100)}%", pct(sim["var"]), delta=money(-sim["var_soles"], moneda), delta_color="inverse")
    k6.metric("Ganancia", money(sim["ganancia"], moneda))

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown(f'{card_open("Asignación de capital")}', unsafe_allow_html=True)
        st.plotly_chart(fig_pesos(sim["pesos"]), use_container_width=True, key="plotly_pesos_sim")
        st.markdown(card_close(), unsafe_allow_html=True)
    with right:
        st.markdown(f'{card_open(f"Escenarios a {horizonte} meses")}', unsafe_allow_html=True)
        e1, e2, e3 = st.columns(3)
        e1.metric("Favorable", money(sim["favorable"], moneda))
        e2.metric("Esperado", money(sim["esperado"], moneda))
        e3.metric("Adverso", money(sim["adverso"], moneda))
        st.markdown(card_close(), unsafe_allow_html=True)
        st.markdown(f'{card_open("Portafolio vs S&P 500")}', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({
            "Métrica": ["Retorno", "Volatilidad", "Sharpe", f"VaR {int(confianza*100)}%"],
            "Portafolio": [pct(sim["retorno_anual"]), pct(sim["vol_anual"]), num(sim["sharpe"]), pct(sim["var_anual"])],
            "S&P 500": [pct(bm["retorno_anual"]), pct(bm["vol_anual"]), num(bm["sharpe"]), pct(bm["var"])],
        }), hide_index=True, use_container_width=True)
        st.markdown(card_close(), unsafe_allow_html=True)

    st.markdown(f'{card_open("Comparador de perfiles")}', unsafe_allow_html=True)
    sims_cmp = {
        p: simular(capital=capital, horizonte_meses=int(horizonte), perfil=p,
                   confianza=confianza, n_activos=int(n_activos), moneda=moneda)
        for p in ("Conservador", "Máx. Sharpe", "Agresivo")
    }
    st.plotly_chart(fig_comparador(sims_cmp), use_container_width=True, key="plotly_comparador")
    st.dataframe(pd.DataFrame([
        {
            "Perfil": p,
            "Retorno": pct(s["retorno_anual"]),
            "Vol": pct(s["vol_anual"]),
            "Sharpe": num(s["sharpe"]),
            "VaR": pct(s["var_anual"]),
            "Ganancia": money(s["ganancia"], moneda),
            "Estado": estado_semaforo(s["criterios"])[1],
        }
        for p, s in sims_cmp.items()
    ]), hide_index=True, use_container_width=True)
    st.markdown(card_close(), unsafe_allow_html=True)

# -- CARTERA --
elif pagina == "Cartera":
    st.markdown('<p class="kicker">Reporte de composición</p>', unsafe_allow_html=True)
    st.caption(f"{money(sim['capital_m'], moneda)} · {n_activos} activos · cinco clases")
    left, right = st.columns([1.35, 1])
    with left:
        st.markdown(f'{card_open("Posiciones del portafolio")}', unsafe_allow_html=True)
        tabla = sim["pesos"].copy()
        tabla["Peso %"] = (tabla["Peso"] * 100).round(2)
        tabla["Capital"] = tabla["Capital"].round(0)
        st.dataframe(tabla[["Ticker", "Clase de Activo", "Peso %", "Capital"]],
                     hide_index=True, use_container_width=True,
                     height=min(520, 38 * len(tabla) + 40))
        st.plotly_chart(fig_pesos(sim["pesos"]), use_container_width=True, key="plotly_pesos_cartera")
        st.markdown(card_close(), unsafe_allow_html=True)
    with right:
        st.markdown(f'{card_open("Diversificación por clase")}', unsafe_allow_html=True)
        st.plotly_chart(fig_clases(sim["clases"]), use_container_width=True, key="plotly_clases")
        st.metric("Ratio de diversificación", f"{sim['diversificacion']:.2f}")
        ticker_sel = st.selectbox("Explorar rol", sim["pesos"]["Ticker"].tolist())
        row = sim["pesos"].loc[sim["pesos"]["Ticker"] == ticker_sel].iloc[0]
        rol = ROLES_ACTIVO.get(ticker_sel, "Parte de la selección diversificada del mandato.")
        st.markdown(f"**{ticker_sel}** · {row['Clase de Activo']}\n\n"
                    f"- Peso **{pct(row['Peso'])}** · {money(row['Capital'], moneda)}\n- {rol}")
        st.markdown(card_close(), unsafe_allow_html=True)
    if "distribucion" in graficos:
        st.image(str(graficos["distribucion"]), caption="Referencia Colab", use_container_width=True)

# -- RIESGO --─
elif pagina == "Riesgo":
    st.markdown('<p class="kicker">Reporte de riesgo</p>', unsafe_allow_html=True)
    st.caption(f"{money(sim['capital_m'], moneda)} · {horizonte} m · {int(confianza*100)}%")
    main, side = st.columns([2, 1])
    with main:
        st.markdown(f'{card_open(f"VaR y CVaR · {int(confianza*100)}%")}', unsafe_allow_html=True)
        v1, v2 = st.columns(2)
        v1.metric(f"VaR {int(confianza*100)}%", pct(sim["var_anual"]),
                  delta=f"máx {money(sim['var_soles'], moneda)}", delta_color="inverse")
        v2.metric(f"CVaR {int(confianza*100)}%", pct(sim["cvar_anual"]),
                  delta=f"cola {money(sim['cvar_soles'], moneda)}", delta_color="inverse")
        f1, f2, f3 = st.columns(3)
        f1.metric("Favorable", money(sim["favorable"], moneda))
        f2.metric("Esperado", money(sim["esperado"], moneda))
        f3.metric("Adverso", money(sim["adverso"], moneda))
        st.markdown(card_close(), unsafe_allow_html=True)
        if "bootstrap" in graficos:
            st.image(str(graficos["bootstrap"]), caption="Bootstrap Colab", use_container_width=True)
    with side:
        st.markdown(
            f"""{card_open("Riesgos que gestionamos")}
            <p>⚠ Rentabilidad pasada ≠ futura<br/>◎ Riesgo cambiario PEN/USD<br/>
            ✸ Correlación en crisis<br/>▤ Sesgo ventana 2020–2026</p>{card_close()}
            {card_open("Reglas")}
            <p>🔒 Sin cortos ni apalancamiento<br/>🛡 ≥ 1 activo por clase<br/>
            ▦ Piso 1% · tope 15%</p>{card_close()}""",
            unsafe_allow_html=True,
        )

# -- DESEMPEÑO --
elif pagina == "Desempeño":
    st.markdown('<p class="kicker">Reporte de desempeño</p>', unsafe_allow_html=True)
    left, right = st.columns([1.3, 1])
    with left:
        st.markdown(f'{card_open("Portafolio vs S&P 500")}', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({
            "Métrica": ["Retorno anual", "Volatilidad", "Sharpe",
                        f"VaR {int(confianza*100)}%", f"CVaR {int(confianza*100)}%"],
            "Portafolio": [pct(sim["retorno_anual"]), pct(sim["vol_anual"]), num(sim["sharpe"]),
                           pct(sim["var_anual"]), pct(sim["cvar_anual"])],
            "S&P 500": [pct(bm["retorno_anual"]), pct(bm["vol_anual"]), num(bm["sharpe"]),
                        pct(bm["var"]), pct(bm["cvar"])],
            "Diff": [
                f"{(sim['retorno_anual']-bm['retorno_anual'])*100:+.2f} pp",
                f"{(sim['vol_anual']-bm['vol_anual'])*100:+.2f} pp",
                f"{sim['sharpe']-bm['sharpe']:+.2f}",
                f"{(sim['var_anual']-bm['var'])*100:+.1f} pp",
                f"{(sim['cvar_anual']-bm['cvar'])*100:+.1f} pp",
            ],
        }), hide_index=True, use_container_width=True)
        st.markdown(card_close(), unsafe_allow_html=True)
    with right:
        checks = [
            ("Sharpe ≥ 1.0", crit["sharpe_ok"], num(sim["sharpe"])),
            ("Vol ≤ 15%", crit["vol_ok"], pct(sim["vol_anual"])),
            ("Vs S&P Sharpe", crit["vs_mercado_ok"], f"+{sim['sharpe']-bm['sharpe']:.2f}"),
            ("5 clases", crit["clases_ok"], "ok" if crit["clases_ok"] else "revisar"),
        ]
        items = "".join(f"<p>{'✅' if ok else '❌'} <b>{label}</b> → {val}</p>" for label, ok, val in checks)
        st.markdown(
            f"""{card_open("Criterios de éxito")}{items}
            <span class="{pill_cls}">{etiqueta}</span>{card_close()}""",
            unsafe_allow_html=True,
        )
    if "vs_benchmark" in graficos or "frontera" in graficos:
        g1, g2 = st.columns(2)
        if "vs_benchmark" in graficos:
            g1.image(str(graficos["vs_benchmark"]), use_container_width=True)
        if "frontera" in graficos:
            g2.image(str(graficos["frontera"]), use_container_width=True)

# -- EL ASISTENTE --─
elif pagina == "El asistente":
    st.markdown('<p class="kicker">El asistente</p>', unsafe_allow_html=True)
    col_arch, col_chat = st.columns([1, 1.35])
    with col_arch:
        st.markdown(
            f"""{card_open("Arquitectura del agente")}
            <p>1. Ingesta · 2. Cuant · 3. Selección · 4. Optimizador<br/>
            5. Riesgo · 6. Comité humano</p>
            <p><b>Gobierno</b><br/>• Solo datos del simulador<br/>• Rechaza temas ajenos<br/>
            • No usa LLM · reglas + KPIs vivos</p>{card_close()}""",
            unsafe_allow_html=True,
        )
        with st.expander("Supuestos y parámetros"):
            for k, v in PARAMETROS_GRUPO3.items():
                st.write(f"- **{k}:** {v}")
    with col_chat:
        st.markdown(f'{card_open("Chat del comité")}', unsafe_allow_html=True)
        st.caption(f"{perfil} · {n_activos} activos · {horizonte} m · VaR {int(confianza*100)}%")
        if "chat_msgs" not in st.session_state:
            st.session_state.chat_msgs = [{
                "role": "assistant",
                "content": (
                    "Soy el asistente del portafolio Grupo 3. "
                    "Pregúntame por empresas, riesgo, Sharpe o elegibilidad."
                ),
            }]
        cols = st.columns(2)
        for i, sug in enumerate(PREGUNTAS_SUGERIDAS):
            if cols[i % 2].button(sug, key=f"sug_{i}", use_container_width=True):
                st.session_state.chat_msgs.append({"role": "user", "content": sug})
                st.session_state.chat_msgs.append({"role": "assistant", "content": responder(sug, sim)})
                st.rerun()
        for msg in st.session_state.chat_msgs:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        prompt = st.chat_input("Ej: en qué empresas debería invertir, dame 3")
        if prompt:
            st.session_state.chat_msgs.append({"role": "user", "content": prompt})
            st.session_state.chat_msgs.append({"role": "assistant", "content": responder(prompt, sim)})
            st.rerun()
        if st.button("Limpiar chat", type="secondary"):
            st.session_state.chat_msgs = [{
                "role": "assistant",
                "content": "Chat reiniciado. Pregúntame sobre el portafolio.",
            }]
            st.rerun()
        st.markdown(card_close(), unsafe_allow_html=True)

st.markdown(
    '<p class="foot">Simulación académica Grupo 3 · UTEC · Management Analytics & IA. '
    "VaR/CVaR paramétricos (vivos). No constituye recomendación de inversión. "
    "La decisión final es del comité humano.</p>",
    unsafe_allow_html=True,
)
