# service-automation

*[English](README.md)*

**Taxa de contenção é o número pelo qual toda automação de atendimento é julgada, e é o cálculo
correto da quantidade errada.**

Ela conta como sucesso sessões que o cliente abandonou. Conta contatos que o cliente teria resolvido
sozinho. Ignora a segunda conversa que um contato não resolvido produz amanhã. E o business case de
headcount construído sobre ela multiplica uma fila por uma proporção, quando uma fila é Erlang.

Este repositório é esse exercício, com os bots realmente rodando. O `svclab` é um pacote Python que
contém uma central de atendimento com semente, uma política de bot implantável que a encontra, as
quatro leituras defensáveis do que esse bot conteve, e a aritmética de fila que precifica o que a
operação recebeu. Toda ferramenta aqui **se recusa a devolver um número quando a premissa por trás dele
não vale** — uma taxa de desvio sem braço de controle volta com um motivo anexado em vez de como uma
cifra que parece evidência.

Toda tabela vem do `svclab.synth`, um gerador com semente cujos parâmetros estão escritos, inclusive as
duas colunas que nenhuma central real tem: **o quão difícil cada contato realmente era, e se o cliente
teria chegado lá sem ajuda alguma.** Essas colunas são a razão pela qual as afirmações aqui podem ser
conferidas contra a verdade em vez de contra outra taxa de contenção. Nenhum dado de empregador,
cliente, consumidor, fornecedor ou plataforma é usado em qualquer parte, e não existe modelo de
linguagem no repositório — ver [`DISCLAIMER.md`](DISCLAIMER.md).

## O achado, numa tabela

Quatro políticas de bot encontram os mesmos 31.802 contatos. Ranqueadas por contenção, melhor primeiro:

| Política | Contenção de sessão | Contenção necessária | Taxa de resolução | Recontatos por contato | Horas humanas |
| --- | --- | --- | --- | --- | --- |
| patient | **0,8169** | **0,2187** | **0,4476** | **0,3211** | 2.316,78 |
| three-turns | 0,6065 | 0,2145 | 0,6355 | 0,2099 | 2.730,43 |
| guarded | 0,4886 | 0,2029 | **0,7271** | 0,1410 | 2.861,54 |
| human-only | 0,0000 | 0,0000 | 0,9305 | 0,0436 | 3.645,64 |

**O ranking por contenção é o inverso exato do ranking por resolução.** A política que parece melhor no
KPI resolve 44,76% dos contatos contra 72,71% da que parece pior, e faz isso abandonando um terço dos
clientes — que depois voltam. Todas as quatro definições de contenção, inclusive a mais estrita,
preferem ela.

Então a resposta não é um numerador mais estrito. Contenção é uma afirmação sobre o que o bot fez;
resolução é uma afirmação sobre o que aconteceu com o cliente. **Nenhuma definição da primeira consegue
ranquear a segunda.**

Mais três resultados da mesma conta:

- **28% da contenção citada nunca chegou à fila.** Medido contra clientes que nunca encontraram o bot:
  o `three-turns` citou 0,6065 e desviou 0,4377 por contato. Quanto mais uma política contém, mais ela
  superestima — o `patient` citou 0,8169 e desviou 0,5370.
- **A automação que conteve mais elevou o total de conversas em 26,6%**, de 33.190 sessões para 42.015.
  Um contato contido que volta era um contato postergado.
- **O resíduo é 1,58 vez mais difícil do que o que o bot resolveu.** O volume pela fila humana caiu 39%
  e o tempo médio de atendimento do que sobrou subiu 17%, porque um bot não tira uma amostra aleatória
  de uma fila. E **21,98% do que o bot resolveu teria se resolvido sozinho.**

## E o business case de headcount foi construído sobre a primeira coluna

| Passo | Atendentes | Movimento |
| --- | --- | --- |
| a promessa, como multiplicação | 5,51 | — |
| só volume, através de Erlang | 7,00 | **+1,49** |
| mais o resíduo mais difícil | 8,00 | **+1,00** |
| mais o fluxo de recontatos | 11,00 | **+3,00** |

O case prometeu **8,49 atendentes** de economia contra uma linha-base de 14. A fila devolve **3** — a
promessa superestima em **2,83 vezes**. Três efeitos se compõem, e o maior é o fluxo de recontatos, que
é o que nenhum business case modela: um modelo que conta sessões contidas não tem como representar um
contato chegando duas vezes.

