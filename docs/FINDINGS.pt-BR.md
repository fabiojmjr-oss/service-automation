# Nove achados, para quem assina o business case

*[English](FINDINGS.md)*

O [README raiz](../README.pt-BR.md) apresenta cada achado ao lado da aritmética que o produziu. Este
documento faz o outro trabalho: diz, para cada um dos nove, **em que decisão o achado desemboca, o que
uma operação competente teria decidido sem ele, e o que fazer em vez disso.** Nenhuma cifra nova aparece
aqui. Todo número abaixo está citado do README, que por sua vez está sob teste — uma cifra que se moveu
quebra o build antes de chegar a esta página.

Um aviso antes da lista. Estes são achados sobre **uma conta sintética declarada**, gerada pelo
`svclab.synth` a partir de parâmetros escritos. Não são estatísticas de mercado e não são benchmark. O
que se transfere é o **método** — e, em cinco dos nove casos, uma **forma fechada** que vale em qualquer
conta, não só nesta.

| # | A decisão em que desemboca | A cifra que decide |
| --- | --- | --- |
| 1 | Por qual número julgar uma automação | Contenção ranqueia as quatro políticas no inverso exato da resolução |
| 2 | Se a nota de qualidade pode ser usada como evidência | O painel reporta 69,45% de qualquer diferença real, exatamente |
| 3 | Três defaults que ninguém foi chamado a aprovar | O headcount prometido é alcançável se 29,23% dos clientes desistirem |
| 4 | Se um cliente é uma pessoa ou uma linha | Uma correlação de 0,2500 entre pessoas chega a 0,0448 no desfecho |
| 5 | De quem o volume realmente vem | Usuários intensos geram 58,1% dos contatos e 61,2% das horas |
| 6 | Quanto custa um contato não resolvido depois de hoje | A cauda é 1,0448 sessões, e a alavanca não é o cliente |
| 7 | Qual restrição decidiu o headcount | Teto de ocupação sozinho é satisfeito por subdimensionamento |
| 8 | A diferença entre contagem de atendentes e folha | Onze atendentes custam doze pessoas, por ponto fixo |
| 9 | Se corrigir o insumo de um modelo ou o modelo | A fórmula erra 7,33% num score perfeitamente calibrado |

## 1. O KPI ranqueia as políticas ao contrário

**A decisão.** Por qual número único um programa de automação é conduzido, e portanto qual política
recebe verba.

**O que o case dizia.** Contenção, a métrica padrão, em 0,8169 para a política de bot mais agressiva.
Nesse número o programa é um sucesso e a política é a vencedora.

**O que a conta diz.** A mesma política resolve **0,4476** dos contatos contra **0,7271** da política que
a contenção coloca em último. O ranking por contenção é o inverso exato do ranking por resolução, e todas
as quatro definições defensáveis de contenção — inclusive a mais estrita — preferem a mesma política
errada. **28%** da contenção citada nunca chegou à fila, medido contra clientes que nunca encontraram o
bot. O total de conversas subiu **26,6%**, porque um contato contido que volta era um contato postergado.
O resíduo deixado para humanos é **1,58** vez mais difícil do que o que o bot resolveu, e **21,98%** do
que o bot resolveu teria se resolvido sozinho.

O business case de headcount herda tudo isso. Prometeu **8,49** atendentes de economia contra uma base de
14; a fila devolve **3**, uma superestimação de **2,83** vezes. E **1,49** atendente dessa diferença é
pura não linearidade de Erlang — o mesmo volume reduzido, o mesmo tempo de atendimento, sem nenhuma
premissa comportamental dentro.

**O que fazer em vez disso.** Conduzir por resolução e pelo total de conversas, e exigir que qualquer
cifra de contenção diga qual das quatro definições ela é. Nunca apresentar economia de headcount obtida
multiplicando uma fila por uma proporção: uma fila é Erlang, e o erro não é conservador.

Confira: [`examples/01_the_containment_that_wasnt.py`](../examples/01_the_containment_that_wasnt.py) ·
[`svclab.containment`](../src/svclab/containment/README.md) ·
[`svclab.capacity`](../src/svclab/capacity/README.md)

