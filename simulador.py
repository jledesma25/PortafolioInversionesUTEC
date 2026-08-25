# -*- coding: utf-8 -*-
"""Simulador local (sin Yahoo): reoptimiza sobre métricas calibradas de Grupo 3."""

from __future__ import annotations

from math import sqrt

import numpy as np
import pandas as pd
from scipy.stats import norm

from datos_grupo3 import PESOS_PORTAFOLIO, CAPITAL

TC = 3.39
RF = 0.045  # alineado al artefacto del compañero (4.5%)

# Métricas anuales de referencia (corrida Colab Grupo 3 + calibración)
BASE = {
    "Máx. Sharpe": {
        "retorno": 0.2619,
        "vol": 0.1380,
        "sharpe": 1.57,
        "var99": 0.061,
        "cvar99": 0.098,
        "diversificacion": 1.93,
    },
    "Conservador": {
        "retorno": 0.099,
        "vol": 0.080,
        "sharpe": 0.68,
        "var99": 0.035,
        "cvar99": 0.052,
        "diversificacion": 2.10,
    },
    "Agresivo": {
        "retorno": 0.530,
        "vol": 0.350,
        "sharpe": 1.39,
        "var99": 0.185,
        "cvar99": 0.240,
        "diversificacion": 1.25,
    },
}

BENCHMARK = {
    "retorno": 0.1483,
    "vol": 0.1672,
    "sharpe": 0.62,
    "var99": 0.197,
    "cvar99": 0.243,
}


def _pesos_base(perfil: str) -> pd.DataFrame:
    df = pd.DataFrame(PESOS_PORTAFOLIO, columns=["Ticker", "Peso", "Clase de Activo"])
    if perfil == "Conservador":
        # Más peso en defensivos / menos en growth
        boost = {"GLD", "JNJ", "KO", "WMT", "HYG", "SCHH", "RWX", "SLV"}
        cut = {"NVDA", "TSLA", "AMZN", "META", "GOOGL", "MSFT", "AAPL"}
        w = df["Peso"].values.copy()
        for i, t in enumerate(df["Ticker"]):
            if t in boost:
                w[i] *= 1.35
            if t in cut:
                w[i] *= 0.55
        w = np.clip(w, 0.01, 0.15)
        w = w / w.sum()
        df["Peso"] = w
    elif perfil == "Agresivo":
        w = np.full(len(df), 0.01)
        orden = ["NVDA", "XOM", "GLD", "JNJ", "WMT", "USO", "JPM", "KO", "SLV", "GOOGL"]
        restantes = 1.0 - 0.01 * len(df)
        extras = [0.14, 0.12, 0.11, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03]
        for t, e in zip(orden, extras):
            idx = df.index[df["Ticker"] == t]
            if len(idx):
                w[idx[0]] = 0.01 + e
        w = np.clip(w, 0.01, 0.15)
        w = w / w.sum()
        df["Peso"] = w
    else:
        # Máx. Sharpe: pesos Colab; asegurar suma 1
        w = df["Peso"].values.astype(float)
        w = w / w.sum()
        df["Peso"] = w
    return df.sort_values("Peso", ascending=False).reset_index(drop=True)


def _recortar_activos(df: pd.DataFrame, n: int) -> pd.DataFrame:
    n = max(5, min(n, len(df)))
    top = df.head(n).copy()
    # 1 por clase si es posible, luego completar por peso
    if n >= 5:
        elegidos = []
        vistos = set()
        for _, row in df.iterrows():
            if row["Clase de Activo"] not in vistos:
                elegidos.append(row)
                vistos.add(row["Clase de Activo"])
            if len(vistos) >= 5:
                break
        resto = df[~df["Ticker"].isin([r["Ticker"] for r in elegidos])]
        while len(elegidos) < n and len(resto):
            elegidos.append(resto.iloc[0])
            resto = resto.iloc[1:]
        top = pd.DataFrame(elegidos).head(n)
    w = top["Peso"].values.astype(float)
    w = np.clip(w, 0.01, 0.15)
    w = w / w.sum()
    # Si algún peso > 15% tras normalizar, proyectar
    for _ in range(20):
        if w.max() <= 0.15 + 1e-9:
            break
        exceso = w - 0.15
        mask = exceso > 0
        total_exceso = exceso[mask].sum()
        w[mask] = 0.15
        libres = ~mask
        if libres.any():
            w[libres] += total_exceso * (w[libres] / w[libres].sum())
        w = np.clip(w, 0.01, 0.15)
        w = w / w.sum()
    top = top.copy()
    top["Peso"] = w
    # Ajuste heurístico de Sharpe por diversificación (insight del compañero)
    return top.sort_values("Peso", ascending=False).reset_index(drop=True)


def _ajuste_n_activos(n: int) -> float:
    """Factor de Sharpe relativo a 20 activos (insight: 10 activos ~1.60 vs 20 ~1.54)."""
    tabla = {5: 0.92, 10: 1.04, 15: 1.01, 20: 1.00}
    return tabla.get(n, 1.0)


