# -*- coding: utf-8 -*-
"""Motor cuantitativo de ComitéQuant: calidad de datos, Markowitz, riesgo y gobernanza."""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import minimize
from scipy.stats import norm

TICKERS = [
    "HYG", "USO", "SCHH", "NVDA", "VGK",
    "JNJ", "XOM", "WMT", "GLD", "JPM",
    "KO", "GOOGL", "CSCO", "BAC", "MSFT",
    "TSLA", "EFA", "META", "RWX", "CRM",
]

CLASES_ACTIVO = {
    "HYG": "Bonos",
    "USO": "Commodities",
    "GLD": "Commodities",
    "SCHH": "REITs",
    "RWX": "REITs",
    "VGK": "Renta variable internacional",
    "EFA": "Renta variable internacional",
    "NVDA": "Renta variable EE.UU.",
    "JNJ": "Renta variable EE.UU.",
    "XOM": "Renta variable EE.UU.",
    "WMT": "Renta variable EE.UU.",
    "JPM": "Renta variable EE.UU.",
    "KO": "Renta variable EE.UU.",
    "GOOGL": "Renta variable EE.UU.",
    "CSCO": "Renta variable EE.UU.",
    "BAC": "Renta variable EE.UU.",
    "MSFT": "Renta variable EE.UU.",
    "TSLA": "Renta variable EE.UU.",
    "META": "Renta variable EE.UU.",
    "CRM": "Renta variable EE.UU.",
}

DEFAULTS = {
    "capital_soles": 1_000_000,
    "tipo_cambio": 3.39,
    "anios_historia": 5,
    "dias_anuales": 252,
    "tasa_libre_riesgo_anual": 0.04,
    "benchmark": "^GSPC",
    "peso_minimo": 0.00,
    "peso_maximo": 0.15,
    "numero_portafolios_simulados": 2_500,
    "numero_simulaciones_bootstrap": 2_000,
    "horizonte_inversion_dias": 252,
    "tamano_bloque_bootstrap": 21,
    "proporcion_entrenamiento": 0.80,
    "sharpe_minimo_fuera_muestra": 1.20,
    "var_anual_maximo": 0.08,
    "drawdown_simulado_maximo": 0.15,
    "cobertura_minima": 0.98,
    "semilla": 29,
}


class AnalisisError(Exception):
    """El agente detiene el proceso por calidad de datos o incumplimiento de reglas."""


def _avisar(callback, pct, mensaje):
    if callback:
        callback(pct, mensaje)


def extraer_precios(data, tickers):
    if isinstance(data.columns, pd.MultiIndex):
        nivel0 = set(data.columns.get_level_values(0))
        if "Adj Close" in nivel0:
            precios = data["Adj Close"]
        elif "Close" in nivel0:
            precios = data["Close"]
        else:
            raise AnalisisError("Yahoo Finance no devolvió precios de cierre.")
        if isinstance(precios, pd.Series):
            precios = precios.to_frame()
    else:
        precios = data.copy()
    faltantes = [t for t in tickers if t not in precios.columns]
    if faltantes:
        raise AnalisisError(f"Faltan tickers en la descarga: {', '.join(faltantes)}")
    return precios[tickers]


def regularizar_covarianza(cov):
    valores = np.linalg.eigvalsh(cov)
    if np.all(valores > 0):
        return cov, False
    ajuste = cov + np.eye(cov.shape[0]) * 1e-6
    ajuste = (ajuste + ajuste.T) / 2
    if not np.all(np.linalg.eigvalsh(ajuste) > -1e-10):
        raise AnalisisError("La matriz de covarianza no pudo regularizarse.")
    return ajuste, True


def retorno_portafolio(pesos, retornos_anual):
    return float(np.dot(pesos, retornos_anual))


def volatilidad_portafolio(pesos, cov_anual):
    return float(np.sqrt(np.dot(pesos, np.dot(cov_anual, pesos))))