Os outros dois são pelo menos discutíveis a partir do modelo que foi usado. **1,49 atendente da
diferença é não-linearidade pura** — Erlang sobre o mesmo volume reduzido com o mesmo tempo de
atendimento, sem nenhuma premissa comportamental.

## E o medidor com que você o substituiria nunca foi qualificado

A conclusão da onda 1 é julgar uma política por resolução e não por contenção. Uma operação mede isso
avaliando sessões — então o painel de qualidade se torna o instrumento, e **um painel é um instrumento
de medição que se qualifica antes de usar.** Isso é prática comum para um paquímetro e praticamente
inédito para uma régua de qualidade.

- **O painel não concorda consigo mesmo.** Lendo a mesma sessão duas vezes, cada avaliador contradiz o
  próprio veredito anterior em **17% a 23%** delas. Entre avaliadores, a concordância bruta é de 76% a
  78% com kappa de **0,54 a 0,57** — e a taxa de aprovação reportada nas sessões idênticas vai de
  **0,3815 a 0,5683** dependendo de quem estava na escala. Um fator de 1,49 no número principal.
- **E erro de medição não adiciona ruído a uma comparação, ele a encolhe — por um fator com forma
  fechada.** Um avaliador binário transforma uma taxa real `p` em `p·se + (1−p)·(1−sp)`, então uma
  diferença entre dois grupos sai multiplicada por `se + sp − 1`: o índice de Youden, **em direção a
  zero, sempre**. O gap real entre os braços é de 0,5459 sessões aceitáveis. O índice deste painel é
  0,6945, então ele reporta **0,3791 — 69,45% da diferença real.** Exatamente, não aproximadamente.
- **Um instrumento cuja sensibilidade mais especificidade soma um reporta exatamente zero**, por maior
  que seja a diferença real. Abaixo disso ele inverte o sinal: não é ruidoso, é invertido, e o
  relatório diz o oposto com a mesma confiança.
- **Atenuação se paga em tamanho de amostra.** Detectar esse gap leva 10,07 sessões por braço com um
  instrumento perfeito e **25,03** com este painel — inflação de 2,49×, pior que as 2,07 que o quadrado
  do índice de Youden prevê, porque as taxas atenuadas também ficam mais perto de 0,5, onde a variância
  de uma proporção é maior. Tamanho de amostra é a alavanca que todo mundo puxa *antes* de verificar se
  o instrumento funciona.
- **E o juiz automático é mais acurado que qualquer avaliador individual, e seria validado contra
  eles.** Ele concorda com o padrão declarado 0,8850 das vezes contra os 0,8675 do melhor avaliador.
  Validado contra um avaliador, ele tira de **0,5450 a 0,7121** de kappa — dispersão de 0,17 decidida
  por qual semana era. "Concordância com nossos revisores humanos" é uma medição dos revisores tanto
  quanto do juiz. O contrapeso honesto, na mesma frase: o painel como **comitê** ganha do juiz, 0,7979
  contra 0,7826 — fazer a média de três avaliadores moderados recupera a maior parte do que cada um
  perde, o que é argumento a favor de um painel e não de nenhum de seus membros.

## E três números que as duas primeiras ondas nunca precificaram

A política `guarded` da onda 1 recusou dois intents com base num rótulo e nunca perguntou quanto valia o
rótulo. Toda cifra de capacidade acima assume que ninguém desiste de esperar. E as duas ondas compararam
políticas na conta inteira, como se contatos fossem independentes. Três decisões tomadas por omissão,
precificadas:

- **Ajustar o limiar do roteador por acurácia em vez de por custo custa 7,51 horas-humano por mês.** O
  corte de máxima acurácia é 0,45 e o de mínimo custo é 0,48 — três centésimos, 0,8506 segundos por
  contato, sobre 31.802 contatos. Varrer um limiar por intent em vez de um único para os cinco economiza
  mais **11,5552 segundos por contato**: 102,1 horas no mesmo mês, porque um limiar único é um
  compromisso entre cinco intents que queriam respostas muito diferentes.