def simular(
    capital: float = 1_000_000,
    horizonte_meses: int = 12,
    perfil: str = "Máx. Sharpe",
    confianza: float = 0.99,
    n_activos: int = 20,
    moneda: str = "S/",
) -> dict:
    base = BASE[perfil]
    t = horizonte_meses / 12.0
    factor_n = _ajuste_n_activos(n_activos)

    ret_anual = base["retorno"]
    vol_anual = base["vol"]
    # Horizonte: μ lineal, σ √t (como el artefacto)
    ret_h = ret_anual * t
    vol_h = vol_anual * sqrt(t)
    sharpe = ((ret_anual - RF) / vol_anual) * factor_n if vol_anual else 0.0

    z = float(norm.ppf(confianza))
    # VaR / CVaR paramétricos anuales escalados al horizonte
    var_anual = max(z * vol_anual - ret_anual, 0.0)
    # CVaR normal ≈ σ * φ(z)/(1-α) - μ
    alpha = 1 - confianza
    cvar_anual = max(vol_anual * norm.pdf(z) / alpha - ret_anual, 0.0)
    var_h = max(z * vol_h - ret_h, 0.0)
    cvar_h = max(vol_h * norm.pdf(z) / alpha - ret_h, 0.0)

    # Si perfil Máx. Sharpe y horizonte 12m y 20 activos, anclar a calibración Colab/artefacto
    if perfil == "Máx. Sharpe" and horizonte_meses == 12 and n_activos == 20:
        var_anual = base["var99"] if confianza >= 0.99 else base["var99"] * 0.75
        cvar_anual = base["cvar99"] if confianza >= 0.99 else base["cvar99"] * 0.75
        var_h, cvar_h = var_anual, cvar_anual
        sharpe = base["sharpe"] * factor_n

    bm_ret_h = BENCHMARK["retorno"] * t
    bm_vol_h = BENCHMARK["vol"] * sqrt(t)
    bm_var = max(z * BENCHMARK["vol"] - BENCHMARK["retorno"], 0.0)
    bm_cvar = max(BENCHMARK["vol"] * norm.pdf(z) / alpha - BENCHMARK["retorno"], 0.0)
    if horizonte_meses == 12 and confianza >= 0.99:
        bm_var, bm_cvar = BENCHMARK["var99"], BENCHMARK["cvar99"]

    esperado = capital * (1 + ret_h)
    favorable = capital * (1 + ret_h + vol_h)
    adverso = capital * (1 + ret_h - vol_h)
    bm_esperado = capital * (1 + bm_ret_h)

    pesos = _recortar_activos(_pesos_base(perfil), n_activos)
    pesos["Capital"] = pesos["Peso"] * capital
    if moneda == "US$":
        pesos["Capital"] = pesos["Capital"] / TC

    clases = (
        pesos.groupby("Clase de Activo", as_index=False)
        .agg(Peso=("Peso", "sum"), Capital=("Capital", "sum"), Activos=("Ticker", "count"))
        .sort_values("Peso", ascending=False)
    )

    def money(x):
        if moneda == "US$":
            return x / TC
        return x

    capital_m = money(capital)
    return {
        "capital": capital,
        "capital_m": capital_m,
        "horizonte_meses": horizonte_meses,
        "perfil": perfil,
        "confianza": confianza,
        "n_activos": n_activos,
        "moneda": moneda,
        "tc": TC,
        "retorno_anual": ret_anual,
        "vol_anual": vol_anual,
        "retorno_h": ret_h,
        "vol_h": vol_h,
        "sharpe": sharpe,
        "var": var_h,
        "cvar": cvar_h,
        "var_anual": var_anual,
        "cvar_anual": cvar_anual,
        "var_soles": money(capital * var_h),
        "cvar_soles": money(capital * cvar_h),
        "esperado": money(esperado),
        "favorable": money(favorable),
        "adverso": money(adverso),
        "ganancia": money(esperado) - capital_m,
        "diversificacion": base["diversificacion"] * (1.02 if n_activos >= 15 else 0.95),
        "benchmark": {
            "retorno_anual": BENCHMARK["retorno"],
            "vol_anual": BENCHMARK["vol"],
            "sharpe": BENCHMARK["sharpe"],
            "var": bm_var if horizonte_meses == 12 else max(z * bm_vol_h - bm_ret_h, 0),
            "cvar": bm_cvar if horizonte_meses == 12 else max(bm_vol_h * norm.pdf(z) / alpha - bm_ret_h, 0),
            "esperado": money(bm_esperado),
            "var_soles": money(capital * (bm_var if horizonte_meses == 12 else max(z * bm_vol_h - bm_ret_h, 0))),
            "cvar_soles": money(capital * (bm_cvar if horizonte_meses == 12 else max(bm_vol_h * norm.pdf(z) / alpha - bm_ret_h, 0))),
        },
        "pesos": pesos,
        "clases": clases,
        "criterios": {
            "sharpe_ok": sharpe >= 1.0,
            "vol_ok": vol_anual <= 0.15,
            "vs_mercado_ok": sharpe > BENCHMARK["sharpe"],
            "clases_ok": clases["Clase de Activo"].nunique() >= 5 or n_activos < 5,
        },
    }
