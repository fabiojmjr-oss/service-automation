# `svclab.experiment` — the test that counted strangers

*[Português](#svclabexperiment--o-teste-que-contou-estranhos)*

## The business problem

Waves 1 and 2 compared two bot policies on the whole account. A real deployment tests one policy
against another on a fraction of the volume, and the fraction has to be sized. The arithmetic for that
is in every textbook, applied to independent observations.

**Contacts are not independent, because customers come back.** One person's two contacts share
everything about that person — how patient they are, how hard their problems tend to be, whether they
are the sort to abandon a chat. They carry less information than two contacts from two people, and a
test randomised by customer but analysed by contact is counting each customer's contacts as if they
were strangers.

The correction is one number, and its consequence is not the one people expect. A test that ignores
its clustering does not merely lose power. **It runs at the wrong error rate**, and the rate is
computable.

## The decision it enables

1. **How many contacts does this comparison need?** Which is the textbook answer multiplied by the
   design effect.
2. **What error rate is the test I already ran actually running at?** Which is a single formula and is
   usually the first time anybody has seen it.
3. **And does this account's clustering cost anything?** Which is a question with a measurable answer,
   and on this generator the answer is no — for a reason worth stating plainly.

## Usage

```python
from svclab.experiment import (
    actual_alpha,
    contacts_for_difference,
    design_effect,
    intracluster_correlation,
    sizing_table,
)

design_effect(1.9637, 0.30)  # 1.2891
actual_alpha(0.05, 1.2891)  # 0.0843 - what a nominal five per cent really is
contacts_for_difference(0.7271, 0.6355, effect=1.2891)  # 522.55 per arm

intracluster_correlation(first_sessions, cluster="customer", outcome="resolved_num")
```

## Result 1: the design effect, and the three corners that pin it

With clusters averaging `m` observations and an intra-cluster correlation `rho`, every variance in the
comparison is inflated by

> **design effect = 1 + (m − 1) · rho**

Three corners fix it without computing anything, and all three are asserted in the tests: it is **one**
when the clusters hold a single observation each, **one** when the correlation inside them is zero, and
**equal to the cluster size** when the correlation is total — which is the honest statement that a
cluster of identical observations is one observation.

The correlation estimator is pinned the same way. Two clusters whose members are identical return
**exactly 1**; two clusters constructed so that every cluster has the same mean and all the variation
sits inside it return **exactly −1**, which is a real thing a sample can do and is reported rather than
clipped to zero.

## Result 2: this account's clustering costs nothing, and that is a fact about the generator

The treated arm: 31,802 contacts from 16,195 customers, **1.9637 contacts per customer**.

| Outcome | Intra-cluster correlation | Design effect |
| --- | --- | --- |
| resolved | **−0.012563** | 0.9879 |
| reached a human | **+0.000876** | 1.0008 |

**Approximately zero, and that is not a discovery about contact centres.** This generator draws
difficulty, patience, self-service and every other trait **per contact**, so a customer is a label
rather than a person. The estimator returning zero here is therefore a **check on the estimator** —
exactly what it should return on data with no cluster structure — and a limitation of the generator,
which the roadmap carries as the first job of the next wave.

Publishing it that way round is deliberate. The alternative was to report a design effect of 1.00 as a
finding, which would have presented a modelling shortcut of mine as a property of the world.

## Result 3: what the clustering costs at the correlations a real account has

Detecting the difference wave 1 found — `guarded` resolves **0.7271** against `three-turns`' **0.6355**,
a gap of 0.0916 — at 80% power and a nominal 5%:

| Scenario | Design effect | Contacts per arm | Customers per arm | Nominal alpha | **Actual alpha** |
| --- | --- | --- | --- | --- | --- |
| independent contacts | 1.0000 | **405.36** | 206.43 | 0.05 | **0.0500** |
| correlation 0.05 | 1.0482 | 424.89 | 216.37 | 0.05 | 0.0556 |
| correlation 0.10 | 1.0964 | 444.42 | 226.32 | 0.05 | 0.0612 |
| correlation 0.20 | 1.1927 | 483.48 | 246.21 | 0.05 | 0.0727 |
| correlation 0.30 | 1.2891 | **522.55** | 266.10 | 0.05 | **0.0843** |
| total correlation | 1.9637 | 795.99 | 405.36 | 0.05 | **0.1619** |

Read the last column before the others. **A test that believes it is running at five per cent, on
clusters of two with a correlation of 0.30, is really running at 8.43%** — the statistic was divided by
a standard error too small by the square root of the design effect, so the critical value it was
compared against was that much closer to zero. At total correlation it is **16.19%**: one result in six
is a false positive on a test that reported one in twenty.

And the sample cost, which is the part that gets budgeted: at a correlation of 0.30 the test needs
**28.9% more contacts** than the textbook says. With clusters averaging two, the ceiling on the damage
is a factor of two — which is the reassuring half of a small cluster size, and the reason this
correction is a rounding error in a contact centre and a catastrophe in a study randomised by clinic or
by school.

## Assumptions and limitations

- **Every number here comes from a seeded synthetic generator.** No employer, client, vendor or
  platform data is used anywhere, and there is no language model. See
  [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **The generator has no customer-level effects at all**, which Result 2 states rather than hides. Every
  trait is drawn per contact, so the measured correlation is zero by construction. Adding a persistent
  per-customer difficulty and patience is the right fix and would move every figure waves 1 and 2
  published, which is why it is a wave of its own rather than a patch.
- **The sizing is the normal approximation to a two-proportion test, multiplied by the design effect.**
  It ignores the continuity correction and assumes equal arms, both of which are the standard
  simplifications and both of which make it slightly optimistic.
- **The design effect assumes clusters of equal size.** The estimator handles unequal sizes through the
  analysis-of-variance correction, and the effect itself uses the mean - which is the usual practice and
  understates the inflation when the sizes vary a lot.
- **Nothing here estimates the correlation from a pilot.** The scenarios are assumed, which is what a
  design has to do before the data exists; the honest version quotes the sample size across a range and
  says which end it was budgeted at.
- **And the correction is for the analysis, not a substitute for it.** A test that clusters by customer
  should be *analysed* by customer, or with a robust variance, rather than sized up and then analysed
  naively. The design effect is what to do when the analysis cannot be changed.

## Sources

Cited as the origin of a *method*, never as a source of any number in these tables.

- Kish, L. (1965). *Survey Sampling.* Wiley. — the design effect, and the sense in which a clustered
  sample of n is a smaller sample.
- Donner, A., Klar, N. (2000). *Design and Analysis of Cluster Randomization Trials in Health
  Research.* Arnold. — why the unit of randomisation has to be the unit of analysis, and the
  analysis-of-variance estimator for unequal clusters.
- Fleiss, J. L., Levin, B., Paik, M. C. (2003). *Statistical Methods for Rates and Proportions*, 3rd
  ed. — the two-proportion sample size this module inflates.

---

# `svclab.experiment` — o teste que contou estranhos

*[English](#svclabexperiment--the-test-that-counted-strangers)*

## O problema de negócio

As ondas 1 e 2 compararam duas políticas de bot na conta inteira. Uma implantação real testa uma
política contra outra numa fração do volume, e a fração tem de ser dimensionada. A aritmética disso
está em todo livro-texto, aplicada a observações independentes.

**Contatos não são independentes, porque clientes voltam.** Os dois contatos de uma pessoa compartilham
tudo sobre essa pessoa — o quão paciente ela é, o quão difíceis tendem a ser seus problemas, se ela é do
tipo que abandona um chat. Eles carregam menos informação que dois contatos de duas pessoas, e um teste
randomizado por cliente mas analisado por contato está contando os contatos de cada cliente como se
fossem estranhos.

A correção é um número, e sua consequência não é a que se espera. Um teste que ignora seu agrupamento
não apenas perde poder. **Ele roda na taxa de erro errada**, e a taxa é calculável.

## A decisão que habilita

1. **Quantos contatos esta comparação precisa?** Que é a resposta do livro-texto multiplicada pelo
   efeito de desenho.
2. **Em que taxa de erro o teste que eu já rodei está de fato rodando?** Que é uma fórmula só e
   normalmente é a primeira vez que alguém a vê.
3. **E o agrupamento desta conta custa algo?** Que é uma pergunta com resposta mensurável, e neste
   gerador a resposta é não — por um motivo que vale dizer com clareza.

## Uso

```python
from svclab.experiment import (
    actual_alpha,
    contacts_for_difference,
    design_effect,
    intracluster_correlation,
    sizing_table,
)

design_effect(1.9637, 0.30)  # 1,2891
actual_alpha(0.05, 1.2891)  # 0,0843 - o que cinco por cento nominais realmente são
contacts_for_difference(0.7271, 0.6355, effect=1.2891)  # 522,55 por braço

intracluster_correlation(primeiras_sessoes, cluster="customer", outcome="resolved_num")
```

## Resultado 1: o efeito de desenho, e os três cantos que o fixam

Com grupos de em média `m` observações e correlação intragrupo `rho`, toda variância da comparação é
inflada por

> **efeito de desenho = 1 + (m − 1) · rho**

Três cantos o fixam sem calcular nada, e os três estão asseridos nos testes: ele é **um** quando os
grupos têm uma observação cada, **um** quando a correlação dentro deles é zero, e **igual ao tamanho do
grupo** quando a correlação é total — que é a afirmação honesta de que um grupo de observações idênticas
é uma observação.

O estimador da correlação é fixado do mesmo jeito. Dois grupos cujos membros são idênticos devolvem
**exatamente 1**; dois grupos construídos para que todo grupo tenha a mesma média e toda a variação
fique dentro dele devolvem **exatamente −1**, que é algo real que uma amostra pode fazer e é reportado
em vez de truncado em zero.

## Resultado 2: o agrupamento desta conta não custa nada, e isso é um fato sobre o gerador

O braço tratado: 31.802 contatos de 16.195 clientes, **1,9637 contato por cliente**.

| Desfecho | Correlação intragrupo | Efeito de desenho |
| --- | --- | --- |
| resolvido | **−0,012563** | 0,9879 |
| chegou a um humano | **+0,000876** | 1,0008 |

**Aproximadamente zero, e isso não é uma descoberta sobre centrais de atendimento.** Este gerador
sorteia dificuldade, paciência, autoatendimento e todo outro traço **por contato**, então um cliente é
um rótulo e não uma pessoa. O estimador devolver zero aqui é portanto uma **verificação do estimador** —
exatamente o que ele deve devolver em dados sem estrutura de grupo — e uma limitação do gerador, que o
roadmap carrega como a primeira tarefa da próxima onda.

Publicar nessa ordem é deliberado. A alternativa era reportar um efeito de desenho de 1,00 como achado,
o que apresentaria um atalho de modelagem meu como propriedade do mundo.

## Resultado 3: o que o agrupamento custa nas correlações que uma conta real tem

Detectar a diferença que a onda 1 achou — o `guarded` resolve **0,7271** contra os **0,6355** do
`three-turns`, gap de 0,0916 — com 80% de poder e 5% nominais:

| Cenário | Efeito de desenho | Contatos por braço | Clientes por braço | Alfa nominal | **Alfa real** |
| --- | --- | --- | --- | --- | --- |
| contatos independentes | 1,0000 | **405,36** | 206,43 | 0,05 | **0,0500** |
| correlação 0,05 | 1,0482 | 424,89 | 216,37 | 0,05 | 0,0556 |
| correlação 0,10 | 1,0964 | 444,42 | 226,32 | 0,05 | 0,0612 |
| correlação 0,20 | 1,1927 | 483,48 | 246,21 | 0,05 | 0,0727 |
| correlação 0,30 | 1,2891 | **522,55** | 266,10 | 0,05 | **0,0843** |
| correlação total | 1,9637 | 795,99 | 405,36 | 0,05 | **0,1619** |

Leia a última coluna antes das outras. **Um teste que acredita estar rodando a cinco por cento, em
grupos de dois com correlação de 0,30, está de fato rodando a 8,43%** — a estatística foi dividida por um
erro-padrão pequeno demais pela raiz do efeito de desenho, então o valor crítico contra o qual foi
comparada estava mais perto de zero nessa proporção. Na correlação total é **16,19%**: um resultado em
seis é falso positivo num teste que reportou um em vinte.

E o custo em amostra, que é a parte que entra no orçamento: com correlação de 0,30 o teste precisa de
**28,9% mais contatos** do que o livro-texto diz. Com grupos de em média dois, o teto do dano é um fator
de dois — que é a metade tranquilizadora de um grupo pequeno, e a razão pela qual esta correção é um erro
de arredondamento numa central de atendimento e uma catástrofe num estudo randomizado por clínica ou por
escola.

## Premissas e limitações

- **Todo número aqui vem de um gerador sintético com semente.** Nenhum dado de empregador, cliente,
  fornecedor ou plataforma é usado em qualquer parte, e não existe modelo de linguagem. Ver
  [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **O gerador não tem efeito algum de nível de cliente**, o que o Resultado 2 declara em vez de
  esconder. Todo traço é sorteado por contato, então a correlação medida é zero por construção.
  Acrescentar dificuldade e paciência persistentes por cliente é a correção certa e moveria toda cifra
  publicada nas ondas 1 e 2, e é por isso que é uma onda inteira e não um remendo.
- **O dimensionamento é a aproximação normal ao teste de duas proporções, multiplicada pelo efeito de
  desenho.** Ignora a correção de continuidade e supõe braços iguais, ambas simplificações padrão e
  ambas ligeiramente otimistas.
- **O efeito de desenho supõe grupos de tamanho igual.** O estimador lida com tamanhos desiguais pela
  correção da análise de variância, e o efeito em si usa a média — que é a prática usual e subestima a
  inflação quando os tamanhos variam muito.
- **Nada aqui estima a correlação a partir de um piloto.** Os cenários são supostos, que é o que um
  desenho tem de fazer antes de os dados existirem; a versão honesta cita o tamanho de amostra numa
  faixa e diz em que ponta o orçamento foi feito.
- **E a correção é para a análise, não substituto dela.** Um teste que agrupa por cliente deveria ser
  *analisado* por cliente, ou com variância robusta, em vez de ser dimensionado para cima e analisado
  ingenuamente. O efeito de desenho é o que fazer quando a análise não pode ser mudada.

## Fontes

Citadas como origem de um *método*, nunca como fonte de qualquer número destas tabelas.

- Kish, L. (1965). *Survey Sampling.* Wiley. — o efeito de desenho, e o sentido em que uma amostra
  agrupada de n é uma amostra menor.
- Donner, A., Klar, N. (2000). *Design and Analysis of Cluster Randomization Trials in Health
  Research.* Arnold. — por que a unidade de randomização tem de ser a unidade de análise, e o estimador
  por análise de variância para grupos desiguais.
- Fleiss, J. L., Levin, B., Paik, M. C. (2003). *Statistical Methods for Rates and Proportions*, 3ª ed.
  — o tamanho de amostra de duas proporções que este módulo infla.
