# -*- coding: utf-8 -*-
"""Portafolio Óptimo · Asistente Cuantitativo (Grupo 3 / UTEC)."""

from __future__ import annotations

import importlib

import agente_chat
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

importlib.reload(agente_chat)
from agente_chat import PREGUNTAS_SUGERIDAS, ROLES_ACTIVO, responder
from datos_grupo3 import PARAMETROS_GRUPO3, cargar_resultados
from simulador import simular

st.set_page_config(
    page_title="Portafolio Óptimo · Grupo 3",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "tema" not in st.session_state:
    st.session_state.tema = "Oscuro"

# Toggle temprano para aplicar CSS en el mismo render
_tb1, _tb2, _tb3 = st.columns([3.2, 1.1, 2.2])
with _tb1:
    st.markdown(
        '<div class="brand" style="padding-top:6px">Portafolio Óptimo '
        '<span style="font-weight:400;font-size:13px">· Asistente Cuantitativo · Grupo 3</span></div>',
        unsafe_allow_html=True,
    )
with _tb2:
    st.segmented_control(
        "Tema",
        options=["Oscuro", "Claro"],
        key="tema",
        label_visibility="collapsed",
    )
with _tb3:
    st.markdown(
        '<div class="uteclog" style="text-align:right;padding-top:8px">'
        "UTEC · Management Analytics & IA</div>",
        unsafe_allow_html=True,
    )

ES_OSCURO = st.session_state.tema == "Oscuro"

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(
        color="#c8ddd2" if ES_OSCURO else "#2a3d34",
        family="DM Sans, sans-serif",
    ),
    margin=dict(l=10, r=10, t=30, b=10),
)