def sharpe_portafolio(pesos, retornos_anual, cov_anual, rf):
    vol = volatilidad_portafolio(pesos, cov_anual)
    if vol == 0:
        return -np.inf
    return (retorno_portafolio(pesos, retornos_anual) - rf) / vol


def optimizar(objetivo, n, retornos_anual, cov_anual, rf, peso_min, peso_max, semilla):
    bounds = [(peso_min, peso_max)] * n
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
    iniciales = [np.full(n, 1.0 / n)]
    rng = np.random.default_rng(semilla)
    for _ in range(4):
        w = rng.random(n)
        w = np.clip(w, peso_min, peso_max)
        w = w / w.sum()
        if np.all(w <= peso_max + 1e-9):
            iniciales.append(w)

    mejor = None
    for w0 in iniciales:
        if objetivo == "sharpe":
            fun = lambda w: -sharpe_portafolio(w, retornos_anual, cov_anual, rf)
            args = ()
        else:
            fun = lambda w: volatilidad_portafolio(w, cov_anual)
            args = ()
        res = minimize(fun, w0, args=args, method="SLSQP", bounds=bounds, constraints=constraints)
        if res.success:
            if mejor is None or res.fun < mejor.fun:
                mejor = res
    if mejor is None:
        raise AnalisisError(f"El optimizador de {objetivo} no convergió.")
    pesos = np.clip(mejor.x, peso_min, peso_max)
    pesos = pesos / pesos.sum()
    if abs(pesos.sum() - 1) > 1e-6 or pesos.max() > peso_max + 1e-6 or pesos.min() < peso_min - 1e-6:
        raise AnalisisError("Los pesos optimizados incumplen las restricciones.")
    return pesos


def pesos_aleatorios(n, peso_min, peso_max, rng):
    for _ in range(40):
        w = rng.random(n)
        w = np.clip(w, peso_min, peso_max)
        w = w / w.sum()
        if w.max() <= peso_max + 1e-9 and w.min() >= peso_min - 1e-9:
            return w
    w = np.full(n, 1.0 / n)
    return w


def var_cvar_diario(retornos, capital, niveles=(0.95, 0.99)):
    serie = pd.Series(retornos).dropna()
    media, std = float(serie.mean()), float(serie.std())
    out = {}
    for nivel in niveles:
        alpha = 1 - nivel
        var_p = float(-norm.ppf(alpha, loc=media, scale=std))
        var_h = float(-serie.quantile(alpha))
        cola = serie[serie <= serie.quantile(alpha)]
        cvar = float(-cola.mean()) if len(cola) else 0.0
        etiqueta = f"{int(nivel * 100)}"
        out[f"var_param_{etiqueta}"] = max(var_p, 0)
        out[f"var_hist_{etiqueta}"] = max(var_h, 0)
        out[f"cvar_hist_{etiqueta}"] = max(cvar, 0)
        out[f"var_param_{etiqueta}_soles"] = max(var_p, 0) * capital
        out[f"var_hist_{etiqueta}_soles"] = max(var_h, 0) * capital
        out[f"cvar_hist_{etiqueta}_soles"] = max(cvar, 0) * capital
    return out


