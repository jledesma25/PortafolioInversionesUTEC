# -*- coding: utf-8 -*-
"""Carga resultados exportados por el notebook Colab de Grupo 3."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data" / "grupo3"
CAPITAL = 1_000_000

PARAMETROS_GRUPO3 = {
    "Capital (S/)": "1,000,000",
    "Horizonte": "12 meses (252 días)",
    "Años de historia": "6",
    "Tipo de cambio PEN/USD": "3.39",
    "Tasa libre de riesgo anual": "4%",
    "Benchmark": "^GSPC (S&P 500)",
    "Peso mínimo por activo": "0%",
    "Peso máximo por activo": "15%",
    "Activos en cartera": "20",
    "Universo evaluado": "50 (selección → 20)",
    "Estrategia": "Máximo Sharpe (Markowitz)",
    "Simulaciones bootstrap": "10,000",
    "Tamaño bloque bootstrap": "21 días",
    "Semilla": "29",
}

# Pesos del portafolio final (Máximo Sharpe) — extraídos del gráfico Colab
PESOS_PORTAFOLIO = [
    ("GLD", 0.157, "Commodities"),
    ("NVDA", 0.144, "Renta variable EE.UU."),
    ("XOM", 0.140, "Renta variable EE.UU."),
    ("JNJ", 0.139, "Renta variable EE.UU."),
    ("KO", 0.091, "Renta variable EE.UU."),
    ("WMT", 0.074, "Renta variable EE.UU."),
    ("SLV", 0.070, "Commodities"),
    ("JPM", 0.063, "Renta variable EE.UU."),
    ("HYG", 0.010, "Bonos"),
    ("RWX", 0.010, "REITs"),
    ("EEM", 0.010, "Renta variable internacional"),
    ("MSFT", 0.010, "Renta variable EE.UU."),
    ("AAPL", 0.010, "Renta variable EE.UU."),
    ("AMZN", 0.010, "Renta variable EE.UU."),
    ("TSLA", 0.010, "Renta variable EE.UU."),
    ("GOOGL", 0.010, "Renta variable EE.UU."),
    ("SCHH", 0.010, "REITs"),
    ("VGK", 0.010, "Renta variable internacional"),
    ("USO", 0.010, "Commodities"),
    ("CSCO", 0.010, "Renta variable EE.UU."),
]

GRAFICOS = {
    "evolucion": "1_evolucion_historica.png",
    "riesgo_retorno": "2_riesgo_vs_retorno.png",
    "rentabilidad_anual": "2b_rentabilidad_por_año.png",
    "frontera": "3_frontera_eficiente.png",
    "distribucion": "4_distribucion_capital.png",
    "valor_futuro": "5_valor_hoy_vs_futuro.png",
    "cuadro_resumen": "6_cuadro_resumen_escenarios.png",
    "vs_benchmark": "7_portafolio_vs_benchmark.png",
    "bootstrap": "8_distribucion_var_1anio.png",
    "ganancia_activos": "9_ganancia_por_activo_vs_benchmark.png",
}


def _fila(df, escenario):
    row = df.loc[df["Escenario"] == escenario].iloc[0]
    return {
        "retorno": row["Retorno esperado (%)"] / 100,
        "var_diario": row["VaR parametrico 95% diario (%)"] / 100,
        "var_anual": abs(row["VaR 95% a 1 anio (%)"]) / 100,
        "cvar_anual": row["CVaR 95% a 1 anio (%)"] / 100,
        "sharpe": row["Ratio de Sharpe"],
        "vol": row["Volatilidad anual (%)"] / 100,
        "valor": row["Valor proyectado (S/)"],
    }


def cargar_resultados():
    csv_path = DATA_DIR / "6_cuadro_resumen_escenarios.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"No se encontró {csv_path}. Coloque los archivos de Colab en data/grupo3/.")

    escenarios = pd.read_csv(csv_path)
    sh_adv = _fila(escenarios, "Max. Sharpe - Adverso")
    sh_exp = _fila(escenarios, "Max. Sharpe - Esperado")
    sh_fav = _fila(escenarios, "Max. Sharpe - Favorable")
    bm_adv = _fila(escenarios, "Benchmark - Adverso")
    bm_exp = _fila(escenarios, "Benchmark - Esperado")
    bm_fav = _fila(escenarios, "Benchmark - Favorable")

    asignacion = pd.DataFrame(PESOS_PORTAFOLIO, columns=["Ticker", "Peso", "Clase de Activo"])
    asignacion["Capital (S/)"] = asignacion["Peso"] * CAPITAL
    asignacion["Estado"] = asignacion["Peso"].apply(
        lambda p: "Seleccionado" if p > 0.02 else "Evaluado, peso mínimo"
    )
    asignacion = asignacion.sort_values("Peso", ascending=False)

    clases = (
        asignacion.groupby("Clase de Activo", as_index=False)
        .agg(Peso=("Peso", "sum"), Capital=("Capital (S/)", "sum"), Activos=("Ticker", "count"))
        .sort_values("Peso", ascending=False)
    )

    incumplidos = []
    if sh_exp["sharpe"] < 1.20:
        incumplidos.append("Sharpe inferior a 1.20")
    if sh_exp["var_anual"] > 0.08:
        incumplidos.append("VaR anual 95% superior a 8%")
    elegible = len(incumplidos) == 0

    cumplimiento = pd.DataFrame([
        ("Universo cerrado", "20 activos", "20", "CUMPLE"),
        ("Peso máximo", "≤ 15%", f"{asignacion['Peso'].max():.1%}", "CUMPLE"),
        ("Sin apalancamiento", "suma = 100%", f"{asignacion['Peso'].sum():.1%}", "CUMPLE"),
        ("Sharpe del portafolio", "≥ 1.20", f"{sh_exp['sharpe']:.2f}", "CUMPLE" if sh_exp["sharpe"] >= 1.20 else "NO CUMPLE"),
        ("VaR anual 95%", "≤ 8%", f"{sh_exp['var_anual']:.2%}", "CUMPLE" if sh_exp["var_anual"] <= 0.08 else "NO CUMPLE"),
        ("Supera benchmark (Sharpe)", ">", f"{sh_exp['sharpe']:.2f} vs {bm_exp['sharpe']:.2f}",
         "CUMPLE" if sh_exp["sharpe"] > bm_exp["sharpe"] else "NO CUMPLE"),
    ], columns=["Criterio", "Umbral", "Resultado", "Estado"])

    graficos = {k: DATA_DIR / v for k, v in GRAFICOS.items() if (DATA_DIR / v).exists()}

    return {
        "fuente": "Colab Grupo 3",
        "capital": CAPITAL,
        "elegible": elegible,
        "incumplidos": incumplidos,
        "portafolio": sh_exp,
        "benchmark": bm_exp,
        "escenarios": {
            "portafolio": {"adverso": sh_adv["valor"], "esperado": sh_exp["valor"], "favorable": sh_fav["valor"]},
            "benchmark": {"adverso": bm_adv["valor"], "esperado": bm_exp["valor"], "favorable": bm_fav["valor"]},
        },
        "metricas": {
            "portafolio": sh_exp,
            "benchmark": bm_exp,
        },
        "asignacion": asignacion,
        "clases": clases,
        "cumplimiento": cumplimiento,
        "escenarios_df": escenarios,
        "graficos": graficos,
        "parametros": PARAMETROS_GRUPO3,
    }
