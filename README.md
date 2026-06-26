# 🎓 Passos Mágicos — Predição de Risco de Defasagem Educacional

> Datathon **FIAP PosTech — Fase 5** · Case **Associação Passos Mágicos**

Solução de dados ponta a ponta para **identificar precocemente** alunos com risco de defasagem
educacional, permitindo intervenção antecipada da equipe pedagógica. Usa os indicadores do
**ano corrente** para estimar a probabilidade de defasagem **no ano seguinte**.

🔗 **App online:**  https://pmagicos-datathon.streamlit.app/

---

## 🧭 Sobre a Passos Mágicos

A Associação Passos Mágicos atua há mais de duas décadas na educação de crianças e jovens em
situação de vulnerabilidade social, usando a educação como instrumento de transformação. O dataset
**PEDE** (Pesquisa Extensiva do Desenvolvimento Educacional) consolida a avaliação multidimensional
desses alunos ao longo dos anos.

---

## 📦 Estrutura do repositório

```
passos-magicos/
├── app/
│   └── app.py                 # aplicação Streamlit
├── models/
│   └── model.joblib           # LightGBM calibrado + contrato (features, threshold, PEDRA)
├── notebooks/
│   └── 01_passos_magicos_v1.ipynb   # Fases 1–3: limpeza, EDA, storytelling, modelagem
├── reports/figures/           # figuras da análise
├── docs/
│   ├── dicionario_dados.md    # dicionário de dados (PEDE + base tratada)
│   └── model_card.md          # ficha técnica do modelo
├── requirements.txt
├── .gitignore
└── README.md
```

> **Privacidade:** o dataset bruto e a base tratada (que contêm o campo `NOME`) **não** são
> versionados — são dados sensíveis de menores. O app consome apenas o `model.joblib`.

---

## 🧠 O modelo em uma tabela

| Item | Valor |
|---|---|
| Alvo | Defasagem moderada/severa (`IAN ≤ 5`) no ano seguinte (T+1) |
| Desenho | Temporal **anti-leakage**: features de T → alvo em T+1 |
| Algoritmo | LightGBM calibrado (XGBoost como benchmark) |
| AUC-PR | **0,886** (out-of-time) · 0,887 ± 0,024 (GroupKFold por aluno) |
| Operação | threshold 0,24 — recall ≥ 0,85 |

📄 Detalhes completos em [`docs/model_card.md`](docs/model_card.md) e
[`docs/dicionario_dados.md`](docs/dicionario_dados.md).

---

## ▶️ Rodar localmente

```bash
pip install -r requirements.txt
streamlit run app/app.py
```

Abre em `http://localhost:8501`.

---

## ☁️ Deploy no Streamlit Community Cloud

1. Repositório **público** no GitHub (com o `model.joblib`).
2. Em [share.streamlit.io](https://share.streamlit.io) → **Create app** → conecte o repositório.
3. Configure:
   - **Main file path:** `app/app.py`
   - **Python version:** 3.11
4. **Deploy**. A cada `push`, o app atualiza automaticamente.

> O app gratuito **hiberna** após dias sem uso — acesse-o alguns minutos antes de avaliações/gravações.

---

## 🗂️ Funcionalidades do app

1. **Predição Individual** — indicadores via sliders + PEDRA, Fase e Ponto de Virada → probabilidade, gauge e radar.
2. **Predição em Lote** — upload de CSV para classificar vários alunos, com download do resultado.
3. **Sobre** — dicionário de indicadores e ficha técnica do modelo.

---

## 👥 Equipe

_(adicione aqui os integrantes do grupo)_

---

_Datathon FIAP PosTech — Fase 5 · Case Passos Mágicos._
