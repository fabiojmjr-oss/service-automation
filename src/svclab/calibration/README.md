# `svclab.calibration` — the formula was not wrong, and calibration was not the missing step

*[Português](#svclabcalibration--a-fórmula-não-estava-errada-e-calibração-não-era-o-passo-que-faltava)*

Wave 3 applied the textbook routing threshold — defer below `1 − defer_cost / misroute_cost` — to this
account's classifier score, found it **12.5% worse** than the single swept number, and published a
diagnosis: the formula is a correct answer about a *probability*, the score is a *margin*, and
**calibration is the missing step**.

That diagnosis was an assertion. It had no control case behind it, and this module is what it takes to
test it: a map from the score to a probability, a way to see whether the map worked, and — the part that
decides the wave — **the probability the generator actually used**, on which the formula must be exactly
optimal if the diagnosis was right.

It is not. And two more decisions wave 3 took by default are priced here at the same time: the
thresholds were swept and priced on the same contacts, and the per-intent rule was keyed on the intent
the contact **actually was**, which no router can read.

```python
from svclab.bot import classifier_labels
from svclab.calibration import formula_table, key_table, optimism_table, resolve_benefit
from svclab.synth import generate_dataset

data = generate_dataset()
month = data.contacts[~data.contacts["holdout"]]
month = month.merge(
    classifier_labels(month)[["contact", "predicted_intent"]], on="contact", how="left"
)

formula_table(month, data.routing_scores)  # the closed form against the sweep, on four scores
optimism_table(month, data.routing_scores)  # what a fitted threshold costs in a period it never saw
key_table(month, data.routing_scores)  # the true label against the one a router can read
```

## Result 1: calibration is real, and it is not the missing step

Fitted on the first three fifths of the month, judged on the remaining **12,709** contacts:

| Score | Calibration error | Naive formula | **Amended formula** | Swept optimum | Naive penalty | Amended penalty |
| --- | --- | --- | --- | --- | --- | --- |
| raw margin | 0.1618 | 392.7469 | **342.1386** | 335.5655 | **17.04%** | **1.96%** |
| isotonic | 0.0066 | 351.5371 | 336.2623 | 335.6177 | 4.74% | 0.19% |
| Platt | 0.0123 | 351.6284 | 336.5567 | 335.5214 | 4.80% | 0.31% |
| **true probability** | 0.0061 | 367.5370 | 344.2607 | 342.4383 | **7.33%** | 0.53% |

Seconds per contact. The naive formula is wave 3's; the amended one is below.

Wave 3 was right about the input. The raw score's calibration error is **26.68 times** the control's,
and calibrating it cuts the formula's penalty by **3.59 times**, from 17.04% to 4.74%. The score really
does not mean what the formula assumes: in the bin where it says **0.6502**, **0.9078** of the labels are
right — a gap of **0.2576** in a single bin, on 2,333 contacts.

**But on the perfectly calibrated probability the penalty is still 7.33%.** There is no calibration left
to do there, by construction, so whatever is wrong is not calibration. The control is what makes that
visible and wave 3 had no control.

## Result 2: what was missing was a term, and it is the reason the bot exists

The closed form prices two outcomes. Attempting a **wrong** label costs `misroute_seconds`; deferring
costs `defer_seconds`; and attempting a **right** label costs nothing. That last one is not a
simplification, it is the omission of the entire case for deploying a bot: a correctly labelled contact
the bot resolves **saves** the human seconds it would otherwise have taken.

Carry the term and the comparison becomes `(1 − p)·misroute − p·benefit` against `defer`, so

> defer below `(misroute − defer) / (misroute + benefit)`

which is the original formula exactly when the benefit is zero — asserted as algebra, not as a
resemblance. The benefit is **measured**, not assumed: run the fitting period with the bot attempting
everything and with it attempting nothing, and take the difference on the contacts whose label was right.

| Intent | Misroute cost | **Benefit** | Naive threshold | **Amended** |
| --- | --- | --- | --- | --- |
| rastreio | 60.0 | **142.68** | 0.6667 | **0.1974** |
| prazo-de-entrega | 90.0 | 139.11 | 0.7778 | 0.3055 |
| cadastro | 150.0 | **161.79** | 0.8667 | 0.4170 |
| reembolso | 420.0 | 65.58 | 0.9524 | 0.8238 |
| reclamacao | 540.0 | **23.32** | 0.9630 | 0.9231 |

The benefit runs the **opposite way** to the misroute cost, and that is the whole mechanism: the intents
whose mistakes are cheap are exactly the ones a bot is good at, so the formula that only prices mistakes
is most wrong precisely where the bot is most useful. On rastreio it demands 0.67 confidence where 0.20
is enough.

And the penalty collapses: **1.96%** on the raw margin, **0.19%** on the isotonic score, **0.53%** on the
control. Which gives the result that decides how to spend an afternoon:

> **The amended formula on the uncalibrated margin (342.14) beats the naive formula on the probability
> the generator actually used (367.54).** Fixing the model beat fixing the input, and wave 3 pointed at
> the input.

The remaining fraction of a per cent is honest and explainable: the benefit is an average over contacts
that differ, so a rule using one number per intent cannot reach a sweep that is free to fit the mixture.

## Result 3: the best-calibrated score is the worst ranker

The control has the lowest calibration error in the table (**0.0061**) and the **highest** swept cost
(**342.4383** against the raw margin's 335.5655). It is the best-calibrated score available and the worst
one to route on.

The reason is that calibration and discrimination are different properties. The true probability is a
function of the intent and the difficulty; it is the chance a contact **like this one** is labelled
correctly. The raw score is built from the realised classification, so it carries information about
whether *this* contact was in fact labelled correctly — information no amount of calibration can put
back. A score can therefore say exactly the right thing on average and rank worse than one that is
biased everywhere.

This is wave 2's finding in a second setting: a gauge can be unbiased and useless. It is also the honest
limitation of this account — see below.

## Result 4: optimism is small, and the threshold is not the thing that was learned

Thresholds swept on the first three fifths of the month, priced on the rest, against that period's own
best:

| Intent | Contacts | Fitted | Its own best | **Optimism** |
| --- | --- | --- | --- | --- |
| rastreio | 4,257 | 0.10 | 0.24 | **0.1116** |
| prazo-de-entrega | 2,998 | 0.22 | 0.38 | 0.9893 |
| cadastro | 1,826 | 0.38 | 0.34 | 1.0777 |
| reembolso | 2,091 | 0.62 | 0.60 | **4.1790** |
| reclamacao | 1,537 | 0.62 | 0.72 | **3.2614** |
| **queue** | 12,709 | — | — | **1.5076** |

Seconds per contact. The queue pays **1.5076** seconds per contact for having fitted its thresholds
somewhere else — **0.45%** of the bill, and **13.05%** of the 11.5552 seconds wave 3 published as the
saving. So the upper bound the roadmap warned about is real and it is a tenth of the finding, not the
finding.

Two things worth more than the number. Optimism concentrates where **the mistake is expensive and the
sample is thin**: reembolso and reclamacao are the two smallest groups and the two dearest misroutes, and
they carry 5.9 of the 7.6 seconds of intent-level optimism between them. And look at the thresholds
themselves — rastreio moves from 0.10 to 0.24, prazo-de-entrega from 0.22 to 0.38 — while the cost moves
by a tenth of a second. **The cost curve is flat near its optimum, so the threshold is barely identified
and the decision is nearly optimal anyway.** An operation arguing about the second decimal of a threshold
is arguing about sampling noise; the quantity that was actually learned is the cost, not the cut.

## Result 5: the label a router can read is the better one to key on

Wave 3's per-intent rule asked for the reclamacao threshold on a contact that *is* a complaint. A
deployment cannot: it only knows what the classifier said. The roadmap recorded the substitution as
open and predicted that the direction would survive and **the size of the gain would shrink**.

It grows. Everything swept on the fitting period and priced on the later one:

| Rule | Seconds per contact | Resolution | Misroutes | Deferred | **Saving** |
| --- | --- | --- | --- | --- | --- |
| best single threshold | 348.0218 | 0.7141 | 857 | 3,191 | — |
| keyed on the true intent | 337.0731 | 0.6916 | 1,522 | 2,309 | 10.9487 |
| **keyed on the predicted intent** | **336.1007** | 0.6915 | **1,447** | 2,291 | **11.9210** |

The deployable rule saves **0.97 more seconds per contact** than the oracle one and makes **75 fewer**
misroutes. It is not a degraded version of wave 3's rule; it is a better-conditioned one.

The mechanism is worth stating carefully, because it generalises past this repository. The cost of a
misroute depends on what the contact *is*. The **probability** of a misroute depends on what the
classifier *said*, because a wrong label is exactly the event in which the reported intent differs from
the true one — so the reported label carries information about the classifier being wrong, and the true
label carries none. Keying on the true intent applies rastreio's permissive threshold to a complaint the
classifier read as a tracking question, which is the misroute the caution existed to prevent. Keying on
the reported label applies the complaint's caution and defers it.

> **Conditioning on what you know beats conditioning on what is true, when what you know is what the
> mistake is made of.**

Which leaves wave 3's headline in an interesting place. Its 11.5552 seconds per contact was fitted and
priced in sample and keyed on an unreadable label. Out of sample and keyed on the readable one, the
saving is **11.9210** — a ratio of **1.0317**, or **42.08** hours over the later period and **105.31** at
the month's treated volume. The two corrections nearly cancel. The roadmap's prediction that all three
pointed the same way was wrong, and the published figure survives for a reason it did not name.

## Assumptions and limitations

- **The raw score is too good a ranker, and that is this account's flaw.** The generator builds it from
  the realised classification, so it knows something a deployed confidence score does not. That is the
  mechanism behind Result 3 and it also means the *level* of discrimination here is optimistic. What
  transfers is that calibration and discrimination are separate, not how far apart they are.
- **The control reads a truth column.** `true_probability` is the declared accuracy curve. No policy may
  see it and nothing outside a study may deploy it; it exists to be the answer key.
- **One benefit per intent.** The amended threshold uses an average over contacts whose resolvability
  differs, which is why it lands near the sweep rather than on it. A benefit conditioned on the score
  itself would close more of the gap and would need its own held-out fit.
- **The calendar split assumes the month is stationary.** Arrivals here are uniform and nothing drifts,
  so the optimism measured is pure fitting noise with no distribution shift in it. A real period has
  both, and only the second is what a held-out period is usually defended as testing.
- **The expected calibration error depends on its bins.** Ten equal-width bins is a convention. The
  control's 0.0061 is the floor that binning imposes rather than a property of the score, which is why
  the table is published beside the number and why isotonic's 0.0066 should be read as *at the floor*
  rather than as better than Platt by a definite amount.
- **The thresholds are still swept on a coarse grid.** Two hundredths, wave 3's grid, kept deliberately:
  a finer grid buys a better in-sample number and a worse out-of-sample one, which is the same optimism
  measured in Result 4 arriving through a different door.
- **Nothing here re-derives wave 3's published figures.** Those remain in-sample, keyed on the true
  intent, and correct as the quantity they are. The corrections are published beside them rather than in
  place of them.

## Sources

- The threshold `1 − defer_cost / misroute_cost` is the standard cost-sensitive decision rule, as in
  Elkan's treatment of cost-sensitive learning; the amended form here is the same derivation carrying a
  benefit term for the correct decision.
- Pool-adjacent-violators for isotonic regression is due to Ayer and colleagues; the logistic
  post-processing is Platt's, and the comparison of the two for probability calibration follows
  Niculescu-Mizil and Caruana.
- The reliability diagram and the decomposition of a probability score into calibration and refinement
  are Murphy's; the expected calibration error is the binned summary in common use, with the caveats on
  binning that Naeini and colleagues raise.
- Optimism as the difference between apparent and out-of-sample performance is standard model-validation
  practice; Efron and Tibshirani's treatment is the one this follows in spirit rather than in method.

---

# `svclab.calibration` — a fórmula não estava errada, e calibração não era o passo que faltava

*[English](#svclabcalibration--the-formula-was-not-wrong-and-calibration-was-not-the-missing-step)*

A onda 3 aplicou o limiar de roteamento de manual — postergar abaixo de `1 − custo_de_postergar /
custo_de_erro` — ao score do classificador desta conta, encontrou-o **12,5% pior** que o número único
varrido, e publicou um diagnóstico: a fórmula é uma resposta correta sobre uma *probabilidade*, o score é
uma *margem*, e **calibração é o passo que falta**.

Esse diagnóstico era uma afirmação. Não tinha caso de controle atrás dele, e este módulo é o que é
preciso para testá-lo: um mapa do score para uma probabilidade, um jeito de ver se o mapa funcionou, e —
a parte que decide a onda — **a probabilidade que o gerador realmente usou**, sobre a qual a fórmula tem
de ser exatamente ótima se o diagnóstico estivesse certo.

Não é. E duas outras decisões que a onda 3 tomou por default são precificadas aqui ao mesmo tempo: os
limiares foram varridos e precificados nos mesmos contatos, e a regra por intenção foi chaveada na
intenção que o contato **realmente era**, que nenhum roteador consegue ler.

```python
from svclab.bot import classifier_labels
from svclab.calibration import formula_table, key_table, optimism_table, resolve_benefit
from svclab.synth import generate_dataset

data = generate_dataset()
mes = data.contacts[~data.contacts["holdout"]]
mes = mes.merge(classifier_labels(mes)[["contact", "predicted_intent"]], on="contact", how="left")

formula_table(mes, data.routing_scores)  # a forma fechada contra a varredura, em quatro scores
optimism_table(mes, data.routing_scores)  # o que um limiar ajustado custa num período que não viu
key_table(mes, data.routing_scores)  # o rótulo verdadeiro contra o que um roteador pode ler
```

## Resultado 1: calibração é real, e não é o passo que falta

Ajustado nos primeiros três quintos do mês, julgado nos **12.709** contatos restantes:

| Score | Erro de calibração | Fórmula ingênua | **Fórmula emendada** | Ótimo varrido | Penalidade ingênua | Penalidade emendada |
| --- | --- | --- | --- | --- | --- | --- |
| margem crua | 0,1618 | 392,7469 | **342,1386** | 335,5655 | **17,04%** | **1,96%** |
| isotônica | 0,0066 | 351,5371 | 336,2623 | 335,6177 | 4,74% | 0,19% |
| Platt | 0,0123 | 351,6284 | 336,5567 | 335,5214 | 4,80% | 0,31% |
| **probabilidade verdadeira** | 0,0061 | 367,5370 | 344,2607 | 342,4383 | **7,33%** | 0,53% |

Segundos por contato. A fórmula ingênua é a da onda 3; a emendada está abaixo.

A onda 3 estava certa sobre o insumo. O erro de calibração da margem crua é **26,68 vezes** o do
controle, e calibrá-la corta a penalidade da fórmula por **3,59 vezes**, de 17,04% para 4,74%. O score
realmente não significa o que a fórmula assume: no bin em que ele diz **0,6502**, **0,9078** dos rótulos
estão certos — uma lacuna de **0,2576** num único bin, sobre 2.333 contatos.

**Mas sobre a probabilidade perfeitamente calibrada a penalidade ainda é 7,33%.** Ali não há calibração
alguma restante a fazer, por construção, então o que está errado não é calibração. O controle é o que
torna isso visível, e a onda 3 não tinha controle.

## Resultado 2: o que faltava era um termo, e ele é a razão de o bot existir

A forma fechada precifica dois desfechos. Tentar com rótulo **errado** custa `custo_de_erro`; postergar
custa `custo_de_postergar`; e tentar com rótulo **certo** não custa nada. Esse último não é uma
simplificação, é a omissão de todo o argumento para implantar um bot: um contato corretamente rotulado
que o bot resolve **economiza** os segundos humanos que ele teria consumido.

Carregue o termo e a comparação passa a ser `(1 − p)·erro − p·benefício` contra `postergar`, então

> postergar abaixo de `(erro − postergar) / (erro + benefício)`

que é exatamente a fórmula original quando o benefício é zero — afirmado como álgebra, não como
semelhança. O benefício é **medido**, não presumido: rode o período de ajuste com o bot tentando tudo e
com ele não tentando nada, e tome a diferença nos contatos cujo rótulo estava certo.

| Intenção | Custo do erro | **Benefício** | Limiar ingênuo | **Emendado** |
| --- | --- | --- | --- | --- |
| rastreio | 60,0 | **142,68** | 0,6667 | **0,1974** |
| prazo-de-entrega | 90,0 | 139,11 | 0,7778 | 0,3055 |
| cadastro | 150,0 | **161,79** | 0,8667 | 0,4170 |
| reembolso | 420,0 | 65,58 | 0,9524 | 0,8238 |
| reclamacao | 540,0 | **23,32** | 0,9630 | 0,9231 |

O benefício corre no sentido **oposto** ao custo do erro, e esse é todo o mecanismo: as intenções cujos
erros são baratos são exatamente aquelas em que o bot é bom, então a fórmula que só precifica erros está
mais errada justamente onde o bot é mais útil. No rastreio ela exige 0,67 de confiança onde 0,20 basta.

E a penalidade colapsa: **1,96%** na margem crua, **0,19%** no score isotônico, **0,53%** no controle. O
que dá o resultado que decide como gastar uma tarde:

> **A fórmula emendada sobre a margem não calibrada (342,14) vence a fórmula ingênua sobre a
> probabilidade que o gerador realmente usou (367,54).** Corrigir o modelo venceu corrigir o insumo, e a
> onda 3 apontou para o insumo.

A fração de por cento que resta é honesta e explicável: o benefício é uma média sobre contatos que
diferem, então uma regra com um número por intenção não alcança uma varredura livre de ajustar a mistura.

## Resultado 3: o score melhor calibrado é o pior ordenador

O controle tem o menor erro de calibração da tabela (**0,0061**) e o **maior** custo varrido
(**342,4383** contra 335,5655 da margem crua). É o score melhor calibrado disponível e o pior para
rotear.

A razão é que calibração e discriminação são propriedades diferentes. A probabilidade verdadeira é função
da intenção e da dificuldade; é a chance de um contato **como este** ser rotulado corretamente. A margem
crua é construída a partir da classificação realizada, então carrega informação sobre se *este* contato
de fato foi rotulado certo — informação que calibração nenhuma recoloca. Um score pode portanto dizer
exatamente a coisa certa na média e ordenar pior que um que é viesado em todo ponto.

Este é o achado da onda 2 num segundo cenário: um instrumento pode ser não viesado e inútil. É também a
limitação honesta desta conta — ver abaixo.

## Resultado 4: o otimismo é pequeno, e o limiar não é a coisa que foi aprendida

Limiares varridos nos primeiros três quintos do mês, precificados no resto, contra o melhor do próprio
período:

| Intenção | Contatos | Ajustado | Melhor do próprio | **Otimismo** |
| --- | --- | --- | --- | --- |
| rastreio | 4.257 | 0,10 | 0,24 | **0,1116** |
| prazo-de-entrega | 2.998 | 0,22 | 0,38 | 0,9893 |
| cadastro | 1.826 | 0,38 | 0,34 | 1,0777 |
| reembolso | 2.091 | 0,62 | 0,60 | **4,1790** |
| reclamacao | 1.537 | 0,62 | 0,72 | **3,2614** |
| **fila** | 12.709 | — | — | **1,5076** |

Segundos por contato. A fila paga **1,5076** segundo por contato por ter ajustado seus limiares em outro
lugar — **0,45%** da conta, e **13,05%** dos 11,5552 segundos que a onda 3 publicou como economia. Então
o limite superior de que o roadmap avisava é real e é um décimo do achado, não o achado.

Duas coisas valem mais que o número. O otimismo concentra onde **o erro é caro e a amostra é rala**:
reembolso e reclamacao são os dois menores grupos e os dois erros mais custosos, e carregam 5,9 dos 7,6
segundos de otimismo por intenção. E olhe os limiares em si — rastreio vai de 0,10 a 0,24,
prazo-de-entrega de 0,22 a 0,38 — enquanto o custo se move um décimo de segundo. **A curva de custo é
plana perto do ótimo, então o limiar é pouco identificado e a decisão é quase ótima de todo modo.** Uma
operação discutindo a segunda decimal de um limiar está discutindo ruído de amostragem; a quantidade que
de fato foi aprendida é o custo, não o corte.

## Resultado 5: o rótulo que um roteador pode ler é o melhor para chavear

A regra por intenção da onda 3 pedia o limiar de reclamacao num contato que *é* uma reclamação. Uma
implantação não pode: ela só sabe o que o classificador disse. O roadmap registrou a substituição como
aberta e previu que a direção sobreviveria e **o tamanho do ganho encolheria**.

Ele cresce. Tudo varrido no período de ajuste e precificado no posterior:

| Regra | Segundos por contato | Resolução | Erros de rota | Postergados | **Economia** |
| --- | --- | --- | --- | --- | --- |
| melhor limiar único | 348,0218 | 0,7141 | 857 | 3.191 | — |
| chaveada na intenção verdadeira | 337,0731 | 0,6916 | 1.522 | 2.309 | 10,9487 |
| **chaveada na intenção prevista** | **336,1007** | 0,6915 | **1.447** | 2.291 | **11,9210** |

A regra implantável economiza **0,97 segundo por contato a mais** que a regra oráculo e comete **75
erros de rota menos**. Ela não é uma versão degradada da regra da onda 3; é uma regra melhor
condicionada.

O mecanismo merece ser dito com cuidado, porque generaliza para além deste repositório. O custo de um
erro de rota depende do que o contato *é*. A **probabilidade** de um erro de rota depende do que o
classificador *disse*, porque um rótulo errado é exatamente o evento em que a intenção reportada difere
da verdadeira — então o rótulo reportado carrega informação sobre o classificador estar errado, e o
rótulo verdadeiro não carrega nenhuma. Chavear na intenção verdadeira aplica o limiar permissivo do
rastreio a uma reclamação que o classificador leu como pergunta de rastreio, que é exatamente o erro que
a cautela existia para evitar. Chavear no rótulo reportado aplica a cautela da reclamação e posterga.

> **Condicionar no que você sabe vence condicionar no que é verdade, quando o que você sabe é aquilo de
> que o erro é feito.**

O que deixa a manchete da onda 3 num lugar interessante. Seus 11,5552 segundos por contato foram
ajustados e precificados dentro da amostra e chaveados num rótulo ilegível. Fora da amostra e chaveada no
legível, a economia é **11,9210** — uma razão de **1,0317**, ou **42,08** horas no período posterior e
**105,31** no volume tratado do mês. As duas correções quase se cancelam. A previsão do roadmap de que as
três apontavam na mesma direção estava errada, e a cifra publicada sobrevive por uma razão que ele não
nomeou.

## Premissas e limitações

- **A margem crua é um ordenador bom demais, e esse é o defeito desta conta.** O gerador a constrói a
  partir da classificação realizada, então ela sabe algo que um score de confiança implantado não sabe.
  Esse é o mecanismo atrás do Resultado 3 e também significa que o *nível* de discriminação aqui é
  otimista. O que se transfere é que calibração e discriminação são separadas, não o quanto estão
  separadas.
- **O controle lê uma coluna de verdade.** `true_probability` é a curva de acurácia declarada. Nenhuma
  política pode vê-la e nada fora de um estudo pode implantá-la; ela existe para ser o gabarito.
- **Um benefício por intenção.** O limiar emendado usa uma média sobre contatos cuja resolubilidade
  difere, e é por isso que ele chega perto da varredura em vez de sobre ela. Um benefício condicionado ao
  próprio score fecharia mais da lacuna e precisaria do seu próprio ajuste fora da amostra.
- **A divisão por calendário assume que o mês é estacionário.** As chegadas aqui são uniformes e nada
  deriva, então o otimismo medido é puro ruído de ajuste, sem deslocamento de distribuição dentro. Um
  período real tem os dois, e só o segundo é aquilo que um período reservado costuma ser defendido como
  testando.
- **O erro esperado de calibração depende dos seus bins.** Dez bins de largura igual é convenção. Os
  0,0061 do controle são o piso que o binning impõe, não uma propriedade do score, e é por isso que a
  tabela é publicada ao lado do número e por isso que os 0,0066 do isotônico devem ser lidos como *no
  piso* e não como melhores que Platt por uma margem definida.
- **Os limiares seguem varridos numa malha grosseira.** Dois centésimos, a malha da onda 3, mantida de
  propósito: uma malha mais fina compra um número melhor dentro da amostra e pior fora dela, que é o
  mesmo otimismo do Resultado 4 chegando por outra porta.
- **Nada aqui re-deriva as cifras publicadas da onda 3.** Elas seguem dentro da amostra, chaveadas na
  intenção verdadeira, e corretas como a quantidade que são. As correções são publicadas ao lado delas,
  não no lugar delas.

## Fontes

- O limiar `1 − custo_de_postergar / custo_de_erro` é a regra padrão de decisão sensível a custo, como no
  tratamento de aprendizado sensível a custo de Elkan; a forma emendada aqui é a mesma derivação
  carregando um termo de benefício para a decisão correta.
- O algoritmo pool-adjacent-violators para regressão isotônica é de Ayer e colegas; o pós-processamento
  logístico é de Platt, e a comparação dos dois para calibração de probabilidade segue Niculescu-Mizil e
  Caruana.
- O diagrama de confiabilidade e a decomposição de um score de probabilidade em calibração e refinamento
  são de Murphy; o erro esperado de calibração é o resumo binado de uso comum, com as ressalvas sobre
  binning que Naeini e colegas levantam.
- Otimismo como a diferença entre desempenho aparente e fora da amostra é prática padrão de validação de
  modelos; o tratamento de Efron e Tibshirani é o que este segue em espírito, não em método.
