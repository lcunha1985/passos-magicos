"""
App Streamlit — Passos Mágicos · Risco de Defasagem (T → T+1)
Datathon FIAP PosTech — Fase 5

Lê o bundle models/model.joblib (LightGBM calibrado) e prevê a probabilidade de
defasagem moderada/severa (IAN ≤ 5) no ANO SEGUINTE a partir dos indicadores do ano corrente.
"""
import io
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ─────────────────────────── Configuração ────────────────────────────────────
st.set_page_config(page_title="Passos Mágicos — Risco de Defasagem",
                   page_icon="🎓", layout="wide")

MODEL_PATH = Path(__file__).parent.parent / "models" / "model.joblib"

# Medianas da base (PEDE 2020–2022) — usadas só para sinalizar indicadores baixos
MEDIANAS = {"INDE": 7.28, "IAN": 5.0, "IDA": 6.33, "IEG": 8.1,
            "IAA": 8.75, "IPS": 7.5, "IPP": 7.3, "IPV": 7.5}

INDICADORES = {
    "INDE": "Índice de Desenvolvimento Educacional — nota global (síntese)",
    "IAN": "Índice de Adequação de Nível — defasagem série/idade",
    "IDA": "Índice de Desempenho Acadêmico — desempenho em avaliações",
    "IEG": "Índice de Engajamento — participação e frequência",
    "IAA": "Índice de Autoavaliação — percepção do aluno sobre si",
    "IPS": "Índice Psicossocial — aspectos emocionais e sociais",
    "IPP": "Índice Psicopedagógico — avaliação psicopedagógica",
    "IPV": "Índice do Ponto de Virada — protagonismo do aluno",
}
INDS_8 = list(INDICADORES.keys())  # INDE, IAN, IDA, IEG, IAA, IPS, IPP, IPV


# ─────────────────────────── Carregamento do modelo ──────────────────────────
@st.cache_resource
def load_bundle():
    bundle = joblib.load(MODEL_PATH)
    return bundle


try:
    BUNDLE = load_bundle()
    MODEL = BUNDLE["model"]
    FEATURES = BUNDLE["features"]            # ordem exata exigida pelo modelo
    THRESHOLD = float(BUNDLE["threshold"])   # ponto de operação (recall ≥ 0,85)
    PEDRA_ORD = BUNDLE["pedra_ord"]          # {'Quartzo':1, ...}
    METRICAS = BUNDLE.get("metricas_teste", {})
    MODELO_OK = True
except Exception as e:  # pragma: no cover
    MODELO_OK = False
    ERRO = str(e)

PEDRAS = ["Quartzo", "Ágata", "Ametista", "Topázio"]


# ─────────────────────────── Funções utilitárias ─────────────────────────────
def montar_X(d: dict) -> pd.DataFrame:
    """Monta o DataFrame de 1 linha na ordem exata de FEATURES."""
    return pd.DataFrame([d])[FEATURES]


# Faixas de COMUNICAÇÃO (probabilidade), independentes do limiar operacional de triagem
FAIXA_MOD, FAIXA_ALTO = 0.40, 0.70


def classificar(proba: float):
    """Faixa de comunicação por probabilidade (cortes intuitivos 40%/70%)."""
    if proba < FAIXA_MOD:
        return "🟢 Baixo Risco", "#d5f5e3"
    if proba < FAIXA_ALTO:
        return "🟡 Risco Moderado", "#fdebd0"
    return "🔴 Alto Risco", "#fadbd8"


def gauge(proba: float):
    cor = "#2ecc71" if proba < FAIXA_MOD else ("#f39c12" if proba < FAIXA_ALTO else "#e74c3c")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(proba * 100, 1),
        number={"suffix": "%", "font": {"size": 36}},
        title={"text": "Probabilidade de defasagem no ano seguinte", "font": {"size": 15}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": cor},
            "steps": [
                {"range": [0, FAIXA_MOD * 100], "color": "#d5f5e3"},
                {"range": [FAIXA_MOD * 100, FAIXA_ALTO * 100], "color": "#fdebd0"},
                {"range": [FAIXA_ALTO * 100, 100], "color": "#fadbd8"},
            ],
            # linha preta = limiar operacional de triagem (recall ≥ 0,85)
            "threshold": {"line": {"color": "black", "width": 4},
                          "thickness": 0.75, "value": THRESHOLD * 100},
        },
    ))
    fig.update_layout(height=300, margin=dict(t=60, b=10))
    return fig


