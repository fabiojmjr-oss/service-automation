# `svclab.capacity` — the headcount the case promised

*[Português](#svclabcapacity--o-headcount-que-o-case-prometeu)*

## The business problem

An automation's headcount case is almost always one multiplication: this many contacts, that
containment rate, so this much less volume, so this many fewer agents. Every step is defensible and
the answer is wrong.

On this account the case promised **8.49 agents** of saving. The queue gives back **3**. The promise
overstates the saving by **2.83 times**, and the gap decomposes into three effects that each have a
closed form and none of which is in the case.

## The decision it enables

1. **How many agents does this queue need at its service level?** Which is Erlang, not a proportion.
2. **How many did the containment rate promise?** Which is the multiplication, kept in the module it
   is wrong in so that the two can be printed side by side.
3. **And where did the difference come from?** Decomposed, because a gap nobody can attribute is a
   gap nobody fixes.

## Usage

```python
from svclab.capacity import agents_for, capacity_table, erlang_c, occupancy, service_level

erlang_c(1, 0.5)  # 0.5 exactly - with one agent, Erlang C is the load
service_level(14, 10.1268, 395.43, 20.0)  # 0.8455
agents_for(10.1268, 395.43, 20.0, 0.80)  # 14
occupancy(14, 10.1268)  # 0.7233

capacity_table(outcomes, containment_rates, baseline="human-only")
```

## Result 1: staffing is not a proportion

A queue's agent count is not linear in its load. At a 20-second target and 80% service level, a load
of 20 erlangs needs 25 agents and a load of 10 needs **14** — half the work needs 56% of the people,
not 50%. The last few points of service level cost far more than the first, and a business case that
scales headcount by volume has used the wrong function before it has used the wrong inputs.

The formulas are Erlang's, computed the safe way: Erlang B by its recursion rather than its
factorials, and Erlang C from B. Two closed forms pin the arithmetic — with one agent, `erlang_c`
equals the offered load exactly, and `erlang_b` equals `a / (1 + a)`. At a target of zero seconds the
service level is exactly `1 - C`, which ties the two formulas to each other.

## Result 2: the queue, four policies, and what each was promised

31,802 contacts over 30 days, 12 staffed hours a day, answering 80% inside 20 seconds:

| Policy | Human sessions | Mean handling seconds | Offered load | Agents needed | Occupancy | Service level | Agents promised | Missing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| human-only | 33,190 | 395.43 | 10.1268 | **14** | 0.7233 | 0.8455 | 14.00 | 0.00 |
| three-turns | 19,189 | **512.25** | 7.5845 | **11** | 0.6895 | 0.8368 | **5.51** | **+5.49** |
| patient | 16,036 | **520.10** | 6.4355 | **10** | 0.6435 | 0.8726 | **2.56** | **+7.44** |
| guarded | 20,750 | 496.46 | 7.9487 | **12** | 0.6624 | 0.8855 | 7.16 | +4.84 |

Read the `mean_handling_seconds` column before the agent count. The baseline handles 395 seconds a
contact; every automated queue handles more than 495. **The volume that left was not the volume that
stayed**, and the load is volume times handling time.

And read `agents_promised` against `agents_needed`. The policy with the highest containment rate —
`patient` at 0.8169 — has the largest shortfall: it promised a queue of 2.56 agents and needs 10.

## Result 3: the gap, decomposed

For `three-turns`, each step computed with the same Erlang function:

| Step | Agents | Movement |
| --- | --- | --- |
| the promise, as a multiplication | 5.51 | — |
| volume only, through Erlang | 7.00 | **+1.49** |
| plus the harder residue | 8.00 | **+1.00** |
| plus the repeat stream | 11.00 | **+3.00** |

Three effects, smallest to largest:

1. **The multiplication is not the queue's arithmetic.** Erlang on the same reduced volume, at the
   same handling time, already needs 7 agents rather than 5.51. That 1.49 is pure non-linearity — no
   behavioural assumption in it at all.
2. **The residue costs more per contact.** Holding the volume fixed and moving only the handling time
   from 395 to 507 seconds adds one agent.
3. **The repeats arrive in the same queue.** 6,674 second conversations from 31,802 contacts adds
   **three agents** — twice the non-linearity effect and three times the mix effect.

**The largest of the three is the one no business case models at all.** The other two are at least
arguable from the model that was used; the repeat stream is invisible to it, because a model that
counts contained sessions has no way to represent a contact arriving twice.

## Result 4: the bot bought slack, and a plan can spend it twice

Occupancy falls from **0.7233** to **0.6895** between the baseline and `three-turns`, and to 0.6435
under `patient`. The automated queues are *less* pressed than the baseline at the same service level,
because an integer agent count on a smaller load overshoots.

That slack is real and it is worth having — it absorbs the day the volume spikes. But it is also the
first thing a second round of cuts will take, and cutting to the promised 5.51 agents does not miss
the service level by a little: at that load the queue has no steady state at all. Occupancy belongs
next to every agent count for that reason, and a queue can hit its service level at an occupancy no
team survives.

## Result 5: the promised headcount is achievable, if a third of the customers give up

Everything above is Erlang C, which assumes **infinite patience**. At a load of 7.5845 erlangs it has
nothing at all to say below eight agents: the queue grows without bound, there is no steady state, and
the service level is reported as zero because there is no wait to report.

Real queues do have a steady state there. The mechanism is the customers leaving, and Erlang A is that
mechanism — the same birth-death chain with an impatience rate added above the agent count. At a mean
patience of four minutes:

| Agents | Erlang C service level | Erlang C has an answer | **Abandonment** | Answered | Effective load | Occupancy |
| --- | --- | --- | --- | --- | --- | --- |
| 5 | 0.0000 | no | **0.3891** | 0.6109 | 4.6335 | **0.9267** |
| **6** | 0.0000 | **no** | **0.2923** | 0.7077 | 5.3672 | **0.8945** |
| 7 | 0.0000 | no | 0.2100 | 0.7900 | 5.9917 | 0.8560 |
| 8 | 0.1751 | yes | 0.1434 | 0.8566 | 6.4967 | 0.8121 |
| 10 | 0.7064 | yes | 0.0565 | 0.9435 | 7.1562 | 0.7156 |
| **11** | 0.8368 | yes | **0.0324** | 0.9676 | 7.3390 | 0.6672 |
| 14 | 0.9794 | yes | 0.0042 | 0.9958 | 7.5525 | 0.5395 |

Result 2 said the business case promised **5.51 agents** and the queue needs **11**. This table says
something sharper. **At six agents the queue is perfectly stable — with 29.23% of the customers
abandoning and the survivors' agents running at 89.45% occupancy.** The promised headcount is not
impossible. It is a decision to answer seven contacts in ten and staff the remainder at an occupancy no
team sustains.

Which is why Erlang C returning "no steady state" is a more useful error than it looks: it is the model
saying that its assumption — that people wait — has been broken. Erlang A tells you *who* broke it.

Two closed-form controls tie the models together, and both are asserted in the tests: abandonment falls
monotonically towards zero as patience lengthens, reaching below 5e-6 at a thousand-hour patience, and
Erlang A returns a finite answer at a load **above** the agent count where Erlang C returns exactly one
and a service level of exactly zero.

## Result 6: and the queue then feeds itself

Wave 1 established that an abandoned contact is not a contact that went away: some share of the people
who gave up come back, and their return is load. So abandonment raises the load, which raises
abandonment, which raises the return. The settled load is the fixed point of

> load = base load × (1 + repeat share × abandonment(load))

solved by iterating it. At the 55% repeat share the generator declares for a tracking question:

| Agents | Base load | **Settled load** | Added by repeats | Abandonment at the fixed point | Iterations |
| --- | --- | --- | --- | --- | --- |
| 6 | 7.5845 | **9.1886** | **+1.6041** | **0.3845** | 20 |
| 8 | 7.5845 | 8.3478 | +0.7633 | 0.1830 | 19 |
| 11 | 7.5845 | 7.7328 | +0.1483 | 0.0356 | 12 |

**At six agents the repeats add 21.1% more load and push abandonment from 29.23% to 38.45%.** The
understaffed queue is not merely worse than the plan; it manufactures its own extra work, and the
arithmetic converges to a worse place than the arithmetic that ignores the feedback.

At eleven agents — the count Result 2 says the work actually needs — the feedback adds 2.0% of load and
settles at 3.56% abandonment. The same mechanism, and at adequate staffing it is a rounding error. That
is the case for the eleven agents, stated in the currency the abandonment is paid in rather than in
service level.

## Assumptions and limitations

- **Every number here comes from a seeded synthetic generator.** No employer, client, vendor or
  platform data is used anywhere. See [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **Erlang C assumes exponential handling times, Poisson arrivals, infinite patience in the human
  queue, and a steady state.** The generator draws handling times exponentially around a declared
  mean so the panel and the formula agree by construction — but real handling times are not
  exponential and real arrivals are not stationary within a day. The infinite patience is no longer
  an unexamined assumption: Results 5 and 6 price what impatience does, with Erlang A, and the agent
  counts in Results 2 and 3 are still Erlang C's because holding the service level fixed is the
  comparison those results are making.
- **Erlang A here reports abandonment and not a service level.** The abandonment rate and the delay
  probability follow exactly from the birth-death chain; the distribution of the wait *among those
  answered* does not, without an approximation this module declines to make. So Results 5 and 6 quote
  what is exact and stop, which is why the service level column in Result 5 is Erlang C's.
- **One pooled queue, one skill, no shifts, no shrinkage.** A real plan multiplies these agent counts
  up for breaks, training, absence and schedule inefficiency, typically by a third or more. That
  multiplier applies to both sides of every comparison, so it scales the gap rather than closing it.
- **Staffed hours are a declared 12 a day for 30 days.** Arrival times are generated uniformly across
  the period, so the plan is priced against average load rather than against a peak hour, which is
  the direction that flatters every queue in the table.
- **`promised_agents` returns a fraction on purpose.** Rounding it would suggest the rounding was the
  error rather than the multiplication.
- **The comparison holds the service level fixed and lets the agent count move.** Holding headcount
  fixed and letting the service level move is the same arithmetic read the other way round, and it is
  what actually happens in a deployment where the saving was already booked.

## Sources

Cited as the origin of a *method*, never as a source of any number in these tables.

- Erlang, A. K. (1917). *Solution of Some Problems in the Theory of Probabilities of Significance in
  Automatic Telephone Exchanges.* Post Office Electrical Engineers' Journal 10. — the two formulas.
- Gans, N., Koole, G., Mandelbaum, A. (2003). *Telephone Call Centers: Tutorial, Review, and Research
  Prospects.* Manufacturing & Service Operations Management 5(2). — where Erlang C's assumptions
  break in a real contact centre, and what Erlang A repairs.
- Garnett, O., Mandelbaum, A., Reiman, M. (2002). *Designing a Call Center with Impatient Customers.*
  Manufacturing & Service Operations Management 4(3). — the impatient queue Results 5 and 6 price,
  and the approximations for its waiting time that this module declines to use.

---

# `svclab.capacity` — o headcount que o case prometeu

*[English](#svclabcapacity--the-headcount-the-case-promised)*

## O problema de negócio

O business case de headcount de uma automação é quase sempre uma multiplicação: tantos contatos, tal
taxa de contenção, então tanto menos volume, então tantos atendentes menos. Cada passo é defensável e
a resposta está errada.

Nesta conta o case prometeu **8,49 atendentes** de economia. A fila devolve **3**. A promessa
superestima a economia em **2,83 vezes**, e a diferença se decompõe em três efeitos que têm forma
fechada e nenhum dos quais está no case.

## A decisão que habilita

1. **Quantos atendentes esta fila precisa no seu nível de serviço?** Que é Erlang, não proporção.
2. **Quantos a taxa de contenção prometeu?** Que é a multiplicação, mantida no módulo em que ela está
   errada para que as duas possam ser impressas lado a lado.
3. **E de onde veio a diferença?** Decomposta, porque uma diferença que ninguém consegue atribuir é
   uma diferença que ninguém corrige.

## Uso

```python
from svclab.capacity import agents_for, capacity_table, erlang_c, occupancy, service_level

erlang_c(1, 0.5)  # exatamente 0,5 - com um atendente, Erlang C é a carga
service_level(14, 10.1268, 395.43, 20.0)  # 0,8455
agents_for(10.1268, 395.43, 20.0, 0.80)  # 14
occupancy(14, 10.1268)  # 0,7233

capacity_table(outcomes, containment_rates, baseline="human-only")
```

## Resultado 1: dimensionamento não é proporção

A contagem de atendentes de uma fila não é linear na carga. Com alvo de 20 segundos e nível de serviço
de 80%, uma carga de 20 erlangs precisa de 25 atendentes e uma de 10 precisa de **14** — metade do
trabalho precisa de 56% das pessoas, não 50%. Os últimos pontos de nível de serviço custam muito mais
que os primeiros, e um business case que escala headcount por volume usou a função errada antes de
usar os dados errados.

As fórmulas são as de Erlang, calculadas do jeito seguro: Erlang B pela recursão em vez dos fatoriais,
e Erlang C a partir de B. Duas formas fechadas fixam a aritmética — com um atendente, a `erlang_c`
iguala exatamente a carga oferecida, e a `erlang_b` iguala `a / (1 + a)`. Com alvo de zero segundo o
nível de serviço é exatamente `1 - C`, o que amarra as duas fórmulas uma à outra.

## Resultado 2: a fila, quatro políticas, e o que cada uma prometeu

31.802 contatos em 30 dias, 12 horas de operação por dia, atendendo 80% dentro de 20 segundos:

| Política | Sessões humanas | Segundos médios | Carga oferecida | Atendentes necessários | Ocupação | Nível de serviço | Atendentes prometidos | Faltando |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| human-only | 33.190 | 395,43 | 10,1268 | **14** | 0,7233 | 0,8455 | 14,00 | 0,00 |
| three-turns | 19.189 | **512,25** | 7,5845 | **11** | 0,6895 | 0,8368 | **5,51** | **+5,49** |
| patient | 16.036 | **520,10** | 6,4355 | **10** | 0,6435 | 0,8726 | **2,56** | **+7,44** |
| guarded | 20.750 | 496,46 | 7,9487 | **12** | 0,6624 | 0,8855 | 7,16 | +4,84 |

Leia a coluna de segundos médios antes da contagem de atendentes. A linha-base atende 395 segundos por
contato; toda fila automatizada atende mais de 495. **O volume que saiu não era o volume que ficou**, e
a carga é volume vezes tempo de atendimento.

E leia os atendentes prometidos contra os necessários. A política com maior contenção — o `patient`,
com 0,8169 — tem o maior déficit: prometeu uma fila de 2,56 atendentes e precisa de 10.

## Resultado 3: a diferença, decomposta

Para o `three-turns`, cada passo calculado com a mesma função de Erlang:

| Passo | Atendentes | Movimento |
| --- | --- | --- |
| a promessa, como multiplicação | 5,51 | — |
| só volume, através de Erlang | 7,00 | **+1,49** |
| mais o resíduo mais difícil | 8,00 | **+1,00** |
| mais o fluxo de recontatos | 11,00 | **+3,00** |

Três efeitos, do menor para o maior:

1. **A multiplicação não é a aritmética da fila.** Erlang sobre o mesmo volume reduzido, com o mesmo
   tempo de atendimento, já precisa de 7 atendentes em vez de 5,51. Esses 1,49 são não-linearidade
   pura — nenhuma premissa comportamental neles.
2. **O resíduo custa mais por contato.** Mantendo o volume fixo e movendo só o tempo de atendimento de
   395 para 507 segundos, soma um atendente.
3. **Os recontatos chegam na mesma fila.** 6.674 segundas conversas a partir de 31.802 contatos somam
   **três atendentes** — o dobro do efeito de não-linearidade e o triplo do efeito de mix.

**O maior dos três é o que nenhum business case modela.** Os outros dois são pelo menos discutíveis a
partir do modelo que foi usado; o fluxo de recontatos é invisível para ele, porque um modelo que conta
sessões contidas não tem como representar um contato chegando duas vezes.

## Resultado 4: o bot comprou folga, e um plano pode gastá-la duas vezes

A ocupação cai de **0,7233** para **0,6895** entre a linha-base e o `three-turns`, e para 0,6435 sob o
`patient`. As filas automatizadas estão *menos* pressionadas que a linha-base no mesmo nível de
serviço, porque uma contagem inteira de atendentes sobre uma carga menor sobra.

Essa folga é real e vale ter — ela absorve o dia em que o volume estoura. Mas também é a primeira coisa
que uma segunda rodada de cortes vai tomar, e cortar para os 5,51 atendentes prometidos não erra o
nível de serviço por pouco: naquela carga a fila não tem estado estacionário nenhum. A ocupação
pertence ao lado de toda contagem de atendentes por esse motivo, e uma fila pode bater seu nível de
serviço com uma ocupação que nenhuma equipe sobrevive.

## Resultado 5: o headcount prometido é alcançável, se um terço dos clientes desistir

Tudo acima é Erlang C, que supõe **paciência infinita**. Com carga de 7,5845 erlangs ele não tem nada a
dizer abaixo de oito atendentes: a fila cresce sem limite, não há estado estacionário, e o nível de
serviço é reportado como zero porque não há espera a reportar.

Filas reais têm estado estacionário ali. O mecanismo são os clientes indo embora, e Erlang A é esse
mecanismo — a mesma cadeia de nascimento e morte com uma taxa de impaciência acrescentada acima da
contagem de atendentes. Com paciência média de quatro minutos:

| Atendentes | Nível de serviço Erlang C | Erlang C tem resposta | **Abandono** | Atendidos | Carga efetiva | Ocupação |
| --- | --- | --- | --- | --- | --- | --- |
| 5 | 0,0000 | não | **0,3891** | 0,6109 | 4,6335 | **0,9267** |
| **6** | 0,0000 | **não** | **0,2923** | 0,7077 | 5,3672 | **0,8945** |
| 7 | 0,0000 | não | 0,2100 | 0,7900 | 5,9917 | 0,8560 |
| 8 | 0,1751 | sim | 0,1434 | 0,8566 | 6,4967 | 0,8121 |
| 10 | 0,7064 | sim | 0,0565 | 0,9435 | 7,1562 | 0,7156 |
| **11** | 0,8368 | sim | **0,0324** | 0,9676 | 7,3390 | 0,6672 |
| 14 | 0,9794 | sim | 0,0042 | 0,9958 | 7,5525 | 0,5395 |

O Resultado 2 disse que o business case prometeu **5,51 atendentes** e a fila precisa de **11**. Esta
tabela diz algo mais afiado. **Com seis atendentes a fila é perfeitamente estável — com 29,23% dos
clientes abandonando e os atendentes dos sobreviventes a 89,45% de ocupação.** O headcount prometido não
é impossível. É uma decisão de atender sete contatos em dez e operar o resto numa ocupação que nenhuma
equipe sustenta.

E é por isso que Erlang C devolver "sem estado estacionário" é um erro mais útil do que parece: é o
modelo dizendo que sua premissa — que as pessoas esperam — foi quebrada. Erlang A diz *quem* a quebrou.

Dois casos de controle em forma fechada amarram os dois modelos, e os dois estão asseridos nos testes: o
abandono cai monotonicamente para zero conforme a paciência aumenta, ficando abaixo de 5e-6 com
paciência de mil horas, e Erlang A devolve resposta finita numa carga **acima** da contagem de
atendentes, onde Erlang C devolve exatamente um e nível de serviço exatamente zero.

## Resultado 6: e então a fila se alimenta

A onda 1 estabeleceu que um contato abandonado não é um contato que foi embora: uma fração dos que
desistiram volta, e o retorno deles é carga. Então abandono aumenta a carga, que aumenta o abandono, que
aumenta o retorno. A carga de equilíbrio é o ponto fixo de

> carga = carga base × (1 + fração de retorno × abandono(carga))

resolvido por iteração. Na fração de retorno de 55% que o gerador declara para uma pergunta de rastreio:

| Atendentes | Carga base | **Carga de equilíbrio** | Adicionado pelos retornos | Abandono no ponto fixo | Iterações |
| --- | --- | --- | --- | --- | --- |
| 6 | 7,5845 | **9,1886** | **+1,6041** | **0,3845** | 20 |
| 8 | 7,5845 | 8,3478 | +0,7633 | 0,1830 | 19 |
| 11 | 7,5845 | 7,7328 | +0,1483 | 0,0356 | 12 |

**Com seis atendentes os retornos acrescentam 21,1% mais carga e empurram o abandono de 29,23% para
38,45%.** A fila subdimensionada não é apenas pior que o plano; ela fabrica o próprio trabalho extra, e
a aritmética converge para um lugar pior que a aritmética que ignora a realimentação.

Com onze atendentes — a contagem que o Resultado 2 diz que o trabalho realmente exige — a realimentação
acrescenta 2,0% de carga e estabiliza em 3,56% de abandono. O mesmo mecanismo, e com dimensionamento
adequado ele é erro de arredondamento. Esse é o argumento a favor dos onze atendentes, dito na moeda em
que o abandono é pago e não em nível de serviço.

## Premissas e limitações

- **Todo número aqui vem de um gerador sintético com semente.** Nenhum dado de empregador, cliente,
  fornecedor ou plataforma é usado em qualquer parte. Ver [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **Erlang C supõe tempos de atendimento exponenciais, chegadas de Poisson, paciência infinita na fila
  humana e estado estacionário.** O gerador sorteia tempos de atendimento exponencialmente em torno de
  uma média declarada, então o painel e a fórmula concordam por construção — mas tempos reais não são
  exponenciais e chegadas reais não são estacionárias dentro do dia. A paciência infinita já não é
  premissa não examinada: os Resultados 5 e 6 precificam o que a impaciência faz, com Erlang A, e as
  contagens de atendentes dos Resultados 2 e 3 continuam sendo as de Erlang C porque manter o nível de
  serviço fixo é a comparação que aqueles resultados fazem.
- **Erlang A aqui reporta abandono e não nível de serviço.** A taxa de abandono e a probabilidade de
  espera decorrem exatamente da cadeia de nascimento e morte; a distribuição da espera *entre os
  atendidos* não, sem uma aproximação que este módulo recusa fazer. Então os Resultados 5 e 6 citam o
  que é exato e param, e é por isso que a coluna de nível de serviço do Resultado 5 é a de Erlang C.
- **Uma fila única, uma habilidade, sem turnos, sem shrinkage.** Um plano real multiplica estas
  contagens para pausas, treinamento, ausência e ineficiência de escala, tipicamente por um terço ou
  mais. Esse multiplicador se aplica aos dois lados de toda comparação, então ele escala a diferença em
  vez de fechá-la.
- **As horas de operação são 12 por dia declaradas, por 30 dias.** As chegadas são geradas
  uniformemente no período, então o plano é precificado contra carga média e não contra hora de pico, o
  que é a direção que lisonjeia toda fila da tabela.
- **A `promised_agents` devolve fração de propósito.** Arredondar sugeriria que o arredondamento era o
  erro, e não a multiplicação.
- **A comparação mantém o nível de serviço fixo e deixa a contagem de atendentes se mover.** Manter o
  headcount fixo e deixar o nível de serviço se mover é a mesma aritmética lida ao contrário, e é o que
  de fato acontece numa implantação em que a economia já foi contabilizada.

## Fontes

Citadas como origem de um *método*, nunca como fonte de qualquer número destas tabelas.

- Erlang, A. K. (1917). *Solution of Some Problems in the Theory of Probabilities of Significance in
  Automatic Telephone Exchanges.* Post Office Electrical Engineers' Journal 10. — as duas fórmulas.
- Gans, N., Koole, G., Mandelbaum, A. (2003). *Telephone Call Centers: Tutorial, Review, and Research
  Prospects.* Manufacturing & Service Operations Management 5(2). — onde as premissas de Erlang C
  quebram numa central real, e o que Erlang A conserta.
- Garnett, O., Mandelbaum, A., Reiman, M. (2002). *Designing a Call Center with Impatient Customers.*
  Manufacturing & Service Operations Management 4(3). — a fila impaciente que os Resultados 5 e 6
  precificam, e as aproximações para seu tempo de espera que este módulo recusa usar.