def block_bootstrap(retornos, capital, n_sims, horizonte, bloque, semilla):
    arr = np.asarray(retornos, dtype=float)
    arr = arr[np.isfinite(arr)]
    n = len(arr)
    if n < bloque:
        raise AnalisisError("Hay menos observaciones que el tamaño de bloque del bootstrap.")
    rng = np.random.default_rng(semilla)
    n_bloques = int(np.ceil(horizonte / bloque))
    inicios = rng.integers(0, n - bloque + 1, size=(n_sims, n_bloques))
    offsets = np.arange(bloque)
    idx = inicios[..., None] + offsets
    idx = idx.reshape(n_sims, -1)[:, :horizonte]
    paths = arr[idx]
    acumulado = np.cumprod(1.0 + paths, axis=1)
    ret_anual = acumulado[:, -1] - 1.0
    valor_final = capital * (1.0 + ret_anual)
    picos = np.maximum.accumulate(acumulado, axis=1)
    dd = 1.0 - acumulado / picos
    mdd = dd.max(axis=1)

    def perdida_positiva(q):
        r = np.quantile(ret_anual, q)
        return float(max(-r, 0.0))

    def cvar_perdida(q):
        umbral = np.quantile(ret_anual, q)
        cola = ret_anual[ret_anual <= umbral]
        if len(cola) == 0:
            return 0.0
        return float(max(-cola.mean(), 0.0))

    return {
        "valores_finales": valor_final,
        "retornos_anuales": ret_anual,
        "media_valor": float(valor_final.mean()),
        "mediana_valor": float(np.median(valor_final)),
        "p5_valor": float(np.quantile(valor_final, 0.05)),
        "p95_valor": float(np.quantile(valor_final, 0.95)),
        "prob_perdida": float((valor_final < capital).mean()),
        "var_95": perdida_positiva(0.05),
        "var_99": perdida_positiva(0.01),
        "cvar_95": cvar_perdida(0.05),
        "cvar_99": cvar_perdida(0.01),
        "var_95_soles": perdida_positiva(0.05) * capital,
        "cvar_95_soles": cvar_perdida(0.05) * capital,
        "mdd_p95": float(np.quantile(mdd, 0.95)),
        "mdd_mediana": float(np.median(mdd)),
        "mdd_peor": float(mdd.max()),
    }


def max_drawdown(retornos):
    acum = (1 + pd.Series(retornos)).cumprod()
    pico = acum.cummax()
    dd = acum / pico - 1
    return float(abs(dd.min()))


def tabla_asignacion(pesos, tickers, metricas, capital, tipo_cambio, retorno_port):
    df = pd.DataFrame({"Ticker": tickers, "Peso": pesos})
    extras = metricas.reset_index().rename(columns={"index": "Ticker"})
    extras = extras.drop(columns=["Clase de Activo"], errors="ignore")
    df = df.merge(extras, on="Ticker", how="left")
    df["Clase de Activo"] = df["Ticker"].map(CLASES_ACTIVO).fillna("Desconocida")
    df["Capital (S/)"] = df["Peso"] * capital
    df["Capital (USD)"] = df["Capital (S/)"] / tipo_cambio
    df["Contribución ganancia (S/)"] = df["Peso"] * df["Retorno anualizado"] * capital
    if retorno_port:
        df["Contribución %"] = (df["Peso"] * df["Retorno anualizado"]) / retorno_port
    else:
        df["Contribución %"] = 0.0
    df["Estado"] = np.where(df["Peso"] > 1e-4, "Seleccionado", "Evaluado, no seleccionado")
    return df.sort_values("Peso", ascending=False)


def resumen_clases(asignacion):
    return (
        asignacion.groupby("Clase de Activo", as_index=False)
        .agg(
            Peso=("Peso", "sum"),
            Capital_Soles=("Capital (S/)", "sum"),
            Contribucion=("Contribución ganancia (S/)", "sum"),
            Activos=("Ticker", "count"),
            Seleccionados=("Peso", lambda s: int((s > 1e-4).sum())),
        )
        .sort_values("Peso", ascending=False)
    )