## 2. O medidor substituto é um instrumento não qualificado

**A decisão.** Se a taxa de aprovação do painel de qualidade pode servir de evidência numa comparação de
duas políticas — que é exatamente o que o achado 1 pede a ela.

**O que o case dizia.** Nada. Uma rubrica de qualidade é tratada como leitura, não como instrumento, e
praticamente nunca é qualificada.

**O que a conta diz.** Lendo a mesma sessão duas vezes, cada avaliador contradiz seu próprio veredito
anterior em **17%** a **23%** delas, com kappa entre avaliadores de **0,54** a **0,57**. A taxa de
aprovação nas sessões idênticas vai de **0,3815** a **0,5683** dependendo de quem estava na escala — um
fator de **1,49** no número de capa. E erro de medição não adiciona ruído a uma comparação, ele a
**encolhe**, por uma forma fechada: um avaliador binário multiplica qualquer diferença pelo índice de
Youden. O índice deste painel é **0,6945**, então uma diferença real de 0,5459 é reportada como
**0,3791** — **69,45%** da diferença real, exatamente e não aproximadamente. Um instrumento cuja
sensibilidade e especificidade somam um reporta exatamente zero, por grande que seja a verdade; abaixo
disso, inverte o sinal. A conta chega em tamanho de amostra: **10,07** sessões por braço com um
instrumento perfeito, **25,03** com este.

O juiz automatizado concorda com o padrão declarado **0,8850** das vezes contra **0,8675** do melhor
avaliador humano — e validado contra um único avaliador pontua de 0,5450 a 0,7121 de kappa. O
contrapeso pertence à mesma frase: o painel como **comitê** vence o juiz, **0,7979** a **0,7826**.

**O que fazer em vez disso.** Rodar o estudo de medição antes da comparação, não depois de o resultado
ser contestado. Reportar o índice de Youden junto de todo delta de qualidade, e dimensionar o teste sobre
a diferença atenuada. Tratar "concordância com nossos revisores" como uma medição dos revisores.

Confira: [`examples/02_the_meter_that_was_noise.py`](../examples/02_the_meter_that_was_noise.py) ·
[`svclab.quality`](../src/svclab/quality/README.md)

## 3. Três defaults que ninguém foi chamado a aprovar

**A decisão.** Onde cortar o score do roteador, se clientes impacientes existem, e qual o tamanho de um
teste de política. Os três foram resolvidos por default e nenhum foi precificado.

**O que o case dizia.** Calibrar o classificador por acurácia; dimensionar por nível de serviço; comparar
duas políticas sobre os contatos que aconteceram.

**O que a conta diz.** Calibrar por acurácia em vez de por custo custa **7,51** horas humanas por mês — o
corte que maximiza acurácia é 0,45 e o que minimiza custo é 0,48, três centésimos. Um limiar por intenção
em vez de um para as cinco economiza outros **11,5552** segundos por contato, **102,1** horas no mesmo
mês. E a forma fechada de manual para esse corte é **12,5%** pior do que o número único que ela deveria
melhorar, porque assume uma probabilidade calibrada e este score é uma margem.

Na fila: o headcount prometido é alcançável, se **29,23%** dos clientes desistirem. Erlang C não tem nada
a dizer abaixo de oito atendentes nesta carga; Erlang A tem, e com seis atendentes a fila é estável com
29,23% de abandono e o resto a **89,45%** de ocupação. Os 5,51 atendentes do business case nunca foram
impossíveis — foram uma decisão não declarada de atender sete contatos em dez. Pior: uma fila
subdimensionada fabrica o próprio trabalho — contatos abandonados voltam, então a carga assenta num ponto
fixo **21,1%** acima da base e o abandono sobe a **38,45%**. Com onze atendentes o mesmo feedback soma
2,0%.

No teste: clientes repetem, então um teste por contato que acredita rodar a cinco por cento roda de fato
a **8,43%**, e detectar a diferença entre políticas exige **523** contatos por braço em vez de **405**.