if ES_OSCURO:
    st.markdown(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');
          html, body, [class*="css"]  { font-family: 'DM Sans', sans-serif; }
          .stApp {
            background:
              radial-gradient(900px 420px at 8% -10%, rgba(45,120,90,0.28), transparent 55%),
              radial-gradient(700px 380px at 100% 0%, rgba(200,110,70,0.12), transparent 50%),
              linear-gradient(180deg, #07110e 0%, #0c1914 45%, #0a1411 100%);
            color: #e8f0ec;
          }
          [data-testid="stHeader"] { background: rgba(7,17,14,0.85); backdrop-filter: blur(8px); }
          h1, h2, h3, .hero h1 { font-family: 'Fraunces', Georgia, serif; }
          .brand { font-weight: 700; letter-spacing: 0.02em; color: #e8f0ec; }
          .brand span { color: #9db5aa; }
          .uteclog { color:#9db5aa; font-size:12px; }
          .disclaimer-bar {
            background: rgba(227,154,120,0.12);
            border: 1px solid rgba(227,154,120,0.35);
            border-radius: 10px; padding: 8px 14px; margin: 8px 0 14px;
            color: #e8c4b0; font-size: 12px; text-align: center;
          }
          .hero {
            background: linear-gradient(135deg, #163f33 0%, #0f2a22 55%, #1d4a3b 100%);
            border: 1px solid rgba(120,180,150,0.25);
            border-radius: 18px; padding: 30px 32px; margin-bottom: 18px;
            box-shadow: 0 18px 40px rgba(0,0,0,0.25);
          }
          .hero h1 { font-size: 1.95rem; margin: 8px 0 12px; color: #f5fbf7; line-height: 1.2; }
          .hero p { color: #b7cfc4; margin: 0; line-height: 1.55; max-width: 820px; }
          .kicker {
            color: #e39a78; letter-spacing: 0.16em; font-size: 11px; font-weight: 700;
            text-transform: uppercase;
          }
          .kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 22px; }
          .kpi {
            background: rgba(0,0,0,0.28); border-radius: 12px; padding: 14px 16px;
            border: 1px solid rgba(255,255,255,0.07);
          }
          .kpi .v { font-size: 1.5rem; font-weight: 700; color: #f6d2c4; }
          .kpi .l { font-size: 12px; color: #9db5aa; margin-top: 4px; }
          .card {
            background: linear-gradient(180deg, #142820 0%, #101f19 100%);
            border: 1px solid rgba(90,140,120,0.35);
            border-radius: 16px; padding: 18px 20px; margin-bottom: 14px;
            box-shadow: 0 10px 28px rgba(0,0,0,0.18);
            height: 100%;
          }
          .card h4 { margin: 0 0 10px; color: #f0f7f3; font-size: 1.05rem; }
          .card p, .card li { color: #b7cfc4; font-size: 0.95rem; }
          .pill {
            display:inline-block; padding: 4px 10px; border-radius: 999px;
            background: rgba(93,202,142,0.15); color:#8fe0b0; font-size: 12px;
            border: 1px solid rgba(93,202,142,0.35); margin-right: 6px;
          }
          .pill-amber {
            background: rgba(230,180,80,0.15); color:#f0d080;
            border: 1px solid rgba(230,180,80,0.4);
          }
          .pill-red {
            background: rgba(220,90,90,0.15); color:#f0a0a0;
            border: 1px solid rgba(220,90,90,0.4);
          }
          .semaforo {
            text-align: center; padding: 22px 16px; border-radius: 16px;
            border: 1px solid rgba(90,140,120,0.35);
            background: linear-gradient(180deg, #142820 0%, #101f19 100%);
          }
          .semaforo .luz {
            width: 72px; height: 72px; border-radius: 50%; margin: 0 auto 12px;
            box-shadow: 0 0 28px currentColor;
          }
          .semaforo .luz.verde { background: #3dcf7a; color: #3dcf7a; }
          .semaforo .luz.ambar { background: #e6b450; color: #e6b450; }
          .semaforo .luz.rojo { background: #e05555; color: #e05555; }
          .semaforo .estado { font-size: 1.35rem; font-weight: 700; color: #f0f7f3;
                              font-family: 'Fraunces', Georgia, serif; }
          .semaforo .sub { color: #9db5aa; font-size: 13px; margin-top: 6px; }
          .vivo {
            display: inline-block; background: #1f6b4a; color: #d8ffe9;
            font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 999px;
            margin-left: 6px; vertical-align: middle;
          }
          .foot { color: #7f968c; font-size: 12px; margin-top: 28px; padding-top: 12px;
                  border-top: 1px solid rgba(90,140,120,0.2); }
          div[data-testid="stMetricValue"] { color: #f6d2c4 !important; }
          div[data-testid="stMetricLabel"] { color: #9db5aa !important; }
          [data-testid="stHorizontalBlock"] > div { align-items: stretch; }
          [data-testid="stChatMessage"] {
            background: linear-gradient(180deg, #142820 0%, #101f19 100%) !important;
            border: 1px solid rgba(90,140,120,0.35) !important;
            border-radius: 14px !important; padding: 10px 14px !important;
            margin-bottom: 8px !important;
          }
          /* Widgets Streamlit (config light) → oscurecer en modo Oscuro */
          [data-testid="stMarkdownContainer"] p,
          [data-testid="stCaptionContainer"],
          [data-testid="stWidgetLabel"] *,
          [data-testid="stTabs"] button p {
            color: #e8f0ec !important;
          }
          [data-testid="stExpander"] {
            background: #142820 !important;
            border: 1px solid rgba(90,140,120,0.35) !important;
            border-radius: 12px !important;
          }
          /* Cabecera del expander: evitar blanco-sobre-blanco del tema light */
          [data-testid="stExpander"] details > summary {
            background: #1a3328 !important;
            background-color: #1a3328 !important;
            background-image: none !important;
            color: #f5fbf7 !important;
            border-radius: 12px 12px 0 0 !important;
          }
          [data-testid="stExpander"] details > summary *,
          [data-testid="stExpander"] details > summary p,
          [data-testid="stExpander"] details > summary span,
          [data-testid="stExpander"] details > summary [data-testid="stMarkdownContainer"],
          [data-testid="stExpander"] details > summary [data-testid="stMarkdownContainer"] p {
            color: #f5fbf7 !important;
            background: transparent !important;
          }
          [data-testid="stExpander"] details > summary svg {
            fill: #f5fbf7 !important;
            stroke: #f5fbf7 !important;
          }
          [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
            background-color: #142820 !important;
            color: #e8f0ec !important;
          }
          [data-baseweb="select"] > div {
            background-color: #0f1f19 !important;
            color: #e8f0ec !important;
            border-color: rgba(90,140,120,0.4) !important;
          }
          [data-baseweb="select"] span { color: #e8f0ec !important; }
          .stDownloadButton button,
          [data-testid="stDownloadButton"] button,
          [data-testid="stBaseButton-secondary"],
          [data-testid="stBaseButton-secondary"] p {
            background-color: #1a3328 !important;
            color: #e8f0ec !important;
            border: 1px solid rgba(90,140,120,0.45) !important;
          }
          @media (max-width: 900px) {
            .kpi-row { grid-template-columns: 1fr 1fr; }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');
          html, body, [class*="css"]  { font-family: 'DM Sans', sans-serif; }
          .stApp {
            background:
              radial-gradient(900px 420px at 0% -10%, rgba(45,120,90,0.14), transparent 55%),
              radial-gradient(700px 380px at 100% 0%, rgba(200,110,70,0.08), transparent 50%),
              linear-gradient(180deg, #f5f8f6 0%, #eef3f0 50%, #e7eeea 100%) !important;
            color: #1a2e26 !important;
          }
          /* Texto general Streamlit (sin tocar .hero / .kpi) */
          [data-testid="stMarkdownContainer"]:not(.hero *),
          [data-testid="stCaptionContainer"],
          [data-testid="stWidgetLabel"] p,
          [data-testid="stWidgetLabel"] label,
          [data-testid="stExpander"] summary span,
          [data-testid="stTabs"] button p,
          .stMarkdown p, .stCaption, label[data-testid="stWidgetLabel"] {
            color: #1a2e26 !important;
          }
          [data-testid="stHeader"] { background: rgba(245,248,246,0.95) !important; }
          h1, h2, h3 { font-family: 'Fraunces', Georgia, serif; color: #132820 !important; }
          .brand { font-weight: 700; color: #132820 !important; }
          .brand span { color: #5a7368 !important; font-weight: 400; font-size: 13px; }
          .uteclog { color:#5a7368 !important; font-size:12px; }
          .disclaimer-bar {
            background: rgba(180,90,50,0.08);
            border: 1px solid rgba(180,90,50,0.28);
            border-radius: 10px; padding: 8px 14px; margin: 8px 0 14px;
            color: #8a4a32 !important; font-size: 12px; text-align: center;
          }
          .hero {
            background: linear-gradient(135deg, #1f5c48 0%, #164536 55%, #247058 100%);
            border: 1px solid rgba(30,90,70,0.25);
            border-radius: 18px; padding: 30px 32px; margin-bottom: 18px;
            box-shadow: 0 14px 32px rgba(20,60,45,0.12);
          }
          .hero .kicker { color: #f0b090 !important; letter-spacing: 0.16em; font-size: 11px;
                          font-weight: 700; text-transform: uppercase; }
          .hero h1 { font-size: 1.95rem; margin: 8px 0 12px; color: #f5fbf7 !important; line-height: 1.2;
                     font-family: 'Fraunces', Georgia, serif; }
          .hero p { color: #d5ebe0 !important; margin: 0; line-height: 1.55; max-width: 820px; }
          .hero strong { color: #ffffff !important; }
          .kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 22px; }
          .kpi {
            background: rgba(0,0,0,0.22); border-radius: 12px; padding: 14px 16px;
            border: 1px solid rgba(255,255,255,0.14);
          }
          .kpi .v { font-size: 1.5rem; font-weight: 700; color: #ffe4d4 !important; }
          .kpi .l { font-size: 12px; color: #d7ebe1 !important; margin-top: 4px; }
          .kicker {
            color: #c45c3a !important; letter-spacing: 0.16em; font-size: 11px; font-weight: 700;
            text-transform: uppercase;
          }
          .card {
            background: #ffffff;
            border: 1px solid rgba(40,90,70,0.18);
            border-radius: 16px; padding: 18px 20px; margin-bottom: 14px;
            box-shadow: 0 8px 22px rgba(20,50,40,0.06);
            height: 100%;
          }
          .card h4 { margin: 0 0 10px; color: #132820 !important; font-size: 1.05rem; }
          .card p, .card li, .card b, .card strong { color: #2d4038 !important; font-size: 0.95rem; }
          .pill {
            display:inline-block; padding: 4px 10px; border-radius: 999px;
            background: rgba(40,140,90,0.12); color:#1a7a4c !important; font-size: 12px;
            border: 1px solid rgba(40,140,90,0.3); margin-right: 6px;
          }
          .pill-amber { background: rgba(200,140,40,0.12); color:#9a6a10 !important;
                        border: 1px solid rgba(200,140,40,0.35); }
          .pill-red { background: rgba(200,60,60,0.1); color:#b03030 !important;
                      border: 1px solid rgba(200,60,60,0.3); }
          .semaforo {
            text-align: center; padding: 22px 16px; border-radius: 16px;
            border: 1px solid rgba(40,90,70,0.18); background: #ffffff;
          }
          .semaforo .luz {
            width: 72px; height: 72px; border-radius: 50%; margin: 0 auto 12px;
            box-shadow: 0 0 22px currentColor;
          }
          .semaforo .luz.verde { background: #2bb86a; color: #2bb86a; }
          .semaforo .luz.ambar { background: #d4a017; color: #d4a017; }
          .semaforo .luz.rojo { background: #d04545; color: #d04545; }
          .semaforo .estado { font-size: 1.35rem; font-weight: 700; color: #132820 !important;
                              font-family: 'Fraunces', Georgia, serif; }
          .semaforo .sub { color: #5a7368 !important; font-size: 13px; margin-top: 6px; }
          .vivo {
            display: inline-block; background: #1f6b4a; color: #d8ffe9 !important;
            font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 999px;
            margin-left: 6px; vertical-align: middle;
          }
          .foot { color: #6a8076 !important; font-size: 12px; margin-top: 28px; padding-top: 12px;
                  border-top: 1px solid rgba(40,90,70,0.15); }
          div[data-testid="stMetricValue"] { color: #b85a38 !important; }
          div[data-testid="stMetricLabel"] { color: #5a7368 !important; }
          [data-testid="stHorizontalBlock"] > div { align-items: stretch; }

          /* Expander de parámetros: fondo claro + labels oscuros */
          [data-testid="stExpander"] {
            background: #ffffff !important;
            border: 1px solid rgba(40,90,70,0.18) !important;
            border-radius: 12px !important;
          }
          [data-testid="stExpander"] details,
          [data-testid="stExpander"] summary,
          [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
            background: #ffffff !important;
            color: #1a2e26 !important;
          }
          [data-testid="stExpander"] label,
          [data-testid="stExpander"] [data-testid="stWidgetLabel"] *,
          [data-testid="stExpander"] p {
            color: #1a2e26 !important;
          }
          [data-baseweb="select"] > div {
            background-color: #f4f7f5 !important;
            border-color: rgba(40,90,70,0.25) !important;
            color: #1a2e26 !important;
          }
          [data-baseweb="select"] span { color: #1a2e26 !important; }
          ul[role="listbox"], ul[role="listbox"] li {
            background-color: #ffffff !important;
            color: #1a2e26 !important;
          }

          /* Botones download / secondary: fondo claro, texto oscuro */
          .stDownloadButton button,
          [data-testid="stDownloadButton"] button,
          [data-testid="stBaseButton-secondary"],
          button[kind="secondary"],
          [data-testid="stBaseButton-secondary"] p,
          .stDownloadButton button p,
          [data-testid="stDownloadButton"] button p {
            background-color: #e8f2ec !important;
            background-image: none !important;
            color: #132820 !important;
            border: 1px solid rgba(40,90,70,0.35) !important;
          }
          [data-testid="stBaseButton-primary"],
          button[kind="primary"],
          [data-testid="stBaseButton-primary"] p {
            background-color: #1f6b4a !important;
            color: #ffffff !important;
            border: none !important;
          }

          [data-testid="stChatMessage"] {
            background: #ffffff !important;
            border: 1px solid rgba(40,90,70,0.18) !important;
            border-radius: 14px !important; padding: 10px 14px !important;
            margin-bottom: 8px !important;
          }
          [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
          [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li,
          [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] span {
            color: #1a2e26 !important;
          }
          [data-testid="stDataFrame"] { color: #1a2e26 !important; }
          [data-testid="stTabs"] button[aria-selected="true"] p { color: #1a7a4c !important; }
          [data-testid="stSegmentedControl"] label,
          [data-testid="stSegmentedControl"] button { color: #1a2e26 !important; }
          @media (max-width: 900px) {
            .kpi-row { grid-template-columns: 1fr 1fr; }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )



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
    """Devuelve (clase_css, etiqueta, detalle)."""
    n_ok = sum(1 for k in ("sharpe_ok", "vol_ok", "vs_mercado_ok") if crit[k])
    if n_ok == 3 and crit.get("clases_ok", True):
        return "verde", "ELEGIBLE", "Cumple Sharpe, volatilidad y supera al mercado."
    if n_ok == 0:
        return "rojo", "NO ELEGIBLE", "No cumple los criterios mínimos del mandato."
    return "ambar", "REVISAR", "Cumple parcialmente — el comité debe evaluar."


def fig_pesos(pesos: pd.DataFrame, moneda: str):
    df = pesos.copy()
    df["Peso %"] = df["Peso"] * 100
    df["Label"] = df.apply(
        lambda r: f"{r['Ticker']}  {r['Peso']*100:.1f}%", axis=1
    )
    fig = px.bar(
        df.sort_values("Peso"),
        x="Peso %",
        y="Ticker",
        color="Clase de Activo",
        orientation="h",
        hover_data={"Capital": ":,.0f", "Peso %": ":.2f", "Ticker": False},
        color_discrete_sequence=["#e08a6a", "#5dca8e", "#7eb6d9", "#c9a227", "#a78bfa"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=max(320, 28 * len(df)), showlegend=True,
                      legend=dict(orientation="h", y=-0.15))
    grid = "rgba(0,0,0,0.08)" if not ES_OSCURO else "rgba(255,255,255,0.06)"
    fig.update_xaxes(title="Peso (%)", gridcolor=grid)
    fig.update_yaxes(title="", gridcolor=grid)
    return fig


def fig_clases(clases: pd.DataFrame):
    fig = px.pie(
        clases,
        values="Peso",
        names="Clase de Activo",
        hole=0.45,
        color_discrete_sequence=["#5dca8e", "#e08a6a", "#7eb6d9", "#c9a227", "#a78bfa"],
    )
    text_c = "#1a2e26" if not ES_OSCURO else "#e8f0ec"
    fig.update_traces(textposition="inside", textinfo="percent+label",
                      textfont_size=11, textfont_color=text_c)
    fig.update_layout(**PLOTLY_LAYOUT, height=360, showlegend=False)
    return fig


def fig_comparador(sims: dict[str, dict]):
    metricas = ["Retorno %", "Volatilidad %", "Sharpe", "VaR %"]
    fig = go.Figure()
    colors = {"Conservador": "#7eb6d9", "Máx. Sharpe": "#5dca8e", "Agresivo": "#e08a6a"}
    for nombre, s in sims.items():
        vals = [
            s["retorno_anual"] * 100,
            s["vol_anual"] * 100,
            s["sharpe"],
            s["var_anual"] * 100,
        ]
        fig.add_trace(go.Bar(
            name=nombre,
            x=metricas,
            y=vals,
            marker_color=colors.get(nombre, "#9db5aa"),
            text=[f"{v:.2f}" for v in vals],
            textposition="outside",
            textfont=dict(color="#1a2e26" if not ES_OSCURO else "#e8f0ec"),
        ))
    fig.update_layout(**PLOTLY_LAYOUT, barmode="group", height=380,
                      legend=dict(orientation="h", y=1.12))
    grid = "rgba(0,0,0,0.08)" if not ES_OSCURO else "rgba(255,255,255,0.06)"
    fig.update_yaxes(gridcolor=grid)
    return fig


def informe_txt(sim: dict) -> str:
    bm = sim["benchmark"]
    crit = sim["criterios"]
    luz, etiqueta, detalle = estado_semaforo(crit)
    mon = sim["moneda"]
    lineas = [
        "INFORME DE COMITÉ · Portafolio Óptimo Grupo 3 · UTEC",
        "=" * 56,
        f"Estado: {etiqueta} ({detalle})",
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
        f"  Diversificación: {sim['diversificacion']:.2f}",
        "",
        "Criterios",
        f"  Sharpe ≥ 1.0: {'OK' if crit['sharpe_ok'] else 'NO'}",
        f"  Vol ≤ 15%:    {'OK' if crit['vol_ok'] else 'NO'}",
        f"  Vs S&P:       {'OK' if crit['vs_mercado_ok'] else 'NO'}",
        f"  5 clases:     {'OK' if crit['clases_ok'] else 'NO'}",
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
        "VaR/CVaR del simulador son paramétricos. Decisión final: comité humano.",
    ]
    return "\n".join(lineas)


st.markdown(
    '<div class="disclaimer-bar">'
    "Simulación académica Grupo 3 · UTEC — no constituye recomendación de inversión. "
    "La decisión final es del comité humano."
    "</div>",
    unsafe_allow_html=True,
)

with st.expander("Parámetros del simulador 🟢 VIVO", expanded=True):
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        capital_sel = st.selectbox("Capital", ["S/ 1 MM", "S/ 2 MM", "S/ 3 MM", "S/ 5 MM"], index=0)
    with c2:
        horizonte = st.selectbox("Horizonte", [6, 12, 24, 36], index=1, format_func=lambda m: f"{m} m")
    with c3:
        perfil = st.selectbox("Perfil", ["Conservador", "Máx. Sharpe", "Agresivo"], index=1)
    with c4:
        conf_lbl = st.selectbox("Confianza VaR", ["99%", "95%"], index=0)
    with c5:
        n_activos = st.selectbox("N.º activos", [5, 10, 15, 20], index=3)
    with c6:
        moneda = st.selectbox("Moneda", ["S/", "US$"], index=0)

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

# Aviso si cambian los controles VIVO (chat)
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
                f"{horizonte} m · VaR {int(confianza*100)}% · {money(sim['capital_m'], moneda)}. "
                "Las próximas respuestas usarán estos números."
            ),
        })

try:
    colab = cargar_resultados()
    graficos = colab["graficos"]
except FileNotFoundError:
    colab = None
    graficos = {}

bm = sim["benchmark"]
crit = sim["criterios"]
luz, etiqueta, detalle_sem = estado_semaforo(crit)
pill_cls = {"verde": "pill", "ambar": "pill pill-amber", "rojo": "pill pill-red"}[luz]

tab_res, tab_sim, tab_car, tab_riesgo, tab_des, tab_asist = st.tabs(
    ["Resumen", "Simulador", "Cartera", "Riesgo", "Desempeño", "El asistente"]
)

# ── RESUMEN ──────────────────────────────────────────────
with tab_res:
    st.markdown(
        f"""
        <div class="hero">
          <div class="kicker">Gestión cuantitativa de patrimonio</div>
          <h1>Su capital, invertido con criterio, disciplina y evidencia.</h1>
          <p>
            El asistente construye un portafolio diversificado, maximiza retorno por unidad de riesgo,
            cuantifica la pérdida potencial y entrega una recomendación trazable.
            <strong>La decisión final siempre es humana.</strong>
          </p>
          <div class="kpi-row">
            <div class="kpi"><div class="v">{num(sim['sharpe'])}</div><div class="l">Ratio de Sharpe (vs {num(bm['sharpe'])} mercado)</div></div>
            <div class="kpi"><div class="v">{pct(sim['retorno_anual'])}</div><div class="l">Retorno esperado anual</div></div>
            <div class="kpi"><div class="v">{money(sim['ganancia'], moneda)}</div><div class="l">Ganancia esperada ({sim['horizonte_meses']} m)</div></div>
            <div class="kpi"><div class="v">{pct(sim['var'])}</div><div class="l">VaR {int(confianza*100)}% · {sim['horizonte_meses']} m</div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    s1, s2, s3 = st.columns([1, 1.4, 1.2])
    with s1:
        st.markdown(
            f"""
            <div class="semaforo">
              <div class="luz {luz}"></div>
              <div class="estado">{etiqueta}</div>
              <div class="sub">{detalle_sem}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            f"""
            {card_open("Recomendación de referencia")}
            <p>
              Retorno anual <b>{pct(sim['retorno_anual'])}</b> · volatilidad <b>{pct(sim['vol_anual'])}</b>
              · Sharpe <b>{num(sim['sharpe'])}</b>.<br/>
              Diversificación <b>{sim['diversificacion']:.2f}</b>.<br/>
              Perfil <b>{perfil}</b> · {n_activos} activos · {horizonte} meses.
            </p>
            <span class="{pill_cls}">{etiqueta}</span>
            {card_close()}
            """,
            unsafe_allow_html=True,
        )
    with s3:
        st.markdown(f'{card_open("Exportar para el comité")}', unsafe_allow_html=True)
        csv_pesos = sim["pesos"].copy()
        csv_pesos["Peso"] = csv_pesos["Peso"].map(lambda x: round(float(x), 6))
        st.download_button(
            "Descargar cartera CSV",
            data=csv_pesos.to_csv(index=False).encode("utf-8"),
            file_name=f"cartera_grupo3_{perfil.replace(' ', '_').lower()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.download_button(
            "Descargar informe TXT",
            data=informe_txt(sim).encode("utf-8"),
            file_name="informe_comite_grupo3.txt",
            mime="text/plain",
            use_container_width=True,
        )
        st.caption("CSV de pesos + informe ejecutivo listo para pegar.")
        st.markdown(card_close(), unsafe_allow_html=True)

    a, b, c, d = st.columns(4)
    for col, title, body in [
        (a, "Mejor retorno ajustado", "Sharpe del portafolio frente al S&P 500."),
        (b, "Menor riesgo extremo", "VaR y CVaR claramente bajo el mercado."),
        (c, "Trazabilidad total", "Cada peso responde a reglas del mandato."),
        (d, "Disciplina", "Tope 15%, piso 1%, cinco clases de activo."),
    ]:
        with col:
            st.markdown(
                f'{card_open(title)}<p>{body}</p>{card_close()}',
                unsafe_allow_html=True,
            )

# ── SIMULADOR ────────────────────────────────────────────
with tab_sim:
    st.markdown(
        '<p class="kicker">Simulador <span class="vivo">VIVO</span></p>',
        unsafe_allow_html=True,
    )
    st.caption("Recalcula sin internet sobre métricas del modelo Grupo 3.")
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Capital bajo gestión", money(sim["capital_m"], moneda))
    k2.metric("Retorno esperado", pct(sim["retorno_anual"]))
    k3.metric("Volatilidad", pct(sim["vol_anual"]))
    k4.metric("Sharpe", num(sim["sharpe"]), delta=f"vs {num(bm['sharpe'])} mercado")
    k5.metric(
        f"VaR {int(confianza*100)}% · {horizonte}m",
        pct(sim["var"]),
        delta=money(-sim["var_soles"], moneda),
        delta_color="inverse",
    )
    k6.metric("Ganancia esperada", money(sim["ganancia"], moneda))

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown(f'{card_open("Asignación de capital")}', unsafe_allow_html=True)
        st.caption("Pesos vivos · piso 1% · tope 15% · sin cortos")
        st.plotly_chart(fig_pesos(sim["pesos"], moneda), use_container_width=True, key="plotly_pesos_sim")
        st.markdown(card_close(), unsafe_allow_html=True)
    with right:
        st.markdown(f'{card_open("Escenarios a " + str(horizonte) + " meses")}', unsafe_allow_html=True)
        e1, e2, e3 = st.columns(3)
        e1.metric("Favorable", money(sim["favorable"], moneda))
        e2.metric("Esperado", money(sim["esperado"], moneda))
        e3.metric("Adverso", money(sim["adverso"], moneda))
        st.markdown(card_close(), unsafe_allow_html=True)
        st.markdown(f'{card_open("Portafolio vs S&P 500")}', unsafe_allow_html=True)
        comp = pd.DataFrame({
            "Métrica": ["Retorno", "Volatilidad", "Sharpe", f"VaR {int(confianza*100)}%"],
            "Portafolio": [pct(sim["retorno_anual"]), pct(sim["vol_anual"]),
                           num(sim["sharpe"]), pct(sim["var_anual"])],
            "S&P 500": [pct(bm["retorno_anual"]), pct(bm["vol_anual"]),
                        num(bm["sharpe"]), pct(bm["var"])],
        })
        st.dataframe(comp, hide_index=True, use_container_width=True)
        st.markdown(card_close(), unsafe_allow_html=True)

    st.markdown(f'{card_open("Comparador de perfiles")}', unsafe_allow_html=True)
    st.caption("Misma capital / horizonte / N activos — solo cambia el perfil de riesgo.")
    sims_cmp = {
        p: simular(
            capital=capital,
            horizonte_meses=int(horizonte),
            perfil=p,
            confianza=confianza,
            n_activos=int(n_activos),
            moneda=moneda,
        )
        for p in ("Conservador", "Máx. Sharpe", "Agresivo")
    }
    st.plotly_chart(fig_comparador(sims_cmp), use_container_width=True, key="plotly_comparador")
    cmp_df = pd.DataFrame([
        {
            "Perfil": p,
            "Retorno": pct(s["retorno_anual"]),
            "Volatilidad": pct(s["vol_anual"]),
            "Sharpe": num(s["sharpe"]),
            f"VaR {int(confianza*100)}%": pct(s["var_anual"]),
            "Ganancia": money(s["ganancia"], moneda),
            "Estado": estado_semaforo(s["criterios"])[1],
        }
        for p, s in sims_cmp.items()
    ])
    st.dataframe(cmp_df, hide_index=True, use_container_width=True)
    st.markdown(card_close(), unsafe_allow_html=True)

# ── CARTERA ──────────────────────────────────────────────
with tab_car:
    st.markdown('<p class="kicker">Reporte de composición</p>', unsafe_allow_html=True)
    st.caption(f"{money(sim['capital_m'], moneda)} · {n_activos} activos · cinco clases")
    left, right = st.columns([1.35, 1])
    with left:
        st.markdown(f'{card_open("Posiciones del portafolio")}', unsafe_allow_html=True)
        tabla = sim["pesos"].copy()
        tabla["Peso %"] = (tabla["Peso"] * 100).round(2)
        tabla["Capital"] = tabla["Capital"].round(0)
        st.dataframe(
            tabla[["Ticker", "Clase de Activo", "Peso %", "Capital"]],
            hide_index=True,
            use_container_width=True,
            height=min(520, 38 * len(tabla) + 40),
        )
        st.plotly_chart(fig_pesos(sim["pesos"], moneda), use_container_width=True, key="plotly_pesos_cartera")
        st.markdown(card_close(), unsafe_allow_html=True)
    with right:
        st.markdown(f'{card_open("Diversificación por clase")}', unsafe_allow_html=True)
        st.plotly_chart(fig_clases(sim["clases"]), use_container_width=True, key="plotly_clases")
        st.metric("Ratio de diversificación", f"{sim['diversificacion']:.2f}")
        st.caption("1.0 = sin beneficio de diversificación.")
        st.markdown("**¿Por qué este activo?**")
        ticker_sel = st.selectbox(
            "Explorar rol en el mandato",
            sim["pesos"]["Ticker"].tolist(),
            label_visibility="collapsed",
        )
        row = sim["pesos"].loc[sim["pesos"]["Ticker"] == ticker_sel].iloc[0]
        rol = ROLES_ACTIVO.get(
            ticker_sel,
            "Forma parte de la selección diversificada del mandato.",
        )
        st.markdown(
            f"**{ticker_sel}** · {row['Clase de Activo']}\n\n"
            f"- Peso **{pct(row['Peso'])}** · {money(row['Capital'], moneda)}\n"
            f"- {rol}"
        )
        st.markdown(card_close(), unsafe_allow_html=True)
    if "distribucion" in graficos:
        st.image(str(graficos["distribucion"]), caption="Referencia Colab", use_container_width=True)

# ── RIESGO ───────────────────────────────────────────────
with tab_riesgo:
    st.markdown('<p class="kicker">Reporte de riesgo</p>', unsafe_allow_html=True)
    st.caption(
        f"{money(sim['capital_m'], moneda)} · {horizonte} m · confianza {int(confianza*100)}% "
        "(paramétrico en vivo; bootstrap en Colab)."
    )
    main, side = st.columns([2, 1])
    with main:
        st.markdown(f'{card_open(f"VaR y pérdida en cola · {int(confianza*100)}%")}', unsafe_allow_html=True)
        v1, v2 = st.columns(2)
        v1.metric(
            f"VaR {int(confianza*100)}% anual",
            pct(sim["var_anual"]),
            delta=f"pérdida máx {money(sim['var_soles'], moneda)}",
            delta_color="inverse",
        )
        v1.caption(f"S&P 500: {pct(bm['var'])} ({money(bm['var_soles'], moneda)})")
        v2.metric(
            f"CVaR {int(confianza*100)}% anual",
            pct(sim["cvar_anual"]),
            delta=f"peor cola {money(sim['cvar_soles'], moneda)}",
            delta_color="inverse",
        )
        v2.caption(f"S&P 500: {pct(bm['cvar'])} ({money(bm['cvar_soles'], moneda)})")
        f1, f2, f3 = st.columns(3)
        f1.metric("Favorable (+1σ)", money(sim["favorable"], moneda))
        f2.metric("Esperado", money(sim["esperado"], moneda))
        f3.metric("Adverso (−1σ)", money(sim["adverso"], moneda))
        st.markdown(card_close(), unsafe_allow_html=True)
        if "bootstrap" in graficos:
            st.image(str(graficos["bootstrap"]), caption="Bootstrap Colab", use_container_width=True)
    with side:
        st.markdown(
            f"""
            {card_open("Riesgos que gestionamos")}
            <p>⚠ Rentabilidad pasada ≠ futura<br/>
            ◎ Riesgo cambiario PEN/USD<br/>
            ✸ Correlación en crisis<br/>
            ▤ Sesgo por ventana 2020–2026</p>
            {card_close()}
            {card_open("Reglas y restricciones")}
            <p>🔒 Sin corto ni apalancamiento<br/>
            🛡 ≥ 1 activo por clase<br/>
            ▦ Piso 1% · tope 15%<br/>
            📅 Ventana histórica 6 años</p>
            {card_close()}
            """,
            unsafe_allow_html=True,
        )

# ── DESEMPEÑO ────────────────────────────────────────────
with tab_des:
    st.markdown('<p class="kicker">Reporte de desempeño</p>', unsafe_allow_html=True)
    st.caption("Métricas anuales del modelo · ventana 2020–2026.")
    left, right = st.columns([1.3, 1])
    with left:
        st.markdown(f'{card_open("Portafolio vs S&P 500")}', unsafe_allow_html=True)
        tabla = pd.DataFrame({
            "Métrica": ["Retorno anual", "Volatilidad anual", "Ratio de Sharpe",
                        f"VaR {int(confianza*100)}% anual", f"CVaR {int(confianza*100)}% anual"],
            "Portafolio": [pct(sim["retorno_anual"]), pct(sim["vol_anual"]), num(sim["sharpe"]),
                           pct(sim["var_anual"]), pct(sim["cvar_anual"])],
            "S&P 500": [pct(bm["retorno_anual"]), pct(bm["vol_anual"]), num(bm["sharpe"]),
                        pct(bm["var"]), pct(bm["cvar"])],
            "Diferencia": [
                f"{(sim['retorno_anual']-bm['retorno_anual'])*100:+.2f} pp",
                f"{(sim['vol_anual']-bm['vol_anual'])*100:+.2f} pp",
                f"{sim['sharpe']-bm['sharpe']:+.2f}",
                f"{(sim['var_anual']-bm['var'])*100:+.1f} pp",
                f"{(sim['cvar_anual']-bm['cvar'])*100:+.1f} pp",
            ],
        })
        st.dataframe(tabla, hide_index=True, use_container_width=True)
        st.markdown(card_close(), unsafe_allow_html=True)
    with right:
        checks = [
            ("Sharpe ≥ 1.0", crit["sharpe_ok"], num(sim["sharpe"])),
            ("Volatilidad ≤ 15%", crit["vol_ok"], pct(sim["vol_anual"])),
            ("Superar Sharpe S&P", crit["vs_mercado_ok"], f"+{sim['sharpe']-bm['sharpe']:.2f}"),
            ("Diversificación 5 clases", crit["clases_ok"], "ok" if crit["clases_ok"] else "revisar"),
        ]
        items = "".join(
            f"<p>{'✅' if ok else '❌'} <b>{label}</b> → {val}</p>"
            for label, ok, val in checks
        )
        st.markdown(
            f"""
            {card_open("Criterios de éxito")}
            {items}
            <p>Exceso vs mercado: <b>{(sim['retorno_anual']-bm['retorno_anual'])*100:+.2f} pp</b><br/>
            Diversificación: <b>{sim['diversificacion']:.2f}</b></p>
            <span class="{pill_cls}">{etiqueta}</span>
            {card_close()}
            """,
            unsafe_allow_html=True,
        )
    if "vs_benchmark" in graficos or "frontera" in graficos:
        g1, g2 = st.columns(2)
        if "vs_benchmark" in graficos:
            g1.image(str(graficos["vs_benchmark"]), use_container_width=True)
        if "frontera" in graficos:
            g2.image(str(graficos["frontera"]), use_container_width=True)

# ── EL ASISTENTE ─────────────────────────────────────────
with tab_asist:
    st.markdown('<p class="kicker">El asistente</p>', unsafe_allow_html=True)
    col_arch, col_chat = st.columns([1, 1.35])
    with col_arch:
        st.markdown(
            f"""
            {card_open("Arquitectura del agente")}
            <p>1. Ingesta · 2. Cuant · 3. Selección · 4. Optimizador SLSQP<br/>
            5. Riesgo · 6. Comité humano</p>
            <p><b>Gobierno</b><br/>
            • Solo datos del simulador<br/>
            • Rechaza temas ajenos<br/>
            • Saludos y follow-ups del dominio<br/>
            • No reemplaza al comité<br/>
            • <b>No usa LLM</b>: agente por reglas + KPIs vivos</p>
            {card_close()}
            """,
            unsafe_allow_html=True,
        )
        with st.expander("Supuestos y parámetros"):
            for k, v in PARAMETROS_GRUPO3.items():
                st.write(f"- **{k}:** {v}")

    with col_chat:
        st.markdown(f'{card_open("Chat del comité")}', unsafe_allow_html=True)
        st.caption(
            f"Escenario actual: {perfil} · {n_activos} activos · {horizonte} m · VaR {int(confianza*100)}%"
        )
        if "chat_msgs" not in st.session_state:
            st.session_state.chat_msgs = [{
                "role": "assistant",
                "content": (
                    "Soy el asistente del portafolio Grupo 3. "
                    "Pregúntame por empresas, riesgo, Sharpe, elegibilidad o vs S&P 500. "
                    "Ejemplo: *en qué empresas debería invertir, dame 3*."
                ),
            }]

        st.markdown("**Preguntas sugeridas**")
        cols = st.columns(2)
        for i, sug in enumerate(PREGUNTAS_SUGERIDAS):
            if cols[i % 2].button(sug, key=f"sug_{i}", use_container_width=True):
                st.session_state.chat_msgs.append({"role": "user", "content": sug})
                st.session_state.chat_msgs.append(
                    {"role": "assistant", "content": responder(sug, sim)}
                )
                st.rerun()

        for msg in st.session_state.chat_msgs:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        prompt = st.chat_input("Ej: hola · en qué empresas debería invertir, dame 3")
        if prompt:
            st.session_state.chat_msgs.append({"role": "user", "content": prompt})
            st.session_state.chat_msgs.append(
                {"role": "assistant", "content": responder(prompt, sim)}
            )
            st.rerun()

        if st.button("Limpiar chat", type="secondary"):
            st.session_state.chat_msgs = [{
                "role": "assistant",
                "content": "Chat reiniciado. Pregúntame sobre el portafolio, riesgo o mandato.",
            }]
            st.rerun()
        st.markdown(card_close(), unsafe_allow_html=True)

st.markdown(
    '<p class="foot">Simulación académica Grupo 3 · UTEC. '
    "VaR/CVaR del simulador son paramétricos (vivos). "
    "El informe Colab usa block bootstrap. No constituye recomendación de inversión.</p>",
    unsafe_allow_html=True,
)
