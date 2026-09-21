# `svclab.planning` — the constraint nobody declared decided the headcount

*[Português](#svclabplanning--a-restrição-que-ninguém-declarou-decidiu-o-headcount)*

Every plan in waves 1 to 6 staffed to a **service level** and then reported the occupancy and the
abandonment it happened to land on. Wave 3 printed the sharpest version: a queue *perfectly stable* at
six agents, with 29.23% of the customers abandoning and the survivors' agents at 89.45% occupancy. Both
were outputs.

No real plan treats them that way. An occupancy ceiling is what stops attrition; an abandonment ceiling
is what the brand or the regulator asks for. So this module inverts the arithmetic: declare the
ceilings, and the headcount is whatever satisfies all of them — then say **which one decided it**.

Occupancy here is measured on the **effective** load, the work actually answered, because a customer
who abandons occupies nobody. Using the offered load overstates occupancy exactly where abandonment is
material, which is where the ceiling is being tested.

```python
from svclab.planning import Constraints, agents_at_ceiling, headroom, plan_table, scale_table

LOAD, HANDLING, PATIENCE = 7.5845, 512.25, 240.0

plan_table(
    {
        "service level only": Constraints(service_level=0.80),
        "occupancy only": Constraints(max_occupancy=0.85),
        "all three": Constraints(service_level=0.80, max_occupancy=0.85, max_abandonment=0.05),
    },
    LOAD,
    HANDLING,
    PATIENCE,
)
scale_table(
    (1.0, 20.0, 100.0), HANDLING, PATIENCE, Constraints(service_level=0.80, max_occupancy=0.85)
)
agents_at_ceiling(LOAD, 0.85)  # 9 - the napkin, before any queueing
headroom(11, LOAD, HANDLING, PATIENCE, Constraints(max_abandonment=0.05))  # how close to breaching
```

## Result 1: three ceilings, and only two of them do anything here

Wave 1's queue — 7.5845 erlangs, 512.25 seconds of handling, four minutes of patience, answered inside
twenty seconds:

| Plan | Agents | Service level | Abandonment | Occupancy | Decided by |
| --- | --- | --- | --- | --- | --- |
| service level ≥ 0.80 | **11** | 0.8368 | 0.0324 | 0.6672 | service level |
| occupancy ≤ 0.85 | **8** | **0.1751** | **0.1434** | 0.8121 | occupancy |
| abandonment ≤ 0.05 | **11** | 0.8368 | 0.0324 | 0.6672 | abandonment |
| service level + occupancy | 11 | 0.8368 | 0.0324 | 0.6672 | service level |
| **all three** | **11** | 0.8368 | 0.0324 | 0.6672 | **service level + abandonment** |

Three things, and the middle one is the trap.

**The occupancy ceiling never binds on this queue.** Eleven agents work at 66.72%, comfortably under
0.85, so the plan that wave 3 arrived at was already humane. What was not humane was the *promise* —
5.51 agents — and wave 3's "perfectly stable" six, which we come back to below.

**An occupancy ceiling on its own is satisfied by understaffing.** Eight agents hold occupancy at
0.8121 and answer **17.51%** of contacts inside the target while **14.34% of customers give up**. The
mechanism is worth being explicit about: the customers who abandon are what keeps the occupancy down.
An occupancy target chased alone rewards a queue for losing people, which is the opposite of the reason
it was introduced.

**And the service level and the abandonment ceiling arrive at the same eleven by independent routes**,
then bind **together**: at ten agents both fail. Two ceilings that agree are not redundant — they are
two arguments that cannot be negotiated away one at a time.

## Result 2: which settles what wave 3 left open

Wave 3 reported six agents as a stable queue and declined to call it a plan. Put the three ceilings to
it:

| At six agents | Value | Ceiling | Verdict |
| --- | --- | --- | --- |
| service level | 0.0000 | ≥ 0.80 | **fails** |
| occupancy | 0.8945 | ≤ 0.85 | **fails** |
| abandonment | 0.2923 | ≤ 0.05 | **fails** |

**Six agents fails all three.** "Stable" meant the queue has a steady state, which it does — with one
customer in three walking away and the rest handled by people at 89% occupancy. Stability is not a
plan, and a model that reports it as an answer is answering a question nobody asked.

And the napkin is worth pricing too. The arithmetic a plan can do without a queueing model —
`load / occupancy ceiling` — gives **9** agents. The queue needs **11**. Dividing a load by a ratio
understates the requirement by **18%**, which is wave 1's headcount error in a new costume: the
promise there multiplied a queue by a proportion, and this divides one by a proportion. Neither is a
queue.

## Result 3: and which ceiling binds depends on how big the queue is

The same three ceilings against queues of different sizes:

| Load (erlangs) | Agents | Agents per erlang | Service level | Abandonment | Occupancy | Decided by |
| --- | --- | --- | --- | --- | --- | --- |
| 1.0 | 3 | **3.0000** | 0.9159 | 0.0339 | 0.3220 | service level + abandonment |
| 2.5 | 5 | 2.0000 | 0.8818 | 0.0358 | 0.4821 | service level + abandonment |
| 7.5845 | 11 | 1.4503 | 0.8368 | 0.0324 | 0.6672 | service level + abandonment |
| 20.0 | 25 | 1.2500 | 0.8280 | 0.0232 | 0.7814 | service level |
| 50.0 | 59 | 1.1800 | 0.8932 | 0.0108 | 0.8383 | **occupancy** |
| 100.0 | 118 | **1.1800** | 0.9745 | 0.0026 | 0.8453 | **occupancy** |
| 400.0 | 471 | 1.1775 | 1.0000 | 0.0000 | **0.8493** | **occupancy** |

**Agents per erlang falls from 3.00 to 1.18 — 61% — and that is the whole case for consolidating
queues.** A small queue buys its service level with idle time because there is no pooling to spread a
burst across; a large one does not need to.

**But the economy of scale ends, and it ends at a named place.** The binding constraint is the service
level up to about 35 erlangs, mixed between 35 and 45, and **the occupancy ceiling alone from 45
erlangs upward**. Past that point the queue is no longer limited by the customer waiting — it is
limited by the agent's tolerance, and the service level it reports (0.9745 at a hundred erlangs) is a
by-product of a humane occupancy rather than a target anybody set.

That has a practical edge for anyone consolidating: the gains are real and they stop. Beyond the
turning point, a bigger queue does not buy a cheaper plan; it buys a plan whose constraint has changed
from an external promise to an internal limit, and those two are negotiated with different people.

## Result 4: "compliant" and "one absence from breaching" are the same sentence

Slack at the chosen headcount, in each constraint's own units:

| Agents | Service level slack | Occupancy slack | Abandonment slack |
| --- | --- | --- | --- |
| **11** | +0.0368 | +0.1828 | **+0.0176** |
| 12 | +0.1138 | +0.2290 | +0.0326 |

Eleven agents satisfies everything, and the abandonment ceiling has **1.76 points** of room — the
thinnest of the three. A plan that reports "all constraints met" and a plan that reports this table are
the same plan, and only the second one tells a manager which number moves first when somebody calls in
sick. That is why `headroom` is a published function rather than an assertion inside the search.

## Assumptions and limitations

- **Every number here comes from a seeded synthetic generator** and from declared ceilings. No
  employer, client, vendor or platform data is used anywhere, and there is no language model. See
  [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **The ceilings are declared, not benchmarked.** 0.80 inside twenty seconds, 0.85 occupancy and 0.05
  abandonment are round numbers chosen to make the mechanics visible. No industry standard is quoted
  anywhere in this repository, and any real plan's ceilings come from its own contracts and its own
  attrition data.
- **One period, one steady state.** The whole module staffs a single load, so there is no shift, no
  intraday curve, no peak and no shrinkage. A real plan solves this per interval and then loses
  agents to breaks, training and absence - which is a multiplier on every headcount here, not a
  correction to the argument.
- **Occupancy is a ceiling, not a cost.** Attrition rising with occupancy is the reason the ceiling
  exists, and nothing here models it: the plan treats 0.84 as fine and 0.86 as forbidden, when the
  truth is a curve. Putting attrition in would make the ceiling an optimum rather than a constraint,
  and that is a different and better model.
- **Erlang A's patience is exponential and its abandonment is memoryless.** Real customers abandon in
  bursts, at announcements and at the two-minute mark. The direction of every comparison survives;
  the abandonment levels are as good as that assumption.
- **The search is upward and the measures are monotone in agents**, which a test asserts over the
  whole range. If a real model broke that - a queue where more agents raise abandonment - the
  smallest satisfying headcount would not be what this returns.

## Sources

Cited as the origin of a *method*, never as a source of any number in these tables.

- Erlang, A. K. (1917). *Solution of some Problems in the Theory of Probabilities of Significance in
  Automatic Telephone Exchanges.* Post Office Electrical Engineers' Journal 10. — the queueing models
  the constraints are evaluated with.
- Palm, C. (1953). *Methods of Judging the Annoyance Caused by Congestion.* Tele 4. — impatience as a
  quantity a plan can be held to, which is what the abandonment ceiling is.
- Halfin, S., Whitt, W. (1981). *Heavy-Traffic Limits for Queues with Many Exponential Servers.*
  Operations Research 29. — why a large queue reaches a service level at an occupancy a small one
  cannot, which is Result 3.
- Gans, N., Koole, G., Mandelbaum, A. (2003). *Telephone Call Centers: Tutorial, Review, and Research
  Prospects.* Manufacturing & Service Operations Management 5. — staffing as a constrained problem
  rather than a single target.

---

# `svclab.planning` — a restrição que ninguém declarou decidiu o headcount

*[English](#svclabplanning--the-constraint-nobody-declared-decided-the-headcount)*

Todo plano das ondas 1 a 6 dimensionava por **nível de serviço** e então reportava a ocupação e o
abandono em que por acaso caía. A onda 3 imprimiu a versão mais nítida disso: uma fila *perfeitamente
estável* com seis atendentes, 29,23% dos clientes abandonando e os atendentes dos sobreviventes a
89,45% de ocupação. As duas coisas eram saídas.

Nenhum plano real as trata assim. Um teto de ocupação é o que contém a rotatividade; um teto de abandono
é o que a marca ou o regulador pede. Então este módulo inverte a aritmética: declare os tetos, e o
headcount é o que satisfaz todos eles — e depois diga **qual deles decidiu**.

A ocupação aqui é medida sobre a carga **efetiva**, o trabalho de fato atendido, porque quem abandona
não ocupa ninguém. Usar a carga oferecida superestima a ocupação exatamente onde o abandono é material,
que é onde o teto está sendo testado.

```python
from svclab.planning import Constraints, agents_at_ceiling, headroom, plan_table, scale_table

LOAD, HANDLING, PATIENCE = 7.5845, 512.25, 240.0

plan_table(
    {
        "service level only": Constraints(service_level=0.80),
        "occupancy only": Constraints(max_occupancy=0.85),
        "all three": Constraints(service_level=0.80, max_occupancy=0.85, max_abandonment=0.05),
    },
    LOAD,
    HANDLING,
    PATIENCE,
)
scale_table(
    (1.0, 20.0, 100.0), HANDLING, PATIENCE, Constraints(service_level=0.80, max_occupancy=0.85)
)
agents_at_ceiling(LOAD, 0.85)  # 9 - a conta de guardanapo, antes de qualquer fila
headroom(
    11, LOAD, HANDLING, PATIENCE, Constraints(max_abandonment=0.05)
)  # a que distância de furar
```

## Resultado 1: três tetos, e só dois fazem algo aqui

A fila da onda 1 — 7,5845 erlangs, 512,25 segundos de atendimento, quatro minutos de paciência,
atendida em vinte segundos:

| Plano | Atendentes | Nível de serviço | Abandono | Ocupação | Decidido por |
| --- | --- | --- | --- | --- | --- |
| nível de serviço ≥ 0,80 | **11** | 0,8368 | 0,0324 | 0,6672 | nível de serviço |
| ocupação ≤ 0,85 | **8** | **0,1751** | **0,1434** | 0,8121 | ocupação |
| abandono ≤ 0,05 | **11** | 0,8368 | 0,0324 | 0,6672 | abandono |
| nível de serviço + ocupação | 11 | 0,8368 | 0,0324 | 0,6672 | nível de serviço |
| **as três** | **11** | 0,8368 | 0,0324 | 0,6672 | **nível de serviço + abandono** |

Três coisas, e a do meio é a armadilha.

**O teto de ocupação nunca vincula nesta fila.** Onze atendentes trabalham a 66,72%, confortavelmente
abaixo de 0,85 — então o plano a que a onda 3 chegou já era humano. O que não era humano era a
*promessa*: 5,51 atendentes. E os "perfeitamente estáveis" seis da onda 3, aos quais voltamos abaixo.

**Um teto de ocupação sozinho é satisfeito subdimensionando.** Oito atendentes mantêm a ocupação em
0,8121 e atendem **17,51%** dos contatos dentro da meta enquanto **14,34% dos clientes desistem**. Vale
ser explícito sobre o mecanismo: são os clientes que abandonam que mantêm a ocupação baixa. Uma meta de
ocupação perseguida isoladamente premia a fila por perder gente — o oposto da razão de ela existir.

**E o nível de serviço e o teto de abandono chegam aos mesmos onze por caminhos independentes**, e então
vinculam **juntos**: com dez atendentes os dois falham. Dois tetos que concordam não são redundantes —
são dois argumentos que não podem ser negociados um por vez.

## Resultado 2: o que resolve o que a onda 3 deixou aberto

A onda 3 reportou seis atendentes como fila estável e se recusou a chamar isso de plano. Ponha os três
tetos contra:

| Com seis atendentes | Valor | Teto | Veredicto |
| --- | --- | --- | --- |
| nível de serviço | 0,0000 | ≥ 0,80 | **falha** |
| ocupação | 0,8945 | ≤ 0,85 | **falha** |
| abandono | 0,2923 | ≤ 0,05 | **falha** |

**Seis atendentes falham nos três.** "Estável" significava que a fila tem estado estacionário — e tem,
com um cliente em três indo embora e o resto atendido por gente a 89% de ocupação. Estabilidade não é
plano, e um modelo que a reporta como resposta está respondendo a uma pergunta que ninguém fez.

E a conta de guardanapo também merece preço. A aritmética que um plano faz sem modelo de fila —
`carga / teto de ocupação` — dá **9** atendentes. A fila precisa de **11**. Dividir uma carga por uma
razão subestima a necessidade em **18%**, que é o erro de headcount da onda 1 com outra fantasia: lá a
promessa multiplicava uma fila por uma proporção, aqui divide-se uma por uma proporção. Nenhuma das
duas é uma fila.

## Resultado 3: e qual teto vincula depende do tamanho da fila

Os mesmos três tetos contra filas de tamanhos diferentes:

| Carga (erlangs) | Atendentes | Atendentes por erlang | Nível de serviço | Abandono | Ocupação | Decidido por |
| --- | --- | --- | --- | --- | --- | --- |
| 1,0 | 3 | **3,0000** | 0,9159 | 0,0339 | 0,3220 | nível de serviço + abandono |
| 2,5 | 5 | 2,0000 | 0,8818 | 0,0358 | 0,4821 | nível de serviço + abandono |
| 7,5845 | 11 | 1,4503 | 0,8368 | 0,0324 | 0,6672 | nível de serviço + abandono |
| 20,0 | 25 | 1,2500 | 0,8280 | 0,0232 | 0,7814 | nível de serviço |
| 50,0 | 59 | 1,1800 | 0,8932 | 0,0108 | 0,8383 | **ocupação** |
| 100,0 | 118 | **1,1800** | 0,9745 | 0,0026 | 0,8453 | **ocupação** |
| 400,0 | 471 | 1,1775 | 1,0000 | 0,0000 | **0,8493** | **ocupação** |

**Atendentes por erlang cai de 3,00 para 1,18 — 61% — e esse é todo o argumento para consolidar
filas.** Uma fila pequena compra seu nível de serviço com tempo ocioso porque não há pooling para
diluir um pico; uma grande não precisa.

**Mas a economia de escala acaba, e acaba num lugar com nome.** A restrição vinculante é o nível de
serviço até cerca de 35 erlangs, mista entre 35 e 45, e **o teto de ocupação sozinho a partir de 45
erlangs**. Passado esse ponto a fila não é mais limitada pelo cliente que espera — é limitada pela
tolerância do atendente, e o nível de serviço que ela reporta (0,9745 a cem erlangs) é subproduto de uma
ocupação humana, não meta que alguém definiu.

Isso tem uma consequência prática para quem consolida: os ganhos são reais e eles param. Além do ponto
de virada, uma fila maior não compra um plano mais barato; compra um plano cuja restrição mudou de uma
promessa externa para um limite interno — e essas duas se negociam com pessoas diferentes.

## Resultado 4: "em conformidade" e "a uma falta de furar" são a mesma frase

Folga no headcount escolhido, nas unidades de cada restrição:

| Atendentes | Folga de nível de serviço | Folga de ocupação | Folga de abandono |
| --- | --- | --- | --- |
| **11** | +0,0368 | +0,1828 | **+0,0176** |
| 12 | +0,1138 | +0,2290 | +0,0326 |

Onze atendentes satisfazem tudo, e o teto de abandono tem **1,76 ponto** de espaço — o mais fino dos
três. Um plano que reporta "todas as restrições atendidas" e um plano que reporta esta tabela são o
mesmo plano, e só o segundo diz a um gestor qual número se move primeiro quando alguém falta. É por isso
que `headroom` é função publicada e não uma verificação dentro da busca.

## Premissas e limitações

- **Toda cifra aqui vem de um gerador sintético com semente** e de tetos declarados. Nenhum dado de
  empregador, cliente, fornecedor ou plataforma é usado em lugar algum, e não existe modelo de
  linguagem. Ver [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **Os tetos são declarados, não comparados com mercado.** 0,80 em vinte segundos, 0,85 de ocupação e
  0,05 de abandono são números redondos escolhidos para tornar a mecânica visível. Nenhum padrão de
  indústria é citado em lugar algum deste repositório, e os tetos de um plano real vêm dos contratos
  dele e dos dados de rotatividade dele.
- **Um período, um estado estacionário.** O módulo inteiro dimensiona uma única carga: não há turno,
  não há curva intradiária, não há pico e não há shrinkage. Um plano real resolve isso por intervalo e
  depois perde gente para pausas, treinamento e falta — o que é um multiplicador sobre todo headcount
  aqui, não uma correção do argumento.
- **Ocupação é teto, não custo.** A rotatividade que cresce com a ocupação é a razão de o teto existir,
  e nada aqui a modela: o plano trata 0,84 como ok e 0,86 como proibido, quando a verdade é uma curva.
  Colocar a rotatividade dentro faria do teto um ótimo em vez de uma restrição — o que é um modelo
  diferente e melhor.
- **A paciência do Erlang A é exponencial e seu abandono é sem memória.** Clientes reais abandonam em
  rajadas, nos anúncios e na marca dos dois minutos. A direção de toda comparação sobrevive; os níveis
  de abandono valem tanto quanto essa premissa.
- **A busca é ascendente e as medidas são monótonas no número de atendentes**, o que um teste verifica
  em toda a faixa. Se um modelo real quebrasse isso — uma fila onde mais atendentes elevam o abandono —
  o menor headcount satisfatório não seria o que esta função devolve.

## Fontes

Citadas como origem de um *método*, nunca como fonte de qualquer número destas tabelas.

- Erlang, A. K. (1917). *Solution of some Problems in the Theory of Probabilities of Significance in
  Automatic Telephone Exchanges.* Post Office Electrical Engineers' Journal 10. — os modelos de fila
  com que as restrições são avaliadas.
- Palm, C. (1953). *Methods of Judging the Annoyance Caused by Congestion.* Tele 4. — impaciência como
  quantidade a que um plano pode ser cobrado, que é o que o teto de abandono é.
- Halfin, S., Whitt, W. (1981). *Heavy-Traffic Limits for Queues with Many Exponential Servers.*
  Operations Research 29. — por que uma fila grande alcança um nível de serviço numa ocupação que uma
  pequena não alcança, que é o Resultado 3.
- Gans, N., Koole, G., Mandelbaum, A. (2003). *Telephone Call Centers: Tutorial, Review, and Research
  Prospects.* Manufacturing & Service Operations Management 5. — dimensionamento como problema
  restrito em vez de meta única.