- **E a forma fechada desse limiar, aplicada a este score, é 12,5% pior que o número único que ela
  deveria melhorar.** Postergar abaixo de `1 − custo_de_postergar / custo_de_erro` é exatamente ótimo num
  score que *é* a probabilidade de o rótulo estar certo. Este score é uma margem, então o **ordenamento**
  dos cinco intents que a fórmula produz sobrevive intacto e os **níveis** não — ela posterga 23.304 de
  31.802 contatos para evitar 2.414 erros de roteamento. Calibração é o passo que falta, e a fórmula o
  assume em silêncio.
- **O headcount prometido é alcançável, se 29% dos clientes desistirem.** Erlang C não tem nada a dizer
  abaixo de oito atendentes nesta carga: a fila cresce sem limite, e o nível de serviço é reportado como
  zero porque não existe espera a reportar. Erlang A tem resposta — com **seis** atendentes a fila é
  perfeitamente estável, com **29,23% de abandono** e os atendentes restantes a **89,45% de ocupação**.
  Os 5,51 atendentes do business case nunca foram impossíveis. Eram uma decisão não declarada de atender
  sete contatos em dez.
- **E uma fila subdimensionada fabrica o próprio trabalho extra.** Contatos abandonados voltam e o
  retorno é carga, então a carga estabilizada é um ponto fixo: 9,1886 erlangs contra uma base de 7,5845,
  o que são **+21,1% de carga e o abandono subindo de 29,23% para 38,45%**. Com onze atendentes a mesma
  realimentação acrescenta 2,0% e estabiliza em 3,56% — erro de arredondamento no dimensionamento
  adequado, que é o argumento a favor dos onze atendentes dito na moeda em que o abandono é pago.
- **Um teste de duas políticas que acredita rodar a cinco por cento roda de fato a 8,43%.** Clientes
  repetem, logo contatos são agrupados, e um teste por contato divide por um erro padrão pequeno demais
  pela raiz do efeito de desenho. Detectar a diferença de 0,0916 da onda 1 exige 405 contatos por braço
  se os contatos forem independentes e **523** a uma correlação de 0,30. A metade honesta deste
  resultado: **a correlação medida neste gerador é aproximadamente zero**, porque todo traço é sorteado
  por contato. Isso é uma limitação do simulador, publicada como tal — as correlações dos cenários acima
  são declaradas, não medidas.

## E o cliente, em tudo isso, era um rótulo

Toda cifra acima foi medida num gerador que sorteia cada traço por contato. Um id de cliente é,
portanto, um rótulo numa linha e não alguém com histórico — e é por isso que a onda 3, ao ir medir o
agrupamento sobre o qual ela mesma havia alertado, encontrou correlação intraclasse de
aproximadamente **zero** e teve de precificar correlações *declaradas*.

Então a conta agora existe duas vezes. O mundo **independente** é o de cima. O mundo
**correlacionado** dá a cada cliente uma dificuldade e uma paciência próprias, e é construído a partir
do **ruído idêntico**: o percentil de um traço é misturado ao do seu cliente por uma cópula gaussiana,
que deixa toda distribuição marginal exatamente onde estava e muda apenas a dependência entre dois
contatos de uma mesma pessoa. O mundo independente é, assim, um **controle**, não uma linha de base.

- **Nada do que foi publicado se move.** Contenção de sessão 0,6065 contra 0,6046, resolução 0,6355
  contra 0,6357, e **duas horas humanas em 2.730**. O maior movimento relativo entre oito métricas
  publicadas é **0,89%**. Isso é a pré-condição, não o resultado: é o que faz de tudo abaixo uma
  afirmação sobre dependência e sobre mais nada. **Uma correlação não muda o que aconteceu — muda o
  que se pode concluir disso.**
- **Correlação entre pessoas não é correlação entre desfechos, e a diferença é um fator de 5,6.**
  Declarada em **0,2500** entre clientes, a correlação mede 0,2535 na escala latente, 0,2463 na própria
  dificuldade e **0,0448 na resolução em que um teste de fato roda**. Uma resolução é uma moeda cujo
  viés é correlacionado, não uma moeda correlacionada, e a uma taxa de resolução perto de 0,64 a moeda
  é a maior parte da variância. A regra que segue é curta: **estime a correlação do desfecho que você
  está testando, nunca a do traço que você acredita que o dirige.**
