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

## Assumptions and limitations

- **Every number here comes from a seeded synthetic generator.** No employer, client, vendor or
  platform data is used anywhere. See [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **Erlang C assumes exponential handling times, Poisson arrivals, infinite patience in the human
  queue, and a steady state.** The generator draws handling times exponentially around a declared
  mean so the panel and the formula agree by construction — but real handling times are not
  exponential, real arrivals are not stationary within a day, and **nobody in a real queue waits
  forever**. The last of those is the significant one: modelling human-queue abandonment (Erlang A)
  would change the agent counts and would not change the direction of any comparison here, because
  every policy is priced with the same formula.
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
  Manufacturing & Service Operations Management 4(3). — the abandonment this module deliberately does
  not model, and what it would change.

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

## Premissas e limitações

- **Todo número aqui vem de um gerador sintético com semente.** Nenhum dado de empregador, cliente,
  fornecedor ou plataforma é usado em qualquer parte. Ver [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **Erlang C supõe tempos de atendimento exponenciais, chegadas de Poisson, paciência infinita na fila
  humana e estado estacionário.** O gerador sorteia tempos de atendimento exponencialmente em torno de
  uma média declarada, então o painel e a fórmula concordam por construção — mas tempos reais não são
  exponenciais, chegadas reais não são estacionárias dentro do dia, e **ninguém numa fila real espera
  para sempre**. O último é o significativo: modelar abandono na fila humana (Erlang A) mudaria as
  contagens de atendentes e não mudaria a direção de nenhuma comparação aqui, porque toda política é
  precificada com a mesma fórmula.
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
  Manufacturing & Service Operations Management 4(3). — o abandono que este módulo deliberadamente não
  modela, e o que ele mudaria.