def radar(valores_8):
    fig = go.Figure(go.Scatterpolar(
        r=list(valores_8) + [valores_8[0]],
        theta=INDS_8 + [INDS_8[0]],
        fill="toself", name="Aluno",
        line_color="#6A2C91", fillcolor="rgba(106,44,145,0.25)",
    ))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 10])),
                      title="Perfil dos indicadores", height=380, margin=dict(t=50))
    return fig


def to_num(serie):
    """Converte série textual em número, tolerando vírgula decimal."""
    return pd.to_numeric(serie.astype(str).str.replace(",", ".", regex=False), errors="coerce")


# Nomes amigáveis das 11 features (para os insights dinâmicos)
NOME_FEATURE = {
    "INDE": "INDE (desenvolvimento global)", "IAN": "IAN (adequação de nível)",
    "IDA": "IDA (desempenho acadêmico)", "IEG": "IEG (engajamento)",
    "IAA": "IAA (autoavaliação)", "IPS": "IPS (psicossocial)",
    "IPP": "IPP (psicopedagógico)", "IPV": "IPV (ponto de virada)",
    "PEDRA_ORD": "PEDRA (estágio)", "FASE": "FASE (nível)",
    "PONTO_VIRADA": "Ponto de Virada",
}


@st.cache_resource
def get_explainers():
    """Extrai os LightGBM-base do modelo calibrado e cria TreeExplainers (uma vez)."""
    import shap
    explainers = []
    for cc in MODEL.calibrated_classifiers_:
        est = getattr(cc, "estimator", None) or getattr(cc, "base_estimator", None)
        if est is not None:
            explainers.append(shap.TreeExplainer(est))
    return explainers


def shap_contribs(Xrow):
    """Contribuição SHAP (classe risco) por feature, média do ensemble calibrado."""
    expls = get_explainers()
    vals = []
    for ex in expls:
        sv = ex.shap_values(Xrow)
        sv = sv[1] if isinstance(sv, list) else sv
        vals.append(np.asarray(sv)[0])
    return pd.Series(np.mean(vals, axis=0), index=FEATURES)


def grafico_contrib(contribs):
    c = contribs.reindex(contribs.abs().sort_values().index)
    cores = ["#e74c3c" if v > 0 else "#2ecc71" for v in c.values]
    fig = go.Figure(go.Bar(
        x=c.values, y=[NOME_FEATURE.get(f, f) for f in c.index],
        orientation="h", marker_color=cores))
    fig.update_layout(
        title="Contribuição de cada fator (SHAP) — vermelho eleva, verde reduz o risco",
        height=400, margin=dict(t=50, l=10), xaxis_title="impacto no risco")
    return fig


def recomendacoes(linha):
    """Recomendações pedagógicas dinâmicas, por regras sobre os indicadores."""
    recs = []
    if linha["IEG"] < 6:
        recs.append("Reforçar **engajamento**: frequência e participação nas atividades.")
    if linha["IDA"] < 6:
        recs.append("Oferecer **apoio acadêmico** direcionado (reforço/tutoria).")
    if linha["IPS"] < 6:
        recs.append("Acionar **acompanhamento psicossocial** com a equipe de apoio.")
    if linha["IPP"] < 6:
        recs.append("Encaminhar para **avaliação psicopedagógica**.")
    if linha["PONTO_VIRADA"] == 0:
        recs.append("Trabalhar **protagonismo** para favorecer o ponto de virada.")
    if linha["IAA"] >= 8 and linha["IDA"] < 6:
        recs.append("Aluno **superestima** o próprio desempenho — alinhar autopercepção e resultado real.")
    if not recs:
        recs.append("Perfil sem alertas evidentes — manter acompanhamento regular.")
    return recs


