# -*- coding: utf-8 -*-
"""Portafolio Óptimo · Asistente Cuantitativo (Grupo 3 / UTEC)."""

from __future__ import annotations

import importlib

import agente_chat
import pandas as pd
import streamlit as st

importlib.reload(agente_chat)
from agente_chat import PREGUNTAS_SUGERIDAS, responder
from datos_grupo3 import PARAMETROS_GRUPO3, cargar_resultados
from simulador import simular

st.set_page_config(
    page_title="Portafolio Óptimo · Grupo 3",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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
      .topbar {
        display:flex; justify-content:space-between; align-items:center;
        padding: 4px 2px 14px; border-bottom: 1px solid rgba(90,140,120,0.25);
        margin-bottom: 14px;
      }
      .brand { font-weight: 700; letter-spacing: 0.02em; }
      .brand span { color: #9db5aa; font-weight: 400; font-size: 13px; }
      .uteclog { color:#9db5aa; font-size:12px; }
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


st.markdown(
    '<div class="topbar">'
    '<div class="brand">Portafolio Óptimo <span>· Asistente Cuantitativo · Grupo 3</span></div>'
    '<div class="uteclog">UTEC · Management Analytics & IA</div>'
    "</div>",
    unsafe_allow_html=True,
)

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    capital_sel = st.selectbox("Capital", ["S/ 1 MM", "S/ 2 MM", "S/ 3 MM", "S/ 5 MM"], index=0)
with c2:
    horizonte = st.selectbox("Horizonte 🟢 VIVO", [6, 12, 24, 36], index=1, format_func=lambda m: f"{m} m")
with c3:
    perfil = st.selectbox("Perfil 🟢 VIVO", ["Conservador", "Máx. Sharpe", "Agresivo"], index=1)
with c4:
    conf_lbl = st.selectbox("Confianza VaR 🟢 VIVO", ["99%", "95%"], index=0)
with c5:
    n_activos = st.selectbox("N.º activos 🟢 VIVO", [5, 10, 15, 20], index=3)
with c6:
    moneda = st.selectbox("Moneda 🟢 VIVO", ["S/", "US$"], index=0)

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

try:
    colab = cargar_resultados()
    graficos = colab["graficos"]
except FileNotFoundError:
    colab = None
    graficos = {}

bm = sim["benchmark"]
crit = sim["criterios"]

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

    left, right = st.columns(2)
    with left:
        estado = "ELEGIBLE" if sim["sharpe"] >= 1.0 and sim["vol_anual"] <= 0.15 else "REVISAR"
        st.markdown(
            f"""
            {card_open("Recomendación de referencia")}
            <p>
              Retorno anual <b>{pct(sim['retorno_anual'])}</b> · volatilidad <b>{pct(sim['vol_anual'])}</b>
              · Sharpe <b>{num(sim['sharpe'])}</b>.<br/>
              Diversificación <b>{sim['diversificacion']:.2f}</b>.<br/>
              Perfil <b>{perfil}</b> · {n_activos} activos · {horizonte} meses.
            </p>
            <span class="pill">{estado}</span>
            {card_close()}
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f"""
            {card_open("Qué recibe el comité")}
            <ul>
              <li>Dashboard ejecutivo con KPIs</li>
              <li>Simulador interactivo (capital, horizonte, perfil)</li>
              <li>Reporte de cartera y riesgo</li>
              <li>Chat del agente acotado al mandato</li>
            </ul>
            {card_close()}
            """,
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
        chart_df = sim["pesos"].set_index("Ticker")[["Peso"]]
        try:
            st.bar_chart(chart_df, horizontal=True, color="#e08a6a")
        except TypeError:
            st.bar_chart(chart_df)
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

# ── CARTERA ──────────────────────────────────────────────
with tab_car:
    st.markdown('<p class="kicker">Reporte de composición</p>', unsafe_allow_html=True)
    st.caption(f"{money(sim['capital_m'], moneda)} · {n_activos} activos · cinco clases")
    left, right = st.columns([1.35, 1])
    with left:
        st.markdown(f'{card_open("Posiciones del portafolio")}', unsafe_allow_html=True)
        for _, row in sim["pesos"].iterrows():
            st.markdown(
                f"**{row['Ticker']}** · {row['Clase de Activo']} — "
                f"{pct(row['Peso'])} · {money(row['Capital'], moneda)}"
            )
            st.progress(min(float(row["Peso"]) / 0.15, 1.0))
        st.markdown(card_close(), unsafe_allow_html=True)
    with right:
        st.markdown(f'{card_open("Diversificación por clase")}', unsafe_allow_html=True)
        st.bar_chart(sim["clases"].set_index("Clase de Activo")["Peso"], color="#5dca8e")
        st.metric("Ratio de diversificación", f"{sim['diversificacion']:.2f}")
        st.caption("1.0 = sin beneficio de diversificación.")
        st.markdown(
            """
            **Por qué estos activos**
            - Buen Sharpe individual  
            - Baja correlación relativa  
            - Cobertura defensiva (oro / bonos)  
            - Cinco clases de activo  
            """
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

        prompt = st.chat_input("Ej: en qué empresas debería invertir, dame 3")
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
