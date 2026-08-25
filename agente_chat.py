# -*- coding: utf-8 -*-
"""Agente de chat: responde solo con datos del simulador / portafolio Grupo 3.

Usa puntuación de intenciones + muchas variantes de frase.
Rechaza temas ajenos (deportes, clima, etc.).
"""

from __future__ import annotations

import re
import unicodedata

PREGUNTAS_SUGERIDAS = [
    "¿El portafolio es elegible?",
    "¿En qué empresas debo invertir?",
    "¿Cuánto puedo perder?",
    "¿Cuánto puedo ganar?",
    "¿Ganamos al S&P 500?",
    "¿Por qué no 100% en NVDA?",
    "¿Qué es el Ratio de Sharpe?",
    "¿Qué cambia con 10 activos?",
    "¿Cuáles son las reglas del mandato?",
    "¿Qué perfil y capital estoy usando?",
]

FUERA_DE_ALCANCE = (
    "Solo respondo sobre el **portafolio, riesgo, mandato y resultados del simulador** "
    "de este proyecto (Grupo 3 · UTEC).\n\n"
    "No puedo hablar de temas ajenos (deportes, clima, política, entretenimiento, etc.).\n\n"
    "Prueba, por ejemplo:\n"
    "• ¿En qué empresas debo invertir?\n"
    "• ¿Cuánto puedo perder?\n"
    "• ¿El portafolio es elegible?\n"
    "• ¿Ganamos al S&P 500?"
)

# Intenciones: (id, keywords). Más keywords = más formas de preguntar.
INTENCIONES = {
    "cartera": [
        "empresa", "empresas", "invertir", "inversion", "invierta", "invierto", "invertiria",
        "comprar", "compro", "compra", "ticker", "tickers", "accion", "acciones",
        "etf", "fondo", "activos", "activo", "cartera", "portafolio", "composicion",
        "asignacion", "distribucion", "peso", "pesos", "ponderacion", "holding",
        "donde poner", "donde va", "donde esta", "en que poner", "en que invertir",
        "que comprar", "que compro", "que tengo", "que incluye", "que contiene",
        "lista de", "top", "mayores", "principales", "concentracion del capital",
        "como esta armado", "como se reparte", "reparto", "allocation",
        "nvda", "gld", "jnj", "xom", "msft", "aapl", "meta", "tsla", "hyg", "oro",
        "recomienda comprar", "recomendacion de compra", "sugerencia de inversion",
        "deberia", "deberia invertir", "donde invertir", "en cuales", "cuales empresas",
        "dame 3", "dame tres", "top 3", "las 3", "tres empresas", "pocas empresas",
    ],
    "elegible": [
        "elegible", "elegibilidad", "aprueba", "aprobado", "aprobar", "semaforo",
        "cumple", "cumplimiento", "criterio", "criterios", "viable", "aceptable",
        "presentar al comite", "pasa el filtro", "pasa el umbral", "decision del agente",
        "me lo recomiendan", "es bueno el portafolio", "conviene este portafolio",
        "debo aceptarlo", "lo aprueban", "matriz de cumplimiento",
    ],
    "riesgo": [
        "perder", "perdida", "perdidas", "riesgo", "var", "cvar", "cola",
        "drawdown", "caida", "bajada", "peor escenario", "escenario adverso",
        "cuanto arriesgo", "cuanto puedo perder", "maxima perdida", "perdida maxima",
        "value at risk", "shortfall", "estres", "stress", "seguridad del capital",
        "proteger capital", "cuanto bajo",
    ],
    "retorno": [
        "ganar", "ganancia", "ganancias", "retorno", "rentabilidad", "rendimiento",
        "beneficio", "utilidad", "esperado", "proyeccion", "proyectado", "crecimiento",
        "capital final", "valor final", "cuanto gano", "cuanto rinde", "cuanto obtiene",
        "escenario favorable", "escenario esperado", "upside", "profit",
    ],
    "benchmark": [
        "sp500", "s&p", "s & p", "gspc", "benchmark", "mercado", "indice",
        "comparar", "comparacion", "versus", "vs ", "contra el mercado",
        "superamos", "ganamos al", "mejor que el", "peor que el", "alpha",
        "exceso de retorno", "relativo al mercado", "bolsa americana",
    ],
    "concentracion": [
        "100%", "cien por", "todo en", "solo en", "unicamente", "concentrac",
        "una sola", "un solo", "all in", "sin diversificar", "poner todo",
        "meter todo", "invertir solo",
    ],
    "sharpe": [
        "sharpe", "ratio de sharpe", "retorno ajustado", "eficiencia",
        "compensacion riesgo", "que significa sharpe", "explica sharpe",
        "como se interpreta sharpe",
    ],
    "n_activos": [
        "10 activo", "5 activo", "15 activo", "20 activo", "numero de activo",
        "n de activo", "cuantos activo", "cantidad de activo", "diversific",
        "menos activo", "mas activo", "reducir activo", "ampliar universo",
    ],
    "config": [
        "perfil", "horizonte", "meses", "parametro", "configur",
        "usando", "estoy usando", "ajustes", "simulador", "moneda",
        "dolares", "confianza", "settings", "que tengo configurado",
        "conservador", "agresivo", "maximo sharpe", "max sharpe",
        "cuanto capital tengo", "capital configurado",
    ],
    "mandato": [
        "regla", "reglas", "mandato", "restriccion", "restricciones", "tope",
        "piso", "limite", "limites", "corto", "apalanc", "gobernanza",
        "politica", "normas", "sin ventas", "long only", "constraint",
    ],
    "ayuda": [
        "ayuda", "que puedo preguntar", "que preguntas", "opciones", "menu",
        "como funciona", "para que sirves", "que haces", "alcance",
        "en que me ayudas", "temas",
    ],
}