- **O que torna o alarme da própria onda 3 quatro vezes alto demais nesta conta.** O efeito de desenho
  medido é **1,0693** — 6,93% mais amostra, e um teste nominal de 5% rodando de fato a **5,80%** —
  contra os 1,2891 e 8,43% que a onda 3 precificou a um declarado 0,30. No dimensionamento da onda 3,
  de 405 contatos por braço, o poder é 0,8026 se os contatos forem independentes, **0,7759** no efeito
  medido e 0,6970 no declarado: **2,7 pontos de poder, não 11.** O efeito é real, mensurável e modesto,
  porque um efeito de desenho é produto de dois fatores e os grupos desta conta têm em média dois
  contatos.
- **E o KPI é cego para o que a operação sente.** Entre clientes com exatamente dois contatos, a
  fração falhada nas **duas** vezes sobe de 0,1219 para **0,1406** — 98 pessoas a mais, no mesmo
  volume, enquanto a taxa de resolução se move 0,0002. Uma taxa de resolução é ponderada por contato;
  uma reclamação, um churn e um ofício de regulador são ponderados por cliente. As duas coincidem
  exatamente quando um cliente é um rótulo.
- **E a correção que a maioria usa custa doze vezes o erro que corrige.** Tirar a média da média
  de cada cliente infla o erro padrão em **13,3% no mundo independente** — onde não há correlação
  alguma a corrigir — porque pesar igualmente grupos de tamanhos diferentes descarta informação. A
  contribuição da própria correlação para o mesmo erro padrão é de **1,1%**. A linha do mundo
  independente é a única razão pela qual isso fica visível, e é o argumento a favor de manter um mundo
  de controle em vez de uma história melhor.

## E o cliente que mais contatava era movimentado por acaso

O mundo acima dá a cada cliente uma dificuldade e uma paciência próprias, e deixa a **taxa** dele de
lado: cada contato ainda escolhe um cliente uniformemente, então as contagens de contato são Poisson
com média abaixo de dois e o cliente mais movimentado da conta é movimentado por sorte. Uma conta real
quebra isso duas vezes — o volume dela é **concentrado**, e a minoria que o gera **não é aleatória**,
porque quem mais contata é, em média, quem tem os problemas mais difíceis.

Então os mesmos 31.802 contatos são reagrupados em clientes cuja taxa de contato é log-normal e
correlacionada com a própria dificuldade a um declarado 0,40. O reagrupamento reaproveita o uniforme
que escolheu o cliente originalmente e nunca cruza um braço, então **toda cifra por contato permanece
idêntica, bit a bit** — verificada exatamente, não por tolerância. O controle é o mesmo reagrupamento
com **taxas iguais**, porque reatribuir contatos entre os clientes que a conta de fato viu já aumenta
os grupos por si só.

- **O mesmo volume chega de 10.640 pessoas em vez de 13.087, e a média quase não percebe.** Os
  contatos médios por cliente sobem 23%, de 2,43 para 2,99. O tamanho **efetivo** de grupo — a média
  ponderada por tamanho, que é a quantidade de que um efeito de desenho é calculado — sobe **78%**, de
  3,23 para **5,75**. Concentração é uma afirmação sobre a variância dos tamanhos de grupo.
- **E é aqui que o alarme da onda 3 volta: o efeito de desenho é 1,2246, ou 95% dos 1,2891 que a onda
  3 declarou como seu caso sério.** A onda 4 mediu 1,0693 e chamou aquele alarme de quatro vezes alto
  demais — num mundo em que todos contatam na mesma taxa, o que ela havia assumido e não escolhido.
  Duas premissas erradas em direções opostas cujo produto ficou perto do certo — e um teste nominal de
  5% aqui roda de fato a **7,65%**.
- **O custo se concentra mais rápido que o volume.** Usuários pesados — quatro contatos ou mais no
  mês, uma contagem declarada e não um decil — são 2.643 pessoas no controle, e geram 38,75% dos
  contatos, 38,97% das falhas e 39,01% das horas humanas: um único número, porque ser pesado não diz
  nada sobre ser difícil. Concentrado, 2.885 pessoas geram **58,1% do volume, 59,9% das falhas e 61,2%
  das horas**. A separação é o achado — volume e horas diferem em 0,3 ponto no controle e em **3,1
  pontos** aqui, porque usuários pesados não apenas contatam mais: cada contato deles custa mais. E a
  população falhada três vezes ou mais vai de 794 clientes para **1.305**.
