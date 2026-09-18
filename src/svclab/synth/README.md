# `svclab.synth` — a contact centre that has the columns a real one cannot

*[Português](#svclabsynth--uma-central-que-tem-as-colunas-que-uma-real-não-pode-ter)*

## The business problem

Nothing in this repository could be checked against a real contact centre, because the two questions
that decide whether an automation worked are not in any operational dataset: **how hard was each
contact, and would the customer have got there without us?**

So the centre is built rather than borrowed. Forty thousand contacts from 20,377 customers over thirty
days, every parameter written down in `config.py`, and two columns no operation has.

## The decision it enables

1. **Can a containment rate be checked at all?** Only against `would_self_serve`.
2. **Is a policy comparison a comparison?** Only if both policies meet the same contacts, which is
   why everything random is drawn here, before any bot exists.
3. **Do the published figures reproduce elsewhere?** Only if no draw samples by rejection.

## Usage

```python
from svclab.synth import CENTRE, INTENTS, generate_dataset

data = generate_dataset()
data.contacts  # one row per contact, truth columns included
data.intent_truth  # one row per intent, with the share where automation creates anything
```

## Result 1: the five reasons for contact, and the one column that matters

| Intent | Share | Contacts | Mean difficulty | Bot can resolve | Would self-serve | **Resolvable and needed** | Mean human seconds | Human resolves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rastreio | 0.34 | 13,583 | 0.3340 | 0.6493 | 0.2295 | **0.4822** | 259.34 | 0.9625 |
| prazo-de-entrega | 0.24 | 9,485 | 0.3347 | 0.5069 | 0.1414 | **0.4212** | 329.20 | 0.9467 |
| cadastro | 0.14 | 5,652 | 0.3324 | 0.5117 | 0.0826 | **0.4570** | 329.68 | 0.9321 |
| reembolso | 0.16 | 6,516 | 0.3338 | 0.1036 | 0.0124 | **0.1014** | 537.60 | 0.8958 |
| reclamacao | 0.12 | 4,764 | 0.3347 | **0.0050** | 0.0061 | **0.0048** | 713.65 | 0.8539 |

`resolvable_and_needed` is the intersection of the two middle columns: contacts a bot can resolve
**and** that would not have resolved themselves. It is the only share of the volume where automation
creates anything, and it is the column no real operation can compute. Across the account it is
**34.53%**, against **43.05%** that a bot can resolve — so a fifth of everything automatable was never
work.

Two intents carry the design. `rastreio` is mostly answerable and mostly self-serving, so a bot that
handles it earns credit for contacts that needed nobody. `reclamacao` is neither — 0.5% resolvable —
so it is the residue every automation leaves behind, at 714 seconds a contact.

## Result 2: the disciplines, and why each one is a test rather than a convention

**Everything random is drawn before any bot runs.** A bot in [`svclab.bot`](../bot/README.md) is a
deterministic function of this table, so running a policy twice gives the identical frame and two
policies differ by their policy alone. If the bot drew its own randomness, every comparison between
two policies would be confounded by noise — and the confounding would be invisible, because both runs
would look like measurements.

**Which draws a bot may read is a line with a test on it.** `difficulty`, `would_self_serve` and
`human_seconds` are truth, and `svclab.bot.policy` is parsed by a test that fails if the code reaches
any of them. The first version of that test grepped the file text and failed on the docstring
explaining the rule: prose is allowed to name a column, code is not.

**No draw samples by rejection.** Every one is an inverse transform of the uniform stream, so the
number of uniforms consumed depends only on how many values are asked for, never on the values. That
rule is a sibling repository's scar tissue: there, a generator drawing with `Generator.binomial`
published figures that held on one machine and moved on a clean install. A test reads this package's
source and fails on any draw that is not `rng.random`.

**The holdout is drawn per customer, not per contact.** The same customer comes back, and splitting
one person's contacts across the arms would let the bot's effect leak into the control. It costs a
wider interval and it is the only correct choice.

## Assumptions and limitations

- **Nothing here is a measurement of any real operation.** The intent labels, the shares, the handling
  times, the patience, the two counterfactual columns and the difficulty distribution were all chosen
  to make a particular measurement situation visible. See [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **Difficulty is one number, drawn from a declared Beta, and it drives everything.** Whether a bot
  can resolve a contact, whether a classifier labels it correctly, how long a human takes and whether
  the human succeeds are all declared linear functions of that one number. A real contact is harder
  along several axes at once, and a bot can be excellent at a hard thing and hopeless at an easy one.
- **The probabilities fall linearly with difficulty and are clipped, not logistic.** That makes the
  ceiling and the slope readable as the two numbers a stakeholder would argue about, at the cost of a
  kink where the clip bites.
- **Handling time is exponential around its mean**, which is the assumption
  [`svclab.capacity`](../capacity/README.md) is built on, so the panel and the queueing formula agree
  by construction rather than by luck. Real handling times are not exponential.
- **Arrivals are uniform across the period.** There is no hour of the day, no Monday, no peak. A
  capacity plan built on average load is the flattering version of the problem.
- **A contact has one intent and one attempt at being classified.** No multi-intent conversations, no
  re-classification mid-session.

## Sources

Cited as the origin of a *method*, never as a source of any number in these tables.

- Devroye, L. (1986). *Non-Uniform Random Variate Generation.* Springer. — inverse-transform sampling,
  and why a rejection sampler's stream consumption is not something to build on.

---

# `svclab.synth` — uma central que tem as colunas que uma real não pode ter

*[English](#svclabsynth--a-contact-centre-that-has-the-columns-a-real-one-cannot)*

## O problema de negócio

Nada neste repositório poderia ser conferido contra uma central de atendimento real, porque as duas
perguntas que decidem se uma automação funcionou não estão em nenhum dataset operacional: **quão
difícil era cada contato, e o cliente teria chegado lá sem nós?**

Então a central é construída, não emprestada. Quarenta mil contatos de 20.377 clientes em trinta dias,
todo parâmetro escrito no `config.py`, e duas colunas que nenhuma operação tem.

## A decisão que habilita

1. **Uma taxa de contenção pode ser conferida?** Só contra a `would_self_serve`.
2. **Uma comparação de políticas é uma comparação?** Só se as duas encontrarem os mesmos contatos, e é
   por isso que tudo aleatório é sorteado aqui, antes de qualquer bot existir.
3. **As cifras publicadas se reproduzem em outro lugar?** Só se nenhum sorteio amostrar por rejeição.

## Uso

```python
from svclab.synth import CENTRE, INTENTS, generate_dataset

data = generate_dataset()
data.contacts  # uma linha por contato, colunas de verdade incluídas
data.intent_truth  # uma linha por intenção, com a fração em que automação cria algo
```

## Resultado 1: as cinco razões de contato, e a única coluna que importa

| Intenção | Fração | Contatos | Dificuldade média | Bot resolve | Resolveria sozinho | **Resolvível e necessário** | Segundos humanos | Humano resolve |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rastreio | 0,34 | 13.583 | 0,3340 | 0,6493 | 0,2295 | **0,4822** | 259,34 | 0,9625 |
| prazo-de-entrega | 0,24 | 9.485 | 0,3347 | 0,5069 | 0,1414 | **0,4212** | 329,20 | 0,9467 |
| cadastro | 0,14 | 5.652 | 0,3324 | 0,5117 | 0,0826 | **0,4570** | 329,68 | 0,9321 |
| reembolso | 0,16 | 6.516 | 0,3338 | 0,1036 | 0,0124 | **0,1014** | 537,60 | 0,8958 |
| reclamacao | 0,12 | 4.764 | 0,3347 | **0,0050** | 0,0061 | **0,0048** | 713,65 | 0,8539 |

A `resolvable_and_needed` é a interseção das duas colunas do meio: contatos que um bot consegue
resolver **e** que não teriam se resolvido sozinhos. É a única fração do volume em que a automação cria
algo, e é a coluna que nenhuma operação real consegue calcular. Na conta inteira ela é **34,53%**,
contra **43,05%** que um bot consegue resolver — então um quinto de tudo o que era automatizável nunca
foi trabalho.

Duas intenções sustentam o desenho. `rastreio` é em boa parte respondível e em boa parte
autorresolvível, então um bot que a atende ganha crédito por contatos que não precisavam de ninguém.
`reclamacao` não é nem uma coisa nem outra — 0,5% resolvível — então é o resíduo que toda automação
deixa atrás, a 714 segundos por contato.

## Resultado 2: as disciplinas, e por que cada uma é um teste em vez de uma convenção

**Tudo aleatório é sorteado antes de qualquer bot rodar.** Um bot no [`svclab.bot`](../bot/README.md) é
função determinística desta tabela, então rodar uma política duas vezes dá o mesmo quadro e duas
políticas diferem apenas pela política. Se o bot sorteasse a própria aleatoriedade, toda comparação
entre duas políticas estaria confundida por ruído — e a confusão seria invisível, porque as duas
execuções pareceriam medições.

**Quais sorteios um bot pode ler é uma linha com um teste em cima.** `difficulty`, `would_self_serve` e
`human_seconds` são verdade, e o `svclab.bot.policy` é analisado por um teste que falha se o código
alcançar qualquer uma delas. A primeira versão desse teste procurava no texto do arquivo e falhou na
docstring que explicava a regra: a prosa pode nomear uma coluna, o código não.

**Nenhum sorteio amostra por rejeição.** Todos são transformada inversa do stream uniforme, então o
número de uniformes consumidos depende só de quantos valores são pedidos, nunca dos valores. Essa regra
é cicatriz de um repositório irmão: lá, um gerador que sorteava com `Generator.binomial` publicou
cifras que valiam numa máquina e mudavam numa instalação limpa. Um teste lê o código deste pacote e
falha em qualquer sorteio que não seja `rng.random`.

**O holdout é sorteado por cliente, não por contato.** O mesmo cliente volta, e dividir os contatos de
uma pessoa entre os braços deixaria o efeito do bot vazar para o controle. Custa um intervalo mais
largo e é a única escolha correta.

## Premissas e limitações

- **Nada aqui é medição de operação real alguma.** Os rótulos de intenção, as frações, os tempos de
  atendimento, a paciência, as duas colunas contrafactuais e a distribuição de dificuldade foram todos
  escolhidos para tornar visível uma situação de medição específica. Ver
  [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **Dificuldade é um número só, sorteado de uma Beta declarada, e governa tudo.** Se um bot resolve o
  contato, se um classificador o rotula certo, quanto um humano leva e se o humano tem êxito são todas
  funções lineares declaradas desse único número. Um contato real é difícil em vários eixos ao mesmo
  tempo, e um bot pode ser excelente numa coisa difícil e inútil numa fácil.
- **As probabilidades caem linearmente com a dificuldade e são truncadas, não logísticas.** Isso torna
  o teto e a inclinação legíveis como os dois números que um interlocutor discutiria, ao custo de uma
  quina onde o truncamento morde.
- **O tempo de atendimento é exponencial em torno da média**, que é a premissa sobre a qual o
  [`svclab.capacity`](../capacity/README.md) é construído, então o painel e a fórmula de fila concordam
  por construção e não por sorte. Tempos reais não são exponenciais.
- **As chegadas são uniformes no período.** Não há hora do dia, não há segunda-feira, não há pico. Um
  plano de capacidade construído sobre carga média é a versão lisonjeira do problema.
- **Um contato tem uma intenção e uma tentativa de ser classificado.** Sem conversas multi-intenção,
  sem reclassificação no meio da sessão.

## Fontes

Citadas como origem de um *método*, nunca como fonte de qualquer número destas tabelas.

- Devroye, L. (1986). *Non-Uniform Random Variate Generation.* Springer. — amostragem por transformada
  inversa, e por que o consumo de stream de um amostrador por rejeição não é algo em que se construir.
