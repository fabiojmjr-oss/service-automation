# `svclab.population` — the customer who was a label

*[Português](#svclabpopulation--o-cliente-que-era-um-rótulo)*

Wave 3 measured the intracluster correlation of this account and found approximately **zero**. That
was not a discovery about contact centres. The generator drew every trait per contact, so a customer
id was a label on a row rather than somebody with a history, and the design effects wave 3 priced had
to be **declared** because there was none to observe.

This module closes that, and the way it closes it is the point. The account now exists **twice**:

- the **independent** world, where every trait is drawn per contact — the one waves 1 to 3 published;
- the **correlated** world, where each customer has a difficulty and a patience of their own.

The second is built from the **identical noise**. A contact's percentile is pushed through the normal
quantile, mixed with its customer's percentile at declared loadings, and pushed back out through its
own quantile function — a Gaussian copula, which leaves every **marginal distribution exactly where
it was** and changes only the dependence between two contacts of one person. The uniforms behind
every outcome are reused rather than redrawn.

So the independent world is a **control**, not a baseline. What an estimator does on data with no
structure in it is a fact about the estimator, and two of the five results below are only legible
against that row.

```python
from svclab.bot import HUMAN_ONLY, THREE_TURNS, run
from svclab.population import (
    correlation_table,
    design_table,
    error_table,
    pair_failures,
    world_table,
)
from svclab.synth import correlated_dataset, generate_dataset

data = generate_dataset()
other = correlated_dataset(data)  # the same account, with customers who are people

contacts = {"independent": data.contacts, "correlated": other.contacts}
treated = {name: run(table[~table["holdout"]], THREE_TURNS) for name, table in contacts.items()}
control = {name: run(table[table["holdout"]], HUMAN_ONLY) for name, table in contacts.items()}

world_table(contacts, treated)  # did anything already published move?
correlation_table(contacts, treated)  # declared, latent, observed, and on the outcome
design_table(treated)  # what the surviving correlation costs a comparison
pair_failures(treated)  # the same person failed twice
error_table(treated, control)  # three standard errors on one difference
```

## Result 1: nothing that was published moves

The `three-turns` policy on the treated arm of each world:

| | Independent | Correlated | Difference |
| --- | --- | --- | --- |
| mean difficulty | 0.3340 | 0.3347 | +0.0007 |
| difficulty sd | 0.1776 | 0.1782 | +0.0006 |
| mean patience turns | 4.5178 | 4.5117 | −0.0061 |
| session containment | 0.6065 | 0.6046 | −0.0019 |
| needed containment | 0.2145 | 0.2126 | −0.0019 |
| resolution rate | 0.6355 | 0.6357 | +0.0002 |
| repeats per contact | 0.2099 | 0.2094 | −0.0005 |
| human hours | 2,730.43 | 2,728.43 | **−2.00** |

**The largest relative movement in the table is 0.89%**, on `needed containment`, and every figure
waves 1 to 3 published still passes its own test unchanged. Two human hours out of 2,730 is the
correlation's effect on the month's workload.

This is a **precondition and not a finding**. It is what says the comparisons below are about
dependence and about nothing else — and it is the reason the copula replaced a convex combination of
two draws, which would have narrowed the marginal spread to 54.5% of its variance and left every
difference attributable to two causes at once. The first version of this module did exactly that, and
the resolution rate moved by eight points for a reason that had nothing to do with customers — the
defect is recorded in [`docs/ROADMAP.md`](../../../docs/ROADMAP.md) with the figures it produced.

**A correlation does not change what happened. It changes what you can conclude from it.**

## Result 2: a correlation between people is not a correlation between outcomes

The declared number, and how much of it is left at each stage:

| Stage | Difficulty | Patience | Resolution |
| --- | --- | --- | --- |
| declared | **0.2500** | **0.1000** | — |
| latent | 0.2535 | 0.0911 | — |
| observed on the trait | 0.2463 | 0.0740 | — |
| on the outcome a test runs on | — | — | **0.0448** |

Three losses, each with a mechanism:

- **Latent to observed.** The copula's guarantee is exact on the normal scale. Pushing back through
  a `Beta(2, 4)` costs a little; rounding a patience up to a whole number of turns costs more,
  which is why 0.1000 arrives as 0.0740.
- **Trait to outcome.** This is the large one. A resolution is **a coin whose bias is correlated,
  not a correlated coin**, and at a resolution rate near 0.64 the Bernoulli variance is 0.23 while
  the between-customer part of the bias is a fraction of it. A quarter of the difficulty belonging
  to the person survives as **4.5%** of the outcome.

The practical consequence is a rule for anybody sizing a clustered test: **estimate the correlation
of the outcome you are testing, not of the trait you believe drives it.** They differ here by a
factor of 5.6, in the direction that makes the correction smaller — which is the direction nobody
guesses, because the intuition being applied is "customers repeat, so my data must be deeply
clustered".

## Result 3: what the surviving part costs, against what wave 3 assumed

| World | ICC | Mean cluster | Design effect | Extra sample | Nominal α | Actual α |
| --- | --- | --- | --- | --- | --- | --- |
| independent | −0.0126 | 1.9637 | 0.9879 | — | 0.05 | **no answer** |
| correlated | 0.0448 | 1.9637 | **1.0432** | **+4.32%** | 0.05 | **0.0550** |
| wave 3's declared 0.30 | 0.3000 | 1.9637 | 1.2891 | +28.91% | 0.05 | 0.0843 |

The independent row returns **no error rate at all**, and that is wave 3's function working as
specified: a measured design effect below one is a negative correlation estimate, which is not an
inflation, and `actual_alpha` refuses it rather than clipping it to 0.05. A table that printed the
nominal value there would be inventing a number.

And the correlated row is **seven times smaller than the scenario wave 3 priced**. At wave 3's own
sizing of 405 contacts per arm, the power of the comparison it sized is:

| | Power at 405 contacts per arm |
| --- | --- |
| independent contacts | 0.8026 |
| at the **measured** design effect | **0.7859** |
| at wave 3's declared 0.30 | 0.6970 |

So wave 3's alarm was right in **shape** and wrong in **size** on this account: the correction is
1.7 points of power, not 11. Both numbers matter, and the honest statement is the one wave 3 could
not make — the effect is real, measurable, and modest, because a design effect is a product of two
factors and this account's clusters average **two**.

## Result 4: the same person, failed twice

Customers with exactly two contacts, in each world, on identical noise:

| World | Pairs | Failure rate | Failed on both | Expected if independent | Ratio |
| --- | --- | --- | --- | --- | --- |
| independent | 5,234 | 0.3632 | 0.1219 | 0.1319 | 0.9240 |
| correlated | 5,234 | 0.3629 | **0.1406** | 0.1317 | **1.0677** |

**The resolution rate moved by 0.0002 and the share of two-contact customers failed both times rose
15.4%** — 98 more people, out of the same volume, with the same aggregate KPI.

Read the ratios against each other rather than against 1.0. The independent world's 0.9240 is what
this estimator does on data with no dependence in it at all, so the correlation's contribution is the
**15.5% rise between the rows**, not the distance from one.

This is the wave's operational finding. A resolution rate is a **contact-weighted** number, and the
experience that generates a complaint, a churn or a regulator's letter is **customer-weighted**. The
two agree exactly when a customer is a label. When a customer is a person they come apart, and they
come apart in the direction the operation feels and the dashboard does not.

## Result 5: the correction most analysts reach for costs more than the thing it corrects

Three standard errors on one difference — the treated arm's resolution rate against the holdout's:

| World | Estimate | Naive | Cluster mean | Corrected | Cluster-mean ratio | Corrected ratio |
| --- | --- | --- | --- | --- | --- | --- |
| independent | −0.2955 | 0.003889 | 0.004406 | 0.003867 | **1.1330** | 0.9943 |
| correlated | −0.2956 | 0.003886 | 0.004427 | 0.003913 | **1.1392** | 1.0071 |

Read the independent row first. **Averaging customer averages inflates the standard error by 13.3%
in a world with no correlation in it whatever.** That is not a clustering correction, it is an
efficiency loss wearing one's clothes: aggregating to unequal-sized clusters and weighting them
equally discards information about how many contacts each average was built from.

The correlation's own contribution, on the same data, is the **0.7%** in the corrected column. So the
analyst who "handles the clustering" by averaging per customer pays about **nineteen times** the
error they were correcting for.

The corrected error is smaller than the cluster-mean one because it multiplies the naive error by the
square root of the **pooled** design effect — pooled across the two arms, and the holdout arm is
`human-only`, whose resolution is near 0.93 whatever the customer is like. An arm with almost no
between-customer variance halves the correction that applies to a difference. The design effect of
one arm is not the design effect of a comparison, which is the last small trap in a chain of them.

## Assumptions and limitations

- **Every number here comes from a seeded synthetic generator**, including both declared
  correlations. No employer, client, vendor or platform data is used anywhere, and there is no
  language model. See [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **The correlations are declared, not fitted.** 0.25 on difficulty and 0.10 on patience were chosen
  to sit inside the range wave 3 had to guess at. Nothing here is evidence about what a real
  account's correlation is; it is evidence about what a correlation of a given size does, and about
  how much of it survives into an outcome.
- **A Gaussian copula is a strong shape assumption.** It gives one parameter per trait and no tail
  dependence: a customer who is difficult is uniformly more likely to be difficult, rather than
  occasionally catastrophically so. Real frequent callers look more like a heavy tail than like a
  shifted mean, and a heavy tail would move Result 4 further than it moves Result 3.
- **The customer's effect is on difficulty and patience only.** Contact *frequency* is still drawn
  independently, so the customers with the most contacts are not the hardest ones. That is the next
  correction and it is the one that would sharpen Result 4, because in a real account the people who
  contact most and the people who are hardest to satisfy overlap.
- **Clusters here average 1.96 contacts.** Every design effect in this module is bounded by a factor
  of two for that reason alone. The same correlation in a study randomised by clinic, school or
  depot — clusters of fifty — is a different order of problem, and quoting this module's modest
  numbers as reassurance there would be a misreading.
- **One repeat, still.** An unresolved contact returns at most once, so "failed twice" is measured
  on two independent contacts of one customer rather than on a chain. Chains would raise Result 4.
- **The outcome ICC is estimated by analysis of variance on a binary variable.** That estimator is
  known to be biased downwards for rare outcomes; at rates near 0.64 it is well behaved, and the
  independent world's row is the check that it is not manufacturing a correlation.

## Sources

Cited as the origin of a *method*, never as a source of any number in these tables.

- Sklar, A. (1959). *Fonctions de répartition à n dimensions et leurs marges.* Publications de
  l'Institut de Statistique de l'Université de Paris 8. — that a joint distribution splits into
  marginals and a dependence structure, which is why the marginals here can be held fixed.
- Nelsen, R. B. (2006). *An Introduction to Copulas*, 2nd ed. Springer. — the Gaussian copula as a
  construction, and its lack of tail dependence.
- Kish, L. (1965). *Survey Sampling.* Wiley. — the design effect wave 3 uses and this wave measures.
- Donner, A., Klar, N. (2000). *Design and Analysis of Cluster Randomization Trials in Health
  Research.* Arnold. — cluster-level versus individual-level analysis, and the efficiency cost of
  the former with unequal cluster sizes.
- Liang, K.-Y., Zeger, S. L. (1986). *Longitudinal Data Analysis Using Generalized Linear Models.*
  Biometrika 73. — correcting inference for within-cluster dependence without modelling it.
- Ridout, M. S., Demétrio, C. G. B., Firth, D. (1999). *Estimating Intraclass Correlation for Binary
  Data.* Biometrics 55. — why the correlation of a binary outcome is not the correlation of the
  latent trait behind it.

---

# `svclab.population` — o cliente que era um rótulo

*[English](#svclabpopulation--the-customer-who-was-a-label)*

A onda 3 mediu a correlação intraclasse desta conta e encontrou aproximadamente **zero**. Isso não
era uma descoberta sobre centrais de atendimento. O gerador sorteava todo traço por contato, então um
id de cliente era um rótulo numa linha e não alguém com histórico — e os efeitos de desenho que a
onda 3 precificou tiveram de ser **declarados** porque não havia nenhum a observar.

Este módulo fecha isso, e o modo como fecha é o ponto. A conta agora existe **duas vezes**:

- o mundo **independente**, onde todo traço é sorteado por contato — o que as ondas 1 a 3 publicaram;
- o mundo **correlacionado**, onde cada cliente tem uma dificuldade e uma paciência próprias.

O segundo é construído a partir do **ruído idêntico**. O percentil de um contato passa pelo quantil
normal, é misturado ao percentil do seu cliente com cargas declaradas e volta pela função quantil do
próprio traço — uma cópula gaussiana, que deixa toda **distribuição marginal exatamente onde
estava** e muda apenas a dependência entre dois contatos de uma mesma pessoa. Os uniformes por trás
de cada desfecho são reaproveitados, não sorteados de novo.

Logo, o mundo independente é um **controle**, não uma linha de base. O que um estimador faz em dados
sem estrutura alguma é um fato sobre o estimador, e dois dos cinco resultados abaixo só são legíveis
contra essa linha.

```python
from svclab.bot import HUMAN_ONLY, THREE_TURNS, run
from svclab.population import (
    correlation_table,
    design_table,
    error_table,
    pair_failures,
    world_table,
)
from svclab.synth import correlated_dataset, generate_dataset

data = generate_dataset()
other = correlated_dataset(data)  # a mesma conta, com clientes que são pessoas

contacts = {"independent": data.contacts, "correlated": other.contacts}
treated = {name: run(table[~table["holdout"]], THREE_TURNS) for name, table in contacts.items()}
control = {name: run(table[table["holdout"]], HUMAN_ONLY) for name, table in contacts.items()}

world_table(contacts, treated)  # algo já publicado se moveu?
correlation_table(contacts, treated)  # declarada, latente, observada e no desfecho
design_table(treated)  # o que a parte sobrevivente custa a uma comparação
pair_failures(treated)  # a mesma pessoa falhada duas vezes
error_table(treated, control)  # três erros padrão sobre uma diferença
```

## Resultado 1: nada do que foi publicado se move

A política `three-turns` no braço tratado de cada mundo:

| | Independente | Correlacionado | Diferença |
| --- | --- | --- | --- |
| dificuldade média | 0,3340 | 0,3347 | +0,0007 |
| desvio-padrão da dificuldade | 0,1776 | 0,1782 | +0,0006 |
| turnos de paciência médios | 4,5178 | 4,5117 | −0,0061 |
| contenção de sessão | 0,6065 | 0,6046 | −0,0019 |
| contenção necessária | 0,2145 | 0,2126 | −0,0019 |
| taxa de resolução | 0,6355 | 0,6357 | +0,0002 |
| repetições por contato | 0,2099 | 0,2094 | −0,0005 |
| horas humanas | 2.730,43 | 2.728,43 | **−2,00** |

**O maior movimento relativo da tabela é 0,89%**, na `contenção necessária`, e toda cifra publicada
nas ondas 1 a 3 continua passando no seu próprio teste, inalterada. Duas horas humanas em 2.730 é o
efeito da correlação sobre a carga do mês.

Isso é uma **pré-condição, não um achado**. É o que diz que as comparações abaixo são sobre
dependência e sobre mais nada — e é a razão pela qual a cópula substituiu uma combinação convexa de
dois sorteios, que estreitaria a dispersão marginal para 54,5% da variância e deixaria toda diferença
atribuível a duas causas ao mesmo tempo. A primeira versão deste módulo fazia exatamente isso, e a
taxa de resolução se movia oito pontos por um motivo que nada tinha a ver com clientes — o defeito
está registrado em [`docs/ROADMAP.md`](../../../docs/ROADMAP.md) com as cifras que produziu.

**Uma correlação não muda o que aconteceu. Muda o que se pode concluir disso.**

## Resultado 2: correlação entre pessoas não é correlação entre desfechos

O número declarado, e quanto dele sobra em cada estágio:

| Estágio | Dificuldade | Paciência | Resolução |
| --- | --- | --- | --- |
| declarada | **0,2500** | **0,1000** | — |
| latente | 0,2535 | 0,0911 | — |
| observada no traço | 0,2463 | 0,0740 | — |
| no desfecho em que o teste roda | — | — | **0,0448** |

Três perdas, cada uma com um mecanismo:

- **Da latente à observada.** A garantia da cópula é exata na escala normal. Voltar por uma
  `Beta(2, 4)` custa um pouco; arredondar a paciência para um número inteiro de turnos custa mais, e
  é por isso que 0,1000 chega como 0,0740.
- **Do traço ao desfecho.** Esta é a grande. Uma resolução é **uma moeda cujo viés é correlacionado,
  não uma moeda correlacionada**, e a uma taxa de resolução perto de 0,64 a variância de Bernoulli é
  0,23 enquanto a parte entre clientes do viés é uma fração disso. Um quarto da dificuldade
  pertencendo à pessoa sobrevive como **4,5%** do desfecho.

A consequência prática é uma regra para quem dimensiona um teste agrupado: **estime a correlação do
desfecho que está testando, não a do traço que você acredita que o dirige.** Aqui elas diferem por um
fator de 5,6, na direção que torna a correção menor — a direção que ninguém adivinha, porque a
intuição aplicada é "clientes repetem, então meus dados devem estar profundamente agrupados".

## Resultado 3: o que a parte sobrevivente custa, contra o que a onda 3 assumiu

| Mundo | ICC | Grupo médio | Efeito de desenho | Amostra extra | α nominal | α real |
| --- | --- | --- | --- | --- | --- | --- |
| independente | −0,0126 | 1,9637 | 0,9879 | — | 0,05 | **sem resposta** |
| correlacionado | 0,0448 | 1,9637 | **1,0432** | **+4,32%** | 0,05 | **0,0550** |
| os 0,30 declarados na onda 3 | 0,3000 | 1,9637 | 1,2891 | +28,91% | 0,05 | 0,0843 |

A linha independente devolve **nenhuma taxa de erro**, e isso é a função da onda 3 funcionando como
especificada: um efeito de desenho medido abaixo de um é uma estimativa negativa de correlação, o que
não é inflação, e `actual_alpha` a recusa em vez de truncá-la em 0,05. Uma tabela que imprimisse ali
o valor nominal estaria inventando um número.

E a linha correlacionada é **sete vezes menor que o cenário que a onda 3 precificou**. No próprio
dimensionamento da onda 3, de 405 contatos por braço, o poder da comparação que ela dimensionou é:

| | Poder a 405 contatos por braço |
| --- | --- |
| contatos independentes | 0,8026 |
| no efeito de desenho **medido** | **0,7859** |
| nos 0,30 declarados da onda 3 | 0,6970 |

Então o alarme da onda 3 estava certo na **forma** e errado no **tamanho** nesta conta: a correção
são 1,7 pontos de poder, não 11. Os dois números importam, e a afirmação honesta é a que a onda 3 não
podia fazer — o efeito é real, mensurável e modesto, porque um efeito de desenho é produto de dois
fatores e os grupos desta conta têm em média **dois** contatos.

## Resultado 4: a mesma pessoa, falhada duas vezes

Clientes com exatamente dois contatos, em cada mundo, sobre ruído idêntico:

| Mundo | Pares | Taxa de falha | Falhou nos dois | Esperado se independente | Razão |
| --- | --- | --- | --- | --- | --- |
| independente | 5.234 | 0,3632 | 0,1219 | 0,1319 | 0,9240 |
| correlacionado | 5.234 | 0,3629 | **0,1406** | 0,1317 | **1,0677** |

**A taxa de resolução se moveu 0,0002 e a fração de clientes de dois contatos falhados nas duas vezes
subiu 15,4%** — 98 pessoas a mais, no mesmo volume, com o mesmo KPI agregado.

Leia as razões uma contra a outra, não contra 1,0. O 0,9240 do mundo independente é o que este
estimador faz em dados sem dependência nenhuma, então a contribuição da correlação é a **alta de
15,5% entre as linhas**, não a distância até um.

Este é o achado operacional da onda. Uma taxa de resolução é um número **ponderado por contato**, e a
experiência que gera uma reclamação, um churn ou um ofício de regulador é **ponderada por cliente**.
As duas coincidem exatamente quando um cliente é um rótulo. Quando um cliente é uma pessoa, elas se
separam — e se separam na direção que a operação sente e o painel não.

## Resultado 5: a correção que a maioria usa custa mais do que aquilo que ela corrige

Três erros padrão sobre uma diferença — a taxa de resolução do braço tratado contra a do holdout:

| Mundo | Estimativa | Ingênuo | Média por cliente | Corrigido | Razão da média | Razão do corrigido |
| --- | --- | --- | --- | --- | --- | --- |
| independente | −0,2955 | 0,003889 | 0,004406 | 0,003867 | **1,1330** | 0,9943 |
| correlacionado | −0,2956 | 0,003886 | 0,004427 | 0,003913 | **1,1392** | 1,0071 |

Leia a linha independente primeiro. **Fazer média de médias por cliente infla o erro padrão em 13,3%
num mundo sem correlação alguma.** Isso não é correção de agrupamento, é perda de eficiência vestida
de correção: agregar em grupos de tamanhos diferentes e pesá-los igualmente descarta a informação de
quantos contatos formaram cada média.

A contribuição da própria correlação, nos mesmos dados, são os **0,7%** da coluna do corrigido. Ou
seja: quem "trata o agrupamento" tirando média por cliente paga cerca de **dezenove vezes** o erro
que estava corrigindo.

O erro corrigido é menor que o da média por cliente porque multiplica o erro ingênuo pela raiz do
efeito de desenho **combinado** — combinado entre os dois braços, e o braço holdout é `human-only`,
cuja resolução fica perto de 0,93 seja qual for o cliente. Um braço quase sem variância entre
clientes reduz à metade a correção que se aplica a uma diferença. O efeito de desenho de um braço não
é o efeito de desenho de uma comparação, e essa é a última armadilha pequena de uma sequência delas.

## Premissas e limitações

- **Toda cifra aqui vem de um gerador sintético com semente**, inclusive as duas correlações
  declaradas. Nenhum dado de empregador, cliente, fornecedor ou plataforma é usado em lugar algum, e
  não existe modelo de linguagem. Ver [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **As correlações são declaradas, não ajustadas.** 0,25 na dificuldade e 0,10 na paciência foram
  escolhidas para cair dentro da faixa que a onda 3 teve de supor. Nada aqui é evidência sobre qual é
  a correlação de uma conta real; é evidência sobre o que uma correlação de dado tamanho faz, e sobre
  quanto dela sobrevive até um desfecho.
- **Uma cópula gaussiana é uma suposição forte de forma.** Dá um parâmetro por traço e nenhuma
  dependência de cauda: um cliente difícil é uniformemente mais propenso a ser difícil, em vez de
  ocasionalmente catastrófico. Chamadores frequentes reais parecem mais uma cauda pesada que uma
  média deslocada, e uma cauda pesada moveria o Resultado 4 mais do que move o Resultado 3.
- **O efeito do cliente incide só sobre dificuldade e paciência.** A *frequência* de contato ainda é
  sorteada de forma independente, então os clientes com mais contatos não são os mais difíceis. Essa
  é a próxima correção e é a que afiaria o Resultado 4, porque numa conta real as pessoas que mais
  contatam e as mais difíceis de satisfazer se sobrepõem.
- **Os grupos aqui têm em média 1,96 contatos.** Todo efeito de desenho deste módulo é limitado por
  um fator de dois só por isso. A mesma correlação num estudo randomizado por clínica, escola ou
  centro de distribuição — grupos de cinquenta — é um problema de outra ordem, e citar os números
  modestos deste módulo como tranquilizador ali seria leitura errada.
- **Ainda uma repetição só.** Um contato não resolvido volta no máximo uma vez, então "falhou duas
  vezes" é medido em dois contatos independentes de um cliente e não numa cadeia. Cadeias elevariam o
  Resultado 4.
- **O ICC do desfecho é estimado por análise de variância numa variável binária.** Esse estimador é
  conhecidamente enviesado para baixo em desfechos raros; em taxas perto de 0,64 ele se comporta bem,
  e a linha do mundo independente é a verificação de que ele não está fabricando correlação.

## Fontes

Citadas como origem de um *método*, nunca como fonte de qualquer número destas tabelas.

- Sklar, A. (1959). *Fonctions de répartition à n dimensions et leurs marges.* Publications de
  l'Institut de Statistique de l'Université de Paris 8. — que uma distribuição conjunta se separa em
  marginais e estrutura de dependência, e é por isso que aqui as marginais podem ficar fixas.
- Nelsen, R. B. (2006). *An Introduction to Copulas*, 2ª ed. Springer. — a cópula gaussiana como
  construção, e sua ausência de dependência de cauda.
- Kish, L. (1965). *Survey Sampling.* Wiley. — o efeito de desenho que a onda 3 usa e esta onda mede.
- Donner, A., Klar, N. (2000). *Design and Analysis of Cluster Randomization Trials in Health
  Research.* Arnold. — análise no nível do grupo contra no nível do indivíduo, e o custo de
  eficiência da primeira com grupos de tamanhos diferentes.
- Liang, K.-Y., Zeger, S. L. (1986). *Longitudinal Data Analysis Using Generalized Linear Models.*
  Biometrika 73. — corrigir a inferência para dependência intragrupo sem modelá-la.
- Ridout, M. S., Demétrio, C. G. B., Firth, D. (1999). *Estimating Intraclass Correlation for Binary
  Data.* Biometrics 55. — por que a correlação de um desfecho binário não é a do traço latente atrás
  dele.