- **A taxa de resolução cai 1,53 ponto sem mudança nenhuma de política.** A distribuição de dificuldade
  **por cliente** está inalterada; a **por contato** não está, porque os clientes difíceis agora mandam
  mais contatos cada um. A dificuldade média por contato sobe 9,9%. A mistura de dificuldade que a fila
  recebe é propriedade de quem liga, não só de quem essas pessoas são — e nenhum business case modela
  isso.
- **E a estimativa central da onda 1 perde um terço da precisão.** Deflexão por cliente não é
  comparável entre mundos que discordam sobre quantos clientes existem, então a alta de 1,5484 para
  1,7845 é um denominador e não um achado. O que é comparável é o erro: **+66% relativo, intervalo 91%
  mais largo**, sobre os mesmos contatos, os mesmos braços e o mesmo bot. Um número por cliente só é
  tão estável quanto a premissa sobre o que é um cliente.

## Módulos

| Módulo | O que decide |
| --- | --- |
| [`svclab.synth`](src/svclab/synth/README.md) | Contra quais dados testar sem tocar numa operação real, e quais duas colunas tornam o resto verificável. |
| [`svclab.bot`](src/svclab/bot/README.md) | Por quanto tempo o bot deve tentar, o que deve se recusar a tentar, e se a diferença entre duas políticas é a política — o que exige os mesmos contatos nos dois lados e uma linha entre o que uma política pode ver e o que o mundo sabe. |
| [`svclab.containment`](src/svclab/containment/README.md) | Qual número de contenção está sendo mostrado, entre os quatro que estão todos corretos; quanto dele chegou à fila, contra clientes que nunca encontraram o bot; e quais contatos o bot ficou. |
| [`svclab.capacity`](src/svclab/capacity/README.md) | Quantos atendentes a fila precisa no seu nível de serviço, quantos a taxa de contenção prometeu, e de onde veio a diferença. |
| [`svclab.quality`](src/svclab/quality/README.md) | Se a nota de qualidade é uma medição ou um hábito, quanto de uma diferença real este painel vai reportar, e o que um instrumento não qualificado custa em sessões. |
| [`svclab.routing`](src/svclab/routing/README.md) | Onde cortar o score do classificador quando os dois erros custam números diferentes de segundos humanos, o que a forma fechada desse corte assume sobre o score, e por qual objetivo o corte está sendo ajustado. |
| [`svclab.experiment`](src/svclab/experiment/README.md) | Quantos contatos um teste de duas políticas precisa quando clientes repetem, e a qual nível de significância um teste que ignora o agrupamento roda de fato. |
| [`svclab.population`](src/svclab/population/README.md) | Quanto valia a premissa de independência: quanto de uma correlação entre clientes sobrevive até o desfecho em que um teste roda, o que a parte sobrevivente custa, e o que custa a correção usual para ela. |
| [`svclab.concentration`](src/svclab/concentration/README.md) | O que o agrupamento decide quando os clientes não contatam todos igualmente: quão desiguais os grupos realmente são, qual dos dois tamanhos de grupo entra num efeito de desenho, quem paga pelas falhas, e quanta precisão uma estimativa por cliente perde. |

Todo README de módulo é bilíngue e traz uma seção **Premissas e limitações**, porque uma cifra sem suas
premissas não é um resultado.

## Exemplos

| Exemplo | O que mostra |
| --- | --- |
| [`examples/01_the_containment_that_wasnt.py`](examples/01_the_containment_that_wasnt.py) | Quatro políticas numa conta: as quatro taxas de contenção e o ranking que cada uma produz, quais contatos o bot ficou, o que a fila recebeu contra o que foi afirmado, e o business case de headcount decomposto nos seus três erros. |
| [`examples/02_the_meter_that_was_noise.py`](examples/02_the_meter_that_was_noise.py) | O estudo do instrumento rodado antes da comparação: repetibilidade, reprodutibilidade, viés contra um padrão declarado, o fator exato pelo qual o painel encolhe toda diferença, o que isso custa em sessões, e contra o que um juiz automático seria validado. |
| [`examples/03_three_numbers_nobody_priced.py`](examples/03_three_numbers_nobody_priced.py) | Os três padrões precificados: o limiar de roteamento varrido contra os dois objetivos e contra sua forma fechada, a fila com impaciência e com a realimentação de repetições resolvida até o ponto fixo, e o que custa um teste real de duas políticas quando clientes podem repetir. |
| [`examples/04_the_customer_who_was_a_label.py`](examples/04_the_customer_who_was_a_label.py) | A mesma conta construída duas vezes a partir do mesmo ruído: se a correlação move algo já publicado, quanto dela chega ao desfecho, o que custa a uma comparação, quantas pessoas são falhadas duas vezes, e o que três erros padrão diferentes dizem sobre uma mesma diferença. |
| [`examples/05_the_frequent_caller.py`](examples/05_the_frequent_caller.py) | Os mesmos contatos reagrupados em clientes que contatam em taxas diferentes, com os pesados correlacionados aos difíceis: a forma dos grupos, o efeito de desenho que retorna, quem paga por ele, e o que custa à precisão da estimativa da onda 1. |