**O que fazer em vez disso.** Calibrar limiares sobre o custo dos dois erros, por intenção, e calibrar o
score antes de aplicar qualquer forma fechada. Nunca citar nível de serviço de um modelo sem impaciência.
Dimensionar testes de política com o efeito de desenho dentro.

Confira: [`examples/03_three_numbers_nobody_priced.py`](../examples/03_three_numbers_nobody_priced.py) ·
[`svclab.routing`](../src/svclab/routing/README.md) ·
[`svclab.experiment`](../src/svclab/experiment/README.md)

## 4. Correlação entre pessoas não é correlação entre desfechos

**A decisão.** Se o alerta de agrupamento do achado 3 merece ação, e qual correlação estimar ao
dimensionar um teste.

**O que o case dizia.** Ou que clientes são independentes, ou — uma vez alertado — que a correlação entre
seus traços é o número a plugar.

**O que a conta diz.** A conta é construída duas vezes a partir do mesmo ruído, então o mundo
independente é um **controle** e não uma linha de base. Nada do que já foi publicado se move: o maior
movimento relativo entre oito métricas publicadas é **0,89%**. Isso é a precondição, não o resultado — é
o que faz todo o resto ser uma afirmação sobre dependência e sobre nada mais.

Uma correlação declarada em **0,2500** entre clientes mede 0,2535 na escala latente, 0,2463 na
dificuldade em si, e **0,0448** na resolução sobre a qual um teste realmente roda — um fator de **5,6**.
Uma resolução é uma moeda cujo viés é correlacionado, não uma moeda correlacionada. Então o efeito de
desenho medido é **1,0693**, um teste nominal de 5% roda de fato a **5,80%**, e o poder no dimensionamento
antigo é **0,7759** em vez de 0,8026: **2,7 pontos de poder, não 11.**

Duas consequências que merecem ir para qualquer painel. O KPI é cego ao que a operação sente: a parcela
de clientes com dois contatos falhados **nas duas** vezes sobe de 0,1219 para **0,1406** — 98 pessoas a
mais — enquanto a taxa de resolução se move 0,0002, porque uma taxa é ponderada por contato e uma
reclamação é ponderada por cliente. E a correção que a maioria dos analistas busca, a média das médias
por cliente, custa **13,3%** de erro padrão **no mundo independente, onde não há nada a corrigir**,
contra a contribuição própria da correlação de **1,1%**.

**O que fazer em vez disso.** Estimar a correlação do desfecho que se está testando, nunca a do traço que
se acredita conduzi-lo. Reportar uma medida de falha ponderada por cliente ao lado da taxa ponderada por
contato. Manter um mundo de controle em vez de uma história melhor.

Confira: [`examples/04_the_customer_who_was_a_label.py`](../examples/04_the_customer_who_was_a_label.py) ·
[`svclab.population`](../src/svclab/population/README.md)

## 5. O volume vem de pessoas que a média esconde

**A decisão.** Quem a operação atende de fato, e portanto onde vale a pena implantar uma correção.

**O que o case dizia.** Uma média de contatos por cliente, e a premissa implícita de que os clientes mais
ativos são ativos por acaso.

**O que a conta diz.** Os contatos idênticos reagrupados numa distribuição realista de taxa, com os
usuários intensos correlacionados aos difíceis, mantêm **cada cifra por contato idêntica, bit a bit**. A
média de contatos por cliente sobe 23%. O tamanho **efetivo** de cluster — a média ponderada por
tamanho, que é a quantidade de que se calcula um efeito de desenho — sobe **78%**, de **3,23** para
**5,75**. Concentração é uma afirmação sobre a variância dos tamanhos de cluster, e a média quase não a
registra.

O que traz o alerta de volta: o efeito de desenho é **1,2246**, e um teste nominal de 5% aqui roda de
fato a **7,65%**. O custo concentra mais rápido que o volume: usuários intensos são 58,1% dos contatos
mas **61,2%** das horas, uma separação de **3,1** pontos onde o controle de taxas iguais mostra 0,3 —
usuários intensos não apenas contatam mais, cada contato deles custa mais. A taxa de resolução cai
**1,53** ponto sem mudança alguma de política, porque a dificuldade média por contato sobe **9,9%**
quando os clientes difíceis enviam mais contatos cada. E a estimativa central da onda 1 perde um terço da
precisão: **+66%** de erro relativo, nos mesmos contatos, mesmos braços, mesmo bot.