# ─────────────────────────── Header ──────────────────────────────────────────
st.markdown(
    """
    <div style='background: linear-gradient(135deg, #6A2C91 0%, #8E44AD 100%);
                padding: 26px 28px; border-radius: 12px; margin-bottom: 8px;'>
        <h1 style='color: white; margin: 0; font-size: 30px;'>
            🎓 Passos Mágicos — Risco de Defasagem Educacional</h1>
        <p style='color: #EADCF5; margin: 8px 0 0 0; font-size: 15px;'>
            Identificação precoce de alunos com risco de defasagem, a partir dos indicadores do
            ano corrente, para apoiar a intervenção da equipe pedagógica.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption("Datathon FIAP PosTech — Fase 5 · O modelo estima a probabilidade de defasagem "
           "(IAN ≤ 5) **no ano seguinte**.")
st.divider()

if not MODELO_OK:
    st.error(f"Não foi possível carregar o modelo em `models/model.joblib`.\n\nErro: {ERRO}")
    st.stop()

tab1, tab2, tab3 = st.tabs(["🔍 Predição Individual", "📂 Predição em Lote", "ℹ️ Sobre"])

# ══════════════════════════ TAB 1 — INDIVIDUAL ══════════════════════════════
with tab1:
    st.subheader("Informe os indicadores do aluno (ano corrente)")

    c1, c2 = st.columns(2)
    with c1:
        inde = st.slider("INDE — Desenvolvimento Global", 0.0, 10.0, 7.0, 0.1)
        ian = st.slider("IAN — Adequação de Nível", 0.0, 10.0, 5.0, 0.1)
        ida = st.slider("IDA — Desempenho Acadêmico", 0.0, 10.0, 6.0, 0.1)
        ieg = st.slider("IEG — Engajamento", 0.0, 10.0, 8.0, 0.1)
        pedra = st.selectbox("PEDRA (estágio do programa)", PEDRAS, index=1)
    with c2:
        iaa = st.slider("IAA — Autoavaliação", 0.0, 10.0, 8.0, 0.1)
        ips = st.slider("IPS — Psicossocial", 0.0, 10.0, 7.0, 0.1)
        ipp = st.slider("IPP — Psicopedagógico", 0.0, 10.0, 7.0, 0.1)
        ipv = st.slider("IPV — Ponto de Virada", 0.0, 10.0, 7.0, 0.1)
        fase = st.number_input("FASE (nível 0–8)", min_value=0, max_value=8, value=3, step=1)
        pv = st.radio("Atingiu o Ponto de Virada?", ["Não", "Sim"], horizontal=True)

    if st.button("🔮 Calcular Risco", type="primary", use_container_width=True):
        linha = {"INDE": inde, "IAN": ian, "IDA": ida, "IEG": ieg, "IAA": iaa,
                 "IPS": ips, "IPP": ipp, "IPV": ipv,
                 "PEDRA_ORD": PEDRA_ORD[pedra], "FASE": float(fase),
                 "PONTO_VIRADA": 1 if pv == "Sim" else 0}
        proba = float(MODEL.predict_proba(montar_X(linha))[0, 1])
        label, bg = classificar(proba)

        st.markdown(
            f"<div style='background:{bg}; padding:16px; border-radius:8px; "
            f"text-align:center; font-size:24px; font-weight:bold;'>{label}</div>",
            unsafe_allow_html=True,
        )
        if proba >= THRESHOLD:
            st.warning(f"🔎 **Sinalizado para acompanhamento** — probabilidade "
                       f"({proba*100:.0f}%) acima do limiar de triagem de {THRESHOLD*100:.0f}% "
                       f"(calibrado para recall ≥ 0,85 da classe de risco).")
        else:
            st.caption(f"Abaixo do limiar de triagem de {THRESHOLD*100:.0f}% — não entra na "
                       f"lista de acompanhamento prioritário.")

        g, r = st.columns(2)
        g.plotly_chart(gauge(proba), use_container_width=True)
        r.plotly_chart(radar([inde, ian, ida, ieg, iaa, ips, ipp, ipv]), use_container_width=True)

        # ── Insight dinâmico (SHAP) ────────────────────────────────────────────
        st.markdown("#### 🔎 Por que este resultado?")
        try:
            contribs = shap_contribs(montar_X(linha))
            positivos = contribs[contribs > 0].sort_values(ascending=False)
            if len(positivos):
                top = [NOME_FEATURE.get(f, f) for f in positivos.index[:3]]
                st.markdown("Principais fatores que **elevam** o risco neste aluno: "
                            + ", ".join(top) + ".")
            else:
                st.markdown("Nenhum fator empurra o risco para cima de forma relevante.")
            st.plotly_chart(grafico_contrib(contribs), use_container_width=True)
        except Exception:
            # Fallback sem SHAP: usa comparação com a mediana da base
            baixos = [NOME_FEATURE.get(k, k) for k in INDS_8 if linha[k] < MEDIANAS[k]]
            if baixos:
                st.markdown("Indicadores **abaixo da mediana da base** (pontos de atenção): "
                            + ", ".join(baixos) + ".")
            else:
                st.markdown("Todos os indicadores estão na mediana da base ou acima.")

        # ── Recomendações dinâmicas (por regras) ───────────────────────────────
        st.markdown("#### 🧭 Recomendações de acompanhamento")
        for rec in recomendacoes(linha):
            st.markdown(f"- {rec}")

# ══════════════════════════ TAB 2 — LOTE ════════════════════════════════════
with tab2:
    st.subheader("Predição em lote via CSV")
    st.markdown(
        "O arquivo deve conter as colunas: "
        "`INDE, IAN, IDA, IEG, IAA, IPS, IPP, IPV, PEDRA, FASE, PONTO_VIRADA`\n\n"
        "- `PEDRA`: Quartzo, Ágata, Ametista ou Topázio\n"
        "- `PONTO_VIRADA`: Sim/Não (ou 1/0)\n"
        "- Aceita separador `;` ou `,` e decimal `.` ou `,`."
    )
    up = st.file_uploader("Selecione o CSV", type="csv")

    if up is not None:
        try:
            txt = up.getvalue().decode("utf-8-sig", errors="ignore")
            sep = ";" if txt.splitlines()[0].count(";") >= txt.splitlines()[0].count(",") else ","
            df = pd.read_csv(io.StringIO(txt), sep=sep)

            falta = [c for c in INDS_8 + ["PEDRA", "FASE", "PONTO_VIRADA"] if c not in df.columns]
            if falta:
                st.error(f"Colunas ausentes: {falta}")
            else:
                X = pd.DataFrame()
                for ind in INDS_8:
                    X[ind] = to_num(df[ind])
                X["PEDRA_ORD"] = df["PEDRA"].astype(str).str.strip().map(PEDRA_ORD)
                X["FASE"] = to_num(df["FASE"])
                pv_map = {"Sim": 1, "Não": 0, "sim": 1, "não": 0, "1": 1, "0": 0,
                          "True": 1, "False": 0}
                X["PONTO_VIRADA"] = df["PONTO_VIRADA"].astype(str).str.strip().map(pv_map)
                X = X[FEATURES]

                proba = MODEL.predict_proba(X)[:, 1]
                out = df.copy()
                out["prob_risco"] = proba.round(4)
                out["faixa"] = np.where(
                    proba >= FAIXA_ALTO, "🔴 Alto Risco",
                    np.where(proba >= FAIXA_MOD, "🟡 Risco Moderado", "🟢 Baixo Risco"))
                out["sinalizado_triagem"] = np.where(proba >= THRESHOLD, "Sim", "Não")

                st.success(f"{len(out)} alunos processados.")
                a, b, c, d = st.columns(4)
                a.metric("🔴 Alto Risco", int((proba >= FAIXA_ALTO).sum()))
                b.metric("🟡 Risco Moderado", int(((proba >= FAIXA_MOD) & (proba < FAIXA_ALTO)).sum()))
                c.metric("🟢 Baixo Risco", int((proba < FAIXA_MOD).sum()))
                d.metric(f"🔎 Triagem (≥{THRESHOLD*100:.0f}%)", int((proba >= THRESHOLD).sum()))

                st.plotly_chart(
                    px.histogram(out, x="prob_risco", nbins=30,
                                 title="Distribuição da probabilidade de risco",
                                 color_discrete_sequence=["#6A2C91"]),
                    use_container_width=True)

                st.dataframe(out.sort_values("prob_risco", ascending=False),
                             use_container_width=True)

                csv_out = out.to_csv(index=False, sep=";", decimal=".").encode("utf-8-sig")
                st.download_button("⬇️ Baixar resultado (CSV)", data=csv_out,
                                   file_name="resultado_risco_defasagem.csv", mime="text/csv")
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")

# ══════════════════════════ TAB 3 — SOBRE ═══════════════════════════════════
with tab3:
    st.subheader("Como o modelo funciona")
    st.markdown(
        f"""
- **Desenho temporal (anti-leakage):** features do **ano T** preveem defasagem em **T+1**
  (`IAN ≤ 5` = defasagem moderada/severa). Treinado nas transições **2020→2021** e **2021→2022**.
- **Modelo:** LightGBM **calibrado** (sigmoid). Probabilidade pronta para leitura direta.
- **Ponto de operação:** limiar **{THRESHOLD*100:.0f}%**, escolhido para **recall ≥ 0,85** —
  a ferramenta prioriza *não deixar passar* alunos em risco.
"""
    )
    if METRICAS:
        st.markdown("**Desempenho no teste out-of-time (2021→2022):**")
        st.table(pd.DataFrame({"métrica": list(METRICAS.keys()),
                               "valor": [round(v, 3) for v in METRICAS.values()]}))

    st.divider()
    st.subheader("Dicionário de indicadores")
    for k, v in INDICADORES.items():
        st.markdown(f"**{k}** — {v}")

    st.divider()
    st.subheader("PEDRA — estágios do programa")
    st.markdown("Ordem de maturidade: **Quartzo → Ágata → Ametista → Topázio**.")
    st.caption("Datathon FIAP PosTech — Fase 5 | Case Passos Mágicos")