## Instalar e rodar

```bash
python -m pip install -e ".[dev]"
make check       # lint, tipos e a suíte rápida - o que libera um push
make check-all   # o acima mais toda cifra documentada re-derivada
python examples/01_the_containment_that_wasnt.py
python examples/02_the_meter_that_was_noise.py
python examples/03_three_numbers_nobody_priced.py
python examples/04_the_customer_who_was_a_label.py
python examples/05_the_frequent_caller.py
```

## Como as afirmações são mantidas honestas

**273 testes, 100% de cobertura de linhas e de ramos.** 228 deles rodam em segundos e liberam cada push.
Os 45 restantes re-derivam, a partir do gerador, toda cifra citada em todo README deste repositório, e
rodam o script de exemplo. Uma mudança que mova um número publicado quebra o build em vez de deixar o
texto silenciosamente errado.

**Um bot é função determinística do dataset.** Tudo aleatório é sorteado uma vez por contato antes de
qualquer bot existir, então duas políticas encontram os contatos idênticos e qualquer diferença entre
elas é a política. Rodar uma política duas vezes devolve o mesmo quadro, e um teste assere isso.

**Uma política não consegue ver a resposta.** `difficulty`, `would_self_serve` e `human_seconds` são
verdade, e um teste analisa o `svclab.bot.policy` e falha se o código alcançar qualquer uma delas. Todo
business case de automação já escrito foi construído por alguém que podia ver a coluna de resultado; o
motivo pelo qual esses cases estão errados é que o bot não podia.

**Verificação contra formas fechadas e casos de controle, nunca contra a saída do próprio código.** As
taxas de contenção são conferidas em dez sessões cujos quatro numeradores se contam nos dedos; o
estimador de desvio contra dois braços cuja diferença é exatamente um contato por cliente com
dispersão zero; Erlang C contra a forma fechada que o faz igualar a carga oferecida com um atendente, e
Erlang B contra `a / (1 + a)`; e a busca de dimensionamento contra sua própria definição, asserindo que
um atendente menos não atinge o alvo.

**Todo sorteio é uma transformada inversa do stream uniforme, nunca um amostrador por rejeição**, de
modo que a posição no stream depende de quantos valores são pedidos e não de qual versão de biblioteca
responde. Essa regra é verificada contra o código-fonte, porque um repositório irmão publicou cifras
que valiam numa máquina e mudavam numa instalação limpa.

**E defeitos são registrados em vez de corrigidos em silêncio.** Vinte e seis até aqui, em
[`docs/ROADMAP.md`](docs/ROADMAP.md), cada um deles achado conectando os módulos, por um caso de
controle ou verificando uma frase — nenhum lendo código. Dois valem a leitura. A sessão original cobrava
um recontato como segundos extras em vez de como uma linha, o que torna o desvio aritmeticamente
idêntico à contenção e esconde o achado inteiro atrás de uma tautologia. E o id de sessão de um
recontato era único apenas dentro de uma execução, o que nada na onda 1 poderia expor porque a onda 1
nunca juntava duas execuções — a onda 2 juntou os braços e os vetores pararam de se alinhar.

Ver [`docs/ROADMAP.md`](docs/ROADMAP.md) para o que está construído, o que está deliberadamente ausente
— inclusive por que não há modelo de linguagem aqui — e o que continua aberto.

## Licença

MIT. Ver [`LICENSE`](LICENSE).
