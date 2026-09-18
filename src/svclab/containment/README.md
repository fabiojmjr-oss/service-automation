# `svclab.containment` — the containment that wasn't

*[Português](#svclabcontainment--a-contenção-que-não-era)*

## The business problem

Containment is the number every automation programme is judged on, and it is a share with a numerator
nobody agreed on. Does a session the customer abandoned count as contained? One that came back
tomorrow? One the bot answered for somebody who would have found the answer alone?

Each answer is defensible and they do not produce the same number. On this account, for one ordinary
policy, the widest defensible reading is **2.83 times** the narrowest. This module returns **all four**
rather than picking one silently.

Then the harder point, and the reason the module exists. Every one of those four is a share of what the
bot did, and none of them is what the business case claimed: **contacts a human did not have to handle
because the bot existed.** That quantity needs a control arm, and where there is none,
:func:`deflection` refuses to return a number.

## The decision it enables

1. **Which containment number are we actually being shown?** All four, side by side, with the ranking
   each one produces.
2. **How much of it reached the queue?** Measured against customers who never met the bot.
3. **And which contacts did the bot keep?** Because a bot does not take a random sample of a queue.

## Usage

```python
from svclab.bot import HUMAN_ONLY, THREE_TURNS, run
from svclab.containment import containment_table, deflection, selection_profile
from svclab.synth import generate_dataset

data = generate_dataset()
treated = data.contacts[~data.contacts["holdout"]]
held = data.contacts[data.contacts["holdout"]]

outcomes = run(treated, THREE_TURNS)
containment_table({"three-turns": outcomes}, data.contacts)  # all four definitions
selection_profile(outcomes, data.contacts)  # which contacts the bot kept

measured = deflection(outcomes, run(held, HUMAN_ONLY))
measured.deflected_per_customer  # what the queue actually stopped receiving
measured.share_of(0.6065)  # the share of the quoted containment rate that was real
deflection(outcomes, None).untested_because  # the refusal, where there is no control arm
```

## Result 1: four definitions, four numbers, one ranking

The treated arm: 31,802 contacts from 16,195 customers.

| Policy | Sessions | Repeats per contact | Session | Resolution | Repeat-adjusted | Needed | Resolution rate | Human hours |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| human-only | 33,190 | 0.0436 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | **0.9305** | 3,645.64 |
| three-turns | 38,476 | 0.2099 | 0.6065 | 0.2749 | 0.4190 | 0.2145 | 0.6355 | 2,730.43 |
| patient | 42,015 | 0.3211 | **0.8169** | **0.2792** | **0.5059** | **0.2187** | 0.4476 | 2,316.78 |
| guarded | 36,287 | 0.1410 | 0.4886 | 0.2630 | 0.3809 | 0.2029 | 0.7271 | 2,861.54 |

- **Session containment**: the session did not reach a human. The number on the slide, and the only
  one that counts an abandoned customer as a success.
- **Resolution containment**: the bot resolved it. Abandonment is no longer a win.
- **Repeat-adjusted containment**: it did not reach a human *and* the customer did not come back. A
  contained contact that returns within the window was a deferred contact.
- **Needed containment**: the bot resolved it *and* the customer would not have got there alone.
  Requires the counterfactual column, so it is `nan` for every real operation, permanently.

For `three-turns` the four readings are **0.6065, 0.2749, 0.4190 and 0.2145** — the widest is 2.83
times the narrowest, and every one of them is a correct calculation.

**And now read the rows.** Ranked by session containment, the best policy is `patient`. Ranked by
resolution containment: `patient`. By repeat-adjusted containment: `patient`. By needed containment,
the strictest definition in the table: `patient`. Ranked by **resolution rate**, the best policy is
`guarded`.

`patient` contains 0.8169 and resolves 0.4476. `guarded` contains 0.4886 and resolves 0.7271.

So the answer is not to pick a stricter containment definition. **No definition of containment can
rank these policies**, because containment is a statement about what the bot did and resolution is a
statement about what happened to the customer. A tighter numerator does not convert one into the
other.

## Result 2: the bot takes the easy end, and the residue is 1.58 times harder

`three-turns`, by the truth the bot cannot see:

| Group | Contacts | Share | Mean difficulty | Would self-serve | Mean human seconds |
| --- | --- | --- | --- | --- | --- |
| resolved-by-bot | 8,743 | 0.2749 | **0.2383** | **0.2198** | 263.21 |
| abandoned | 10,544 | 0.3316 | 0.3656 | 0.1041 | 410.19 |
| reached-a-human | 12,515 | 0.3935 | **0.3758** | 0.0802 | **451.90** |
| came-back | 6,674 | 0.2099 | 0.3767 | 0.0000 | 467.28 |
| all-contacts | 31,802 | 1.0000 | 0.3346 | 0.1265 | 386.20 |

The residue that reaches a human is **1.58 times harder** than what the bot resolved, and it carries
452 seconds of handling against 386 for the average contact before the bot existed. Volume fell 39%
and the mean cost of what remains rose **17%**. [`svclab.capacity`](../capacity/README.md) prices what
that does to a headcount plan.

**And 21.98% of what the bot resolved would have resolved itself.** That is the self-service
counterfactual, and it is why `needed_containment` exists: a fifth of the bot's wins were contacts
that needed nobody. Nobody who came back would have managed alone — that column reads exactly 0.0000
by construction, which is the session's rule showing up in the measurement that reports it.

## Result 3: what the queue actually received, against what was claimed

Measured per **customer**, because the arms were assigned per customer: 4,182 control customers
against 16,195 treated ones. The control arm receives 2.0428 human contacts per customer.

| Policy | Treated | Quoted containment | Deflection per customer | 95% interval | Per contact | Share of the claim that was real |
| --- | --- | --- | --- | --- | --- | --- |
| three-turns | 1.1849 | 0.6065 | 0.8579 | 0.8201 to 0.8958 | 0.4377 | **0.7216** |
| patient | 0.9902 | **0.8169** | 1.0526 | 1.0153 to 1.0900 | 0.5370 | **0.6573** |
| guarded | 1.2813 | 0.4886 | 0.7615 | 0.7234 to 0.7997 | 0.3885 | **0.7952** |

**The more a policy contains, the more it overstates.** `patient` quoted 0.8169 and delivered 0.5370
per contact: a third of the claim was not there. `guarded`, which contains least, is the most honest
of the three.

The gap is the repeat stream, and it is not subtle: `patient` turned 31,802 contacts into **42,015
sessions**. The automation that contained the most **raised total conversations by 26.6%**.

And where there is no control arm — which is every real deployment that did not build one — the
module says so rather than reporting:

> there is no arm to compare against, so what the bot removed from the queue is not a quantity this
> data contains

## Assumptions and limitations

- **Every number here comes from a seeded synthetic generator**, including the self-service
  counterfactual the strictest containment definition is built on. No employer, client, vendor or
  platform data is used anywhere. See [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **The four containment rates are computed over first sessions, and the hours over all sessions.**
  A repeat was never a containment opportunity — it arrives routed to a human — but the queue
  receives it. That difference of denominator is the whole argument, and mixing the two is the
  easiest way to make the argument disappear.
- **The control arm is fully human-handled and its queue is never short-staffed.** A real control arm
  would have its own waits and its own abandonment before an agent answered, which would make the
  measured deflection larger. The figures here are therefore conservative about the bot's benefit in
  one direction and, through the single-repeat cap, conservative about its cost in the other.
- **The arms are randomised by customer, and the analysis is per customer to match.** Using the
  contact as the unit would treat one person's four contacts as four independent observations and
  report an interval narrower than the design earned. The price of doing it correctly is a wider
  interval, and it is the right price.
- **`share_of` compares a per-customer deflection with a per-contact containment rate** by dividing
  through the control arm's contacts per customer. That is a like-for-like conversion only while the
  two arms have the same contacts per customer, which is true here by construction and would need
  checking anywhere else.
- **Nothing here measures customer satisfaction, cost per resolution in money, or anything the bot
  might be worth beyond queue relief.** A bot that answers at three in the morning has a value this
  module cannot see, and the honest statement is that it is not in these tables rather than that it
  does not exist.

## Sources

Cited as the origin of a *method*, never as a source of any number in these tables.

- Welch, B. L. (1947). *The Generalization of Student's Problem when Several Different Population
  Variances are Involved.* Biometrika 34. — the unequal-variance comparison behind the deflection
  interval.
- Donner, A., Klar, N. (2000). *Design and Analysis of Cluster Randomization Trials in Health
  Research.* Arnold. — why the unit of randomisation has to be the unit of analysis.
- Gans, N., Koole, G., Mandelbaum, A. (2003). *Telephone Call Centers: Tutorial, Review, and Research
  Prospects.* Manufacturing & Service Operations Management 5(2). — repeat contacts and resolution as
  distinct quantities.

---

# `svclab.containment` — a contenção que não era

*[English](#svclabcontainment--the-containment-that-wasnt)*

## O problema de negócio

Contenção é o número pelo qual todo programa de automação é julgado, e é uma fração com um numerador
que ninguém combinou. Uma sessão que o cliente abandonou conta como contida? Uma que voltou amanhã?
Uma que o bot respondeu para alguém que teria achado a resposta sozinho?

Cada resposta é defensável e elas não produzem o mesmo número. Nesta conta, para uma política comum, a
leitura defensável mais ampla é **2,83 vezes** a mais estreita. Este módulo devolve **todas as quatro**
em vez de escolher uma em silêncio.

E então o ponto mais difícil, que é a razão de o módulo existir. Cada uma dessas quatro é uma fração do
que o bot fez, e nenhuma delas é o que o business case afirmou: **contatos que um humano não precisou
atender porque o bot existia.** Essa quantidade exige um braço de controle, e onde não há um, a
`deflection` se recusa a devolver um número.

## A decisão que habilita

1. **Qual número de contenção estão nos mostrando?** Todos os quatro, lado a lado, com o ranking que
   cada um produz.
2. **Quanto disso chegou à fila?** Medido contra clientes que nunca encontraram o bot.
3. **E quais contatos o bot ficou?** Porque um bot não tira uma amostra aleatória de uma fila.

## Uso

```python
from svclab.bot import HUMAN_ONLY, THREE_TURNS, run
from svclab.containment import containment_table, deflection, selection_profile
from svclab.synth import generate_dataset

data = generate_dataset()
treated = data.contacts[~data.contacts["holdout"]]
held = data.contacts[data.contacts["holdout"]]

outcomes = run(treated, THREE_TURNS)
containment_table({"three-turns": outcomes}, data.contacts)  # as quatro definições
selection_profile(outcomes, data.contacts)  # quais contatos o bot ficou

measured = deflection(outcomes, run(held, HUMAN_ONLY))
measured.deflected_per_customer  # o que a fila realmente deixou de receber
measured.share_of(0.6065)  # a fração da contenção citada que era real
deflection(outcomes, None).untested_because  # a recusa, onde não há braço de controle
```

## Resultado 1: quatro definições, quatro números, um ranking

O braço tratado: 31.802 contatos de 16.195 clientes.

| Política | Sessões | Recontatos por contato | Sessão | Resolução | Ajustada por recontato | Necessária | Taxa de resolução | Horas humanas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| human-only | 33.190 | 0,0436 | 0,0000 | 0,0000 | 0,0000 | 0,0000 | **0,9305** | 3.645,64 |
| three-turns | 38.476 | 0,2099 | 0,6065 | 0,2749 | 0,4190 | 0,2145 | 0,6355 | 2.730,43 |
| patient | 42.015 | 0,3211 | **0,8169** | **0,2792** | **0,5059** | **0,2187** | 0,4476 | 2.316,78 |
| guarded | 36.287 | 0,1410 | 0,4886 | 0,2630 | 0,3809 | 0,2029 | 0,7271 | 2.861,54 |

- **Contenção de sessão**: a sessão não chegou a um humano. O número do slide, e o único que conta um
  cliente abandonado como sucesso.
- **Contenção por resolução**: o bot resolveu. Abandono deixa de ser vitória.
- **Contenção ajustada por recontato**: não chegou a um humano *e* o cliente não voltou. Um contato
  contido que retorna dentro da janela era um contato postergado.
- **Contenção necessária**: o bot resolveu *e* o cliente não teria chegado lá sozinho. Exige a coluna
  contrafactual, então é `nan` para toda operação real, permanentemente.

Para o `three-turns` as quatro leituras são **0,6065, 0,2749, 0,4190 e 0,2145** — a mais ampla é 2,83
vezes a mais estreita, e todas são cálculos corretos.

**E agora leia as linhas.** Ranqueado por contenção de sessão, a melhor política é `patient`. Por
contenção por resolução: `patient`. Por contenção ajustada por recontato: `patient`. Por contenção
necessária, a definição mais estrita da tabela: `patient`. Ranqueado por **taxa de resolução**, a
melhor política é `guarded`.

O `patient` contém 0,8169 e resolve 0,4476. O `guarded` contém 0,4886 e resolve 0,7271.

Então a resposta não é escolher uma definição mais estrita de contenção. **Nenhuma definição de
contenção consegue ranquear estas políticas**, porque contenção é uma afirmação sobre o que o bot fez e
resolução é uma afirmação sobre o que aconteceu com o cliente. Um numerador mais apertado não converte
uma na outra.

## Resultado 2: o bot fica com a ponta fácil, e o resíduo é 1,58 vez mais difícil

`three-turns`, pela verdade que o bot não vê:

| Grupo | Contatos | Fração | Dificuldade média | Resolveria sozinho | Segundos humanos médios |
| --- | --- | --- | --- | --- | --- |
| resolved-by-bot | 8.743 | 0,2749 | **0,2383** | **0,2198** | 263,21 |
| abandoned | 10.544 | 0,3316 | 0,3656 | 0,1041 | 410,19 |
| reached-a-human | 12.515 | 0,3935 | **0,3758** | 0,0802 | **451,90** |
| came-back | 6.674 | 0,2099 | 0,3767 | 0,0000 | 467,28 |
| all-contacts | 31.802 | 1,0000 | 0,3346 | 0,1265 | 386,20 |

O resíduo que chega a um humano é **1,58 vez mais difícil** do que o que o bot resolveu, e carrega 452
segundos de atendimento contra 386 do contato médio antes de o bot existir. O volume caiu 39% e o
custo médio do que sobrou subiu **17%**. O [`svclab.capacity`](../capacity/README.md) precifica o que
isso faz com um plano de headcount.

**E 21,98% do que o bot resolveu teria se resolvido sozinho.** Esse é o contrafactual de
autoatendimento, e é por isso que a `needed_containment` existe: um quinto das vitórias do bot eram
contatos que não precisavam de ninguém. Ninguém que voltou teria resolvido sozinho — aquela coluna lê
exatamente 0,0000 por construção, que é a regra da sessão aparecendo na medição que a reporta.

## Resultado 3: o que a fila recebeu, contra o que foi afirmado

Medido por **cliente**, porque os braços foram atribuídos por cliente: 4.182 clientes de controle
contra 16.195 tratados. O braço de controle recebe 2,0428 contatos humanos por cliente.

| Política | Tratado | Contenção citada | Desvio por cliente | Intervalo de 95% | Por contato | Fração da afirmação que era real |
| --- | --- | --- | --- | --- | --- | --- |
| three-turns | 1,1849 | 0,6065 | 0,8579 | 0,8201 a 0,8958 | 0,4377 | **0,7216** |
| patient | 0,9902 | **0,8169** | 1,0526 | 1,0153 a 1,0900 | 0,5370 | **0,6573** |
| guarded | 1,2813 | 0,4886 | 0,7615 | 0,7234 a 0,7997 | 0,3885 | **0,7952** |

**Quanto mais uma política contém, mais ela superestima.** O `patient` citou 0,8169 e entregou 0,5370
por contato: um terço da afirmação não estava lá. O `guarded`, que contém menos, é o mais honesto dos
três.

A diferença é o fluxo de recontatos, e não é subtil: o `patient` transformou 31.802 contatos em
**42.015 sessões**. A automação que conteve mais **elevou o total de conversas em 26,6%**.

E onde não há braço de controle — que é toda implantação real que não construiu um — o módulo diz isso
em vez de reportar:

> there is no arm to compare against, so what the bot removed from the queue is not a quantity this
> data contains

## Premissas e limitações

- **Todo número aqui vem de um gerador sintético com semente**, inclusive o contrafactual de
  autoatendimento sobre o qual a definição mais estrita de contenção é construída. Nenhum dado de
  empregador, cliente, fornecedor ou plataforma é usado em qualquer parte. Ver
  [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **As quatro taxas de contenção são calculadas sobre primeiras sessões, e as horas sobre todas as
  sessões.** Um recontato nunca foi oportunidade de contenção — ele chega roteado a um humano — mas a
  fila o recebe. Essa diferença de denominador é o argumento inteiro, e misturar os dois é a forma
  mais fácil de fazer o argumento desaparecer.
- **O braço de controle é inteiramente atendido por humanos e sua fila nunca está subdimensionada.**
  Um braço de controle real teria as próprias esperas e o próprio abandono antes de um atendente
  responder, o que aumentaria o desvio medido. As cifras aqui são portanto conservadoras sobre o
  benefício do bot numa direção e, pelo limite de um único recontato, conservadoras sobre seu custo na
  outra.
- **Os braços são randomizados por cliente, e a análise é por cliente para acompanhar.** Usar o
  contato como unidade trataria os quatro contatos de uma pessoa como quatro observações independentes
  e reportaria um intervalo mais estreito do que o desenho comprou. O preço de fazer certo é um
  intervalo mais largo, e é o preço correto.
- **A `share_of` compara um desvio por cliente com uma taxa de contenção por contato** dividindo pelos
  contatos por cliente do braço de controle. Isso é uma conversão equivalente apenas enquanto os dois
  braços tiverem os mesmos contatos por cliente, o que é verdade aqui por construção e precisaria ser
  verificado em qualquer outro lugar.
- **Nada aqui mede satisfação do cliente, custo por resolução em dinheiro, ou qualquer coisa que o bot
  possa valer além de alívio de fila.** Um bot que responde às três da manhã tem um valor que este
  módulo não vê, e a afirmação honesta é que ele não está nestas tabelas, não que ele não exista.

## Fontes

Citadas como origem de um *método*, nunca como fonte de qualquer número destas tabelas.

- Welch, B. L. (1947). *The Generalization of Student's Problem when Several Different Population
  Variances are Involved.* Biometrika 34. — a comparação com variâncias desiguais por trás do
  intervalo de desvio.
- Donner, A., Klar, N. (2000). *Design and Analysis of Cluster Randomization Trials in Health
  Research.* Arnold. — por que a unidade de randomização tem de ser a unidade de análise.
- Gans, N., Koole, G., Mandelbaum, A. (2003). *Telephone Call Centers: Tutorial, Review, and Research
  Prospects.* Manufacturing & Service Operations Management 5(2). — recontatos e resolução como
  quantidades distintas.