def ejecutar_analisis(params, progress=None):
    cfg = {**DEFAULTS, **params}
    capital = float(cfg["capital_soles"])
    tipo_cambio = float(cfg["tipo_cambio"])
    anios = int(cfg["anios_historia"])
    dias = int(cfg["dias_anuales"])
    rf = float(cfg["tasa_libre_riesgo_anual"])
    benchmark = cfg["benchmark"]
    peso_min = float(cfg["peso_minimo"])
    peso_max = float(cfg["peso_maximo"])
    n_front = int(cfg["numero_portafolios_simulados"])
    n_boot = int(cfg["numero_simulaciones_bootstrap"])
    horizonte = int(cfg["horizonte_inversion_dias"])
    bloque = int(cfg["tamano_bloque_bootstrap"])
    prop_train = float(cfg["proporcion_entrenamiento"])
    sharpe_oos_min = float(cfg["sharpe_minimo_fuera_muestra"])
    var_max = float(cfg["var_anual_maximo"])
    mdd_max = float(cfg["drawdown_simulado_maximo"])
    cobertura_min = float(cfg["cobertura_minima"])
    semilla = int(cfg["semilla"])

    np.random.seed(semilla)
    rng = np.random.default_rng(semilla)

    _avisar(progress, 0.05, "Descargando precios de Yahoo Finance…")
    fin = datetime.now()
    inicio = fin - timedelta(days=int(anios * 365.25) + 10)
    universo = TICKERS + [benchmark]
    crudo = yf.download(universo, start=inicio.strftime("%Y-%m-%d"), end=fin.strftime("%Y-%m-%d"),
                        progress=False, auto_adjust=True, threads=True)
    if crudo is None or crudo.empty:
        raise AnalisisError("No se pudieron descargar datos. Revise la conexión a internet.")

    precios = extraer_precios(crudo, universo)
    precios = precios.sort_index()
    n_bruto = len(precios)
    cobertura = (precios.notna().sum() / n_bruto).astype(float)
    calidad = pd.DataFrame({
        "Ticker": cobertura.index,
        "Observaciones": precios.notna().sum().values,
        "Nulos": precios.isna().sum().values,
        "Cobertura": cobertura.values,
        "Estado": np.where(cobertura.values >= cobertura_min, "CUMPLE", "NO CUMPLE"),
    })
    if (calidad["Estado"] == "NO CUMPLE").any():
        malos = calidad.loc[calidad["Estado"] == "NO CUMPLE", "Ticker"].tolist()
        raise AnalisisError(
            "ANÁLISIS NO EJECUTADO: el universo cerrado no cumple la cobertura mínima. "
            f"Activos: {', '.join(malos)}"
        )

    precios = precios.dropna()
    if len(precios) < dias:
        raise AnalisisError(f"Hay menos de {dias} observaciones útiles tras alinear fechas.")

    precios_activos = precios[TICKERS]
    precios_bench = precios[benchmark]
    ret_act = precios_activos.pct_change().dropna()[TICKERS]
    ret_bench = precios_bench.pct_change().dropna()
    ret_act, ret_bench = ret_act.align(ret_bench, join="inner", axis=0)
    if ret_act.isna().any().any() or np.isinf(ret_act.values).any():
        raise AnalisisError("Los retornos contienen nulos o infinitos.")

    _avisar(progress, 0.25, "Calculando métricas por activo y optimizando Markowitz…")
    metricas = pd.DataFrame({
        "Clase de Activo": [CLASES_ACTIVO[t] for t in TICKERS],
        "Retorno anualizado": (ret_act.mean() * dias).reindex(TICKERS).values,
        "Volatilidad anualizada": (ret_act.std() * np.sqrt(dias)).reindex(TICKERS).values,
    }, index=TICKERS)
    metricas["Sharpe"] = (metricas["Retorno anualizado"] - rf) / metricas["Volatilidad anualizada"]
    corr = ret_act.corr()
    metricas["Correlación promedio"] = corr.reindex(index=TICKERS, columns=TICKERS).apply(
        lambda s: s[s < 0.999].mean()
    )
    metricas.index.name = "Ticker"

    ret_anual = ret_act.mean() * dias
    cov_anual = ret_act.cov() * dias
    cov_anual, cov_ajustada = regularizar_covarianza(cov_anual.values)
    cov_anual = pd.DataFrame(cov_anual, index=TICKERS, columns=TICKERS)
    n = len(TICKERS)

    w_sharpe = optimizar("sharpe", n, ret_anual.values, cov_anual.values, rf, peso_min, peso_max, semilla)
    w_minvol = optimizar("minvol", n, ret_anual.values, cov_anual.values, rf, peso_min, peso_max, semilla + 7)
    w_sharpe[w_sharpe < 1e-8] = 0.0
    w_minvol[w_minvol < 1e-8] = 0.0

    def metricas_w(w):
        r = retorno_portafolio(w, ret_anual.values)
        v = volatilidad_portafolio(w, cov_anual.values)
        s = (r - rf) / v if v else -np.inf
        return r, v, s

    r_sh, v_sh, s_sh = metricas_w(w_sharpe)
    r_mv, v_mv, s_mv = metricas_w(w_minvol)
    r_bm = float(ret_bench.mean() * dias)
    v_bm = float(ret_bench.std() * np.sqrt(dias))
    s_bm = (r_bm - rf) / v_bm if v_bm else -np.inf

    _avisar(progress, 0.40, "Simulando frontera eficiente…")
    vols, rets, sharpes = [], [], []
    for _ in range(n_front):
        w = pesos_aleatorios(n, peso_min, peso_max, rng)
        rr, vv, ss = metricas_w(w)
        rets.append(rr)
        vols.append(vv)
        sharpes.append(ss)
    frontera = pd.DataFrame({"Volatilidad": vols, "Retorno": rets, "Sharpe": sharpes})

    ret_sh_serie = ret_act.values @ w_sharpe
    ret_mv_serie = ret_act.values @ w_minvol
    ret_bm_serie = ret_bench.values

    riesgo_sh = var_cvar_diario(ret_sh_serie, capital)
    riesgo_mv = var_cvar_diario(ret_mv_serie, capital)
    riesgo_bm = var_cvar_diario(ret_bm_serie, capital)

    _avisar(progress, 0.55, "Simulando riesgo anual (block bootstrap)…")
    boot_sh = block_bootstrap(ret_sh_serie, capital, n_boot, horizonte, bloque, semilla)
    boot_mv = block_bootstrap(ret_mv_serie, capital, n_boot, horizonte, bloque, semilla + 1)
    boot_bm = block_bootstrap(ret_bm_serie, capital, n_boot, horizonte, bloque, semilla + 2)

    def escenarios(r, v):
        return {
            "adverso": capital * (1 + r - v),
            "esperado": capital * (1 + r),
            "favorable": capital * (1 + r + v),
        }

    esc_sh, esc_mv, esc_bm = escenarios(r_sh, v_sh), escenarios(r_mv, v_mv), escenarios(r_bm, v_bm)

    _avisar(progress, 0.78, "Validando fuera de muestra…")
    split = int(len(ret_act) * prop_train)
    train, test = ret_act.iloc[:split], ret_act.iloc[split:]
    bench_test = ret_bench.iloc[split:]
    ret_train = train.mean() * dias
    cov_train, _ = regularizar_covarianza((train.cov() * dias).values)
    w_oos = optimizar("sharpe", n, ret_train.values, cov_train, rf, peso_min, peso_max, semilla + 3)
    ret_oos = test.values @ w_oos
    r_oos = float(ret_oos.mean() * dias)
    v_oos = float(ret_oos.std() * np.sqrt(dias))
    s_oos = (r_oos - rf) / v_oos if v_oos else -np.inf
    r_bm_oos = float(bench_test.mean() * dias)
    v_bm_oos = float(bench_test.std() * np.sqrt(dias))
    s_bm_oos = (r_bm_oos - rf) / v_bm_oos if v_bm_oos else -np.inf
    mdd_oos = max_drawdown(ret_oos)
    acum_oos = (1 + pd.Series(ret_oos, index=test.index)).cumprod()
    acum_bm_oos = (1 + bench_test).cumprod()

    asign_sh = tabla_asignacion(w_sharpe, TICKERS, metricas, capital, tipo_cambio, r_sh)
    asign_mv = tabla_asignacion(w_minvol, TICKERS, metricas, capital, tipo_cambio, r_mv)
    clases_sh = resumen_clases(asign_sh)
    clase_alerta = clases_sh.loc[clases_sh["Peso"] > 0.70, "Clase de Activo"].tolist()

    filas = [
        ("Universo cerrado", "20 activos válidos", str(len(TICKERS)), len(TICKERS) == 20),
        ("Peso mínimo", "≥ 0%", f"{w_sharpe.min():.2%}", w_sharpe.min() >= peso_min - 1e-6),
        ("Peso máximo", "≤ 15%", f"{w_sharpe.max():.2%}", w_sharpe.max() <= peso_max + 1e-6),
        ("Sin ventas en corto", "pesos ≥ 0%", f"{w_sharpe.min():.2%}", w_sharpe.min() >= -1e-8),
        ("Sin apalancamiento", "suma = 100%", f"{w_sharpe.sum():.2%}", abs(w_sharpe.sum() - 1) <= 1e-6),
        ("Cobertura de datos", f"≥ {cobertura_min:.0%}", f"{calidad['Cobertura'].min():.1%}", True),
        ("Horizonte", "12 meses / 252 días", str(horizonte), horizonte == 252),
        ("Sharpe fuera de muestra", f"≥ {sharpe_oos_min:.2f}", f"{s_oos:.2f}", s_oos >= sharpe_oos_min),
        ("VaR anual 95%", f"≤ {var_max:.0%}", f"{boot_sh['var_95']:.2%}", boot_sh["var_95"] <= var_max),
        ("Drawdown simulado P95", f"≤ {mdd_max:.0%}", f"{boot_sh['mdd_p95']:.2%}", boot_sh["mdd_p95"] <= mdd_max),
        ("Trazabilidad", "100%", "Métricas calculadas", True),
    ]
    cumplimiento = pd.DataFrame(filas, columns=["Criterio", "Umbral", "Resultado", "ok"])
    cumplimiento["Estado"] = np.where(cumplimiento["ok"], "CUMPLE", "NO CUMPLE")
    incumplidos = cumplimiento.loc[~cumplimiento["ok"], "Criterio"].tolist()
    elegible = len(incumplidos) == 0

    _avisar(progress, 1.0, "Análisis listo.")
    return {
        "params": cfg,
        "fecha_descarga": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "fecha_inicio": precios.index.min().strftime("%Y-%m-%d"),
        "fecha_fin": precios.index.max().strftime("%Y-%m-%d"),
        "observaciones": int(len(ret_act)),
        "calidad": calidad,
        "metricas": metricas.reset_index(),
        "correlacion": corr,
        "frontera": frontera,
        "max_sharpe": {"retorno": r_sh, "vol": v_sh, "sharpe": s_sh, "pesos": w_sharpe},
        "min_vol": {"retorno": r_mv, "vol": v_mv, "sharpe": s_mv, "pesos": w_minvol},
        "benchmark": {"retorno": r_bm, "vol": v_bm, "sharpe": s_bm},
        "asignacion_sharpe": asign_sh,
        "asignacion_minvol": asign_mv,
        "clases_sharpe": clases_sh,
        "alerta_clase": clase_alerta,
        "riesgo_diario": {"sharpe": riesgo_sh, "minvol": riesgo_mv, "bench": riesgo_bm},
        "bootstrap": {"sharpe": boot_sh, "minvol": boot_mv, "bench": boot_bm},
        "escenarios": {"sharpe": esc_sh, "minvol": esc_mv, "bench": esc_bm},
        "oos": {
            "sharpe": s_oos,
            "retorno": r_oos,
            "vol": v_oos,
            "sharpe_bench": s_bm_oos,
            "mdd": mdd_oos,
            "inicio": test.index.min().strftime("%Y-%m-%d"),
            "fin": test.index.max().strftime("%Y-%m-%d"),
            "acum": acum_oos,
            "acum_bench": acum_bm_oos,
        },
        "cumplimiento": cumplimiento,
        "incumplidos": incumplidos,
        "elegible": elegible,
        "cov_ajustada": cov_ajustada,
        "mdd_historico": {
            "sharpe": max_drawdown(ret_sh_serie),
            "minvol": max_drawdown(ret_mv_serie),
            "bench": max_drawdown(ret_bm_serie),
        },
    }