DOMINIO = {
    "portafolio", "sharpe", "var", "cvar", "riesgo", "retorno", "volatilidad",
    "sp500", "s&p", "benchmark", "nvda", "peso", "capital", "soles", "activo",
    "cartera", "inversion", "invertir", "empresa", "ticker", "accion", "etf",
    "elegible", "mandato", "diversific", "horizonte", "perfil", "bootstrap",
    "markowitz", "ganar", "perder", "ganancia", "drawdown", "comite", "agente",
    "utec", "grupo", "oro", "gld", "jnj", "xom", "comprar", "asignacion",
    "rendimiento", "rentabilidad", "mercado", "indice", "restriccion", "tope",
    "simulador", "va r", "financ", "millon", "patrimonio", "fondo",
}

FUERA = {
    "mundial", "fifa", "futbol", "football", "messi", "ronaldo", "partido",
    "pelicula", "netflix", "cancion", "spotify", "chiste", "receta", "cocinar",
    "clima", "temperatura", "lluvia", "presidente", "eleccion", "congreso",
    "guerra", "novia", "novio", "horoscopo", "signo", "loteria", "pokemon",
    "minecraft", "quien gano", "cuentame un", "escribe un poema", "traduce esto",
    "receta de", "como cocinar", "serie de", "actor", "actriz", "tiktok",
    "instagram", "whatsapp", "chisme", "chismes",
}