**O que fazer em vez disso.** Segmentar por frequência de contato antes de custear qualquer correção, e
reportar horas por segmento em vez de volume por segmento. Usar a média de cluster ponderada por tamanho
em qualquer efeito de desenho. Tratar toda métrica por cliente como condicional a uma definição de
"cliente" que precisa estar declarada.

Confira: [`examples/05_the_frequent_caller.py`](../examples/05_the_frequent_caller.py) ·
[`svclab.concentration`](../src/svclab/concentration/README.md)

## 6. A cauda é curta aqui, e isso é o achado

**A decisão.** Quanto trabalho futuro um contato não resolvido compromete, e qual alavanca o reduz.

**O que o case dizia.** Que um contato contido está encerrado. Toda onda anterior permitia exatamente um
retorno e apontava isso como a razão pela qual suas cifras subestimavam a fila.

**O que a conta diz.** Rodando a cadeia até o fim declarado, **720** contatos precisam de uma terceira
tentativa e sete de uma quarta: **4,88%** mais horas humanas, resolução eventual de 0,8067 para
**0,8291**. Pequeno — e a forma fechada diz por quê. Um contato reabre apenas se o cliente volta **e** o
humano falhou de novo, então as sessões que um contato não resolvido gera são uma série geométrica no
**produto**. Aqui esse produto é **0,0429** e a série vale **1,0448** sessões, por quantas tentativas se
permitam. Truncar em um retorno custou **0,18%**; a uma taxa de reabertura de 0,5 teria custado um terço.

Ou seja: a cauda geométrica não é uma propriedade de clientes que voltam — é uma propriedade de uma
operação que continua falhando com eles, e a alavanca é a resolução no primeiro contato humano, não a
taxa de retorno do cliente. A cadeia também cobra da política que a contenção mais premiou: horas extras
de **5,74%** contra 3,86% da fila humana. E produz um **terceiro** ranking, o mais inclinado até agora —
dias até a resolução **1,31** contra **0,16**, com **40,5%** das resoluções eventuais da política
agressiva chegando numa tentativa posterior.

**O que fazer em vez disso.** Medir a taxa de reabertura primeiro, e só então decidir se vale construir
um modelo de cauda: na taxa desta conta, um retorno captura a fila a menos de 0,18%, e a 0,5 ele perde um
terço. Pôr dias até a resolução ao lado da taxa — uma taxa não tem tempo dentro, e três dias não são erro
de arredondamento, são a reclamação.

Confira: [`examples/06_the_contact_that_came_back_twice.py`](../examples/06_the_contact_that_came_back_twice.py) ·
[`svclab.chain`](../src/svclab/chain/README.md)

## 7. Nomeie a restrição que decidiu o headcount

**A decisão.** Como um número de dimensionamento é produzido: batendo uma meta e reportando o resto, ou
declarando todos os tetos e dizendo qual deles decidiu.

**O que o case dizia.** Dimensione por nível de serviço. Ocupação e abandono saem como resultados — que
foi como uma fila acabou chamada de "perfeitamente estável" com seis atendentes enquanto um terço dos
clientes ia embora.

**O que a conta diz.** Um teto de ocupação perseguido sozinho é satisfeito por **subdimensionamento**:
oito atendentes mantêm a ocupação em **0,8121** enquanto atendem **17,51%** dentro da meta e perdem
**14,34%** dos clientes, porque os clientes que abandonam são o que mantém a ocupação baixa. Uma meta de
aparência humana premia uma fila por perder gente. O nível de serviço e o teto de abandono chegam aos
mesmos onze atendentes por rotas independentes e passam a restringir juntos. Seis atendentes falham nos
três: **estabilidade não é um plano.** A conta de guardanapo — carga dividida pelo teto de ocupação — dá
9 onde a fila precisa de 11, o erro da onda 1 em nova fantasia.

