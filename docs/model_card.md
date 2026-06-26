# 🗂️ Model Card — Preditor de Risco de Defasagem (Passos Mágicos)

Documento técnico do modelo de machine learning do projeto, no formato *model card*.

---

## 1. Visão geral

| Item | Descrição |
|---|---|
| **Nome** | Preditor de Risco de Defasagem Educacional (T → T+1) |
| **Objetivo** | Estimar a probabilidade de um aluno apresentar defasagem moderada/severa **no ano seguinte** |
| **Tipo** | Classificação binária |
| **Algoritmo** | LightGBM (produção), calibrado; XGBoost como benchmark |
| **Saída** | Probabilidade calibrada de risco (0–1) + classificação por faixa |
| **Versão dos dados** | PEDE 2020–2022 (Associação Passos Mágicos) |

---

## 2. Uso pretendido

- **Para quê:** apoiar a equipe pedagógica na **identificação precoce** de alunos com risco de
  defasagem, permitindo intervenção antecipada.
- **Por quem:** equipe técnica/pedagógica da ONG.
- **Como:** o usuário informa os indicadores do **ano corrente** e recebe a probabilidade de
  defasagem **no ano seguinte**.
- **Fora de escopo:** não substitui avaliação pedagógica humana; não deve ser usado para punir,
  ranquear publicamente ou excluir alunos. É ferramenta de **priorização de atenção**, não de decisão
  automática.

---

## 3. Desenho do modelo (anti-leakage)

- **Features:** indicadores do **ano T** — INDE, IAN, IDA, IEG, IAA, IPS, IPP, IPV, PEDRA (ordinal),
  FASE (0–8), Ponto de Virada.
- **Alvo:** `IAN ≤ 5` (defasagem moderada/severa) no **ano T+1**.
- **Transições empilhadas:** 2020→2021 e 2021→2022 (914 pares aluno-ano).
- **Anti-leakage:** nenhuma informação do ano-alvo entra como feature. Usar `IAN_T` é autoregressão
  legítima (passado prevendo futuro), não vazamento.

---

## 4. Validação e métricas

Duas estratégias complementares, com resultados convergentes:

| Estratégia | AUC-PR | Observação |
|---|---|---|
| **Out-of-time** (treina 2020→2021, testa 2021→2022) | **0,886** | espelha o uso real em produção |
| **StratifiedGroupKFold por aluno** | **0,887 ± 0,024** | controla vazamento aluno-safra |

Demais métricas (teste out-of-time): **AUC-ROC 0,753** · Recall(risco) 0,74 · Precision(risco) 0,85
· F1 0,79. **Baseline** (prevalência) = 0,673 → **lift +0,21**.

- **Métrica norte:** AUC-PR e **recall da classe de risco** — não acurácia (a classe de risco é
  majoritária; acurácia seria enganosa).
- **Ponto de operação:** threshold **0,24**, calibrado para **recall ≥ 0,85** (prioriza não deixar
  passar alunos em risco, aceitando mais falsos positivos).
- **Calibração:** sigmoid; Brier 0,213 → **0,176**.

---

## 5. Interpretabilidade

Drivers de maior peso (importância por ganho + SHAP): **INDE, IEG e IPV**. O risco futuro é previsto
sobretudo pelo **perfil de desenvolvimento e engajamento** do aluno — e **não** pelo nível de
defasagem atual (IAN tem peso baixo). Leitura acionável: agir sobre o **engajamento** é a principal
alavanca de prevenção.

---

## 6. Limitações

- **Janela pandêmica:** os dados cobrem 2020–2022; a coorte pareada mostra **queda** do INDE no
  período (efeito COVID). O modelo prevê risco nesse contexto, que pode não se repetir em anos típicos.
- **IAN discreto:** apenas 3 níveis (2,5/5/10), o que limita a granularidade do alvo.
- **Amostra:** 914 transições — robusto, mas modesto. Reestimar a cada novo ciclo do PEDE.
- **Recorrência de alunos** entre as duas safras é controlada no GroupKFold, mas presente no split
  out-of-time (documentado).
- **Generalização:** treinado em dados de uma única ONG; não validado em outras populações.

---

## 7. Ética e privacidade

- **Dados sensíveis de menores:** o dataset bruto e a base tratada (`pede_long`, que contém `NOME`)
  **não são versionados** no repositório público. Apenas o modelo treinado é distribuído.
- **Risco de estigmatização:** a saída deve orientar **apoio**, nunca rotulação negativa do aluno.
- **Humano no circuito:** toda decisão pedagógica permanece com a equipe; o modelo informa, não decide.

---

## 8. Manutenção

- **Reestimar** a cada novo ciclo anual do PEDE (novas transições T→T+1).
- **Monitorar** mudança de distribuição dos indicadores (drift), sobretudo pós-pandemia.
- **Revisar** o threshold conforme a capacidade de atendimento da equipe.

---

_Datathon FIAP PosTech — Fase 5 · Case Passos Mágicos._
