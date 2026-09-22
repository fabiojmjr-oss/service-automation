# `svclab.workforce` — the headcount that produces the work is not the headcount you hire

*[Português](#svclabworkforce--o-quadro-que-produz-o-trabalho-não-é-o-quadro-que-você-contrata)*

Wave 7 declared occupancy a **ceiling**: 0.84 fine, 0.86 forbidden. What a ceiling stands in for is a
**curve** — attrition rises with how hard the work is — and a curve turns a constraint into a price.

Pricing it closes a loop every operations manager knows and no staffing model contains:

> occupancy raises attrition → attrition empties seats → an empty seat is not an agent → fewer agents
> raise occupancy

So the headcount that produces the work and the headcount on the payroll are two different numbers,
joined by a **fixed point** rather than by a margin. This module solves it, prices a point of occupancy
in hires a year, and then asks whether the loop ever runs away.

There is still no money in this repository. The trade is therefore published as an **exchange rate** —
hires a year per agent on the payroll — and the decision about what a departure is worth stays with the
reader, which turns out to be the honest place for it.

```python
from svclab.planning import Constraints
from svclab.workforce import exchange_rate, payroll_table, regime_table, settle, trade_table

LOAD, HANDLING, PATIENCE = 7.5845, 512.25, 240.0
CEILINGS = Constraints(service_level=0.80, max_occupancy=0.85, max_abandonment=0.05)

settle(12, LOAD, HANDLING, PATIENCE)  # where the loop comes to rest for a payroll of twelve
payroll_table((1.0, LOAD, 20.0, 50.0, 100.0), HANDLING, PATIENCE, CEILINGS)
trade = trade_table((0.90, 0.85, 0.80, 0.75, 0.70), 100.0, HANDLING, PATIENCE, CEILINGS)
exchange_rate(trade)  # hires a year bought per agent added
regime_table((0.12, 0.60, 1.00, 1.50), 12, LOAD, HANDLING, PATIENCE)  # does the loop run away?
```

## Result 1: a payroll is not an agent count, and the gap is not a margin

Wave 7's plans, funded rather than sized:

| Load | Agents needed | **Payroll** | Premium | Occupancy | Attrition/month | Per year | Hires/year | Empty seats | Ramping |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.0 | 3 | **4** | 1.3333 | 0.2532 | 0.0200 | 21.5% | 0.96 | 0.12 | 0.16 |
| 7.5845 | 11 | **12** | 1.0909 | 0.6411 | 0.0200 | 21.5% | 2.88 | 0.36 | 0.48 |
| 20.0 | 25 | **27** | 1.0800 | 0.7753 | 0.0290 | 29.8% | 9.41 | 1.18 | 1.57 |
| 50.0 | 59 | **65** | 1.1017 | 0.8283 | 0.0354 | 35.1% | 27.61 | 3.45 | 4.60 |
| 100.0 | 119 | **130** | 1.0924 | 0.8382 | 0.0366 | 36.1% | 57.07 | 7.13 | 9.51 |

**Wave 7's eleven agents cost twelve people.** At a hundred erlangs, 119 agents cost 130 — with 7.13
seats empty and 9.51 people still ramping at any moment. The premium is not a planning buffer somebody
chose; it is the solution of the loop, and it moves when the occupancy does.

**And the premium is not monotone in the size of the queue** — 1.3333, then 1.0800, then back up to
1.1017. Two forces run against each other. At one erlang the integer arithmetic dominates: three agents
need four people because you cannot hire 3.06 of one. At fifty the attrition dominates: the queue runs
at 0.83 occupancy, which is above the knee, so it loses 35% of its people a year and carries the
vacancies that follow.

Which prices something wave 7 celebrated. Wave 7's Result 3 found that a large queue needs only **1.18
agents per erlang** against 3.00 for a small one, and called that the case for consolidating queues.
The efficiency is real and it is **paid for in people**: the same large queue runs at 0.84 occupancy,
loses **36.1% of its staff a year** and hires **57 people a year** to stand still. A consolidation
business case that counts the agents saved and not the recruiting it commits to has counted one side.

## Result 2: the exchange rate, and the queue where there is no trade to make

The same hundred-erlang queue, holding the service level and the abandonment ceiling fixed and moving
only the occupancy ceiling:

| Ceiling | Payroll | Agents | Occupancy | Attrition/month | Per year | Hires/year | Δ payroll | Δ hires |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.90 | 123 | 110 | 0.8912 | 0.0429 | 40.9% | **63.39** | — | — |
| 0.85 | 130 | 119 | 0.8382 | 0.0366 | 36.1% | 57.07 | +7 | −6.33 |
| 0.80 | 135 | 125 | 0.7990 | 0.0319 | 32.2% | 51.64 | +5 | −5.42 |
| 0.75 | 143 | 134 | 0.7420 | 0.0250 | 26.2% | 42.97 | +8 | −8.67 |
| 0.70 | 150 | 143 | 0.6988 | 0.0200 | 21.5% | **36.00** | +7 | −6.97 |

**Twenty-seven more people on the payroll buys 27.39 fewer hires a year: an exchange rate of 1.01.**
One agent, one hire. That is the number a manager asks for and a staffing model never prints.

And here the refusal to price things in money earns its keep, because the rate can be read in the
repository's own currency and the answer is uncomfortable. A departure wastes
`1.5 + 2.0 × (1 − 0.60) = 2.30` person-months — the empty seat plus the productivity a new agent has
not reached. So one extra agent on the payroll costs **12 person-months a year** and returns
**2.33 person-months a year** of recovered capacity: a ratio of **0.19**.

**On the queue's own books, loosening the occupancy does not pay for itself — it loses by a factor of
five.** Which does not make it wrong. It means the case rests entirely on what a departure costs
*outside* the queue: the recruiting, the knowledge that walks out, the manager's week, the quality of a
team that is a third new. This repository declines to invent those numbers, so what it delivers instead
is the exchange rate and a precise statement of the missing information. **A plan that loosens
occupancy is buying something this model cannot see, and it should say so.**

There is also a queue where the whole question is empty. On wave 1's 7.58 erlangs the trade **does not
exist**: the service level already delivers 0.64 occupancy, under the knee, so attrition sits at its
floor of 21.5% and no ceiling from 0.90 down to 0.70 changes the payroll by a single person. The
exchange rate is reported as `nan` rather than as zero, because zero would say the trade was free and
the truth is that there is nothing to trade. **The occupancy-attrition problem is a large-queue
problem**, and that is the same boundary wave 7 found for the binding ceiling.

## Result 3: the loop does not run away — and the margin is a property of the payroll

The question the loop invites: occupancy raises attrition which raises occupancy, so does it spiral?
Settled twice at each slope — once from a calm operation, once from one in crisis:

**At the payroll the plan calls for (12, on wave 1's queue):**

| Attrition slope | From calm | From crisis | Two regimes? |
| --- | --- | --- | --- |
| **0.12** *(declared)* | occupancy 0.6411, attrition 0.0200 | identical | **no** |
| 0.60 | 0.6411, 0.0200 | identical | no |
| 1.00 | 0.6411, 0.0200 | identical | no |
| **1.50** | 0.6411, 0.0200 | **collapse** | **yes** |

**At a payroll two short of the plan (10):**

| Attrition slope | From calm | From crisis | Two regimes? |
| --- | --- | --- | --- |
| 0.12 | 0.7270, 0.0232 | identical | no |
| **0.60** | 0.7285, 0.0371 | 0.7252, **0.0351** | **yes** |
| 1.00 | 0.8088, **0.1288** | 0.7551, **0.0751** | yes |
| 1.50 | 0.7379, 0.0769 | **collapse** | yes |

Three things.

**At the declared curve there is no spiral.** The fixed point is unique and the iteration reaches it
from either end, so an operation at this payroll cannot be pushed into a worse steady state by a bad
quarter. The dramatic story is available and this model does not support it, which is worth saying
plainly.

**The slope has to be 12.5 times steeper before the plan's payroll can collapse** — 1.50 against the
declared 0.12. That is the margin, and it is quantified rather than asserted.

**And robustness is a property of the payroll, not only of the curve.** Two people short, the same
queue splits into two regimes at a slope of 0.60 — **five times** the declared one instead of 12.5.
Understaffing does not merely breach wave 7's ceilings; it moves the operation closer to a regime it
cannot leave by trying harder. That is a second, independent argument for funding the plan, and it is
not an argument any queueing model makes.

The two regimes at slope 1.00 are worth reading closely, because they are not what the phrase "death
spiral" suggests. The state reached **from crisis** has *lower* occupancy (0.7551 against 0.8088) and
*lower* attrition (0.0751 against 0.1288, a factor of 1.71) — and the identical abandonment of 21.0%.
The operation that went through the crisis settled somewhere with **less pressure on its agents and the
same share of customers walking away**. The abandonment is the escape valve: the customers who give up
are what stops the loop from tightening.

That is the **third** time in this repository that abandonment turns out to be what prevents a
divergence. Wave 3: Erlang A has a steady state exactly where Erlang C has none, because people leave.
Wave 7: an occupancy ceiling on its own is satisfied by understaffing, because the customers who
abandon keep the occupancy down. Wave 8: the attrition loop finds a second resting place by losing
customers rather than by keeping agents. **Every model in this family is stabilised by the same thing,
and it is the thing the business is trying not to do.**

## Assumptions and limitations

- **Every number here comes from declared parameters and a seeded generator.** No employer, client,
  vendor or platform data is used anywhere, and there is no language model. See
  [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **The attrition curve is invented.** A base of 2% a month, a knee at 0.70 occupancy and a slope of
  0.12 are round numbers chosen to make the mechanics visible. No benchmark is quoted and none should
  be inferred: a real curve is fitted to a real operation's leavers, and its knee and slope are the
  two things worth measuring before any of this arithmetic is trusted.
- **Attrition depends on occupancy and on nothing else.** Pay, management, commute, the labour market
  and the season all matter more in most operations. Occupancy is isolated here because it is the one
  a staffing plan controls.
- **Steady state only.** Every figure is a fixed point, which assumes the load, the curve and the
  hiring pipeline have been stable long enough to settle. A plan that changes every quarter never
  reaches these numbers, and the transition is where the pain of a spiral actually lives.
- **A departure is replaced, always, and immediately begins to be recruited.** No hiring freeze, no
  market where the role cannot be filled, and no queue of candidates that empties. Each of those makes
  the premium worse.
- **The ramp is a flat productivity for a fixed number of months**, not a curve. Real ramps are
  gradual and vary by person, and the aggregate is what this approximates.
- **The loop is solved at a whole number of agents** by flooring the producing headcount, because a
  queue cannot be served by four fifths of a person. That rounding is conservative and it is the same
  one wave 3's staffing search makes.

## Sources

Cited as the origin of a *method*, never as a source of any number in these tables.

- Forrester, J. W. (1961). *Industrial Dynamics.* MIT Press. — a stock and its outflow solved as a
  loop rather than as a forecast, which is what this module does to a payroll.
- Bartholomew, D. J., Forbes, A. F., McClean, S. I. (1991). *Statistical Techniques for Manpower
  Planning*, 2nd ed. Wiley. — the steady-state arithmetic of leavers, vacancies and recruits.
- Gans, N., Zhou, Y.-P. (2002). *Managing Learning and Turnover in Employee Staffing.* Operations
  Research 50. — staffing a queue whose agents learn and leave, which is the problem this wave states.
- Aksin, Z., Armony, M., Mehrotra, V. (2007). *The Modern Call Center: A Multi-Disciplinary
  Perspective on Operations Management Research.* Production and Operations Management 16. — occupancy
  and turnover as connected decisions rather than separate reports.

---

# `svclab.workforce` — o quadro que produz o trabalho não é o quadro que você contrata

*[English](#svclabworkforce--the-headcount-that-produces-the-work-is-not-the-headcount-you-hire)*

A onda 7 declarou a ocupação um **teto**: 0,84 ok, 0,86 proibido. O que um teto substitui é uma
**curva** — a rotatividade cresce com o quanto o trabalho é duro — e uma curva transforma uma restrição
em preço.

Precificá-la fecha um laço que todo gestor de operações conhece e nenhum modelo de dimensionamento
contém:

> ocupação eleva a rotatividade → a rotatividade esvazia cadeiras → uma cadeira vazia não é um
> atendente → menos atendentes elevam a ocupação

Então o quadro que produz o trabalho e o quadro na folha são dois números diferentes, unidos por um
**ponto fixo** e não por uma margem. Este módulo o resolve, precifica um ponto de ocupação em
contratações por ano, e depois pergunta se o laço alguma vez escapa.

Continua não havendo dinheiro neste repositório. A troca é portanto publicada como **taxa de câmbio** —
contratações por ano por atendente na folha — e a decisão sobre quanto vale uma saída fica com o
leitor, o que se revela o lugar honesto para ela.

```python
from svclab.planning import Constraints
from svclab.workforce import exchange_rate, payroll_table, regime_table, settle, trade_table

LOAD, HANDLING, PATIENCE = 7.5845, 512.25, 240.0
CEILINGS = Constraints(service_level=0.80, max_occupancy=0.85, max_abandonment=0.05)

settle(12, LOAD, HANDLING, PATIENCE)  # onde o laço descansa para uma folha de doze
payroll_table((1.0, LOAD, 20.0, 50.0, 100.0), HANDLING, PATIENCE, CEILINGS)
trade = trade_table((0.90, 0.85, 0.80, 0.75, 0.70), 100.0, HANDLING, PATIENCE, CEILINGS)
exchange_rate(trade)  # contratações por ano compradas por atendente adicionado
regime_table((0.12, 0.60, 1.00, 1.50), 12, LOAD, HANDLING, PATIENCE)  # o laço escapa?
```

## Resultado 1: uma folha de pagamento não é uma contagem de atendentes, e a diferença não é margem

Os planos da onda 7, financiados em vez de dimensionados:

| Carga | Atendentes | **Folha** | Prêmio | Ocupação | Rotat./mês | Por ano | Contratações/ano | Cadeiras vazias | Em ramp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1,0 | 3 | **4** | 1,3333 | 0,2532 | 0,0200 | 21,5% | 0,96 | 0,12 | 0,16 |
| 7,5845 | 11 | **12** | 1,0909 | 0,6411 | 0,0200 | 21,5% | 2,88 | 0,36 | 0,48 |
| 20,0 | 25 | **27** | 1,0800 | 0,7753 | 0,0290 | 29,8% | 9,41 | 1,18 | 1,57 |
| 50,0 | 59 | **65** | 1,1017 | 0,8283 | 0,0354 | 35,1% | 27,61 | 3,45 | 4,60 |
| 100,0 | 119 | **130** | 1,0924 | 0,8382 | 0,0366 | 36,1% | 57,07 | 7,13 | 9,51 |

**Os onze atendentes da onda 7 custam doze pessoas.** A cem erlangs, 119 atendentes custam 130 — com
7,13 cadeiras vazias e 9,51 pessoas ainda em ramp em qualquer instante. O prêmio não é um colchão de
planejamento que alguém escolheu; é a solução do laço, e ele se move quando a ocupação se move.

**E o prêmio não é monótono no tamanho da fila** — 1,3333, depois 1,0800, e de volta a 1,1017. Duas
forças correm em direções opostas. A um erlang a aritmética inteira domina: três atendentes exigem
quatro pessoas porque não se contrata 3,06 de uma. A cinquenta, a rotatividade domina: a fila roda a
0,83 de ocupação, acima do joelho, então perde 35% da gente por ano e carrega as vagas que isso gera.

O que precifica algo que a onda 7 celebrou. O Resultado 3 dela encontrou que uma fila grande precisa de
apenas **1,18 atendentes por erlang** contra 3,00 de uma pequena, e chamou isso de argumento para
consolidar filas. A eficiência é real e é **paga em pessoas**: a mesma fila grande roda a 0,84 de
ocupação, perde **36,1% do quadro por ano** e contrata **57 pessoas por ano** para ficar parada. Um
business case de consolidação que conta os atendentes economizados e não o recrutamento que assume
contou um lado só.

## Resultado 2: a taxa de câmbio, e a fila onde não há troca a fazer

A mesma fila de cem erlangs, mantendo fixos o nível de serviço e o teto de abandono e movendo só o teto
de ocupação:

| Teto | Folha | Atendentes | Ocupação | Rotat./mês | Por ano | Contratações/ano | Δ folha | Δ contratações |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0,90 | 123 | 110 | 0,8912 | 0,0429 | 40,9% | **63,39** | — | — |
| 0,85 | 130 | 119 | 0,8382 | 0,0366 | 36,1% | 57,07 | +7 | −6,33 |
| 0,80 | 135 | 125 | 0,7990 | 0,0319 | 32,2% | 51,64 | +5 | −5,42 |
| 0,75 | 143 | 134 | 0,7420 | 0,0250 | 26,2% | 42,97 | +8 | −8,67 |
| 0,70 | 150 | 143 | 0,6988 | 0,0200 | 21,5% | **36,00** | +7 | −6,97 |

**Vinte e sete pessoas a mais na folha compram 27,39 contratações a menos por ano: taxa de câmbio de
1,01.** Um atendente, uma contratação. É o número que um gestor pede e que um modelo de dimensionamento
nunca imprime.

E aqui a recusa de precificar em dinheiro se paga, porque a taxa pode ser lida na moeda do próprio
repositório e a resposta é incômoda. Uma saída desperdiça `1,5 + 2,0 × (1 − 0,60) = 2,30` pessoa-meses —
a cadeira vazia mais a produtividade que o novato ainda não alcançou. Então um atendente adicional na
folha custa **12 pessoa-meses por ano** e devolve **2,33 pessoa-meses por ano** de capacidade
recuperada: razão de **0,19**.

**Nos livros da própria fila, afrouxar a ocupação não se paga — perde por um fator de cinco.** O que não
a torna errada. Significa que o caso repousa inteiramente sobre o que uma saída custa *fora* da fila: o
recrutamento, o conhecimento que vai embora, a semana do gestor, a qualidade de um time que é um terço
novo. Este repositório se recusa a inventar esses números, então o que entrega no lugar é a taxa de
câmbio e um enunciado preciso da informação que falta. **Um plano que afrouxa a ocupação está comprando
algo que este modelo não vê, e deveria dizer isso.**

Há também uma fila onde a pergunta toda é vazia. Nos 7,58 erlangs da onda 1 a troca **não existe**: o
nível de serviço já entrega 0,64 de ocupação, abaixo do joelho, então a rotatividade fica no seu piso de
21,5% e nenhum teto de 0,90 a 0,70 muda a folha em uma única pessoa. A taxa de câmbio é reportada como
`nan` e não como zero, porque zero diria que a troca é grátis e a verdade é que não há o que trocar. **O
problema ocupação-rotatividade é um problema de fila grande** — e é a mesma fronteira que a onda 7
encontrou para o teto vinculante.

## Resultado 3: o laço não escapa — e a margem é propriedade da folha

A pergunta que o laço convida: a ocupação eleva a rotatividade que eleva a ocupação, então há espiral?
Assentado duas vezes em cada inclinação — uma partindo de operação calma, outra de operação em crise:

**Na folha que o plano pede (12, na fila da onda 1):**

| Inclinação | Partindo de calmo | Partindo de crise | Dois regimes? |
| --- | --- | --- | --- |
| **0,12** *(declarada)* | ocupação 0,6411, rotat. 0,0200 | idêntico | **não** |
| 0,60 | 0,6411, 0,0200 | idêntico | não |
| 1,00 | 0,6411, 0,0200 | idêntico | não |
| **1,50** | 0,6411, 0,0200 | **colapso** | **sim** |

**Numa folha duas pessoas abaixo do plano (10):**

| Inclinação | Partindo de calmo | Partindo de crise | Dois regimes? |
| --- | --- | --- | --- |
| 0,12 | 0,7270, 0,0232 | idêntico | não |
| **0,60** | 0,7285, 0,0371 | 0,7252, **0,0351** | **sim** |
| 1,00 | 0,8088, **0,1288** | 0,7551, **0,0751** | sim |
| 1,50 | 0,7379, 0,0769 | **colapso** | sim |

Três coisas.

**Na curva declarada não há espiral.** O ponto fixo é único e a iteração o alcança dos dois extremos,
então uma operação nesta folha não pode ser empurrada para um estado estacionário pior por um trimestre
ruim. A narrativa dramática está disponível e este modelo não a sustenta — o que vale dizer sem rodeios.

**A inclinação precisa ser 12,5 vezes mais forte para a folha do plano colapsar** — 1,50 contra os 0,12
declarados. Essa é a margem, quantificada em vez de afirmada.

**E robustez é propriedade da folha, não só da curva.** Duas pessoas a menos, a mesma fila se divide em
dois regimes já numa inclinação de 0,60 — **cinco vezes** a declarada em vez de 12,5. Subdimensionar
não apenas fura os tetos da onda 7; aproxima a operação de um regime do qual ela não sai tentando mais
forte. É um segundo argumento, independente, para financiar o plano — e não é um argumento que nenhum
modelo de fila faz.

Os dois regimes na inclinação 1,00 merecem leitura atenta, porque não são o que a expressão "espiral da
morte" sugere. O estado alcançado **de crise** tem ocupação *menor* (0,7551 contra 0,8088) e
rotatividade *menor* (0,0751 contra 0,1288, fator de 1,71) — e abandono idêntico, de 21,0%. A operação
que passou pela crise se acomodou num lugar com **menos pressão sobre os atendentes e a mesma fração de
clientes indo embora**. O abandono é a válvula de escape: os clientes que desistem são o que impede o
laço de apertar.

É a **terceira** vez neste repositório que o abandono se revela o que impede uma divergência. Onda 3:
Erlang A tem estado estacionário exatamente onde Erlang C não tem, porque pessoas vão embora. Onda 7: um
teto de ocupação sozinho é satisfeito subdimensionando, porque quem abandona mantém a ocupação baixa.
Onda 8: o laço de rotatividade encontra um segundo repouso perdendo clientes em vez de mantendo
atendentes. **Todo modelo desta família é estabilizado pela mesma coisa, e é a coisa que o negócio está
tentando não fazer.**

## Premissas e limitações

- **Toda cifra aqui vem de parâmetros declarados e de um gerador com semente.** Nenhum dado de
  empregador, cliente, fornecedor ou plataforma é usado em lugar algum, e não existe modelo de
  linguagem. Ver [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **A curva de rotatividade é inventada.** Base de 2% ao mês, joelho em 0,70 de ocupação e inclinação
  de 0,12 são números redondos escolhidos para tornar a mecânica visível. Nenhum benchmark é citado e
  nenhum deve ser inferido: uma curva real é ajustada aos desligamentos de uma operação real, e seu
  joelho e sua inclinação são as duas coisas que valem medir antes de confiar nesta aritmética.
- **A rotatividade depende da ocupação e de nada mais.** Salário, gestão, deslocamento, mercado de
  trabalho e sazonalidade importam mais na maioria das operações. A ocupação é isolada aqui porque é a
  que um plano de dimensionamento controla.
- **Só estado estacionário.** Toda cifra é um ponto fixo, o que assume que a carga, a curva e o
  pipeline de contratação ficaram estáveis o bastante para assentar. Um plano que muda todo trimestre
  nunca alcança estes números — e a transição é onde a dor de uma espiral de fato vive.
- **Uma saída é reposta, sempre, e o recrutamento começa de imediato.** Sem congelamento de vagas, sem
  mercado em que a vaga não se preenche e sem fila de candidatos que esvazia. Cada um desses piora o
  prêmio.
- **O ramp é uma produtividade fixa por um número fixo de meses**, não uma curva. Ramps reais são
  gradativos e variam por pessoa, e o agregado é o que isto aproxima.
- **O laço é resolvido num número inteiro de atendentes**, truncando o quadro produtivo para baixo,
  porque uma fila não é atendida por quatro quintos de uma pessoa. Esse arredondamento é conservador e
  é o mesmo que a busca de dimensionamento da onda 3 faz.

## Fontes

Citadas como origem de um *método*, nunca como fonte de qualquer número destas tabelas.

- Forrester, J. W. (1961). *Industrial Dynamics.* MIT Press. — um estoque e sua saída resolvidos como
  laço em vez de previsão, que é o que este módulo faz com uma folha de pagamento.
- Bartholomew, D. J., Forbes, A. F., McClean, S. I. (1991). *Statistical Techniques for Manpower
  Planning*, 2ª ed. Wiley. — a aritmética de estado estacionário de saídas, vagas e admissões.
- Gans, N., Zhou, Y.-P. (2002). *Managing Learning and Turnover in Employee Staffing.* Operations
  Research 50. — dimensionar uma fila cujos atendentes aprendem e vão embora, que é o problema que
  esta onda enuncia.
- Aksin, Z., Armony, M., Mehrotra, V. (2007). *The Modern Call Center: A Multi-Disciplinary
  Perspective on Operations Management Research.* Production and Operations Management 16. — ocupação
  e rotatividade como decisões conectadas em vez de relatórios separados.