Escala corta nos dois sentidos. Atendentes por erlang cai de **3,00** em um erlang para **1,18** em
quatrocentos, uma queda de **61%**, que é o argumento da consolidação. Mas a restrição ativa migra do
nível de serviço para o teto de ocupação por volta de 45 erlangs: dali em diante a fila é limitada pela
tolerância do atendente e não pela do cliente, e essas duas se negociam com pessoas diferentes. E no
plano escolhido a margem mais fina é **+0,0176** no abandono — "todas as restrições atendidas" e "uma
ausência de estourar" são a mesma frase.

**O que fazer em vez disso.** Escrever os tetos antes de calcular um headcount, e publicar qual deles
restringiu mais a margem de cada um. Nunca apresentar meta de ocupação sem nível de serviço e teto de
abandono ao lado.

Confira: [`examples/07_the_constraint_nobody_declared.py`](../examples/07_the_constraint_nobody_declared.py) ·
[`svclab.planning`](../src/svclab/planning/README.md)

## 8. Contagem de atendentes não é folha

**A decisão.** Quantas pessoas financiar, distinto de quantos atendentes a fila precisa — e se afrouxar
uma meta de ocupação se paga.

**O que o case dizia.** Um headcount, mais uma folga que alguém escolheu.

**O que a conta diz.** O prêmio não é uma folga, é a solução de um laço que nenhum modelo de
dimensionamento contém: ocupação eleva atrito, atrito esvazia cadeiras, cadeira vazia não é atendente,
menos atendentes elevam a ocupação. Onze atendentes custam doze pessoas; em cem erlangs **119**
atendentes custam **130**, com **7,13** cadeiras vazias e **9,51** pessoas em rampa a qualquer momento. O
prêmio **não é monótono** no tamanho da fila, porque aritmética inteira domina uma fila pequena e atrito
domina uma grande.

O que precifica a eficiência que o achado 7 celebrou: a fila grande que precisava de apenas 1,18
atendente por erlang perde **36,1%** do quadro por ano e contrata 57 pessoas por ano para ficar parada. A
taxa de câmbio é **1,01** — vinte e sete pessoas a mais compram **27,39** contratações a menos por ano.
Lida na moeda do próprio repositório, uma saída desperdiça **2,30** pessoa-mês, então um atendente extra
custa 12 pessoa-mês por ano e devolve 2,33: uma razão de **0,19**. Nos livros da própria fila, afrouxar a
ocupação perde por um fator de cinco — o que não a torna errada. Significa que o caso repousa
inteiramente sobre o que uma saída custa **fora** da fila, e nomear esse número ausente é a entrega.

Duas fronteiras. Na fila pequena não há troca alguma — todo teto de 0,90 a 0,70 precisa das mesmas doze
pessoas, e a taxa volta como não-número em vez de zero, porque zero diria que a troca era grátis. E o
laço não dispara: a inclinação do atrito teria de ser **12,5** vezes mais íngreme antes de a folha do
plano colapsar, embora apenas cinco vezes duas pessoas abaixo dele — **robustez é uma propriedade da
folha, não só da curva.**

**O que fazer em vez disso.** Financiar uma folha, não uma contagem de atendentes, e mostrar o ponto fixo
em vez de uma margem. Antes de defender um teto de ocupação menor, obter o custo de uma saída fora da
fila nomeado por quem é dono dele — nos livros da fila esse argumento perde. E ler a questão da espiral
como uma questão de financiamento: o plano é robusto, duas pessoas abaixo dele não é.

Confira: [`examples/08_the_payroll_behind_the_plan.py`](../examples/08_the_payroll_behind_the_plan.py) ·
[`svclab.workforce`](../src/svclab/workforce/README.md)

## 9. A fórmula estava sem um termo, e todo mundo teria calibrado em vez disso

**A decisão.** Onde gastar a próxima semana de tempo analítico quando uma regra de decisão rende menos do
que deveria — e, mais amplamente, se corrigir o insumo de um modelo ou o modelo.

