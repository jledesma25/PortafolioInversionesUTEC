# -*- coding: utf-8 -*-
"""Textos de presentación: decisión ejecutiva, glosario y recorrido del comité."""

from __future__ import annotations

GLOSARIO = {
    "Sharpe": (
        "**Ratio de Sharpe** — retorno por unidad de riesgo.\n\n"
        "En lenguaje de comité: *¿cuánto gano por cada punto de volatilidad que asumo?*\n\n"
        "• Sharpe **≥ 1.0** → compensación aceptable según el mandato.\n"
        "• Comparar siempre vs S&P 500.\n\n"
        "No garantiza ganancias futuras; resume eficiencia histórica del modelo."
    ),
    "VaR": (
        "**Value at Risk (VaR)** — pérdida máxima esperada con un nivel de confianza.\n\n"
        "Ejemplo: VaR 99% a 12 meses ≈ *“en el 99% de escenarios, no perderíamos más de X soles”*.\n\n"
        "Es un **límite de referencia** para el comité, no un techo legal ni una promesa."
    ),
    "CVaR": (
        "**Conditional VaR (CVaR)** — pérdida **promedia** cuando ya superamos el VaR.\n\n"
        "Responde: *si entramos en la cola mala del 1%, ¿cuánto perdemos de media?*\n\n"
        "Suele ser mayor que el VaR; útil para medir el **peor escenario sostenido**, no un solo día malo."
    ),
}

PASOS_RECORRIDO = [
    {
        "tab": "Resumen",
        "titulo": "Veredicto del comité",
        "guion": (
            "Con {capital} y perfil **{perfil}**, el semáforo muestra **{etiqueta}**. "
            "Sharpe **{sharpe}** vs mercado **{sharpe_bm}**; retorno esperado **{retorno}**."
        ),
        "tip": "Señala el semáforo, la frase de decisión ejecutiva y los KPIs del hero.",
    },
    {
        "tab": "Simulador",
        "titulo": "Simulador en vivo",
        "guion": (
            "Cambia horizonte o perfil arriba: los KPIs se recalculan **sin internet**. "
            "Muestra el comparador Conservador vs Máx. Sharpe vs Agresivo."
        ),
        "tip": "Abre la pestaña Simulador y mueve un control VIVO (p. ej. 10 activos).",
    },
    {
        "tab": "Cartera",
        "titulo": "Composición y mandato",
        "guion": (
            "Top posiciones: **{top3}**. Cinco clases de activo; tope 15% por ticker. "
            "Elige un activo en el selector para explicar su rol defensivo o de crecimiento."
        ),
        "tip": "Pestaña Cartera → gráfico Plotly + rol de GLD o NVDA.",
    },
    {
        "tab": "Riesgo",
        "titulo": "Riesgo cuantificado",
        "guion": (
            "VaR {conf}% ≈ **{var_soles}**; CVaR ≈ **{cvar_soles}**. "
            "Comparar con S&P: nuestro portafolio concentra menos pérdida extrema."
        ),
        "tip": "Pestaña Riesgo → abre el glosario VaR/CVaR si preguntan.",
    },
    {
        "tab": "El asistente",
        "titulo": "Agente acotado al mandato",
        "guion": (
            "Pregunta demo: *¿El portafolio es elegible?* y *¿En qué empresas debo invertir?* "
            "Luego muestra que rechaza temas ajenos (deportes, clima)."
        ),
        "tip": "Pestaña El asistente → usa las preguntas sugeridas o el botón demo.",
        "chat_demo": "¿El portafolio es elegible?",
    },
]


def _money(x, moneda="S/"):
    if moneda == "US$":
        return f"US$ {x:,.0f}"
    return f"S/ {x:,.0f}"


def _pct(x):
    return f"{x:.2%}"


def _num(x):
    return f"{x:.2f}"


def frase_ejecutiva(sim: dict, crit: dict, luz: str, etiqueta: str, bm: dict) -> dict:
    """Devuelve título, bullets y clase CSS para la carta de decisión."""
    mon = sim["moneda"]
    perfil = sim["perfil"]
    hor = sim["horizonte_meses"]
    cap = _money(sim["capital_m"], mon)

    if luz == "verde":
        titulo = (
            f"✅ Recomendamos **presentar al comité** el portafolio **{perfil}** "
            f"con {cap} a **{hor} meses**."
        )
        bullets = [
            f"Sharpe **{_num(sim['sharpe'])}** supera al S&P (**{_num(bm['sharpe'])}**) "
            f"con volatilidad **{_pct(sim['vol_anual'])}** (umbral ≤ 15%).",
            f"Pérdida máxima estimada VaR {int(sim['confianza']*100)}%: "
            f"**≈ {_money(sim['var_soles'], mon)}** · ganancia esperada **{_money(sim['ganancia'], mon)}**.",
        ]
        css = "decision-verde"
    elif luz == "ambar":
        titulo = (
            f"⚠️ **Revisar antes de presentar:** el perfil **{perfil}** cumple parcialmente "
            f"los criterios del mandato."
        )
        bullets = []
        if not crit["sharpe_ok"]:
            bullets.append(f"Sharpe **{_num(sim['sharpe'])}** no alcanza el umbral ≥ 1.0.")
        if not crit["vol_ok"]:
            bullets.append(f"Volatilidad **{_pct(sim['vol_anual'])}** supera el tope del 15%.")
        if not crit["vs_mercado_ok"]:
            bullets.append("No supera el Sharpe del S&P 500 en este escenario.")
        if not bullets:
            bullets.append("Evaluar diversificación por clase antes de la votación del comité.")
        bullets.append("Sugerencia: probar **Máx. Sharpe** o reducir activos en el simulador.")
        css = "decision-ambar"
    else:
        titulo = (
            f"🔴 **No recomendamos presentar** el perfil **{perfil}** sin reconfigurar el escenario."
        )
        bullets = [
            "No cumple los criterios mínimos de Sharpe, volatilidad y/o benchmark.",
            f"Alternativa: perfil **Máx. Sharpe** · {hor} m · 20 activos (referencia del modelo Grupo 3).",
        ]
        css = "decision-rojo"

    return {"titulo": titulo, "bullets": bullets, "css": css}


def formatear_paso(paso: dict, sim: dict, bm: dict, etiqueta: str, conf_pct: int) -> dict:
    """Rellena placeholders del guion con datos vivos."""
    mon = sim["moneda"]
    top = sim["pesos"].head(3)
    top3 = ", ".join(f"{r['Ticker']} ({_pct(r['Peso'])})" for _, r in top.iterrows())
    guion = paso["guion"].format(
        capital=_money(sim["capital_m"], mon),
        perfil=sim["perfil"],
        etiqueta=etiqueta,
        sharpe=_num(sim["sharpe"]),
        sharpe_bm=_num(bm["sharpe"]),
        retorno=_pct(sim["retorno_anual"]),
        top3=top3,
        conf=conf_pct,
        var_soles=_money(sim["var_soles"], mon),
        cvar_soles=_money(sim["cvar_soles"], mon),
    )
    return {**paso, "guion": guion}
