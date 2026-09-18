# `svclab.quality` — the meter that was noise

*[Português](#svclabquality--o-medidor-que-era-ruído)*

## The business problem

Wave 1 established that no containment definition can rank two bot policies, and that resolution can.
The obvious next move is to stop counting and start grading: sample sessions, have a quality panel
score them against a rubric, and compare the bot's sessions with the humans'.

This module is about what has to be true before that comparison means anything. **A quality panel is a
gauge, and a gauge gets qualified before it gets used** — which is ordinary practice for a caliper and
almost unheard of for a quality rubric.

On this panel: the three graders disagree with **themselves** on 17% to 23% of the sessions they read
twice, they agree with each other 76% to 78% of the time at a kappa of **0.54 to 0.57**, and the pass
rate they report on the identical sessions runs from **0.3815 to 0.5683** depending on who graded.

And then the result the module exists for. Measurement error does not merely add noise to a
comparison — **it shrinks it, by a factor with a closed form**, always towards zero. This panel
reports **69.45%** of the real difference between the two arms. Not because anybody cheated.

## The decision it enables

1. **Is this quality score a measurement or a habit?** Which is repeatability, reproducibility and
   bias against a declared standard — the three columns an attribute agreement analysis produces.
2. **How much of a real difference will this panel report?** Which is one number, and it is
   computable from the gauge study alone, before any comparison is run.
3. **And how many sessions does this panel cost me?** Because attenuation is paid for in sample size.

## Usage

```python
from svclab.bot import THREE_TURNS, run
from svclab.quality import (
    agreement_table,
    attenuation,
    judge_verdicts,
    latent_quality,
    panel_verdicts,
    reproducibility,
    sessions_for_difference,
)
from svclab.synth import generate_dataset

data = generate_dataset()
latent = latent_quality(run(data.contacts, THREE_TURNS), data.contacts)

panel = panel_verdicts(latent, data.panel_noise)
agreement_table(panel, latent)  # repeatability, then sensitivity and specificity
reproducibility(panel)  # every pair of graders, on one replicate

attenuation(0.9596, 0.4137, 0.8161, 0.8784)  # what the panel will report of a real gap
sessions_for_difference(0.9596, 0.4137, 0.8161, 0.8784)  # what it costs in sessions
```

## Result 1: the panel does not agree with itself

The panel samples **1,200 contacts**, which are **1,434 sessions** once the repeats those contacts
generated are counted — a sampled contact that came back is two conversations to grade. Three graders,
two readings each, so **8,604 readings**, and the second reading is the one almost nobody collects:

| Grader | Pass rate | Repeatability | Repeatability kappa | Agreement with truth | Sensitivity | Specificity | Youden |
| --- | --- | --- | --- | --- | --- | --- | --- |
| avaliador-1 | **0.5683** | 0.8298 | 0.6533 | 0.8675 | 0.9252 | 0.8069 | 0.7320 |
| avaliador-2 | **0.3815** | 0.8117 | 0.6010 | 0.8417 | 0.7177 | 0.9721 | 0.6898 |
| avaliador-3 | 0.4829 | 0.7664 | 0.5322 | 0.8302 | 0.8054 | 0.8562 | 0.6617 |

Read the first column first. **The same sessions, graded by three people, produce pass rates of
0.3815 and 0.5683** — a factor of 1.49 on the headline number, decided by the rota.

Then read repeatability, which is the same grader reading the same session twice: 0.7664 to 0.8298.
Between a sixth and a quarter of the time, one person contradicts themselves. An assessor who cannot
agree with themselves cannot agree with anything else, which is why that column comes before the
comparison with the standard.

And notice the two ways of being wrong are opposite. `avaliador-1` catches 92.52% of the acceptable
sessions and waves through 19.31% of the unacceptable ones; `avaliador-2` is the mirror image, at
71.77% and 2.79%. A single accuracy figure — 0.8675 against 0.8417 — hides which, and the difference
between a lenient and a strict grader is not a difference in skill.

## Result 2: seventy-eight per cent agreement is a kappa of 0.57

| Pair | Sessions | Agreement | Kappa |
| --- | --- | --- | --- |
| avaliador-1 vs avaliador-2 | 1,434 | 0.7615 | **0.5355** |
| avaliador-1 vs avaliador-3 | 1,434 | 0.7824 | **0.5668** |
| avaliador-2 vs avaliador-3 | 1,434 | 0.7741 | **0.5440** |

Raw agreement of 78% is the number that gets reported and it sounds like a working instrument. Kappa
is agreement above what two assessors would reach by accident given their own pass rates, and at 0.54
to 0.57 this panel sits in the band the literature calls moderate.

The gap between the two columns is not a technicality. Two assessors who pass 95% of everything agree
90% of the time while knowing nothing about the sessions, and this module's tests contain that case
worked out on paper: agreement 0.90, **kappa −0.053**. Raw agreement on a lopsided task is a
measurement of the lopsidedness.

Both readings here are from the same replicate, deliberately. Comparing one grader's first reading
with another's second measures repeatability and reproducibility at once and attributes the result to
neither.

## Result 3: the panel reports 69% of the difference, exactly

The two arms, by the declared standard: **95.96%** of the control arm's sessions are acceptable
against **41.37%** of the automated arm's. The true gap is **0.5459**.

The panel's average sensitivity is 0.8161 and its average specificity 0.8784, so its Youden index is
**0.6945**. And then:

| | |
| --- | --- |
| True difference | 0.5459 |
| Observed difference | **0.3791** |
| Factor | **0.6945** |
| Control arm, as reported | 0.7881 |
| Automated arm, as reported | 0.4089 |

The identity is exact, not approximate. An assessor with sensitivity `se` and specificity `sp` turns a
true pass rate `p` into `p·se + (1−p)·(1−sp)`; subtract two of those and the true difference comes out
multiplied by `se + sp − 1`. The tests check it at both ends — a perfect gauge changes nothing, and a
gauge whose sensitivity and specificity sum to one reports **exactly zero** however large the real
difference is — and at four gauges in between.

Three consequences worth stating separately:

- **The shrink is always towards zero.** A panel cannot exaggerate a difference through
  misclassification alone. It can only hide one.
- **A gauge below a Youden index of zero reverses the sign.** Not noisy — inverted, and the report
  says the opposite of the truth with the same confidence.
- **And the exactness depends on one assumption**: that the assessor's two error rates are the same in
  both groups. A grader who is harder on the bot's transcripts than on a colleague's breaks it — in the
  direction of **exaggerating** rather than attenuating, which is the one case where a quality panel
  makes automation look worse than it is.

## Result 4: attenuation is paid for in sessions

| Gauge | Sessions per arm |
| --- | --- |
| Perfect | **10.07** |
| This panel | **25.03** |

**An inflation of 2.49 times**, against the 2.07 the square of the Youden index predicts. The rule of
thumb understates the bill, because the attenuated rates also sit closer to 0.5, where a proportion's
variance is largest. The honest version is that a panel with this kappa costs two and a half times the
sessions to see what a qualified one would see — and the sample size is the lever everybody pulls
*before* checking whether the instrument works.

## Result 5: the automated judge is more accurate than the panel, and validated against it

The judge reads all 47,019 sessions rather than 1,200, once each:

| Assessor | Agreement with truth | Sensitivity | Specificity | Youden |
| --- | --- | --- | --- | --- |
| **juiz-automatico** | **0.8850** | 0.9937 | 0.7705 | **0.7642** |
| avaliador-1 | 0.8675 | 0.9252 | 0.8069 | 0.7320 |
| avaliador-2 | 0.8417 | 0.7177 | 0.9721 | 0.6898 |
| avaliador-3 | 0.8302 | 0.8054 | 0.8562 | 0.6617 |

**The judge agrees with the standard more often than any individual grader.** Now the way it would
actually be assessed:

| Comparison | Agreement | Kappa |
| --- | --- | --- |
| judge vs avaliador-1 | 0.8598 | **0.7121** |
| judge vs avaliador-3 | 0.8082 | **0.6198** |
| judge vs avaliador-2 | 0.7608 | **0.5450** |
| judge vs the panel's majority | 0.8466 | 0.6948 |
| judge vs the declared standard | 0.8919 | **0.7826** |

Validating the judge against the panel scores it **0.6948**, and validating it against one grader
scores it anywhere from **0.5450 to 0.7121** — a spread of 0.17 of kappa decided by which colleague
was free that week. Its agreement with the truth is 0.7826. **"Agreement with our human reviewers" is
a measurement of the reviewers as much as of the judge**, and where the reviewers are a moderate gauge,
the number it produces is an underestimate of a good judge and would equally be an overestimate of a
judge that shared the panel's biases.

And the honest counterweight, which belongs in the same breath: **the panel as a committee beats the
judge.** Majority verdict against the standard is kappa **0.7979** against the judge's 0.7826.
Averaging three moderate assessors recovers most of what each one loses, which is the argument for a
panel and is not an argument for any member of it.

## Assumptions and limitations

- **Every number here comes from a seeded synthetic generator**, including the declared standard that
  makes accuracy computable at all. No employer, client, vendor or platform data is used anywhere, and
  **there is no language model** in this repository — the "automated judge" is a declared bias and
  spread, not a model. See [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **A session's quality is a declared function of its outcome and its difficulty, not a draw.** That
  is what isolates measurement error from everything else, and it is also a strong simplification: two
  escalations at the same difficulty are identical here, and in a real operation they are not.
- **The standard is a single declared threshold on a latent score.** Real rubrics have several criteria
  with weights, and a session can fail one and pass four. Everything in this module generalises to
  that, and the kappa arithmetic does not care, but the single threshold is what makes the attenuation
  identity readable in one line.
- **The graders' errors are independent of the arm.** That assumption is what makes the attenuation
  identity exact, and it is the one most likely to be false in practice, because a grader who knows a
  transcript came from a bot is not the same instrument as one who does not. Result 3 names the
  direction that breaks.
- **The judge is deterministic, so it has no repeatability to report.** The table shows `nan` rather
  than 1.0, because claiming a property that was never measured is the failure this whole module is
  about. A sampled language model is not deterministic and would have a repeatability column worth
  reading.
- **The panel reads a sample and the judge reads everything**, which is the real trade and is also why
  their agreement figures are computed on the sampled sessions only.
- **Nothing here corrects for the attenuation.** The factor is measurable, so the correction is
  available — divide the observed difference by the Youden index — and it is deliberately not offered,
  because a correction applied to a gauge study this uncertain buys a point estimate and loses the
  interval. Measuring the instrument is the finding; repairing the estimate is a decision for somebody
  who knows what the number will be used for.

## Sources

Cited as the origin of a *method*, never as a source of any number in these tables.

- Cohen, J. (1960). *A Coefficient of Agreement for Nominal Scales.* Educational and Psychological
  Measurement 20(1). — kappa, and why raw agreement is not enough.
- Landis, J. R., Koch, G. G. (1977). *The Measurement of Observer Agreement for Categorical Data.*
  Biometrics 33(1). — the bands this document calls a moderate gauge.
- Automotive Industry Action Group (2010). *Measurement Systems Analysis*, 4th ed. — attribute
  agreement analysis: repeatability, reproducibility and bias against a known standard, which is the
  study this module runs on a quality rubric instead of on a caliper.
- Youden, W. J. (1950). *Index for Rating Diagnostic Tests.* Cancer 3(1). — the index that turns out to
  be the attenuation factor.
- Bross, I. (1954). *Misclassification in 2 x 2 Tables.* Biometrics 10(4). — that non-differential
  misclassification biases a difference towards the null, which is Result 3.

---

# `svclab.quality` — o medidor que era ruído

*[English](#svclabquality--the-meter-that-was-noise)*

## O problema de negócio

A onda 1 estabeleceu que nenhuma definição de contenção consegue ranquear duas políticas de bot, e que
resolução consegue. O passo óbvio seguinte é parar de contar e começar a avaliar: amostrar sessões, ter
um painel de qualidade pontuando-as contra uma régua, e comparar as sessões do bot com as dos humanos.

Este módulo é sobre o que precisa ser verdade antes de essa comparação significar algo. **Um painel de
qualidade é um instrumento de medição, e um instrumento é qualificado antes de ser usado** — o que é
prática comum para um paquímetro e praticamente inédito para uma régua de qualidade.

Neste painel: os três avaliadores discordam de **si mesmos** em 17% a 23% das sessões que leem duas
vezes, concordam entre si 76% a 78% das vezes com um kappa de **0,54 a 0,57**, e a taxa de aprovação
que reportam nas sessões idênticas vai de **0,3815 a 0,5683** dependendo de quem avaliou.

E então o resultado pelo qual o módulo existe. Erro de medição não apenas adiciona ruído a uma
comparação — **ele a encolhe, por um fator com forma fechada**, sempre em direção a zero. Este painel
reporta **69,45%** da diferença real entre os dois braços. Não porque alguém trapaceou.

## A decisão que habilita

1. **Esta nota de qualidade é uma medição ou um hábito?** Que é repetibilidade, reprodutibilidade e
   viés contra um padrão declarado — as três colunas que uma análise de concordância de atributos
   produz.
2. **Quanto de uma diferença real este painel vai reportar?** Que é um número, e é calculável só a
   partir do estudo do instrumento, antes de qualquer comparação rodar.
3. **E quantas sessões este painel me custa?** Porque atenuação se paga em tamanho de amostra.

## Uso

```python
from svclab.bot import THREE_TURNS, run
from svclab.quality import (
    agreement_table,
    attenuation,
    judge_verdicts,
    latent_quality,
    panel_verdicts,
    reproducibility,
    sessions_for_difference,
)
from svclab.synth import generate_dataset

data = generate_dataset()
latent = latent_quality(run(data.contacts, THREE_TURNS), data.contacts)

panel = panel_verdicts(latent, data.panel_noise)
agreement_table(panel, latent)  # repetibilidade, depois sensibilidade e especificidade
reproducibility(panel)  # cada par de avaliadores, numa réplica

attenuation(0.9596, 0.4137, 0.8161, 0.8784)  # o que o painel vai reportar de um gap real
sessions_for_difference(0.9596, 0.4137, 0.8161, 0.8784)  # o que isso custa em sessões
```

## Resultado 1: o painel não concorda consigo mesmo

O painel amostra **1.200 contatos**, que são **1.434 sessões** quando os recontatos que esses contatos
geraram entram na conta — um contato amostrado que voltou são duas conversas a avaliar. Três
avaliadores, duas leituras cada, portanto **8.604 leituras**, e a segunda leitura é a que quase ninguém
coleta:

| Avaliador | Taxa de aprovação | Repetibilidade | Kappa de repetibilidade | Concordância com a verdade | Sensibilidade | Especificidade | Youden |
| --- | --- | --- | --- | --- | --- | --- | --- |
| avaliador-1 | **0,5683** | 0,8298 | 0,6533 | 0,8675 | 0,9252 | 0,8069 | 0,7320 |
| avaliador-2 | **0,3815** | 0,8117 | 0,6010 | 0,8417 | 0,7177 | 0,9721 | 0,6898 |
| avaliador-3 | 0,4829 | 0,7664 | 0,5322 | 0,8302 | 0,8054 | 0,8562 | 0,6617 |

Leia a primeira coluna primeiro. **As mesmas sessões, avaliadas por três pessoas, produzem taxas de
aprovação de 0,3815 e 0,5683** — um fator de 1,49 no número principal, decidido pela escala de
trabalho.

Depois leia a repetibilidade, que é o mesmo avaliador lendo a mesma sessão duas vezes: 0,7664 a 0,8298.
Entre um sexto e um quarto das vezes, uma pessoa se contradiz. Um avaliador que não consegue concordar
consigo mesmo não consegue concordar com nada, e é por isso que essa coluna vem antes da comparação com
o padrão.

E note que as duas formas de errar são opostas. O `avaliador-1` pega 92,52% das sessões aceitáveis e
deixa passar 19,31% das inaceitáveis; o `avaliador-2` é o espelho, com 71,77% e 2,79%. Uma única cifra
de acurácia — 0,8675 contra 0,8417 — esconde qual, e a diferença entre um avaliador leniente e um
rigoroso não é diferença de competência.

## Resultado 2: setenta e oito por cento de concordância é um kappa de 0,57

| Par | Sessões | Concordância | Kappa |
| --- | --- | --- | --- |
| avaliador-1 vs avaliador-2 | 1.434 | 0,7615 | **0,5355** |
| avaliador-1 vs avaliador-3 | 1.434 | 0,7824 | **0,5668** |
| avaliador-2 vs avaliador-3 | 1.434 | 0,7741 | **0,5440** |

Concordância bruta de 78% é o número que se reporta e soa como um instrumento funcionando. Kappa é
concordância acima do que dois avaliadores alcançariam por acaso dadas as próprias taxas de aprovação,
e em 0,54 a 0,57 este painel fica na faixa que a literatura chama de moderada.

A diferença entre as duas colunas não é tecnicalidade. Dois avaliadores que aprovam 95% de tudo
concordam 90% das vezes sem saber nada sobre as sessões, e os testes deste módulo contêm esse caso
resolvido no papel: concordância 0,90, **kappa −0,053**. Concordância bruta numa tarefa desbalanceada é
uma medição do desbalanceamento.

As duas leituras aqui são da mesma réplica, deliberadamente. Comparar a primeira leitura de um
avaliador com a segunda de outro mede repetibilidade e reprodutibilidade ao mesmo tempo e atribui o
resultado a nenhuma das duas.

## Resultado 3: o painel reporta 69% da diferença, exatamente

Os dois braços, pelo padrão declarado: **95,96%** das sessões do braço de controle são aceitáveis contra
**41,37%** das do braço automatizado. O gap real é **0,5459**.

A sensibilidade média do painel é 0,8161 e a especificidade média 0,8784, então seu índice de Youden é
**0,6945**. E então:

| | |
| --- | --- |
| Diferença real | 0,5459 |
| Diferença observada | **0,3791** |
| Fator | **0,6945** |
| Braço de controle, como reportado | 0,7881 |
| Braço automatizado, como reportado | 0,4089 |

A identidade é exata, não aproximada. Um avaliador com sensibilidade `se` e especificidade `sp`
transforma uma taxa real `p` em `p·se + (1−p)·(1−sp)`; subtraia duas dessas e a diferença real sai
multiplicada por `se + sp − 1`. Os testes verificam isso nos dois extremos — um instrumento perfeito não
muda nada, e um cuja sensibilidade mais especificidade soma um reporta **exatamente zero** por maior que
seja a diferença real — e em quatro instrumentos intermediários.

Três consequências que valem ser ditas à parte:

- **O encolhimento é sempre em direção a zero.** Um painel não consegue exagerar uma diferença apenas
  por erro de classificação. Só consegue esconder uma.
- **Um instrumento com índice de Youden abaixo de zero inverte o sinal.** Não é ruidoso — é invertido, e
  o relatório diz o oposto da verdade com a mesma confiança.
- **E a exatidão depende de uma premissa**: que as duas taxas de erro do avaliador são as mesmas nos
  dois grupos. Um avaliador mais duro com as transcrições do bot que com as de um colega quebra isso —
  na direção de **exagerar** em vez de atenuar, que é o único caso em que um painel de qualidade faz a
  automação parecer pior do que é.

## Resultado 4: atenuação se paga em sessões

| Instrumento | Sessões por braço |
| --- | --- |
| Perfeito | **10,07** |
| Este painel | **25,03** |

**Uma inflação de 2,49 vezes**, contra as 2,07 que o quadrado do índice de Youden prevê. A regra de bolso
subestima a conta, porque as taxas atenuadas também ficam mais perto de 0,5, onde a variância de uma
proporção é maior. A versão honesta é que um painel com esse kappa custa duas vezes e meia as sessões
para ver o que um painel qualificado veria — e o tamanho da amostra é a alavanca que todo mundo puxa
*antes* de verificar se o instrumento funciona.

## Resultado 5: o juiz automático é mais acurado que o painel, e é validado contra ele

O juiz lê todas as 47.019 sessões em vez de 1.200, uma vez cada:

| Avaliador | Concordância com a verdade | Sensibilidade | Especificidade | Youden |
| --- | --- | --- | --- | --- |
| **juiz-automatico** | **0,8850** | 0,9937 | 0,7705 | **0,7642** |
| avaliador-1 | 0,8675 | 0,9252 | 0,8069 | 0,7320 |
| avaliador-2 | 0,8417 | 0,7177 | 0,9721 | 0,6898 |
| avaliador-3 | 0,8302 | 0,8054 | 0,8562 | 0,6617 |

**O juiz concorda com o padrão mais vezes que qualquer avaliador individual.** Agora a forma como ele
seria de fato avaliado:

| Comparação | Concordância | Kappa |
| --- | --- | --- |
| juiz vs avaliador-1 | 0,8598 | **0,7121** |
| juiz vs avaliador-3 | 0,8082 | **0,6198** |
| juiz vs avaliador-2 | 0,7608 | **0,5450** |
| juiz vs a maioria do painel | 0,8466 | 0,6948 |
| juiz vs o padrão declarado | 0,8919 | **0,7826** |

Validar o juiz contra o painel lhe dá **0,6948**, e validá-lo contra um avaliador dá de **0,5450 a
0,7121** — uma dispersão de 0,17 de kappa decidida por qual colega estava livre naquela semana. Sua
concordância com a verdade é 0,7826. **"Concordância com nossos revisores humanos" é uma medição dos
revisores tanto quanto do juiz**, e onde os revisores são um instrumento moderado, o número produzido é
uma subestimativa de um juiz bom — e seria igualmente uma superestimativa de um juiz que
compartilhasse os vieses do painel.

E o contrapeso honesto, que pertence à mesma frase: **o painel como comitê ganha do juiz.** O veredito
por maioria contra o padrão dá kappa **0,7979** contra os 0,7826 do juiz. Fazer a média de três
avaliadores moderados recupera a maior parte do que cada um perde, o que é o argumento a favor de um
painel e não é argumento a favor de nenhum de seus membros.

## Premissas e limitações

- **Todo número aqui vem de um gerador sintético com semente**, inclusive o padrão declarado que torna
  a acurácia calculável. Nenhum dado de empregador, cliente, fornecedor ou plataforma é usado em
  qualquer parte, e **não existe modelo de linguagem** neste repositório — o "juiz automático" é um
  viés e uma dispersão declarados, não um modelo. Ver [`DISCLAIMER.md`](../../../DISCLAIMER.md).
- **A qualidade de uma sessão é função declarada do seu resultado e da sua dificuldade, não um
  sorteio.** É isso que isola o erro de medição de todo o resto, e é também uma simplificação forte:
  dois escalonamentos com a mesma dificuldade são idênticos aqui, e numa operação real não são.
- **O padrão é um único limiar declarado sobre uma nota latente.** Réguas reais têm vários critérios com
  pesos, e uma sessão pode falhar um e passar em quatro. Tudo neste módulo generaliza para isso, e a
  aritmética do kappa não se importa, mas o limiar único é o que torna a identidade de atenuação legível
  em uma linha.
- **Os erros dos avaliadores são independentes do braço.** Essa premissa é o que torna a identidade de
  atenuação exata, e é a mais provável de ser falsa na prática, porque um avaliador que sabe que uma
  transcrição veio de um bot não é o mesmo instrumento que um que não sabe. O Resultado 3 nomeia a
  direção que quebra.
- **O juiz é determinístico, então não tem repetibilidade a reportar.** A tabela mostra `nan` em vez de
  1,0, porque afirmar uma propriedade que nunca foi medida é exatamente a falha de que este módulo
  trata. Um modelo de linguagem amostrado não é determinístico e teria uma coluna de repetibilidade
  que vale ler.
- **O painel lê uma amostra e o juiz lê tudo**, que é a troca real e é também por que as cifras de
  concordância entre eles são calculadas somente nas sessões amostradas.
- **Nada aqui corrige a atenuação.** O fator é mensurável, então a correção está disponível — divida a
  diferença observada pelo índice de Youden — e ela é deliberadamente não oferecida, porque uma correção
  aplicada sobre um estudo de instrumento tão incerto compra uma estimativa pontual e perde o intervalo.
  Medir o instrumento é o achado; consertar a estimativa é decisão de quem sabe para que o número vai
  ser usado.

## Fontes

Citadas como origem de um *método*, nunca como fonte de qualquer número destas tabelas.

- Cohen, J. (1960). *A Coefficient of Agreement for Nominal Scales.* Educational and Psychological
  Measurement 20(1). — o kappa, e por que concordância bruta não basta.
- Landis, J. R., Koch, G. G. (1977). *The Measurement of Observer Agreement for Categorical Data.*
  Biometrics 33(1). — as faixas que este documento chama de instrumento moderado.
- Automotive Industry Action Group (2010). *Measurement Systems Analysis*, 4ª ed. — análise de
  concordância de atributos: repetibilidade, reprodutibilidade e viés contra um padrão conhecido, que é
  o estudo que este módulo roda sobre uma régua de qualidade em vez de sobre um paquímetro.
- Youden, W. J. (1950). *Index for Rating Diagnostic Tests.* Cancer 3(1). — o índice que acaba sendo o
  fator de atenuação.
- Bross, I. (1954). *Misclassification in 2 x 2 Tables.* Biometrics 10(4). — que erro de classificação
  não diferencial enviesa uma diferença em direção ao nulo, que é o Resultado 3.
