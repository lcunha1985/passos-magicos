# 📖 Dicionário de Dados — Projeto Passos Mágicos

Documento de referência dos dados usados no projeto. Cobre três camadas: os **indicadores
educacionais** do programa, o **schema bruto** do dataset PEDE e o **schema tratado** (formato long)
gerado na Fase 1.

---

## 1. Indicadores educacionais (escala 0–10)

O programa Passos Mágicos avalia cada aluno por um conjunto de indicadores. O **INDE** é o índice
síntese, composto pelos demais.

| Código | Nome | O que mede | Direção |
|---|---|---|---|
| **INDE** | Índice de Desenvolvimento Educacional | Nota global; síntese ponderada dos demais indicadores | maior = melhor |
| **IAN** | Índice de Adequação de Nível | Adequação série/idade (defasagem) | maior = mais adequado (menos defasagem) |
| **IDA** | Índice de Desempenho Acadêmico | Desempenho em avaliações | maior = melhor |
| **IEG** | Índice de Engajamento | Participação, frequência, entrega | maior = melhor |
| **IAA** | Índice de Autoavaliação | Percepção do próprio aluno sobre si | maior = melhor |
| **IPS** | Índice Psicossocial | Aspectos emocionais e sociais | maior = melhor |
| **IPP** | Índice Psicopedagógico | Avaliação psicopedagógica | maior = melhor |
| **IPV** | Índice do Ponto de Virada | Protagonismo / maturidade do aluno | maior = melhor |

### Escala do IAN e leitura de defasagem
O IAN é **discreto** no dataset (valores 2,5 / 5,0 / 10,0) e mapeia diretamente a defasagem:

| IAN | Interpretação | Defasagem média observada |
|---|---|---|
| 10,0 | Adequado ao nível | ~0 (no nível) |
| 5,0 | Defasagem moderada | ~1 ano atrás |
| 2,5 | Defasagem severa | ~3 anos atrás |

> Validação: `corr(IAN, DEFASAGEM_2021) = +0,858`. **Target do modelo:** `IAN ≤ 5` no ano seguinte.

---

## 2. PEDRA e FASE (não confundir)

São dimensões **diferentes**, frequentemente confundidas:

- **PEDRA** — estágio de maturidade no programa, ordinal crescente:
  **Quartzo (1) → Ágata (2) → Ametista (3) → Topázio (4)**.
- **FASE** — nível/série acadêmica, **numérica de 0 a 8** (0 = Alfabetização/ingressante).
  Em 2020 vem embutida em `FASE_TURMA` (ex.: `"8A"`); em 2021/2022 há a coluna `FASE` separada.

---

## 3. Schema bruto do dataset PEDE (`PEDE_PASSOS_DATASET_FIAP.csv`)

Formato **wide**: 1 linha por aluno (1.349 alunos), 69 colunas. Separador `;`, decimal `.`,
encoding UTF-8. Colunas sufixadas por ano (ex.: `IDA_2020`). Anos: **2020, 2021, 2022**.

| Campo (base) | Anos | Tipo | Descrição |
|---|---|---|---|
| NOME | — | texto | Identificador do aluno (anonimizado ALUNO-N) |
| INDE / IAA / IEG / IPS / IDA / IPP / IPV / IAN | 2020–2022 | numérico | Indicadores (ver seção 1) |
| PEDRA | 2020–2022 | categórico | Quartzo / Ágata / Ametista / Topázio |
| FASE | 2021–2022 | numérico | Nível acadêmico 0–8 |
| FASE_TURMA | 2020 | texto | Fase + turma combinadas (ex.: "8A") |
| TURMA | 2021–2022 | texto | Turma do aluno |
| PONTO_VIRADA | 2020–2022 | Sim/Não | Atingiu o ponto de virada |
| INDE_CONCEITO | 2020 | texto | Conceito (letra) do INDE |
| DEFASAGEM | 2021 | numérico | Anos de defasagem (negativo = atrás) |
| NIVEL_IDEAL | 2021–2022 | texto | Nível ideal esperado para a idade |
| INSTITUICAO_ENSINO_ALUNO | 2020–2021 | texto | Escola de origem |
| IDADE_ALUNO | 2020 | numérico | Idade |
| ANOS_PM | 2020 | numérico | Anos no programa |
| ANO_INGRESSO | 2022 | numérico | Ano de entrada |
| BOLSISTA / INDICADO_BOLSA | 2022 | Sim/Não | Situação de bolsa |
| CG / CF / CT | 2022 | numérico | Componentes de cálculo |
| NOTA_PORT / NOTA_MAT / NOTA_ING | 2022 | numérico | Notas por disciplina |
| QTD_AVAL | 2022 | numérico | Quantidade de avaliações |
| DESTAQUE_IEG / DESTAQUE_IDA / DESTAQUE_IPV | 2020,2022 | texto | Comentários qualitativos de destaque |
| REC_EQUIPE_1..4 | 2021 | texto | Recomendações da equipe |
| REC_AVA_1..4 | 2022 | texto | Recomendações de avaliação |
| SINALIZADOR_INGRESSANTE | 2021 | texto | Marcador de ingressante |

---

## 4. Schema tratado — `pede_long.parquet` (saída da Fase 1)

Formato **long**: 1 linha por **aluno × ano** (2.275 linhas), gerado pelo *reshape* wide→long.
**Não é versionado** no repositório por conter o campo `NOME` (dado de menores).

| Coluna | Tipo | Descrição |
|---|---|---|
| NOME | texto | Identificador do aluno |
| ANO | int | 2020, 2021 ou 2022 |
| INDE, IAA, IEG, IPS, IDA, IPP, IPV, IAN | float | Indicadores no ano |
| PEDRA | categórico | Estágio (Quartzo…Topázio) |
| PEDRA_ORD | int | Codificação ordinal da PEDRA (1–4) |
| FASE | float | Nível acadêmico 0–8 |
| PONTO_VIRADA | int | 1 = Sim, 0 = Não |
| DEFASAGEM_FAIXA | categórico | Faixa derivada do IAN (Adequado/Moderado/Severo) |

> **Regra de limpeza central:** ausência de avaliação em um ano é `NaN` estrutural, **nunca 0**.
> Linhas em que o aluno não foi avaliado no ano são removidas; nulos pontuais são preservados.
