# `svclab.chain` — the contact that came back twice

*[Português](#svclabchain--o-contato-que-voltou-duas-vezes)*

Waves 1 to 5 allowed an unresolved contact **one** return. Every one of them named that as the reason
its figures were an underestimate — wave 1 wrote that a containment rate becomes a permanent queue
through the geometric tail, and then truncated the tail at one term. This module runs the chain: up to
four attempts, a customer 15% less likely to come back each time, and a human 15% more likely to
resolve it each time.

The default chain is still one return, so **every figure the earlier waves published is unmoved** —
`run(contacts, policy)` and `run(contacts, policy, chain=SINGLE_RETURN)` produce the identical frame,
asserted by hash rather than by tolerance, and the 45 claims tests pass unchanged.

Two things came out of the chain, pointing in opposite directions.

```python
from svclab.bot import POLICIES, THREE_TURNS, run
from svclab.chain import attempt_table, chain_table, reopen_rate, tail_table, time_table
from svclab.synth import CHAIN, generate_dataset

data = generate_dataset()
treated = data.contacts[~data.contacts["holdout"]]
single = {policy.name: run(treated, policy) for policy in POLICIES}
chained = {
    policy.name: run(treated, policy, chain=CHAIN, draws=data.return_draws) for policy in POLICIES
}

attempt_table(chained["three-turns"], len(treated))  # what each attempt held
chain_table(single, chained)  # what the chain costs each policy
tail_table((0.05, 0.2, 0.5, 0.7))  # what truncating at one return costs, in closed form
time_table(chained)  # the third ranking, and the one nobody reports
```

## Result 1: the chain is real, and it is short

The `three-turns` policy on the treated arm, one row per attempt:

| Attempt | Sessions | Resolved | Resolution rate | Cumulative | Human hours |
| --- | --- | --- | --- | --- | --- |
| 1 | 31,802 | 20,210 | 0.6355 | 0.6355 | 1,762.19 |
| 2 | 6,674 | 5,444 | 0.8157 | 0.8067 | 968.24 |
| 3 | 720 | 705 | **0.9792** | 0.8288 | 131.95 |
| 4 | 7 | 7 | 1.0000 | 0.8291 | 1.18 |

**720 contacts need a third attempt and seven need a fourth.** The chain adds 727 sessions and 4.88%
to the month's human hours, and it lifts eventual resolution from 0.8067 to 0.8291 — 2.24 points that
waves 1 to 5 were not counting.

That is a smaller tail than wave 1 expected when it warned about one, and the reason is not modest at
all.

## Result 2: because a tail needs an operation that keeps failing

A contact reopens only when **both** things happen: the customer comes back *and* the human failed
again. So the sessions one unresolved contact generates are a geometric series in

> `r = P(return) × P(human does not resolve)`

and at this centre's declared curves `r = 0.6174 × 0.0695 = 0.0429`. The series is **1.0448** sessions
per unresolved contact, however many attempts are allowed. There is no tail to find.

| Reopen rate | Two attempts | Four attempts | Unbounded | What truncating at two costs |
| --- | --- | --- | --- | --- |
| **0.0429** *(here)* | 1.0429 | 1.0448 | 1.0448 | **0.18%** |
| 0.05 | 1.0500 | 1.0526 | 1.0526 | 0.25% |
| 0.10 | 1.1000 | 1.1110 | 1.1111 | 1.01% |
| 0.20 | 1.2000 | 1.2480 | 1.2500 | 4.17% |
| 0.30 | 1.3000 | 1.4170 | 1.4286 | 9.89% |
| 0.50 | 1.5000 | 1.8750 | 2.0000 | **33.33%** |
| 0.70 | 1.7000 | 2.5330 | 3.3333 | **96.08%** |

Read the last column as the price of wave 1's truncation at each possible operation. Here it is
**0.18%** — the truncation was almost free, and five waves of figures are therefore very nearly right
about the queue. At a reopen rate of 0.5 it would have been **a third**, and at 0.7 the single-return
model would report half the sessions that actually happen.

**So the geometric tail is not a property of customers who return. It is a property of an operation
that keeps failing them.** A centre where humans resolve 93% of what reaches them has no tail whatever
its repeat rate; a centre where they resolve 70% has one that doubles its own workload. That is a
sharper statement than wave 1's warning, and it is the one an operation can act on: the lever is
first-contact resolution by the human, not the return rate of the customer.

A note on consistency with wave 3. Its repeat feedback solved `load = base × (1 + repeat × abandon)`
by iterating to a fixed point, and iterating that map **is** summing the geometric series — so wave 3
was not truncating anything, and the chain confirms its algebra by simulation rather than correcting
it. The truncation was in the **session runtime**, not in the queue model.

## Result 3: and the chain punishes the policy containment rewarded

| Policy | Sessions | Per contact | First attempt | Eventual | Human hours | Extra sessions | Extra hours |
| --- | --- | --- | --- | --- | --- | --- | --- |
| human-only | 33,989 | 1.0688 | 0.9305 | 0.9552 | 3,786.22 | 799 | **+3.86%** |
| guarded | 37,025 | 1.1642 | 0.7271 | 0.8515 | 2,996.57 | 738 | +4.72% |
| three-turns | 39,203 | 1.2327 | 0.6355 | 0.8291 | 2,863.56 | 727 | +4.88% |
| patient | 42,741 | 1.3440 | 0.4476 | 0.7526 | 2,449.82 | 726 | **+5.74%** |

The extra hours rise with containment, and the ordering is not a coincidence: a policy that contains
more leaves more contacts unresolved, and an unresolved contact is the only thing a chain can act on.
`patient` pays 1.5 times what `human-only` pays for the same chain.

## Result 4: the third ranking, and the one nobody reports

| Policy | Containment | Eventual resolution | Hours to resolution | Days | Resolved after attempt 1 | After attempt 2 |
| --- | --- | --- | --- | --- | --- | --- |
| human-only | 0.0000 | **0.9552** | 3.73 | **0.1555** | 0.0258 | 0.0258 |
| guarded | 0.4886 | 0.8515 | 12.46 | 0.5193 | 0.1461 | 0.0267 |
| three-turns | 0.6065 | 0.8291 | 18.77 | 0.7823 | 0.2335 | 0.0270 |
| patient | **0.8169** | 0.7526 | 31.34 | **1.3057** | **0.4052** | 0.0297 |

**Days to resolution is monotone in containment, and it is the steepest of the three rankings.**
`patient` takes **8.4 times** as long as `human-only` to resolve a contact and **2.5 times** as long
as `guarded`, and **40.5% of the contacts it eventually resolves are resolved on a later attempt** —
against 2.6% for the human queue.

So the repository now has three rankings of the same four policies:

| Ranked best first by | Order |
| --- | --- |
| containment | patient, three-turns, guarded, human-only |
| resolution | human-only, guarded, three-turns, patient |
| **days to resolution** | human-only, guarded, three-turns, patient |

Containment is the exact reverse of both of the others. Wave 1 said no definition of containment can
rank resolution; wave 6 adds that resolution itself is not the whole of what the customer experiences,
because a problem fixed after two returns and three days was fixed **and** the customer waited. A rate
has no time in it. **Three days is not a rounding error on a KPI: it is the complaint.**

## Assumptions and limitations

- **Every number here comes from a seeded synthetic generator**, including the chain's three declared
  parameters. No employer, client, vendor or platform data is used anywhere, and there is no language
  model. See [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **The chain is cut at four attempts by a parameter, and reality has no such parameter.** Every
  figure in Results 1, 3 and 4 is therefore a lower bound on a world where the tail runs to its end.
  Result 2 is the closed form that says how much that matters, which is why it exists.
- **The lift compounds and clips at one**, so a long enough chain here always terminates: by the
  fourth attempt a `reclamacao` at middling difficulty is resolved with probability 1.0576, clipped.
  An operation whose escalation path does not actually improve has no such guarantee, and that is the
  case this model cannot represent.
- **Every return lands exactly one repeat window later.** Real returns arrive on a distribution, some
  the same afternoon and some in three weeks, and the days-to-resolution column would gain a spread it
  does not have here. The ordering would survive; the levels are a grid.
- **A return goes straight to a human, always.** No second bot attempt, no "we see you contacted us
  about this" routing, and no escalation queue with a different handling time. All three exist and all
  three would change Result 3 rather than Result 4.
- **The second attempt reuses the first attempt's human draw**, so a human who failed once fails again
  on that attempt by construction. It is what keeps the two-attempt world identical to the published
  one, and it makes the second attempt's resolution rate a property of who was still open rather than
  a fresh trial.
- **Nothing here models the customer giving up on the company** instead of giving up on the contact.
  A chain that ends because somebody churned looks identical to one that ends because somebody was
  helped, and the difference is the only one the business cares about.

## Sources

Cited as the origin of a *method*, never as a source of any number in these tables.

- Feller, W. (1968). *An Introduction to Probability Theory and Its Applications*, vol. 1, 3rd ed.
  Wiley. — the geometric series and the expected number of trials it counts.
- Ross, S. M. (2014). *Introduction to Probability Models*, 11th ed. Academic Press. — renewal
  arguments for a request that reappears until it is served.
- Kendall, D. G. (1953). *Stochastic Processes Occurring in the Theory of Queues.* Annals of
  Mathematical Statistics 24. — the queue-discipline vocabulary the repeat stream is described in.
- Little, J. D. C. (1961). *A Proof for the Queuing Formula L = λW.* Operations Research 9. — that
  time in system is a quantity in its own right, which is Result 4's whole point.

---

# `svclab.chain` — o contato que voltou duas vezes

*[English](#svclabchain--the-contact-that-came-back-twice)*

As ondas 1 a 5 permitiam **um** retorno a um contato não resolvido. Todas elas apontaram isso como a
razão de suas cifras serem subestimativas — a onda 1 escreveu que uma taxa de contenção se torna uma
fila permanente pela cauda geométrica, e então truncou a cauda em um termo. Este módulo roda a cadeia:
até quatro tentativas, um cliente 15% menos propenso a voltar a cada vez e um humano 15% mais propenso
a resolver a cada vez.

A cadeia padrão continua sendo um retorno, então **toda cifra publicada pelas ondas anteriores está
intacta** — `run(contacts, policy)` e `run(contacts, policy, chain=SINGLE_RETURN)` produzem o frame
idêntico, verificado por hash e não por tolerância, e os 45 testes de cifras passam inalterados.

Duas coisas saíram da cadeia, apontando em direções opostas.

```python
from svclab.bot import POLICIES, THREE_TURNS, run
from svclab.chain import attempt_table, chain_table, reopen_rate, tail_table, time_table
from svclab.synth import CHAIN, generate_dataset

data = generate_dataset()
treated = data.contacts[~data.contacts["holdout"]]
single = {policy.name: run(treated, policy) for policy in POLICIES}
chained = {
    policy.name: run(treated, policy, chain=CHAIN, draws=data.return_draws) for policy in POLICIES
}

attempt_table(chained["three-turns"], len(treated))  # o que cada tentativa continha
chain_table(single, chained)  # o que a cadeia custa a cada política
tail_table((0.05, 0.2, 0.5, 0.7))  # o custo de truncar em um retorno, em forma fechada
time_table(chained)  # o terceiro ranking, e o que ninguém reporta
```

## Resultado 1: a cadeia é real, e é curta

A política `three-turns` no braço tratado, uma linha por tentativa:

| Tentativa | Sessões | Resolvidas | Taxa de resolução | Acumulada | Horas humanas |
| --- | --- | --- | --- | --- | --- |
| 1 | 31.802 | 20.210 | 0,6355 | 0,6355 | 1.762,19 |
| 2 | 6.674 | 5.444 | 0,8157 | 0,8067 | 968,24 |
| 3 | 720 | 705 | **0,9792** | 0,8288 | 131,95 |
| 4 | 7 | 7 | 1,0000 | 0,8291 | 1,18 |

**720 contatos precisam de uma terceira tentativa e sete de uma quarta.** A cadeia acrescenta 727
sessões e 4,88% às horas humanas do mês, e leva a resolução eventual de 0,8067 para 0,8291 — 2,24
pontos que as ondas 1 a 5 não contavam.

É uma cauda menor do que a onda 1 esperava ao alertar sobre ela, e a razão não é nada modesta.

## Resultado 2: porque uma cauda exige uma operação que segue falhando

Um contato reabre só quando **as duas** coisas acontecem: o cliente volta *e* o humano falhou de novo.
Então as sessões que um contato não resolvido gera são uma série geométrica em

> `r = P(volta) × P(humano não resolve)`

e nas curvas declaradas desta central `r = 0,6174 × 0,0695 = 0,0429`. A série dá **1,0448** sessões por
contato não resolvido, por mais tentativas que se permitam. Não existe cauda a encontrar.

| Taxa de reabertura | Duas tentativas | Quatro tentativas | Ilimitado | O custo de truncar em duas |
| --- | --- | --- | --- | --- |
| **0,0429** *(aqui)* | 1,0429 | 1,0448 | 1,0448 | **0,18%** |
| 0,05 | 1,0500 | 1,0526 | 1,0526 | 0,25% |
| 0,10 | 1,1000 | 1,1110 | 1,1111 | 1,01% |
| 0,20 | 1,2000 | 1,2480 | 1,2500 | 4,17% |
| 0,30 | 1,3000 | 1,4170 | 1,4286 | 9,89% |
| 0,50 | 1,5000 | 1,8750 | 2,0000 | **33,33%** |
| 0,70 | 1,7000 | 2,5330 | 3,3333 | **96,08%** |

Leia a última coluna como o preço do truncamento da onda 1 em cada operação possível. Aqui é **0,18%**
— o truncamento foi praticamente gratuito, e cinco ondas de cifras estão portanto quase exatamente
certas sobre a fila. A uma taxa de reabertura de 0,5 teria sido **um terço**, e a 0,7 o modelo de
retorno único reportaria metade das sessões que de fato acontecem.

**Então a cauda geométrica não é propriedade de clientes que voltam. É propriedade de uma operação que
segue falhando com eles.** Uma central em que humanos resolvem 93% do que lhes chega não tem cauda
nenhuma, qualquer que seja a taxa de recontato; uma em que resolvem 70% tem uma cauda que dobra o
próprio trabalho. É uma afirmação mais afiada que o alerta da onda 1, e é a que uma operação pode
acionar: a alavanca é a resolução no primeiro contato pelo humano, não a taxa de retorno do cliente.

Uma nota de consistência com a onda 3. A realimentação de recontatos dela resolvia
`carga = base × (1 + recontato × abandono)` iterando até um ponto fixo, e iterar esse mapa **é** somar
a série geométrica — então a onda 3 não truncava nada, e a cadeia confirma sua álgebra por simulação em
vez de corrigi-la. O truncamento estava no **runtime de sessão**, não no modelo de fila.

## Resultado 3: e a cadeia pune a política que a contenção premiava

| Política | Sessões | Por contato | 1ª tentativa | Eventual | Horas humanas | Sessões extra | Horas extra |
| --- | --- | --- | --- | --- | --- | --- | --- |
| human-only | 33.989 | 1,0688 | 0,9305 | 0,9552 | 3.786,22 | 799 | **+3,86%** |
| guarded | 37.025 | 1,1642 | 0,7271 | 0,8515 | 2.996,57 | 738 | +4,72% |
| three-turns | 39.203 | 1,2327 | 0,6355 | 0,8291 | 2.863,56 | 727 | +4,88% |
| patient | 42.741 | 1,3440 | 0,4476 | 0,7526 | 2.449,82 | 726 | **+5,74%** |

As horas extra crescem com a contenção, e a ordenação não é coincidência: uma política que contém mais
deixa mais contatos não resolvidos, e um contato não resolvido é a única coisa sobre a qual uma cadeia
pode agir. `patient` paga 1,5 vez o que `human-only` paga pela mesma cadeia.

## Resultado 4: o terceiro ranking, e o que ninguém reporta

| Política | Contenção | Resolução eventual | Horas até resolver | Dias | Resolvidos após a 1ª | Após a 2ª |
| --- | --- | --- | --- | --- | --- | --- |
| human-only | 0,0000 | **0,9552** | 3,73 | **0,1555** | 0,0258 | 0,0258 |
| guarded | 0,4886 | 0,8515 | 12,46 | 0,5193 | 0,1461 | 0,0267 |
| three-turns | 0,6065 | 0,8291 | 18,77 | 0,7823 | 0,2335 | 0,0270 |
| patient | **0,8169** | 0,7526 | 31,34 | **1,3057** | **0,4052** | 0,0297 |

**Dias até resolver é monótono na contenção, e é o mais inclinado dos três rankings.** `patient` leva
**8,4 vezes** o tempo de `human-only` para resolver um contato e **2,5 vezes** o de `guarded`, e
**40,5% dos contatos que ela eventualmente resolve são resolvidos numa tentativa posterior** — contra
2,6% na fila humana.

Então o repositório tem agora três rankings das mesmas quatro políticas:

| Ordenado do melhor por | Ordem |
| --- | --- |
| contenção | patient, three-turns, guarded, human-only |
| resolução | human-only, guarded, three-turns, patient |
| **dias até resolver** | human-only, guarded, three-turns, patient |

A contenção é o inverso exato dos outros dois. A onda 1 dizia que nenhuma definição de contenção pode
ordenar resolução; a onda 6 acrescenta que a resolução em si não é tudo o que o cliente experimenta,
porque um problema resolvido depois de dois retornos e três dias foi resolvido **e** o cliente esperou.
Uma taxa não tem tempo dentro. **Três dias não são erro de arredondamento num KPI: são a reclamação.**

## Premissas e limitações

- **Toda cifra aqui vem de um gerador sintético com semente**, inclusive os três parâmetros declarados
  da cadeia. Nenhum dado de empregador, cliente, fornecedor ou plataforma é usado em lugar algum, e não
  existe modelo de linguagem. Ver [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **A cadeia é cortada em quatro tentativas por um parâmetro, e a realidade não tem esse parâmetro.**
  Toda cifra dos Resultados 1, 3 e 4 é portanto um piso em relação a um mundo onde a cauda corre até o
  fim. O Resultado 2 é a forma fechada que diz quanto isso importa, e é por isso que ele existe.
- **O ganho por tentativa é composto e truncado em um**, então uma cadeia longa aqui sempre termina: na
  quarta tentativa uma `reclamacao` de dificuldade média é resolvida com probabilidade 1,0576,
  truncada. Uma operação cujo caminho de escalonamento não melhora de fato não tem essa garantia — e é
  o caso que este modelo não representa.
- **Todo retorno cai exatamente uma janela de recontato depois.** Retornos reais chegam numa
  distribuição, alguns na mesma tarde e outros em três semanas, e a coluna de dias até resolver ganharia
  uma dispersão que não tem aqui. A ordenação sobreviveria; os níveis são uma grade.
- **Um retorno vai direto a um humano, sempre.** Sem segunda tentativa do bot, sem roteamento do tipo
  "vimos que você já falou com a gente sobre isso" e sem fila de escalonamento com outro tempo de
  atendimento. Os três existem e os três mudariam o Resultado 3, não o 4.
- **A segunda tentativa reaproveita o sorteio humano da primeira**, então um humano que falhou uma vez
  falha de novo naquela tentativa por construção. É o que mantém o mundo de duas tentativas idêntico ao
  publicado, e faz da taxa de resolução da segunda tentativa uma propriedade de quem ainda estava
  aberto, não um ensaio novo.
- **Nada aqui modela o cliente desistindo da empresa** em vez de desistir do contato. Uma cadeia que
  termina porque alguém foi embora é idêntica a uma que termina porque alguém foi atendido, e a
  diferença é a única que interessa ao negócio.

## Fontes

Citadas como origem de um *método*, nunca como fonte de qualquer número destas tabelas.

- Feller, W. (1968). *An Introduction to Probability Theory and Its Applications*, vol. 1, 3ª ed.
  Wiley. — a série geométrica e o número esperado de tentativas que ela conta.
- Ross, S. M. (2014). *Introduction to Probability Models*, 11ª ed. Academic Press. — argumentos de
  renovação para uma demanda que reaparece até ser atendida.
- Kendall, D. G. (1953). *Stochastic Processes Occurring in the Theory of Queues.* Annals of
  Mathematical Statistics 24. — o vocabulário de disciplina de fila em que o fluxo de recontatos é
  descrito.
- Little, J. D. C. (1961). *A Proof for the Queuing Formula L = λW.* Operations Research 9. — que tempo
  no sistema é uma quantidade por si, o que é todo o ponto do Resultado 4.
