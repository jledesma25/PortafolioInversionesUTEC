# Portafolio Óptimo · Grupo 3

**Asistente cuantitativo** para el comité de inversión — Maestría Management Analytics & IA · UTEC  
Curso: *Programación para ejecutivos*

Aplicación web en **Streamlit** que presenta un portafolio óptimo (Máximo Sharpe / Markowitz), permite simular escenarios, evaluar riesgo frente al S&P 500 y consultar un asistente acotado a los datos del mandato.

---

## Qué hace la app

| Módulo UI | Función |
|-----------|---------|
| **Resumen** | KPIs, elegibilidad, recomendación ejecutiva, exportación CSV/TXT/PDF |
| **Simulador** | Ajuste de capital, perfil, horizonte, nº de activos, moneda |
| **Cartera** | Pesos por ticker y por clase de activo (gráficos Plotly) |
| **Riesgo** | VaR / CVaR, volatilidad, comparación vs benchmark |
| **Desempeño** | Retorno esperado, escenarios adverso / esperado / favorable |
| **El asistente** | Chat por intenciones (sin LLM externo); solo responde sobre el portafolio |

Extras: **modo claro / oscuro**, barra de parámetros en vivo, recorrido guiado del comité.

---

## Stack técnico

- **Python 3.10+**
- **Streamlit** — interfaz y deploy
- **Pandas / NumPy / SciPy** — datos y métricas
- **Plotly** — gráficos interactivos
- Datos calibrados del notebook Colab del Grupo 3 (`data/grupo3/`)

**Identidad visual:** modo oscuro forest (`#0D1110`), cards `#1A231F`, acento coral `#E69984`, sage `#94B8A3`, tipografía Inter + Playfair Display.

La app en producción usa un **simulador local** (`simulador.py`) sobre métricas ya calibradas. El módulo `motor.py` contiene el pipeline cuantitativo completo (yfinance + Markowitz + bootstrap) usado en el análisis original.

---

## Cómo ejecutar en local

```bash
cd App
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Abrir: [http://localhost:8501](http://localhost:8501)

---

## Estructura del proyecto

```text
App/
├── app.py                  # UI Streamlit (páginas, CSS, gráficos, export)
├── simulador.py            # Simulación en vivo (sin Yahoo Finance)
├── datos_grupo3.py         # Parámetros, pesos y carga de CSV Grupo 3
├── agente_chat.py          # Asistente por matching de intenciones
├── presentacion.py         # Textos ejecutivos, glosario, recorrido
├── motor.py                # Motor cuantitativo completo (laboratorio)
├── requirements.txt
├── .streamlit/config.toml  # Tema base Streamlit
├── assets/                 # Logos e ilustración hero
├── data/grupo3/            # CSV exportados desde Colab
└── docs/
    └── DOCUMENTACION_TECNICA.md   # Detalle técnico ampliado
```

| Archivo | Responsabilidad |
|---------|-----------------|
| `app.py` | Orquesta la UI, `session_state`, tema, navegación y visualización |
| `simulador.py` | Recalcula pesos/métricas al cambiar perfil, capital, horizonte o nº de activos |
| `datos_grupo3.py` | Fuente de verdad del mandato (capital, TC, RF, pesos Máx. Sharpe, CSV) |
| `agente_chat.py` | Clasifica la pregunta → responde solo con datos del `sim` actual |
| `presentacion.py` | Frases para el comité y pasos del recorrido demo |
| `motor.py` | Descarga de precios, optimización Markowitz, VaR bootstrap, gobernanza |

Documentación ampliada (arquitectura, flujo de datos, decisiones de diseño):

- Markdown: [`docs/DOCUMENTACION_TECNICA.md`](docs/DOCUMENTACION_TECNICA.md)
- PDF: [`docs/DOCUMENTACION_TECNICA.pdf`](docs/DOCUMENTACION_TECNICA.pdf)

---

## Parámetros del mandato (Grupo 3)

| Parámetro | Valor |
|-----------|-------|
| Capital | S/ 1,000,000 |
| Horizonte | 12 meses (252 días) |
| Historia | 6 años |
| Tipo de cambio PEN/USD | 3.39 |
| Tasa libre de riesgo | ~4–4.5% anual |
| Benchmark | ^GSPC (S&P 500) |
| Universo → cartera | 50 evaluados → 20 seleccionados |
| Peso máximo por activo | 15% |
| Estrategia | Máximo Sharpe (Markowitz) |
| Bootstrap (artefacto Colab) | 10,000 sims · bloque 21 días |

---

## Deploy

Compatible con **Streamlit Community Cloud**: apuntar el repo a `app.py` e instalar desde `requirements.txt`.

---

## Autores

**Grupo 3** · UTEC · Management Analytics & IA
