# `svclab.routing` — the threshold nobody priced

*[Português](#svclabrouting--o-limiar-que-ninguém-precificou)*

## The business problem

A routing classifier reports a label and a confidence in it. Somewhere there is a number below which
the contact should go straight to a human instead of to the bot, and that number is almost always
chosen by maximising accuracy — or by somebody saying "let us start at eighty per cent".

**Accuracy is the wrong objective, because the two mistakes do not cost the same.** Handing the bot a
complaint it has read as a tracking question costs nine minutes of a human's day and a customer who
has explained a problem to a machine answering about parcels. Deferring a tracking question the bot
would have answered costs twenty seconds of queue entry. A threshold that treats those as
interchangeable is optimising a quantity nobody pays.

## The decision it enables

1. **Where should the bot stop trying?** Priced in seconds, which is what the operation pays, rather
   than in accuracy, which is what the classifier reports.
2. **One threshold, or one per intent?** Because the cost of a mistake differs between intents by a
   factor of nine.
3. **And can the closed form be used?** It can, on a calibrated score. Result 3 is what happens when
   it is used on one that is not.

## Usage

```python
from svclab.bot import THREE_TURNS
from svclab.routing import best_by, calibrated_threshold, cost_curve, cost_of, defer_below
from svclab.synth import generate_dataset

data = generate_dataset()
treated = data.contacts[~data.contacts["holdout"]]

curve = cost_curve(treated, data.routing_scores, THREE_TURNS, (0.4, 0.45, 0.5, 0.55))
best_by(curve, "label_accuracy", largest=True)  # the objective usually tuned on
best_by(curve, "seconds_per_contact", largest=False)  # the one that is paid

calibrated_threshold(20.0, 540.0)  # 0.9630 - correct, for a calibrated score
routed = defer_below(treated, data.routing_scores, {"reclamacao": 0.62, "rastreio": 0.10})
```

## Result 1: the score ranks correctness, and is not a probability

A contact is labelled correctly when its classifier draw falls under the accuracy its intent and
difficulty imply, so the distance between those two is how comfortably the label was reached. The
score is that **margin**, rescaled and blurred by a declared spread.

It works as a ranker: on the treated arm the mean score is **0.6975** where the label is right and
**0.4293** where it is wrong, against an overall label accuracy of **0.7771**. It is not calibrated:
above a cut of 0.7 the share correct is **0.9907**, not 0.7, so the number is informative about
correctness without being equal to the probability of it. That distinction has no effect on Results 1 and 2 and is the whole of
Result 3.

## Result 2: the two objectives do not have their optimum in the same place

31,802 contacts, the `three-turns` policy behind the router, thresholds swept at 0.01:

| | Threshold | Seconds per contact |
| --- | --- | --- |
| Accuracy-maximising | **0.45** | 346.4851 |
| Cost-minimising | **0.48** | **345.6345** |

Tuning on accuracy lands three hundredths high and costs **0.8506 seconds per contact** — **7.51 human
hours over the month**, on this queue, from one number chosen against the wrong objective. The
magnitude is modest and the direction is the point: accuracy has no units, and the thing being traded
does.

The curve is also worth reading for its shape. At a threshold of zero the bot tries everything: 7,090
misroutes and 1,812,030 seconds of misroute penalty. At 0.95 it tries almost nothing: no misroutes at
all, and 600,720 seconds of deferral plus every contact handled by a human. Both ends are worse than
the middle, which is what a cost curve looks like when both mistakes are real.

## Result 3: one threshold per intent beats the best single number

Swept per intent rather than assumed, against the closed form for comparison:

| Intent | Misroute cost | Cost-optimal threshold | Closed form |
| --- | --- | --- | --- |
| rastreio | 60s | **0.10** | 0.6667 |
| prazo-de-entrega | 90s | **0.28** | 0.7778 |
| cadastro | 150s | **0.38** | 0.8667 |
| reembolso | 420s | **0.60** | 0.9524 |
| reclamacao | 540s | **0.62** | 0.9630 |

| Rule | Seconds per contact | Resolution | Misroutes | Deferred |
| --- | --- | --- | --- | --- |
| one threshold at 0.48 | 345.6345 | 0.7067 | 2,472 | 7,036 |
| **per intent, swept** | **334.0793** | 0.6925 | 3,754 | 5,525 |
| per intent, closed form | **388.8874** | **0.8611** | 58 | 23,304 |

**Sweeping a threshold per intent saves 11.5552 seconds per contact** against the best single number —
**102.1 human hours over the month**. A single threshold is a compromise between five intents that
wanted very different answers, and the compromise is payable.

**And the closed form, applied to this score, is 12.5% worse than the single threshold it was meant to
improve on.** It is not a wrong formula. On a score that *is* the probability the label is right, the
optimum is exactly to defer below `1 − defer_cost / misroute_cost`, and this module computes it. The
score here is a margin, so the formula's **levels** are far too high — it defers 23,304 of 31,802
contacts to avoid 2,414 misroutes.

What survives is its **ranking**. The closed form orders the five intents by caution in exactly the
order the swept optima do. The formula knows which intents deserve more care and cannot know how much,
because the input it needs is a probability and nobody produced one. Calibration looked like the
missing step, and **it is not the whole of it**: wave 9 gave the formula the probability this generator
actually uses and it was still 7.33% worse than sweeping, because the formula treats a *correct* label
as free. See [`svclab.calibration`](../calibration/README.md).

The last row is not simply a mistake, either. It resolves **0.8611** against the swept rule's 0.6925,
because deferring to a human resolves. It buys 17 points of resolution for 54.8 seconds a contact, and
whether that is a good trade is a decision rather than an optimisation — which is the honest end of
this document.

## Assumptions and limitations

- **Every number here comes from a seeded synthetic generator**, including the misroute costs the
  whole argument turns on. No employer, client, vendor or platform data is used anywhere, and there is
  no language model. See [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **The misroute cost is a declared number of human seconds per intent.** A real misroute costs a
  customer's patience, a complaint that escalates and sometimes a churn, none of which are seconds.
  Everything here is therefore an underestimate, and the ranking it produces would only sharpen if the
  other costs were added.
- **A deferral costs twenty seconds plus the human handling that would have happened anyway.** No
  model of the customer preferring a human, or of the queue lengthening because of the deferrals - the
  second of those is [`svclab.capacity`](../capacity/README.md)'s subject and it is not wired into this
  cost curve.
- **The score is the generator's margin, blurred once.** A real classifier's confidence is
  miscalibrated in ways that vary by intent and drift with the model version, and a threshold chosen
  on last quarter's calibration is a different threshold today.
- **Per-intent thresholds are keyed on the true intent here**, which a deployment cannot do: the rule
  has to fire on the predicted label. Keying it on the prediction is strictly harder and the direction
  of the result does not change, because the classifier is right 78% of the time - but the size of the
  gain would shrink.
- **The thresholds are swept on the same data they are then priced on.** That is in-sample selection,
  and the honest version holds out a period to choose on. Wave 3 does not, and the saving quoted for
  the swept rule is therefore an upper bound on what a deployment would get.

## Sources

Cited as the origin of a *method*, never as a source of any number in these tables.

- Elkan, C. (2001). *The Foundations of Cost-Sensitive Learning.* IJCAI. — the closed-form threshold
  on a calibrated probability, and why it is a statement about probabilities rather than about scores.
- Zadrozny, B., Elkan, C. (2001). *Obtaining Calibrated Probability Estimates from Decision Trees and
  Naive Bayesian Classifiers.* ICML. — the calibration step Result 3 is missing.
- Provost, F., Fawcett, T. (2001). *Robust Classification for Imprecise Environments.* Machine
  Learning 42. — choosing an operating point when the costs are what vary.

---

# `svclab.routing` — o limiar que ninguém precificou

*[English](#svclabrouting--the-threshold-nobody-priced)*

## O problema de negócio

Um classificador de roteamento reporta um rótulo e uma confiança nele. Em algum lugar existe um número
abaixo do qual o contato deveria ir direto para um humano em vez de para o bot, e esse número é quase
sempre escolhido maximizando acurácia — ou por alguém dizendo "vamos começar em oitenta por cento".

**Acurácia é o objetivo errado, porque os dois erros não custam o mesmo.** Entregar ao bot uma
reclamação que ele leu como pergunta de rastreio custa nove minutos do dia de um humano e um cliente
que explicou um problema a uma máquina respondendo sobre encomendas. Postergar uma pergunta de rastreio
que o bot teria respondido custa vinte segundos de entrada de fila. Um limiar que trata as duas como
intercambiáveis está otimizando uma quantidade que ninguém paga.

## A decisão que habilita

1. **Onde o bot deve parar de tentar?** Precificado em segundos, que é o que a operação paga, e não em
   acurácia, que é o que o classificador reporta.
2. **Um limiar, ou um por intenção?** Porque o custo de um erro difere entre intenções por um fator de
   nove.
3. **E a forma fechada pode ser usada?** Pode, sobre um score calibrado. O Resultado 3 é o que
   acontece quando ela é usada sobre um que não é.

## Uso

```python
from svclab.bot import THREE_TURNS
from svclab.routing import best_by, calibrated_threshold, cost_curve, cost_of, defer_below
from svclab.synth import generate_dataset

data = generate_dataset()
treated = data.contacts[~data.contacts["holdout"]]

curve = cost_curve(treated, data.routing_scores, THREE_TURNS, (0.4, 0.45, 0.5, 0.55))
best_by(curve, "label_accuracy", largest=True)  # o objetivo em que normalmente se ajusta
best_by(curve, "seconds_per_contact", largest=False)  # o que é pago

calibrated_threshold(20.0, 540.0)  # 0,9630 - correto, para um score calibrado
routed = defer_below(treated, data.routing_scores, {"reclamacao": 0.62, "rastreio": 0.10})
```

## Resultado 1: o score ordena correção, e não é uma probabilidade

Um contato é rotulado corretamente quando seu sorteio de classificador cai abaixo da acurácia que sua
intenção e dificuldade implicam, então a distância entre os dois é o quão confortavelmente o rótulo foi
alcançado. O score é essa **margem**, reescalada e embaçada por uma dispersão declarada.

Como ordenador, funciona: no braço tratado o score médio é **0,6975** onde o rótulo está certo e
**0,4293** onde está errado, contra uma acurácia geral de rótulo de **0,7771**. Não é calibrado: acima
de um corte de 0,7 a fração correta é **0,9907**, não 0,7, então o número é informativo sobre correção
sem ser igual à probabilidade dela. Essa distinção não afeta os Resultados 1 e 2 e é todo o Resultado 3.

## Resultado 2: os dois objetivos não têm o ótimo no mesmo lugar

31.802 contatos, a política `three-turns` atrás do roteador, limiares varridos a 0,01:

| | Limiar | Segundos por contato |
| --- | --- | --- |
| Máxima acurácia | **0,45** | 346,4851 |
| Mínimo custo | **0,48** | **345,6345** |

Ajustar por acurácia erra três centésimos para cima e custa **0,8506 segundo por contato** — **7,51
horas humanas no mês**, nesta fila, por um número escolhido contra o objetivo errado. A magnitude é
modesta e a direção é o ponto: acurácia não tem unidade, e o que está sendo trocado tem.

A curva também vale pela forma. No limiar zero o bot tenta tudo: 7.090 roteamentos errados e 1.812.030
segundos de penalidade. Em 0,95 ele quase não tenta: nenhum roteamento errado, e 600.720 segundos de
postergação mais todo contato atendido por humano. Os dois extremos são piores que o meio, que é a
forma de uma curva de custo quando os dois erros são reais.

## Resultado 3: um limiar por intenção ganha do melhor número único

Varrido por intenção em vez de suposto, contra a forma fechada para comparação:

| Intenção | Custo do erro | Limiar de mínimo custo | Forma fechada |
| --- | --- | --- | --- |
| rastreio | 60s | **0,10** | 0,6667 |
| prazo-de-entrega | 90s | **0,28** | 0,7778 |
| cadastro | 150s | **0,38** | 0,8667 |
| reembolso | 420s | **0,60** | 0,9524 |
| reclamacao | 540s | **0,62** | 0,9630 |

| Regra | Segundos por contato | Resolução | Erros de rota | Postergados |
| --- | --- | --- | --- | --- |
| um limiar em 0,48 | 345,6345 | 0,7067 | 2.472 | 7.036 |
| **por intenção, varrido** | **334,0793** | 0,6925 | 3.754 | 5.525 |
| por intenção, forma fechada | **388,8874** | **0,8611** | 58 | 23.304 |

**Varrer um limiar por intenção economiza 11,5552 segundos por contato** contra o melhor número único —
**102,1 horas humanas no mês**. Um limiar único é um acordo entre cinco intenções que queriam respostas
muito diferentes, e o acordo é pagável.

**E a forma fechada, aplicada a este score, é 12,5% pior que o limiar único que deveria melhorar.** Não
é uma fórmula errada. Sobre um score que *é* a probabilidade de o rótulo estar certo, o ótimo é
exatamente postergar abaixo de `1 − custo_de_postergar / custo_do_erro`, e este módulo o calcula. O
score aqui é uma margem, então os **níveis** da fórmula são altos demais — ela posterga 23.304 de
31.802 contatos para evitar 2.414 erros de rota.

O que sobrevive é seu **ordenamento**. A forma fechada ordena as cinco intenções por cautela exatamente
na ordem em que os ótimos varridos o fazem. A fórmula sabe quais intenções merecem mais cuidado e não
consegue saber quanto, porque a entrada de que ela precisa é uma probabilidade e ninguém produziu uma.
Calibração parecia ser o passo que faltava, e **não é o todo dele**: a onda 9 deu à fórmula a
probabilidade que este gerador realmente usa e ela seguiu 7,33% pior que varrer, porque a fórmula trata
um rótulo *correto* como gratuito. Ver [`svclab.calibration`](../calibration/README.md).

A última linha também não é simplesmente um erro. Ela resolve **0,8611** contra os 0,6925 da regra
varrida, porque postergar para um humano resolve. Compra 17 pontos de resolução por 54,8 segundos por
contato, e se essa é uma boa troca é uma decisão em vez de uma otimização — que é o fim honesto deste
documento.

## Premissas e limitações

- **Todo número aqui vem de um gerador sintético com semente**, inclusive os custos de erro de rota em
  que todo o argumento se apoia. Nenhum dado de empregador, cliente, fornecedor ou plataforma é usado
  em qualquer parte, e não existe modelo de linguagem. Ver [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **O custo de um erro de rota é um número declarado de segundos humanos por intenção.** Um erro real
  custa a paciência de um cliente, uma reclamação que escala e às vezes um cancelamento, nada disso em
  segundos. Tudo aqui é portanto subestimativa, e o ordenamento que produz só ficaria mais nítido se os
  outros custos entrassem.
- **Uma postergação custa vinte segundos mais o atendimento humano que aconteceria de todo modo.** Sem
  modelo de o cliente preferir um humano, nem de a fila alongar por causa das postergações — o segundo
  é assunto do [`svclab.capacity`](../capacity/README.md) e não está ligado a esta curva de custo.
- **O score é a margem do gerador, embaçada uma vez.** A confiança de um classificador real é
  descalibrada de formas que variam por intenção e derivam com a versão do modelo, e um limiar escolhido
  na calibração do trimestre passado é um limiar diferente hoje.
- **Os limiares por intenção são chaveados na intenção verdadeira aqui**, o que uma implantação não
  consegue fazer: a regra tem de disparar no rótulo previsto. Chavear na previsão é estritamente mais
  difícil e a direção do resultado não muda, porque o classificador acerta 78% das vezes — mas o tamanho
  do ganho encolheria.
- **Os limiares são varridos nos mesmos dados em que depois são precificados.** Isso é seleção dentro da
  amostra, e a versão honesta separa um período para escolher. A onda 3 não faz isso, e a economia
  citada para a regra varrida é portanto um limite superior do que uma implantação obteria.

## Fontes

Citadas como origem de um *método*, nunca como fonte de qualquer número destas tabelas.

- Elkan, C. (2001). *The Foundations of Cost-Sensitive Learning.* IJCAI. — o limiar em forma fechada
  sobre uma probabilidade calibrada, e por que ele é uma afirmação sobre probabilidades e não sobre
  scores.
- Zadrozny, B., Elkan, C. (2001). *Obtaining Calibrated Probability Estimates from Decision Trees and
  Naive Bayesian Classifiers.* ICML. — o passo de calibração que falta no Resultado 3.
- Provost, F., Fawcett, T. (2001). *Robust Classification for Imprecise Environments.* Machine
  Learning 42. — escolher um ponto de operação quando o que varia são os custos.
