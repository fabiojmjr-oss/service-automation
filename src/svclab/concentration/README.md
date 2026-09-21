# `svclab.concentration` — the frequent caller who is also a difficult one

*[Português](#svclabconcentration--o-chamador-frequente-que-também-é-difícil)*

Wave 4 gave a customer a difficulty and a patience of their own and left their **rate** alone. Every
contact still picked a customer uniformly, so contact counts were Poisson with a mean below two, the
busiest customer in the account was busy by accident, and the design effect that followed was 1.0693.

Both halves of that are assumptions, and a real account breaks both. Volume is **concentrated** — a
minority of customers generate a large share of it — and that minority is **not random**: the people
who contact most are, on average, the people whose problems are hardest. That is the entire reason a
frequent caller is expensive rather than merely frequent.

This module regroups the same contacts into customers who do not all contact equally often. A
customer's propensity is log-normal and its latent value correlates with their own difficulty at a
declared **0.40**. The regrouping reuses the uniform that chose the customer in the first place and
never crosses an arm, so:

- the treated and holdout arms hold the **identical contacts**;
- every contact keeps **every trait** — difficulty, handling time, patience, the counterfactuals;
- and therefore **every per-contact figure in waves 1 to 4 is bit-for-bit identical**, asserted
  exactly rather than to a tolerance.

The control is the world regrouped with **equal rates**, not the world waves 1 to 4 published.
Reassigning contacts among the customers an account actually saw makes clusters larger on its own —
13,087 customers instead of 16,195 — and attributing that to concentration would be attributing an
artefact.

```python
from svclab.bot import HUMAN_ONLY, THREE_TURNS, run
from svclab.concentration import burden_table, concentration_table, precision_table
from svclab.population import design_table
from svclab.synth import EQUAL_RATES, concentrated_dataset, correlated_dataset, generate_dataset

data = generate_dataset()
# Regroup first, then correlate: the copula has to know who the customer is.
worlds = {
    "equal rates": correlated_dataset(concentrated_dataset(data, EQUAL_RATES)),
    "concentrated": correlated_dataset(concentrated_dataset(data)),
}
treated = {name: world.contacts[~world.contacts["holdout"]] for name, world in worlds.items()}
outcomes = {name: run(table, THREE_TURNS) for name, table in treated.items()}

concentration_table(treated)  # how unequal, and whether the heavy users are the difficult ones
burden_table(treated, outcomes)  # who pays for it
design_table(outcomes)  # what unequal clusters do to a comparison
```

## Result 1: the same volume, from fewer people, and they are the harder ones

The treated arm of each world — the identical 31,802 contacts throughout:

| | Equal rates (control) | Concentrated |
| --- | --- | --- |
| customers seen | 13,087 | **10,640** |
| contacts | 31,802 | 31,802 |
| mean contacts per customer | 2.4300 | 2.9889 |
| **effective** contacts per customer | 3.2272 | **5.7454** |
| Gini of the contact counts | 0.3039 | 0.4195 |
| share of volume from the top decile | 0.2197 | **0.3161** |
| correlation of rate with difficulty | 0.0004 | **0.1595** |

Two things to read carefully.

**The declared correlation is 0.40 and the measured one is 0.1595.** That is not a discrepancy, it is
wave 4's attenuation chain again: 0.40 is the latent correlation between a customer's propensity and
their difficulty, and what this column measures is the correlation between an integer contact **count**
and a mean of contact difficulties. A rate becomes a count by a Poisson draw, and a count of two or
three carries little information about the rate behind it. The declared number is checked on the latent
scale, in the tests, where the construction is exact.

**And the effective cluster size moves further than the mean.** 2.43 to 2.99 is a 23% rise in the mean;
3.23 to 5.75 is a 78% rise in the quantity a design effect is actually computed from. Concentration is
a statement about the variance of the cluster sizes, and the mean barely sees it.

## Result 2: which is where wave 3's alarm comes back

| World | ICC | Mean cluster | Effective cluster | Design effect | At the mean | Extra sample | Actual α |
| --- | --- | --- | --- | --- | --- | --- | --- |
| equal rates | 0.0417 | 2.4300 | 3.2272 | 1.0928 | 1.0596 | +9.28% | 0.0608 |
| concentrated | 0.0473 | 2.9889 | 5.7454 | **1.2246** | 1.0941 | **+22.46%** | **0.0765** |
| wave 3's declared 0.30 | 0.3000 | 1.9637 | — | 1.2891 | — | +28.91% | 0.0843 |

**The design effect of the concentrated world is 1.2246 against the 1.2891 wave 3 declared as its
serious case — 95% of it.** Wave 4 measured 1.0693 and called wave 3's alarm four times too loud; wave
4 was measuring a world in which everybody contacts at the same rate, which it had assumed rather than
chosen. Two wrong assumptions in opposite directions, and their product was close to right. That is
how a number survives being wrong twice, and it is not a defence of either.

The column headed **At the mean** is the second half of the correction. Using the plain mean cluster
size here reports an inflation of 9.41% where the correct figure is 22.46% — **less than half** — and
it is wrong in the direction that lets a test ship. The two columns are kept side by side for that
reason.

## Result 3: the cost concentrates faster than the volume

| | Equal rates (control) | Concentrated |
| --- | --- | --- |
| mean difficulty per contact | 0.3352 | **0.3684** |
| resolution rate | 0.6358 | **0.6205** |
| top decile's share of volume | 0.2197 | 0.3161 |
| top decile's share of unresolved contacts | 0.2201 | **0.3265** |
| top decile's share of human hours | 0.2201 | **0.3541** |
| customers failed three times or more | 794 | **1,305** |

**In the control the three shares are one number.** 0.2197, 0.2201, 0.2201 — the heaviest tenth of
customers generates 22% of the volume and consumes 22% of the queue, because being heavy says nothing
about being difficult. Concentration separates them: 31.6% of the volume, 32.7% of the failures and
**35.4% of the human hours**. The cost is more concentrated than the contacts, and the gap between
those two numbers is what a per-contact cost model cannot represent.

And **the resolution rate falls 1.53 points with no change of policy whatsoever.** This is the one
per-contact figure that moves in this wave, and the mechanism is worth being precise about: the
distribution of difficulty **per customer** is unchanged, and the distribution **per contact** is not,
because the difficult customers now send more contacts each. The queue's mix of difficulty is a
property of who calls, not only of who they are. Mean difficulty per contact rises 9.9% and the bot
loses a point and a half of resolution to arithmetic nobody in the business case would have modelled.

Finally, 794 customers failed three times or more becomes **1,305** — a 64% rise in the population that
generates complaints, escalations and churn, on a resolution rate that fell by one and a half points.
Wave 4 found the same shape at pairs; concentration compounds it, because a customer with six contacts
has six chances to be failed and a correlated reason to be.

## Result 4: and wave 1's central estimate loses a third of its precision

Deflection per customer, treated against holdout, with the identical contacts and policy:

| World | Customers | Deflected per customer | Standard error | Relative error | Interval width |
| --- | --- | --- | --- | --- | --- |
| equal rates | 13,087 | 1.5484 | 0.0381 | **2.46%** | 0.1495 |
| concentrated | 10,640 | 1.7845 | 0.0730 | **4.09%** | 0.2862 |

**The estimates are not comparable and the errors are.** Deflection per customer divides by a count of
customers, and the two worlds disagree about how many customers produced the same volume — so 1.5484
against 1.7845 is a denominator, not a finding. What is comparable is the precision: the relative error
rises **66%** and the interval is **91% wider**, on the same contacts, the same arms and the same bot.

That is the practical shape of the whole wave. A per-customer number is only as stable as the
assumption about who a customer is, and wave 1's business case is a per-customer number.

## Assumptions and limitations

- **Every number here comes from a seeded synthetic generator**, including the dispersion and the
  correlation the whole argument turns on. No employer, client, vendor or platform data is used
  anywhere, and there is no language model. See [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **The reassignment draws from the customers the account already saw**, because a customer with no
  contacts in the original world has no arm to be reassigned within, and inventing one would move the
  holdout share every earlier wave reported. That shrinks the pool and enlarges the clusters on its
  own, which is exactly why the control is the regrouped world with equal rates rather than the
  published one.
- **A log-normal rate is a declared shape.** It gives a smooth heavy-ish tail and no true outliers. The
  customer with two hundred contacts a month — the one an operation actually names in meetings — is a
  different distribution, and it would move Result 3 further than it moves Result 2.
- **The total volume is fixed.** Concentration here redistributes 31,802 contacts among fewer people.
  A real account with difficult frequent callers has *more* contacts, not the same number differently
  arranged, so every figure here is the pure regrouping effect with the volume effect held out.
- **A customer's rate is constant over the period.** No escalation, no month where somebody contacts
  nine times and then never again, and no relationship between a failure and the next contact's timing
  beyond wave 1's single repeat.
- **The top decile is defined by contact count, and counts tie.** With most customers at one or two
  contacts, which ties are broken into the decile is arbitrary; the comparison between worlds holds
  because the definition is identical in both.
- **One repeat, still.** "Failed three times" therefore means three separate contacts of one customer,
  not a chain, and a chain would raise every figure in Result 3.

## Sources

Cited as the origin of a *method*, never as a source of any number in these tables.

- Gini, C. (1912). *Variabilità e mutabilità.* — the inequality coefficient Result 1 reports.
- Lorenz, M. O. (1905). *Methods of Measuring the Concentration of Wealth.* Publications of the
  American Statistical Association 9. — the curve that coefficient summarises.
- Kish, L. (1965). *Survey Sampling.* Wiley. — the design effect, and the size-weighted mean cluster
  size that belongs in it when clusters are unequal.
- Cochran, W. G. (1977). *Sampling Techniques*, 3rd ed. Wiley. — cluster sampling with unequal
  clusters, and why a contact's expected cluster is larger than the average cluster.
- Donner, A., Klar, N. (2000). *Design and Analysis of Cluster Randomization Trials in Health
  Research.* Arnold. — the consequences of unequal cluster sizes for a comparison's error rate.

---

# `svclab.concentration` — o chamador frequente que também é difícil

*[English](#svclabconcentration--the-frequent-caller-who-is-also-a-difficult-one)*

A onda 4 deu ao cliente uma dificuldade e uma paciência próprias e deixou a **taxa** de lado. Todo
contato ainda escolhia um cliente uniformemente, então as contagens de contato eram Poisson com média
abaixo de dois, o cliente mais movimentado da conta era movimentado por acaso, e o efeito de desenho
que saía dali era 1,0693.

As duas metades disso são premissas, e uma conta real quebra ambas. O volume é **concentrado** — uma
minoria de clientes gera parcela grande dele — e essa minoria **não é aleatória**: quem mais contata
é, em média, quem tem os problemas mais difíceis. É essa a razão inteira de um chamador frequente ser
caro em vez de apenas frequente.

Este módulo reagrupa os mesmos contatos em clientes que não contatam todos igualmente. A propensão de
um cliente é log-normal e seu valor latente se correlaciona com a dificuldade dele a um declarado
**0,40**. O reagrupamento reaproveita o uniforme que escolheu o cliente originalmente e nunca cruza um
braço, então:

- os braços tratado e holdout contêm os **contatos idênticos**;
- todo contato conserva **todos os traços** — dificuldade, tempo de atendimento, paciência, os
  contrafactuais;
- e portanto **toda cifra por contato das ondas 1 a 4 é idêntica bit a bit**, verificada exatamente e
  não por tolerância.

O controle é o mundo reagrupado com **taxas iguais**, não o mundo que as ondas 1 a 4 publicaram.
Reatribuir contatos entre os clientes que a conta de fato viu já aumenta os grupos por si só — 13.087
clientes em vez de 16.195 — e atribuir isso à concentração seria atribuir um artefato.

```python
from svclab.bot import HUMAN_ONLY, THREE_TURNS, run
from svclab.concentration import burden_table, concentration_table, precision_table
from svclab.population import design_table
from svclab.synth import EQUAL_RATES, concentrated_dataset, correlated_dataset, generate_dataset

data = generate_dataset()
# Reagrupar primeiro, correlacionar depois: a cópula precisa saber quem é o cliente.
worlds = {
    "equal rates": correlated_dataset(concentrated_dataset(data, EQUAL_RATES)),
    "concentrated": correlated_dataset(concentrated_dataset(data)),
}
treated = {name: world.contacts[~world.contacts["holdout"]] for name, world in worlds.items()}
outcomes = {name: run(table, THREE_TURNS) for name, table in treated.items()}

concentration_table(treated)  # quão desigual, e se os pesados são os difíceis
burden_table(treated, outcomes)  # quem paga por isso
design_table(outcomes)  # o que grupos desiguais fazem a uma comparação
```

## Resultado 1: o mesmo volume, vindo de menos gente — e mais difícil

O braço tratado de cada mundo — os mesmos 31.802 contatos em todos:

| | Taxas iguais (controle) | Concentrado |
| --- | --- | --- |
| clientes vistos | 13.087 | **10.640** |
| contatos | 31.802 | 31.802 |
| contatos médios por cliente | 2,4300 | 2,9889 |
| contatos **efetivos** por cliente | 3,2272 | **5,7454** |
| Gini das contagens de contato | 0,3039 | 0,4195 |
| fração do volume do decil de topo | 0,2197 | **0,3161** |
| correlação da taxa com a dificuldade | 0,0004 | **0,1595** |

Dois pontos a ler com atenção.

**A correlação declarada é 0,40 e a medida é 0,1595.** Não é discrepância, é a cadeia de atenuação da
onda 4 outra vez: 0,40 é a correlação latente entre a propensão de um cliente e a dificuldade dele, e o
que esta coluna mede é a correlação entre uma **contagem** inteira de contatos e uma média de
dificuldades. Uma taxa se torna contagem por um sorteio de Poisson, e uma contagem de dois ou três
carrega pouca informação sobre a taxa por trás. O número declarado é verificado na escala latente, nos
testes, onde a construção é exata.

**E o tamanho efetivo de grupo se move mais que a média.** De 2,43 a 2,99 é uma alta de 23% na média;
de 3,23 a 5,75 é uma alta de 78% na quantidade de que um efeito de desenho é de fato calculado.
Concentração é uma afirmação sobre a variância dos tamanhos, e a média quase não a vê.

## Resultado 2: e é aqui que o alarme da onda 3 volta

| Mundo | ICC | Grupo médio | Grupo efetivo | Efeito de desenho | Na média | Amostra extra | α real |
| --- | --- | --- | --- | --- | --- | --- | --- |
| taxas iguais | 0,0417 | 2,4300 | 3,2272 | 1,0928 | 1,0596 | +9,28% | 0,0608 |
| concentrado | 0,0473 | 2,9889 | 5,7454 | **1,2246** | 1,0941 | **+22,46%** | **0,0765** |
| os 0,30 declarados na onda 3 | 0,3000 | 1,9637 | — | 1,2891 | — | +28,91% | 0,0843 |

**O efeito de desenho do mundo concentrado é 1,2246 contra os 1,2891 que a onda 3 declarou como seu
caso sério — 95% dele.** A onda 4 mediu 1,0693 e disse que o alarme da onda 3 era quatro vezes alto
demais; a onda 4 media um mundo em que todos contatam na mesma taxa, o que ela havia assumido e não
escolhido. Duas premissas erradas em direções opostas, e o produto delas ficou perto do certo. É assim
que um número sobrevive a estar errado duas vezes — e isso não defende nenhuma das duas.

A coluna **Na média** é a segunda metade da correção. Usar o tamanho médio simples aqui reporta uma
inflação de 9,41% onde a cifra correta é 22,46% — **menos da metade** — e erra na direção que deixa um
teste ser aprovado. É por isso que as duas colunas ficam lado a lado.

## Resultado 3: o custo se concentra mais rápido que o volume

| | Taxas iguais (controle) | Concentrado |
| --- | --- | --- |
| dificuldade média por contato | 0,3352 | **0,3684** |
| taxa de resolução | 0,6358 | **0,6205** |
| fração do volume no decil de topo | 0,2197 | 0,3161 |
| fração dos não resolvidos no decil de topo | 0,2201 | **0,3265** |
| fração das horas humanas no decil de topo | 0,2201 | **0,3541** |
| clientes falhados três vezes ou mais | 794 | **1.305** |

**No controle as três frações são um único número.** 0,2197, 0,2201, 0,2201 — o décimo mais pesado de
clientes gera 22% do volume e consome 22% da fila, porque ser pesado não diz nada sobre ser difícil. A
concentração separa: 31,6% do volume, 32,7% das falhas e **35,4% das horas humanas**. O custo é mais
concentrado que os contatos, e a distância entre esses dois números é o que um modelo de custo por
contato não consegue representar.

E **a taxa de resolução cai 1,53 ponto sem mudança nenhuma de política.** Esta é a única cifra por
contato que se move nesta onda, e vale ser preciso sobre o mecanismo: a distribuição de dificuldade
**por cliente** está inalterada, e a **por contato** não está, porque os clientes difíceis agora mandam
mais contatos cada um. A mistura de dificuldade que a fila recebe é uma propriedade de quem liga, não
só de quem essas pessoas são. A dificuldade média por contato sobe 9,9% e o bot perde um ponto e meio
de resolução para uma aritmética que nenhum business case teria modelado.

Por fim, 794 clientes falhados três vezes ou mais viram **1.305** — alta de 64% na população que gera
reclamações, escalonamentos e churn, sobre uma taxa de resolução que caiu um ponto e meio. A onda 4
encontrou a mesma forma em pares; a concentração a compõe, porque um cliente com seis contatos tem seis
chances de ser falhado e uma razão correlacionada para isso.

## Resultado 4: e a estimativa central da onda 1 perde um terço da precisão

Deflexão por cliente, tratado contra holdout, com contatos e política idênticos:

| Mundo | Clientes | Deflexão por cliente | Erro padrão | Erro relativo | Largura do intervalo |
| --- | --- | --- | --- | --- | --- |
| taxas iguais | 13.087 | 1,5484 | 0,0381 | **2,46%** | 0,1495 |
| concentrado | 10.640 | 1,7845 | 0,0730 | **4,09%** | 0,2862 |

**As estimativas não são comparáveis e os erros são.** Deflexão por cliente divide por uma contagem de
clientes, e os dois mundos discordam sobre quantos clientes produziram o mesmo volume — então 1,5484
contra 1,7845 é um denominador, não um achado. O que é comparável é a precisão: o erro relativo sobe
**66%** e o intervalo fica **91% mais largo**, sobre os mesmos contatos, os mesmos braços e o mesmo bot.

Esta é a forma prática da onda inteira. Um número por cliente só é tão estável quanto a premissa sobre
o que é um cliente — e o business case da onda 1 é um número por cliente.

## Premissas e limitações

- **Toda cifra aqui vem de um gerador sintético com semente**, inclusive a dispersão e a correlação de
  que todo o argumento depende. Nenhum dado de empregador, cliente, fornecedor ou plataforma é usado em
  lugar algum, e não existe modelo de linguagem. Ver [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **A reatribuição sorteia entre os clientes que a conta já viu**, porque um cliente sem contatos no
  mundo original não tem braço dentro do qual ser reatribuído, e inventar um moveria a fração de
  holdout que toda onda anterior reportou. Isso encolhe o conjunto e aumenta os grupos por si só — e é
  precisamente por isso que o controle é o mundo reagrupado com taxas iguais, e não o publicado.
- **Uma taxa log-normal é uma forma declarada.** Ela dá uma cauda suave e pesada o bastante, e nenhum
  outlier verdadeiro. O cliente com duzentos contatos no mês — aquele que uma operação nomeia em
  reunião — é outra distribuição, e moveria o Resultado 3 mais do que move o Resultado 2.
- **O volume total é fixo.** A concentração aqui redistribui 31.802 contatos entre menos pessoas. Uma
  conta real com chamadores frequentes difíceis tem *mais* contatos, não o mesmo número arranjado de
  outro jeito, então toda cifra aqui é o efeito puro de reagrupamento com o efeito de volume retirado.
- **A taxa de um cliente é constante no período.** Sem escalada, sem mês em que alguém contata nove
  vezes e depois nunca mais, e sem relação entre uma falha e o momento do próximo contato além da
  repetição única da onda 1.
- **O decil de topo é definido por contagem de contatos, e contagens empatam.** Com a maioria dos
  clientes em um ou dois contatos, quais empates entram no decil é arbitrário; a comparação entre
  mundos se sustenta porque a definição é idêntica nos dois.
- **Ainda uma repetição só.** "Falhado três vezes" significa portanto três contatos separados de um
  cliente, não uma cadeia — e uma cadeia elevaria toda cifra do Resultado 3.

## Fontes

Citadas como origem de um *método*, nunca como fonte de qualquer número destas tabelas.

- Gini, C. (1912). *Variabilità e mutabilità.* — o coeficiente de desigualdade do Resultado 1.
- Lorenz, M. O. (1905). *Methods of Measuring the Concentration of Wealth.* Publications of the
  American Statistical Association 9. — a curva que esse coeficiente resume.
- Kish, L. (1965). *Survey Sampling.* Wiley. — o efeito de desenho, e o tamanho médio de grupo
  ponderado por tamanho que entra nele quando os grupos são desiguais.
- Cochran, W. G. (1977). *Sampling Techniques*, 3ª ed. Wiley. — amostragem por conglomerados com
  grupos desiguais, e por que o grupo esperado de um contato é maior que o grupo médio.
- Donner, A., Klar, N. (2000). *Design and Analysis of Cluster Randomization Trials in Health
  Research.* Arnold. — as consequências de tamanhos desiguais de grupo para a taxa de erro de uma
  comparação.