**O que o case dizia.** O achado 3 diagnosticou a própria fórmula do limiar: ela quer uma probabilidade e
o score do classificador não é uma, então **calibre o score**. Essa era a conclusão do próprio
repositório e ficou sem contestação por seis ondas.

**O que a conta diz.** O diagnóstico estava meio certo e apontava para a metade mais barata. Calibrar o
score é trabalho real com retorno real — o erro de calibração da margem crua é **0,1618** contra
**0,0061** de um controle perfeitamente calibrado, **26,68** vezes, e no bin em que o score diz
**0,6502**, **0,9078** dos rótulos estão certos. Calibrar corta a penalidade da fórmula **3,59** vezes, de
**17,04%** para **4,74%**.

Mas entregue à fórmula a probabilidade que o gerador realmente usa — onde não resta calibração a fazer — e
ela segue **7,33%** fora do ótimo varrido. Então o insumo nunca foi o problema inteiro. A fórmula
precifica um rótulo errado e uma postergação e trata um rótulo **certo** como **gratuito**, quando um
contato corretamente rotulado que o bot resolve *economiza* os segundos humanos que ele teria consumido.
Esse termo omitido é todo o argumento para implantar um bot, e ele corre no sentido oposto ao custo do
erro: **142,68** segundos na intenção mais barata contra **23,32** na mais cara. Então a regra está mais
errada exatamente onde o bot é mais útil — exige 0,6667 de confiança onde **0,1974** basta.

Carregue o termo e a penalidade cai para **1,96%**. O que dá o resultado que decide a semana: **342,14**
segundos usando a fórmula corrigida sobre o score *não calibrado* vencem **367,54** usando a fórmula
original sobre o *perfeito*. Corrigir o modelo venceu corrigir o insumo por cerca de quatro para um.

Duas outras correções caem no mesmo lugar. Um limiar ajustado num período custa **1,5076** segundo por
contato mais no seguinte do que o melhor daquele próprio período — **0,45%** da conta, **13,05%** da
economia que o achado 3 publicou — e concentra onde o erro é caro e a amostra é rala. Ainda assim os
cortes se movem muito mais que o custo, de **0,10** para **0,24** na maior intenção por um décimo de
segundo: **a curva de custo é plana perto do ótimo, então o custo foi aprendido e o corte não.** E chavear
a regra no rótulo que um roteador realmente consegue ler — o palpite do classificador em vez da verdade —
*melhora* o resultado, **11,9210** segundos economizados contra **10,9487**, porque um rótulo errado é o
evento de que o custo é feito, então o rótulo reportado carrega informação sobre o erro e o verdadeiro não
carrega nenhuma.

**O que fazer em vez disso.** Antes de calibrar qualquer coisa, escreva todos os desfechos que a regra de
decisão precifica e confira se nenhum está sendo assumido como gratuito — o termo omitido costuma ser o
benefício, porque benefício é a parte pela qual ninguém é cobrado. Reporte o custo no limiar escolhido,
não o limiar. E prefira a regra que seu sistema consegue executar; ela pode ser a melhor regra, não o
compromisso.

Confira: [`examples/09_the_threshold_fitted_on_the_answer.py`](../examples/09_the_threshold_fitted_on_the_answer.py) ·
[`svclab.calibration`](../src/svclab/calibration/README.md)

## O que nada disso diz

Não diz que contenção é inútil — diz que contenção não consegue ranquear resolução, o que é uma afirmação
mais estreita e mais difícil. Não diz que a automação foi um erro: a fila ainda devolve três atendentes,
e três atendentes são reais. Diz que o case que prometeu 8,49 estava errado por um fator, em três lugares
identificáveis, cada um deles mensurável antes de o dinheiro ser comprometido.

E não diz nada sobre a operação real de ninguém. Não há dado de empregador, cliente, consumidor,
fornecedor ou plataforma em qualquer parte deste repositório, e também não há modelo de linguagem nele —
ver [`DISCLAIMER.md`](../DISCLAIMER.md) para ambos, e [`ROADMAP.md`](ROADMAP.md) para o que está
deliberadamente ausente, o que segue aberto, e os defeitos registrados em vez de silenciosamente
corrigidos.
