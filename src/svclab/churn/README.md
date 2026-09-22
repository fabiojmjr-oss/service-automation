# `svclab.churn` — the outcome that looks like a saving

*[Português](#svclabchurn--o-desfecho-que-se-parece-com-uma-economia)*

Three waves of this repository leaned on the same relief valve without pricing it. Erlang A reaches a
steady state **because** customers give up. An occupancy ceiling is satisfied by understaffing
**because** the customers who abandon are what keeps occupancy down. The attrition loop's second
regime is reached **by losing customers**. Each time the note was the same — abandonment is the thing
the business is trying not to do — and each time there was no currency to say how much of it happened.

This module is that currency. A customer gets a declared chance of not coming back, decided by the
worst thing that happened to them; the contacts they would have made are removed; and three things
become measurable that nine waves could not see.

```python
from svclab.bot import POLICIES, run
from svclab.churn import departures, detection_by_frequency, policy_table, silence_flag, surviving
from svclab.synth import generate_dataset

data = generate_dataset()
month = data.contacts[~data.contacts["holdout"]]
outcomes = {policy.name: run(month, policy) for policy in POLICIES}

left = departures(month, outcomes["three-turns"], data.churn_draws)
detection_by_frequency(left, silence_flag(surviving(month, left)))  # the churn rate, as a gauge
policy_table(month, outcomes, data.churn_draws)  # what each policy costs in people
```

## Result 1: a churn rate is a gauge, and this one reports 6% of what it flags

Nobody can see a customer leave. What an operation sees is **silence**, and a rule that calls a silent
customer churned is a binary assessor — so wave 2's gauge study applies to it exactly, and so does
wave 2's attenuation identity.

Ten days of silence, on the 16,195 customers of the treated arm, of whom **775** actually left:

| | Value |
| --- | --- |
| customers | 16,195 |
| actually left | **775** (4.79%) |
| flagged by the rule | **8,040** |
| sensitivity | 0.6477 |
| specificity | 0.5112 |
| **Youden index** | **0.1589** |
| precision | **0.0624** |

Two readings, both damaging. **93.76% of the customers this dashboard flags did not leave** — a
retention campaign built on it spends fifteen sixteenths of its budget on people who were staying. And
because the Youden index is the exact factor by which a binary assessor shrinks any difference, a
comparison of two policies on this churn rate reports **15.89% of the real gap**. Wave 2 found a
quality panel reporting 69.45% of a difference and called it an instrument problem. This is the same
identity at a fifth of the transmission.

## Result 2: the rule is useless at both ends, for opposite reasons

The obvious diagnosis is that silence only means something for somebody who contacts often. It is
wrong, and the split says why:

| Contacts seen | Customers | Left | Sensitivity | Specificity | **Youden** |
| --- | --- | --- | --- | --- | --- |
| 1 | 7,029 | 411 | **0.7640** | **0.3368** | 0.1008 |
| 2 | 5,184 | 222 | 0.5450 | 0.5613 | 0.1063 |
| 3 | 2,629 | 99 | 0.5556 | 0.7123 | **0.2678** |
| 4 or more | 1,353 | 43 | **0.2791** | **0.8137** | 0.0928 |

The index **peaks in the middle**. At one contact the rule is nearly blind to the stayers — a customer
with one contact is silent by construction, so specificity is 0.3368. At four or more it goes blind to
the leavers — a frequent customer who leaves late in the month still has a recent contact, so
sensitivity collapses to 0.2791. The rule works least badly on customers with exactly three contacts,
and even there it transmits a quarter of a difference.

Which is a design rule rather than a curiosity: **a silence window is a statement about contact
frequency, and it can only detect a departure whose silence had time to accumulate.** One window for a
whole book of customers is two different instruments wearing one name.

## Result 3: losing customers reduces the bill, and the KPI cannot see it

| Policy | Customers lost | Share | Human hours | After the departures | **Hours "saved"** | Minutes per customer lost | Containment | After |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| human-only | **257** | 1.59% | 3,645.64 | 3,621.15 | 24.49 | **5.72** | 0.0000 | 0.0000 |
| guarded | 615 | 3.80% | 2,861.54 | 2,817.07 | 44.47 | 4.34 | 0.4886 | 0.4883 |
| three-turns | 775 | 4.79% | 2,730.43 | 2,678.82 | 51.61 | 4.00 | 0.6065 | 0.6063 |
| patient | **1,123** | 6.93% | 2,316.78 | 2,257.29 | **59.49** | **3.18** | 0.8169 | 0.8167 |

Three things are in that table.

**The hours saved are monotone in the customers lost.** The policy that drives away the most people
gets the largest reduction in human hours, and every one of those hours arrives on the report as
efficiency. There is no line anywhere in the first nine waves of this repository where it would show
up as anything else.

**The ranking by customers lost is the containment ranking, exactly.** `patient` first, `human-only`
last — the fourth ranking of the same four policies, and the second one that agrees with the KPI while
disagreeing with resolution and with days to resolution. The containment-maximising policy loses
**4.37 times** as many customers as the human queue.

**And containment cannot see the loss it causes.** Recomputed on the contacts that survive, session
containment moves by **0.00017**. That is not a small effect being reported faithfully; it is the
denominator and the numerator falling together, which is what a ratio does when you remove the people
it is a ratio over.

The exchange rate is the line to read out loud. On the containment-maximising policy, one hour of
saved handling time costs **18.88 customers**. On the human queue a lost customer is worth 5.72
minutes and on `patient` 3.18 — the aggressive policy loses *cheaper* contacts, so it has to lose
*more* people to book the same saving.

## Result 4: the valve three waves used, priced in people

Abandonment converted at the declared rate, on the month's treated volume:

| Decision | Abandonment | Abandoned contacts | **Customers lost** | Share |
| --- | --- | --- | --- | --- |
| wave 3 — six agents, "perfectly stable" | 29.23% | 9,295.7 | **557.74** | 3.44% |
| wave 8 — the regime reached from crisis | 21.00% | 6,678.4 | 400.71 | 2.47% |
| wave 7 — eight agents, occupancy held alone | 14.34% | 4,560.4 | 273.62 | 1.69% |
| wave 7 — eleven agents, every ceiling met | 3.56% | 1,132.2 | **67.93** | 0.42% |

Wave 3's stable queue spends **489.81 more customers a month** than the plan that meets its ceilings.
Wave 7's humane-sounding occupancy target, pursued alone, spends **205.70 more**.

And that closes the question wave 8 left open. Wave 8 priced an extra agent at 12 person-months a year
against 2.33 returned — a ratio of 0.19 — and said plainly that the case rests entirely on what a
departure costs *outside* the queue, which it could not supply. Going from six agents to eleven costs
five agents and retains 489.81 customers: **97.96 customers a month per agent.** This module still
does not price a customer, because there is no money in this repository. It supplies the quantity and
leaves the price with the reader, which is where a decision of that kind belongs.

## The unit was wrong for nine waves

Only **590** contacts disappear under `three-turns` — 1.86% of the month. That number is small for a
structural reason rather than a reassuring one: a customer who leaves on day three loses twenty-seven
days here and **the rest of their life** in an operation. The seconds in this table are a one-month
fragment of a permanent loss.

Which is the argument for the whole wave. Seconds, sessions, agents and hours are monthly quantities
and a month is the window every wave here measured in. Customers are not monthly. Nine waves built an
increasingly careful account in a unit that cannot express the loss at all — and the only reason it
took ten waves to notice is that the unit was never wrong about anything else.

## Assumptions and limitations

- **The curve is declared, not fitted.** 6% after abandoning, 4% after an unresolved contact, 0.5%
  after a resolved one. Those three numbers carry every figure above, and nothing here measures them.
  In a real operation they are the first thing worth estimating and the hardest.
- **The worst experience dominates.** A contact abandoned and later resolved counts as abandoned. That
  is a statement about memory, and a plausible alternative — recency, or an average — would move the
  ranking between policies whose failures arrive in different orders.
- **One decision per contact.** A customer's chance of leaving does not accumulate across a bad month;
  each contact is its own coin at its own declared rate. A real relationship has a threshold, and a
  threshold model would punish the policies that fail the same person twice - which is exactly what
  wave 4 measured and this module does not use.
- **A departure removes contacts and nothing else.** No word of mouth, no complaint to a regulator, no
  effect on anybody else's propensity to contact. Each of those makes the loss larger than published.
- **The monthly window truncates everything.** As above: the contacts removed are the remainder of one
  month, so every hour figure here is a lower bound by roughly the ratio of a customer's lifetime to
  the fortnight they had left.
- **The valve table is first order and an upper bound.** Abandoned contacts times the leaving chance,
  which double-counts a customer who abandons twice. The direction is deliberate: a number whose job
  is to make a cheap-looking decision look expensive should not also be optimistic.
- **The silence rule is measured against a truth no operation has.** That is the whole method of this
  repository, and it is why the gauge study can exist at all.

## Sources

- The gauge framing, the sensitivity–specificity pair and the Youden index are the same instruments
  wave 2 uses; the attenuation identity applied to a churn comparison is the identity in
  `svclab.quality`, not a new result.
- Treating an unobservable departure through an observable proxy, and the precision collapse at low
  prevalence, is the standard base-rate argument about screening tests; the arithmetic here is Bayes
  and nothing more.
- The idea that a customer's continuation depends on the service experience is the service-quality and
  satisfaction-loyalty literature's central claim; this module does not test it, it assumes it and
  declares the parameters.

---

# `svclab.churn` — o desfecho que se parece com uma economia

*[English](#svclabchurn--the-outcome-that-looks-like-a-saving)*

Três ondas deste repositório se apoiaram na mesma válvula de alívio sem precificá-la. Erlang A alcança
um estado estacionário **porque** clientes desistem. Um teto de ocupação é satisfeito por
subdimensionamento **porque** os clientes que abandonam são o que mantém a ocupação baixa. O segundo
regime do laço de rotatividade é alcançado **perdendo clientes**. Toda vez a nota era a mesma —
abandono é aquilo que o negócio tenta não fazer — e toda vez não havia moeda para dizer quanto disso
aconteceu.

Este módulo é essa moeda. Um cliente recebe uma chance declarada de não voltar, decidida pela pior
coisa que lhe aconteceu; os contatos que ele teria feito são removidos; e três coisas ficam
mensuráveis que nove ondas não conseguiam ver.

```python
from svclab.bot import POLICIES, run
from svclab.churn import departures, detection_by_frequency, policy_table, silence_flag, surviving
from svclab.synth import generate_dataset

data = generate_dataset()
mes = data.contacts[~data.contacts["holdout"]]
outcomes = {policy.name: run(mes, policy) for policy in POLICIES}

saiu = departures(mes, outcomes["three-turns"], data.churn_draws)
detection_by_frequency(
    saiu, silence_flag(surviving(mes, saiu))
)  # a taxa de churn, como instrumento
policy_table(mes, outcomes, data.churn_draws)  # o que cada política custa em gente
```

## Resultado 1: uma taxa de churn é um instrumento, e este reporta 6% do que sinaliza

Ninguém consegue ver um cliente ir embora. O que uma operação vê é **silêncio**, e uma regra que chama
um cliente silencioso de perdido é um avaliador binário — então o estudo de instrumento da onda 2 se
aplica exatamente a ela, e a identidade de atenuação da onda 2 também.

Dez dias de silêncio, sobre os 16.195 clientes do braço tratado, dos quais **775** realmente saíram:

| | Valor |
| --- | --- |
| clientes | 16.195 |
| saíram de fato | **775** (4,79%) |
| sinalizados pela regra | **8.040** |
| sensibilidade | 0,6477 |
| especificidade | 0,5112 |
| **índice de Youden** | **0,1589** |
| precisão | **0,0624** |

Duas leituras, ambas danosas. **93,76% dos clientes que este painel sinaliza não saíram** — uma
campanha de retenção construída sobre ele gasta quinze dezesseis avos do orçamento com gente que ia
ficar. E como o índice de Youden é o fator exato pelo qual um avaliador binário encolhe qualquer
diferença, uma comparação de duas políticas por esta taxa de churn reporta **15,89% da diferença
real**. A onda 2 achou um painel de qualidade reportando 69,45% de uma diferença e chamou isso de
problema de instrumento. Esta é a mesma identidade a um quinto da transmissão.

## Resultado 2: a regra é inútil nos dois extremos, por razões opostas

O diagnóstico óbvio é que silêncio só significa algo para quem contata com frequência. Ele está
errado, e a estratificação diz por quê:

| Contatos vistos | Clientes | Saíram | Sensibilidade | Especificidade | **Youden** |
| --- | --- | --- | --- | --- | --- |
| 1 | 7.029 | 411 | **0,7640** | **0,3368** | 0,1008 |
| 2 | 5.184 | 222 | 0,5450 | 0,5613 | 0,1063 |
| 3 | 2.629 | 99 | 0,5556 | 0,7123 | **0,2678** |
| 4 ou mais | 1.353 | 43 | **0,2791** | **0,8137** | 0,0928 |

O índice **tem pico no meio**. Com um contato a regra é quase cega para quem fica — um cliente de um
contato é silencioso por construção, então a especificidade é 0,3368. Com quatro ou mais ela fica cega
para quem sai — um cliente frequente que sai no fim do mês ainda tem contato recente, então a
sensibilidade colapsa para 0,2791. A regra funciona menos mal com clientes de exatamente três
contatos, e mesmo lá transmite um quarto de uma diferença.

O que é regra de projeto e não curiosidade: **uma janela de silêncio é uma afirmação sobre frequência
de contato, e só detecta uma saída cujo silêncio teve tempo de acumular.** Uma janela para toda a
carteira são dois instrumentos diferentes usando um nome.

## Resultado 3: perder clientes reduz a conta, e o KPI não vê

| Política | Clientes perdidos | Parcela | Horas humanas | Depois das saídas | **Horas "economizadas"** | Minutos por cliente perdido | Contenção | Depois |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| human-only | **257** | 1,59% | 3.645,64 | 3.621,15 | 24,49 | **5,72** | 0,0000 | 0,0000 |
| guarded | 615 | 3,80% | 2.861,54 | 2.817,07 | 44,47 | 4,34 | 0,4886 | 0,4883 |
| three-turns | 775 | 4,79% | 2.730,43 | 2.678,82 | 51,61 | 4,00 | 0,6065 | 0,6063 |
| patient | **1.123** | 6,93% | 2.316,78 | 2.257,29 | **59,49** | **3,18** | 0,8169 | 0,8167 |

Três coisas estão nessa tabela.

**As horas economizadas são monótonas nos clientes perdidos.** A política que afasta mais gente obtém
a maior redução de horas humanas, e cada uma dessas horas chega ao relatório como eficiência. Não há
uma linha em nenhuma das nove primeiras ondas deste repositório onde ela apareceria como outra coisa.

**O ranking por clientes perdidos é o ranking por contenção, exatamente.** `patient` primeiro,
`human-only` último — o quarto ranking das mesmas quatro políticas, e o segundo que concorda com o KPI
enquanto discorda de resolução e de dias até resolver. A política que maximiza contenção perde **4,37
vezes** mais clientes que a fila humana.

**E a contenção não consegue ver a perda que causa.** Recalculada sobre os contatos sobreviventes, a
contenção de sessão se move **0,00017**. Isso não é um efeito pequeno sendo reportado fielmente; é o
denominador e o numerador caindo juntos, que é o que uma razão faz quando se removem as pessoas sobre
as quais ela é uma razão.

A taxa de câmbio é a linha para ler em voz alta. Na política que maximiza contenção, uma hora de
atendimento economizada custa **18,88 clientes**. Na fila humana um cliente perdido vale 5,72 minutos
e no `patient` 3,18 — a política agressiva perde contatos *mais baratos*, então tem de perder *mais*
gente para lançar a mesma economia.

## Resultado 4: a válvula que três ondas usaram, precificada em gente

Abandono convertido pela taxa declarada, sobre o volume tratado do mês:

| Decisão | Abandono | Contatos abandonados | **Clientes perdidos** | Parcela |
| --- | --- | --- | --- | --- |
| onda 3 — seis atendentes, "perfeitamente estável" | 29,23% | 9.295,7 | **557,74** | 3,44% |
| onda 8 — o regime alcançado desde a crise | 21,00% | 6.678,4 | 400,71 | 2,47% |
| onda 7 — oito atendentes, ocupação mantida sozinha | 14,34% | 4.560,4 | 273,62 | 1,69% |
| onda 7 — onze atendentes, todos os tetos atendidos | 3,56% | 1.132,2 | **67,93** | 0,42% |

A fila estável da onda 3 gasta **489,81 clientes a mais por mês** que o plano que cumpre seus tetos. A
meta de ocupação de aparência humana da onda 7, perseguida sozinha, gasta **205,70 a mais**.

E isso fecha a questão que a onda 8 deixou aberta. A onda 8 precificou um atendente extra em 12
pessoa-mês por ano contra 2,33 devolvidos — razão de 0,19 — e disse claramente que o caso repousa
inteiramente sobre o que uma saída custa *fora* da fila, o que ela não podia fornecer. Ir de seis
atendentes para onze custa cinco atendentes e retém 489,81 clientes: **97,96 clientes por mês por
atendente.** Este módulo continua não precificando um cliente, porque não há dinheiro neste
repositório. Ele fornece a quantidade e deixa o preço com o leitor, que é onde uma decisão dessas
pertence.

## A unidade estava errada por nove ondas

Só **590** contatos desaparecem sob o `three-turns` — 1,86% do mês. Esse número é pequeno por uma
razão estrutural e não tranquilizadora: um cliente que sai no dia três perde vinte e sete dias aqui e
**o resto da vida** numa operação. Os segundos desta tabela são um fragmento de um mês de uma perda
permanente.

O que é o argumento de toda a onda. Segundos, sessões, atendentes e horas são quantidades mensais, e
um mês é a janela em que toda onda aqui mediu. Clientes não são mensais. Nove ondas construíram uma
conta cada vez mais cuidadosa numa unidade que não consegue expressar a perda — e a única razão pela
qual levou dez ondas para notar é que a unidade nunca esteve errada sobre nada mais.

## Premissas e limitações

- **A curva é declarada, não ajustada.** 6% após abandonar, 4% após um contato não resolvido, 0,5%
  após um resolvido. Esses três números carregam toda cifra acima, e nada aqui os mede. Numa operação
  real são a primeira coisa que vale estimar e a mais difícil.
- **A pior experiência domina.** Um contato abandonado e depois resolvido conta como abandonado. É uma
  afirmação sobre memória, e uma alternativa plausível — recência, ou uma média — moveria o ranking
  entre políticas cujas falhas chegam em ordens diferentes.
- **Uma decisão por contato.** A chance de um cliente sair não acumula ao longo de um mês ruim; cada
  contato é sua própria moeda na sua própria taxa declarada. Uma relação real tem um limiar, e um
  modelo de limiar puniria as políticas que falham com a mesma pessoa duas vezes — que é exatamente o
  que a onda 4 mediu e este módulo não usa.
- **Uma saída remove contatos e nada mais.** Sem boca a boca, sem reclamação a regulador, sem efeito
  na propensidade de contato de mais ninguém. Cada um desses torna a perda maior que a publicada.
- **A janela mensal trunca tudo.** Como acima: os contatos removidos são o restante de um mês, então
  toda cifra de horas aqui é um piso, por aproximadamente a razão entre a vida de um cliente e a
  quinzena que lhe restava.
- **A tabela da válvula é de primeira ordem e um limite superior.** Contatos abandonados vezes a
  chance de sair, o que conta duas vezes o cliente que abandona duas vezes. A direção é deliberada: um
  número cuja função é fazer uma decisão de aparência barata parecer cara não deve também ser otimista.
- **A regra de silêncio é medida contra uma verdade que nenhuma operação tem.** Esse é todo o método
  deste repositório, e é por isso que o estudo de instrumento pode existir.

## Fontes

- O enquadramento como instrumento, o par sensibilidade–especificidade e o índice de Youden são os
  mesmos instrumentos que a onda 2 usa; a identidade de atenuação aplicada a uma comparação de churn é
  a identidade em `svclab.quality`, não um resultado novo.
- Tratar uma saída não observável por um proxy observável, e o colapso de precisão em baixa
  prevalência, é o argumento padrão de taxa-base sobre testes de triagem; a aritmética aqui é Bayes e
  nada mais.
- A ideia de que a continuidade de um cliente depende da experiência de serviço é a afirmação central
  da literatura de qualidade de serviço e de satisfação-lealdade; este módulo não a testa, ele a assume
  e declara os parâmetros.
