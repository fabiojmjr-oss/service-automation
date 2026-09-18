# `svclab.bot` — a bot that runs, and cannot see the answer

*[Português](#svclabbot--um-bot-que-roda-e-não-consegue-ver-a-resposta)*

## The business problem

Every comparison between two automation policies is really a comparison between two datasets: the
bot changed, and so did the month, the mix, the promotion that drove traffic and the agent who quit.
This module removes that. A policy meets the **same** forty thousand contacts with the same
difficulties, the same patience and the same facts, and the outcome is a deterministic function of
the two. Any difference between two policies is the policy.

And it draws a line that automation business cases never draw. A policy sees the **predicted**
intent and the turn number. It does not see how hard the contact is, whether the customer would have
managed alone, or how long a human would have taken — those are the columns
[`svclab.synth`](../synth/README.md) calls truth. Every business case ever written was built by
somebody who could see the outcome column. The reason those cases are wrong is that the bot could
not.

## The decision it enables

1. **How long should the bot try before handing over?** Which is a turn budget, and it trades
   escalations for abandonments rather than buying resolutions.
2. **What should it refuse to attempt?** Which is a list of intents, and it applies to what the
   classifier *thinks* it is looking at.
3. **And is the difference between two policies real?** Which needs the same contacts on both sides.

## Usage

```python
from svclab.bot import GUARDED, THREE_TURNS, BotPolicy, run
from svclab.synth import generate_dataset

data = generate_dataset()
treated = data.contacts[~data.contacts["holdout"]]

outcomes = run(treated, THREE_TURNS)
outcomes["outcome"].value_counts()  # resolved-by-bot, escalated, abandoned, straight-to-human
outcomes["is_repeat"].sum()  # the second contacts the policy generated

# A policy is four fields, and one of them is a refusal list.
mine = BotPolicy(name="mine", turn_budget=2, straight_to_human=frozenset({"reclamacao"}))
run(treated, mine).equals(run(treated, mine))  # True: no draw happens here
```

## Result 1: the session, and the five ways it can end

| Outcome | What happened |
| --- | --- |
| `resolved-by-bot` | The contact was resolvable, correctly classified, and the turns it needed fitted inside both the budget and the customer's patience. |
| `escalated` | The budget ran out first. A human then pays the handling time **plus** the handoff — 55 seconds of reading a conversation somebody else had. |
| `abandoned` | The customer's patience ran out first. Nobody pays anything, which is why this outcome flatters every cost model built on hours. |
| `straight-to-human` | The holdout arm, or an intent the policy refuses, or a policy with no turns at all. |
| `repeat-to-human` | A **second row**: the contact ended unresolved, the customer was going to come back, and would not have got there alone. |

That last row is the design decision that matters. The first version of this module charged a repeat
as extra seconds on the original contact. It is arithmetically tidier and it destroys the finding:
with repeats folded into seconds, the human-handled share per contact is exactly one minus the
containment rate, so deflection and containment become the same number by construction. A queue does
not receive a longer first conversation. It receives a second one.

## Result 2: the four policies, and what a turn budget actually buys

| Policy | Turns | Refuses | What it is |
| --- | --- | --- | --- |
| `human-only` | 0 | — | The control arm, and a legitimate policy to price. |
| `three-turns` | 3 | — | The ordinary deployment. |
| `patient` | 6 | — | Twice the budget, on the theory that more tries means more resolutions. |
| `guarded` | 3 | `reembolso`, `reclamacao` | The policy everybody writes down after the first complaint reaches a director. |

A longer budget does **not** mainly buy resolutions. It converts escalations into abandonments. On
the treated arm, at three turns the split is **39.35% escalated against 33.16% abandoned**; at six
turns it is **18.31% against 53.77%** — while resolution by the bot barely moves, from **27.49% to
27.92%**. The extra turns are spent on contacts that were never resolvable, and the customer leaves
before the bot gives up.

That is worth stating plainly because it inverts the intuition the budget is chosen on. A patient bot
looks better on every containment definition precisely because abandonment is not a transfer.

## Result 3: a refusal list protects the intent it names, not the contact

`guarded` refuses `reembolso` and `reclamacao`, and it applies the rule to the **predicted** label.
The classifier's accuracy falls with difficulty — from a declared ceiling of 0.81 on `reclamacao` to
zero at the hard end — and a complaint read as a tracking question walks straight past the rule
written to protect it. The policy is doing exactly what it was told; the protection is only as good
as the classifier under it, and the classifier is worst on precisely the contacts the rule exists
for.

## Assumptions and limitations

- **Every number here comes from a seeded synthetic generator.** No employer, client, vendor or
  platform data is used anywhere, and no contact centre was read or approximated to build it. See
  [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **There is no language model in this repository, and that is deliberate.** The bot's resolution is
  a declared function of the contact rather than a generated reply. A model would make every
  published figure unreproducible — a new model version changes the output and the claims silently
  become false — and it would require secrets in a public repository. What is being measured here is
  a *policy*, and a policy is arithmetic.
- **One repeat, not a chain.** A customer whose second attempt also fails does not come back a third
  time, which makes every figure here an **underestimate** of what an automation costs the queue.
- **A repeat costs the same handling time as the original plus the handoff.** It is the same
  unresolved issue, so the same time is the defensible assumption; a customer arriving annoyed for
  the second time plausibly costs more.
- **The classifier is a declared accuracy curve, not a model.** It has no confidence score, so a
  policy here cannot threshold on one. Cost-sensitive thresholds are a later wave's subject.
- **Patience is exponential in turns, with a declared mean of four.** That parameter drives the
  abandonment volume directly, and it is the single most consequential assumption in the module. The
  qualitative finding does not depend on its value; the abandonment figures do.
- **A bot turn costs the customer 45 seconds and nothing else.** No token cost, no licence fee, no
  build effort. Every cost in this repository is a queue cost, so a complete case would be worse for
  automation than these figures, not better.

## Sources

Cited as the origin of a *method*, never as a source of any number in these tables.

- Erlang, A. K. (1917). *Solution of Some Problems in the Theory of Probabilities of Significance in
  Automatic Telephone Exchanges.* — the queue the escalations arrive in, priced in
  [`svclab.capacity`](../capacity/README.md).
- Gans, N., Koole, G., Mandelbaum, A. (2003). *Telephone Call Centers: Tutorial, Review, and Research
  Prospects.* Manufacturing & Service Operations Management 5(2). — abandonment and patience as a
  modelled quantity rather than a residual.

---

# `svclab.bot` — um bot que roda e não consegue ver a resposta

*[English](#svclabbot--a-bot-that-runs-and-cannot-see-the-answer)*

## O problema de negócio

Toda comparação entre duas políticas de automação é, na verdade, uma comparação entre dois conjuntos
de dados: o bot mudou, e mudaram também o mês, o mix, a promoção que puxou tráfego e o atendente que
pediu demissão. Este módulo remove isso. Uma política encontra os **mesmos** quarenta mil contatos,
com as mesmas dificuldades, a mesma paciência e os mesmos fatos, e o resultado é função determinística
dos dois. Qualquer diferença entre duas políticas é a política.

E ele traça uma linha que business cases de automação nunca traçam. Uma política vê a intenção
**prevista** e o número do turno. Não vê o quão difícil é o contato, se o cliente teria resolvido
sozinho, nem quanto tempo um humano levaria — essas são as colunas que o
[`svclab.synth`](../synth/README.md) chama de verdade. Todo business case já escrito foi construído
por alguém que podia ver a coluna de resultado. O motivo pelo qual esses cases estão errados é que o
bot não podia.

## A decisão que habilita

1. **Por quanto tempo o bot deve tentar antes de transferir?** Que é um orçamento de turnos, e ele
   troca escalonamentos por abandonos em vez de comprar resoluções.
2. **O que ele deve se recusar a tentar?** Que é uma lista de intenções, e ela se aplica ao que o
   classificador *pensa* estar olhando.
3. **E a diferença entre duas políticas é real?** Que exige os mesmos contatos nos dois lados.

## Uso

```python
from svclab.bot import GUARDED, THREE_TURNS, BotPolicy, run
from svclab.synth import generate_dataset

data = generate_dataset()
treated = data.contacts[~data.contacts["holdout"]]

outcomes = run(treated, THREE_TURNS)
outcomes["outcome"].value_counts()  # resolved-by-bot, escalated, abandoned, straight-to-human
outcomes["is_repeat"].sum()  # os segundos contatos que a política gerou

# Uma política são quatro campos, e um deles é uma lista de recusa.
minha = BotPolicy(name="minha", turn_budget=2, straight_to_human=frozenset({"reclamacao"}))
run(treated, minha).equals(run(treated, minha))  # True: nenhum sorteio acontece aqui
```

## Resultado 1: a sessão, e as cinco formas de ela terminar

| Resultado | O que aconteceu |
| --- | --- |
| `resolved-by-bot` | O contato era resolvível, foi classificado certo, e os turnos necessários couberam no orçamento e na paciência do cliente. |
| `escalated` | O orçamento acabou primeiro. Um humano paga então o tempo de atendimento **mais** o handoff — 55 segundos lendo uma conversa que outro teve. |
| `abandoned` | A paciência do cliente acabou primeiro. Ninguém paga nada, e é por isso que este resultado lisonjeia todo modelo de custo construído sobre horas. |
| `straight-to-human` | O braço de controle, uma intenção que a política recusa, ou uma política sem turnos. |
| `repeat-to-human` | Uma **segunda linha**: o contato terminou sem resolução, o cliente ia voltar, e não teria resolvido sozinho. |

Essa última linha é a decisão de desenho que importa. A primeira versão deste módulo cobrava o
recontato como segundos extras no contato original. É aritmeticamente mais limpo e destrói o achado:
com recontatos dobrados em segundos, a fração atendida por humano por contato é exatamente um menos a
taxa de contenção, então desvio e contenção viram o mesmo número por construção. Uma fila não recebe
uma primeira conversa mais longa. Recebe uma segunda.

## Resultado 2: as quatro políticas, e o que um orçamento de turnos realmente compra

| Política | Turnos | Recusa | O que é |
| --- | --- | --- | --- |
| `human-only` | 0 | — | O braço de controle, e uma política legítima de precificar. |
| `three-turns` | 3 | — | A implantação comum. |
| `patient` | 6 | — | O dobro do orçamento, na teoria de que mais tentativas significam mais resoluções. |
| `guarded` | 3 | `reembolso`, `reclamacao` | A política que todo mundo escreve depois que a primeira reclamação chega a um diretor. |

Um orçamento maior **não** compra principalmente resoluções. Ele converte escalonamentos em
abandonos. No braço tratado, com três turnos a divisão é **39,35% escalonado contra 33,16%
abandonado**; com seis turnos é **18,31% contra 53,77%** — enquanto a resolução pelo bot quase não se
move, de **27,49% para 27,92%**. Os turnos extras são gastos em contatos que nunca foram resolvíveis,
e o cliente vai embora antes de o bot desistir.

Vale dizer isso com clareza porque inverte a intuição sobre a qual o orçamento é escolhido. Um bot
paciente parece melhor em toda definição de contenção precisamente porque abandono não é
transferência.

## Resultado 3: uma lista de recusa protege a intenção que ela nomeia, não o contato

O `guarded` recusa `reembolso` e `reclamacao`, e aplica a regra ao rótulo **previsto**. A acurácia do
classificador cai com a dificuldade — de um teto declarado de 0,81 em `reclamacao` a zero na ponta
difícil — e uma reclamação lida como pergunta de rastreio passa direto pela regra escrita para
protegê-la. A política está fazendo exatamente o que foi mandada; a proteção vale o que vale o
classificador embaixo dela, e o classificador é pior exatamente nos contatos para os quais a regra
existe.

## Premissas e limitações

- **Todo número aqui vem de um gerador sintético com semente.** Nenhum dado de empregador, cliente,
  fornecedor ou plataforma é usado em qualquer parte, e nenhuma central de atendimento foi lida ou
  aproximada para construí-lo. Ver [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **Não existe modelo de linguagem neste repositório, e isso é deliberado.** A resolução do bot é
  função declarada do contato, não uma resposta gerada. Um modelo tornaria toda cifra publicada
  irreproduzível — uma nova versão muda a saída e as afirmações ficam silenciosamente falsas — e
  exigiria segredos num repositório público. O que se mede aqui é uma *política*, e política é
  aritmética.
- **Um recontato, não uma cadeia.** Um cliente cuja segunda tentativa também falha não volta uma
  terceira vez, o que torna toda cifra aqui uma **subestimativa** do que a automação custa à fila.
- **Um recontato custa o mesmo tempo de atendimento do original mais o handoff.** É o mesmo problema
  não resolvido, então o mesmo tempo é a premissa defensável; um cliente que chega irritado pela
  segunda vez plausivelmente custa mais.
- **O classificador é uma curva de acurácia declarada, não um modelo.** Não tem score de confiança,
  então uma política aqui não pode usar limiar. Limiares sensíveis a custo são assunto de uma onda
  posterior.
- **A paciência é exponencial em turnos, com média declarada de quatro.** Esse parâmetro governa
  diretamente o volume de abandono, e é a premissa mais consequente do módulo. O achado qualitativo
  não depende do valor; as cifras de abandono dependem.
- **Um turno de bot custa 45 segundos do cliente e nada mais.** Sem custo de token, sem licença, sem
  esforço de construção. Todo custo neste repositório é custo de fila, então um case completo seria
  pior para a automação do que estas cifras, não melhor.

## Fontes

Citadas como origem de um *método*, nunca como fonte de qualquer número destas tabelas.

- Erlang, A. K. (1917). *Solution of Some Problems in the Theory of Probabilities of Significance in
  Automatic Telephone Exchanges.* — a fila em que os escalonamentos chegam, precificada em
  [`svclab.capacity`](../capacity/README.md).
- Gans, N., Koole, G., Mandelbaum, A. (2003). *Telephone Call Centers: Tutorial, Review, and Research
  Prospects.* Manufacturing & Service Operations Management 5(2). — abandono e paciência como
  quantidade modelada em vez de resíduo.