def _norm(texto: str) -> str:
    t = unicodedata.normalize("NFKD", (texto or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip()


def _money(x, moneda="S/"):
    if moneda == "US$":
        return f"US$ {x:,.0f}"
    return f"S/ {x:,.0f}"


def _pct(x):
    return f"{x:.2%}"


def _num(x):
    return f"{x:.2f}"


def _score(q: str, keywords: list[str]) -> int:
    score = 0
    for k in keywords:
        if k in q:
            # Frases largas pesan más
            score += 2 if " " in k else 1
    return score


def _tiene_dominio(q: str) -> bool:
    return any(d in q for d in DOMINIO)


def _es_fuera_de_tema(q: str) -> bool:
    if any(f in q for f in FUERA) and not _tiene_dominio(q):
        return True
    if q in {"hola", "hi", "hello", "hey", "buenas", "que tal", "gracias", "ok", "vale"}:
        return True
    return False


def _mejor_intencion(q: str) -> tuple[str | None, int]:
    mejor, mejor_score = None, 0
    for nombre, keys in INTENCIONES.items():
        s = _score(q, keys)
        if s > mejor_score:
            mejor, mejor_score = nombre, s
    # Prioridad fuerte a preguntas de inversión / empresas
    if any(p in q for p in (
        "donde pongo", "donde va", "donde esta", "en que invertir", "donde invertir",
        "en que empresas", "que empresas", "cuales empresas", "que acciones",
        "que comprar", "deberia invertir", "donde invertir", "dame 3", "dame tres",
        "top 3", "tres empresas",
    )):
        return "cartera", max(mejor_score, 8)
    if ("empresa" in q or "empresas" in q) and ("invert" in q or "compr" in q or "dame" in q):
        return "cartera", max(mejor_score, 8)
    return mejor, mejor_score


def _extraer_n(q: str, default: int = 5) -> int:
    """Detecta 'dame 3', 'top 5', etc."""
    m = re.search(r"(?:dame|top|las?|muestra(?:me)?|lista(?:me)?)\s*(\d{1,2})", q)
    if m:
        return max(1, min(int(m.group(1)), 15))
    if "tres" in q:
        return 3
    if "cinco" in q:
        return 5
    return default


def _respuesta_cartera(sim: dict, q: str = "") -> str:
    moneda = sim["moneda"]
    pesos = sim["pesos"]
    n = _extraer_n(q, default=5)
    top = pesos.head(n)
    lineas = "\n".join(
        f"{i}. **{row['Ticker']}** ({row['Clase de Activo']}): "
        f"{_pct(row['Peso'])} → {_money(row['Capital'], moneda)}"
        for i, (_, row) in enumerate(top.iterrows(), start=1)
    )
    clases = sim["clases"]
    clases_txt = ", ".join(
        f"{r['Clase de Activo']} {_pct(r['Peso'])}" for _, r in clases.iterrows()
    )
    return (
        f"Con el escenario actual (**{sim['perfil']}**, {sim['n_activos']} activos, "
        f"{sim['horizonte_meses']} m), estas son las **{n} principales** posiciones "
        f"del capital {_money(sim['capital_m'], moneda)}:\n\n{lineas}\n\n"
        f"**Por clase (toda la cartera):** {clases_txt}.\n"
        f"Diversificación: **{sim['diversificacion']:.2f}**.\n\n"
        "Simulación académica con tope 15% por activo — no es una orden de compra "
        "ni consejo personalizado de inversión."
    )


def responder(pregunta: str, sim: dict) -> str:
    q = _norm(pregunta)
    if not q:
        return "Escribe una pregunta sobre el portafolio o elige una sugerida."

    if _es_fuera_de_tema(q):
        return FUERA_DE_ALCANCE

    intencion, score = _mejor_intencion(q)

    # Sin match claro y sin palabras del dominio → rechazo
    if score == 0 and not _tiene_dominio(q):
        return FUERA_DE_ALCANCE

    # Match débil: pedir reformulación con sugerencias
    if score == 0:
        sugeridas = "\n".join(f"• {p}" for p in PREGUNTAS_SUGERIDAS[:6])
        return (
            "Entiendo que hablas del proyecto, pero no identifiqué la pregunta exacta.\n\n"
            f"Prueba una de estas:\n{sugeridas}"
        )

    bm = sim["benchmark"]
    crit = sim["criterios"]
    moneda = sim["moneda"]
    conf = int(sim["confianza"] * 100)
    hor = sim["horizonte_meses"]
    pesos = sim["pesos"]

    # Desempate: "recomienda invertir en empresas" → cartera, no elegible
    if intencion == "elegible" and _score(q, INTENCIONES["cartera"]) >= score:
        intencion = "cartera"
    if intencion == "retorno" and _score(q, INTENCIONES["riesgo"]) > score:
        intencion = "riesgo"
    # "ganar al mercado" → benchmark
    if intencion == "retorno" and _score(q, INTENCIONES["benchmark"]) >= 2:
        intencion = "benchmark"

    if intencion == "cartera":
        return _respuesta_cartera(sim, q)

    if intencion == "elegible":
        ok = crit["sharpe_ok"] and crit["vol_ok"] and crit["vs_mercado_ok"]
        estado = "PORTAFOLIO ELEGIBLE" if ok else "REVISAR CRITERIOS"
        return (
            f"**{estado}** con el perfil **{sim['perfil']}**.\n\n"
            f"• Sharpe {_num(sim['sharpe'])} "
            f"({'≥ 1.0 ✅' if crit['sharpe_ok'] else '< 1.0 ❌'})\n"
            f"• Volatilidad {_pct(sim['vol_anual'])} "
            f"({'≤ 15% ✅' if crit['vol_ok'] else '> 15% ❌'})\n"
            f"• Vs S&P 500: Sharpe mercado {_num(bm['sharpe'])} "
            f"({'superamos ✅' if crit['vs_mercado_ok'] else 'no superamos ❌'})\n\n"
            "La decisión final la toma el **comité humano**; el agente solo reporta evidencia."
        )

    if intencion == "riesgo":
        return (
            f"Con confianza **{conf}%** y horizonte **{hor} meses**:\n\n"
            f"• **VaR {conf}%:** {_pct(sim['var'])} ≈ {_money(sim['var_soles'], moneda)}\n"
            f"• **CVaR {conf}%** (pérdida media en la cola): {_pct(sim['cvar'])} "
            f"≈ {_money(sim['cvar_soles'], moneda)}\n"
            f"• Escenario adverso (−1σ): {_money(sim['adverso'], moneda)}\n\n"
            f"Comparado con el S&P 500: VaR {_pct(bm['var'])} "
            f"({_money(bm['var_soles'], moneda)}).\n\n"
            "Es una estimación del modelo, no una garantía."
        )

    if intencion == "retorno":
        return (
            f"Perfil **{sim['perfil']}** · capital {_money(sim['capital_m'], moneda)} · "
            f"horizonte {hor} meses:\n\n"
            f"• Retorno anual esperado: **{_pct(sim['retorno_anual'])}**\n"
            f"• Valor esperado: **{_money(sim['esperado'], moneda)}**\n"
            f"• Ganancia esperada: **{_money(sim['ganancia'], moneda)}**\n"
            f"• Favorable (+1σ): {_money(sim['favorable'], moneda)}\n"
            f"• Adverso (−1σ): {_money(sim['adverso'], moneda)}\n\n"
            "Simulación académica; no garantiza resultados futuros."
        )

    if intencion == "benchmark":
        return (
            f"**Portafolio vs S&P 500** (datos del simulador):\n\n"
            f"| Métrica | Portafolio | S&P 500 |\n"
            f"|---|---|---|\n"
            f"| Retorno | {_pct(sim['retorno_anual'])} | {_pct(bm['retorno_anual'])} |\n"
            f"| Volatilidad | {_pct(sim['vol_anual'])} | {_pct(bm['vol_anual'])} |\n"
            f"| Sharpe | {_num(sim['sharpe'])} | {_num(bm['sharpe'])} |\n"
            f"| VaR {conf}% | {_pct(sim['var_anual'])} | {_pct(bm['var'])} |\n\n"
            f"Exceso de retorno: **{(sim['retorno_anual']-bm['retorno_anual'])*100:+.2f} pp**."
        )

    if intencion == "concentracion":
        fila = pesos.loc[pesos["Ticker"] == "NVDA"]
        peso_nvda = float(fila["Peso"].iloc[0]) if len(fila) else 0.0
        return (
            "No se puede concentrar el 100% en una sola empresa (p. ej. NVDA).\n\n"
            f"• Mandato: **piso 1% · tope 15%** por activo, sin cortos ni apalancamiento.\n"
            f"• En la cartera actual NVDA pesa **{_pct(peso_nvda)}**.\n"
            "• Debe haber diversificación por clases "
            "(RV EE.UU., commodities, bonos, REITs, internacional).\n\n"
            "El agente bloquea propuestas que violen esas reglas."
        )

    if intencion == "sharpe":
        return (
            "El **Ratio de Sharpe** mide retorno por unidad de riesgo:\n\n"
            "`Sharpe = (retorno − tasa libre de riesgo) / volatilidad`\n\n"
            f"En tu simulación actual: **{_num(sim['sharpe'])}** "
            f"(retorno {_pct(sim['retorno_anual'])}, vol {_pct(sim['vol_anual'])}).\n"
            f"El S&P 500 tiene Sharpe **{_num(bm['sharpe'])}**.\n\n"
            "Más alto = mejor compensación riesgo-retorno. No es garantía de ganancia futura."
        )

    if intencion == "n_activos":
        return (
            f"Ahora mismo el simulador usa **{sim['n_activos']} activos** "
            f"(perfil {sim['perfil']}, Sharpe {_num(sim['sharpe'])}).\n\n"
            "Insight del modelo: con **~10 activos** el Sharpe puede subir "
            "(menos costo de forzar diversificación); con **20** hay más cobertura por clase "
            "pero el Sharpe puede bajar un poco.\n\n"
            "Cambia el control **N.º activos** arriba para ver el efecto en vivo."
        )

    if intencion == "config":
        return (
            "**Configuración actual del simulador:**\n\n"
            f"• Capital: {_money(sim['capital_m'], moneda)}\n"
            f"• Horizonte: {hor} meses\n"
            f"• Perfil: {sim['perfil']}\n"
            f"• Confianza VaR: {conf}%\n"
            f"• Activos: {sim['n_activos']}\n"
            f"• Moneda: {moneda}\n\n"
            "Esos controles están arriba (etiquetados VIVO) y recalculan al instante."
        )

    if intencion == "mandato":
        return (
            "**Reglas del mandato (gobernanza):**\n\n"
            "• Sin ventas en corto ni apalancamiento\n"
            "• Piso **1%** y tope **15%** por activo\n"
            "• Universo cerrado / selección diversificada por clases\n"
            "• Comparación obligatoria vs S&P 500 (`^GSPC`)\n"
            "• Horizonte de referencia: 12 meses (también 6/24/36 en el simulador)\n"
            "• La decisión final es del **comité**, no del chatbot"
        )

    if intencion == "ayuda":
        sugeridas = "\n".join(f"• {p}" for p in PREGUNTAS_SUGERIDAS)
        return (
            "Soy el asistente del **portafolio Grupo 3**. Solo hablo de cartera, "
            f"riesgo, retorno, mandato y comparación vs S&P 500.\n\n"
            f"Preguntas útiles:\n{sugeridas}"
        )

    return FUERA_DE_ALCANCE
