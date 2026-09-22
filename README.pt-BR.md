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

**Se você decide em vez de verificar, leia [`docs/FINDINGS.pt-BR.md`](docs/FINDINGS.pt-BR.md).** Ele
apresenta os mesmos oito achados como decisões — em que cada um desemboca, o que uma operação competente
teria decidido sem ele, e o que fazer em vez disso — e não cita nenhuma cifra que este README não
publique.

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
  31.802 contatos para evitar 2.414 erros de roteamento. A onda 3 concluiu que calibração era o passo
  que faltava. **Não é** — a onda 9 deu à fórmula a probabilidade que o gerador realmente usou e ela
  seguiu 7,33% fora, porque o que a fórmula omite é um termo, não uma calibração. Ver abaixo.
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

## E o contato que voltou voltou só uma vez

Tudo acima permite **um** retorno a um contato não resolvido. Toda onda disse isso, e toda onda apontou
o fato como a razão de suas cifras serem subestimativas — a onda 1 escreveu que uma taxa de contenção se
torna uma fila permanente pela cauda geométrica, e então truncou a cauda em um termo. Agora o runtime
roda a cadeia: até quatro tentativas, um cliente 15% menos propenso a voltar a cada vez, um humano 15%
mais propenso a resolver. O padrão continua sendo um retorno, e `run(contacts, policy)` e
`run(contacts, policy, chain=SINGLE_RETURN)` produzem o **frame idêntico** — verificado por igualdade,
não por tolerância.

- **A cadeia é real e é curta.** 720 contatos precisam de uma terceira tentativa e sete de uma quarta.
  Ela acrescenta 727 sessões, **4,88% das horas humanas do mês**, e leva a resolução eventual de 0,8067
  para **0,8291** — 2,24 pontos que cinco ondas não contavam.
- **Porque uma cauda exige uma operação que segue falhando.** Um contato reabre só se o cliente volta
  **e** o humano falhou de novo, então as sessões que um contato não resolvido gera são uma série
  geométrica em `r = P(volta) × P(humano falha)`. Aqui `r = 0,6174 × 0,0695 = 0,0429`, e a série dá
  **1,0448 sessões por mais tentativas que se permitam**. Truncar em um retorno custou **0,18%** — a uma
  taxa de reabertura de 0,5 teria custado **um terço**, e a 0,7 o modelo de retorno único reporta metade
  das sessões que acontecem. **A cauda geométrica não é propriedade de clientes que voltam; é
  propriedade de uma operação que segue falhando com eles** — e a alavanca é a resolução no primeiro
  contato pelo humano, não a taxa de retorno do cliente.
- **E a cadeia cobra da política que a contenção premiava.** As horas extra crescem com a contenção:
  `human-only` paga +3,86%, `guarded` +4,72%, `three-turns` +4,88%, `patient` **+5,74%** — 1,5 vez o que
  a fila humana paga, porque uma política que contém mais deixa mais coisa não resolvida, e um contato
  não resolvido é a única coisa sobre a qual uma cadeia pode agir.
- **O que produz um terceiro ranking das mesmas quatro políticas, e é o mais inclinado.** Dias até
  resolver: `human-only` **0,16**, `guarded` 0,52, `three-turns` 0,78, `patient` **1,31** — e **40,5% do
  que a `patient` eventualmente resolve é resolvido numa tentativa posterior**, contra 2,6% na fila
  humana. A `patient` leva **8,4 vezes** o tempo da `human-only` e 2,5 vezes o da `guarded`.

| Ordenado do melhor por | Ordem |
| --- | --- |
| contenção | patient, three-turns, guarded, human-only |
| resolução | human-only, guarded, three-turns, patient |
| **dias até resolver** | human-only, guarded, three-turns, patient |

**A contenção é o inverso exato dos outros dois.** A onda 1 dizia que nenhuma definição de contenção
pode ordenar resolução. A onda 6 acrescenta que resolução também não é tudo o que o cliente
experimenta: um problema resolvido depois de dois retornos e três dias foi resolvido **e** o cliente
esperou três dias. Uma taxa não tem tempo dentro — e três dias não são erro de arredondamento num KPI,
são a reclamação.

## E todo plano acima dimensionava por uma meta e reportava o resto

A linha mais nítida da onda 3 foi uma fila **perfeitamente estável** com seis atendentes — com 29,23%
dos clientes abandonando e os atendentes dos sobreviventes a 89,45% de ocupação. As duas coisas eram
saídas. Nenhum plano real as trata assim: um teto de ocupação é o que contém a rotatividade e um teto de
abandono é o que a marca ou o regulador pede. Então a aritmética se inverte — declare os tetos, pegue o
headcount que satisfaz todos eles, e **diga qual deles decidiu**.

- **Um teto de ocupação sozinho é satisfeito subdimensionando.** Oito atendentes mantêm a ocupação em
  0,8121 — e atendem **17,51%** dos contatos dentro da meta enquanto **14,34% dos clientes desistem**.
  São os clientes que abandonam que mantêm a ocupação baixa, então uma meta de ocupação perseguida
  isoladamente premia a fila por perder gente. Enquanto isso, o nível de serviço e o teto de abandono
  chegam aos mesmos **11 atendentes** por caminhos independentes e então vinculam **juntos**: com dez,
  os dois falham.
- **O que resolve o que a onda 3 deixou aberto: seis atendentes falham nos três tetos.** Nível de
  serviço 0,0000 contra 0,80, ocupação 0,8945 contra 0,85, abandono 0,2923 contra 0,05. Estabilidade
  significa que a fila tem estado estacionário — e tem, com um cliente em três indo embora.
  **Estabilidade não é plano.**
- **E a conta de guardanapo fica 18% curta.** `carga / teto de ocupação` dá 9 atendentes onde a fila
  precisa de **11** — o erro de headcount da onda 1 com outra fantasia: lá a promessa multiplicava uma
  fila por uma proporção, aqui divide-se uma por uma proporção. Nenhuma das duas é uma fila.
- **Qual teto vincula depende do tamanho da fila, e esse é o argumento da consolidação — com um fim.**
  Atendentes por erlang cai de **3,00** a um erlang para **1,18** a quatrocentos, queda de 61%. Mas a
  restrição vinculante é o nível de serviço até cerca de 35 erlangs e **o teto de ocupação sozinho a
  partir de 45**: passado esse ponto a fila é limitada pela tolerância do atendente e não pela do
  cliente — e essas duas se negociam com pessoas diferentes.
- **E "em conformidade" e "a uma falta de furar" são a mesma frase.** Com onze atendentes a folga é
  +0,0368 no nível de serviço, +0,1828 na ocupação e **+0,0176 no abandono** — a mais fina das três. Um
  plano que reporta "todas as restrições atendidas" e um que reporta as margens são o mesmo plano, e só
  o segundo diz qual número se move primeiro quando alguém falta.

## E todo headcount acima era uma contagem de atendentes, não uma folha de pagamento

A onda 7 declarou a ocupação um **teto**: 0,84 ok, 0,86 proibido. O que um teto substitui é uma
**curva** — a rotatividade cresce com o quanto o trabalho é duro — e uma curva transforma restrição em
preço. Precificá-la fecha um laço que todo gestor de operações conhece e nenhum modelo de
dimensionamento contém: **a ocupação eleva a rotatividade → a rotatividade esvazia cadeiras → uma
cadeira vazia não é um atendente → menos atendentes elevam a ocupação.** Então o quadro que produz o
trabalho e o quadro na folha são dois números unidos por um ponto fixo, não por uma margem.

- **Os onze atendentes da onda 7 custam doze pessoas, e a cem erlangs 119 atendentes custam 130** — com
  **7,13 cadeiras vazias** e **9,51 pessoas em ramp** em qualquer instante. O prêmio não é um colchão
  que alguém escolheu; é a solução do laço. E ele **não é monótono no tamanho da fila** — 1,3333 a um
  erlang, 1,0800 a vinte, 1,1017 a cinquenta — porque a aritmética inteira domina a fila pequena e a
  rotatividade domina a grande.
- **O que precifica a eficiência que a onda 7 celebrou.** A fila grande que precisava de apenas 1,18
  atendentes por erlang roda a 0,84 de ocupação, perde **36,1% do quadro por ano** e contrata **57
  pessoas por ano para ficar parada**. Um case de consolidação que conta os atendentes economizados e
  não o recrutamento que assume contou um lado só.
- **A taxa de câmbio é 1,01: vinte e sete pessoas a mais na folha compram 27,39 contratações a menos por
  ano.** É o número que um gestor pede e que um modelo de dimensionamento nunca imprime — e, como este
  repositório não tem dinheiro dentro, a taxa pode ser lida na moeda dele mesmo. Uma saída desperdiça
  2,30 pessoa-meses, então um atendente extra custa **12 pessoa-meses por ano** e devolve **2,33**:
  razão de **0,19**. **Nos livros da própria fila, afrouxar a ocupação perde por um fator de cinco** — o
  que não a torna errada: significa que o caso repousa inteiramente sobre o que uma saída custa *fora*
  da fila, e nomear esse número que falta é a entrega.
- **Na fila da onda 1 não há troca alguma.** Todo teto de 0,90 a 0,70 exige as mesmas doze pessoas,
  porque o nível de serviço já entrega 0,6411 de ocupação — abaixo do joelho, onde a rotatividade está
  no piso. A taxa volta como `nan` e não zero: zero diria que a troca é grátis. **O problema
  ocupação-rotatividade é um problema de fila grande**, a mesma fronteira que a onda 7 encontrou.
- **E o laço não escapa.** Na curva declarada o ponto fixo é único e a iteração o alcança dos dois
  extremos; a inclinação precisa ser **12,5 vezes mais forte** para a folha do plano colapsar. Duas
  pessoas abaixo do plano, ela se divide a **cinco vezes** — então **robustez é propriedade da folha,
  não só da curva**, o que é um segundo argumento, independente, para financiar o plano. E onde existem
  dois regimes, o alcançado a partir da crise tem ocupação *menor* e rotatividade *menor*: o abandono é
  a válvula de escape. **É a terceira vez neste repositório que o abandono é o que impede algo de
  divergir** — e é a coisa que o negócio está tentando não fazer.

## E a fórmula que precificou tudo isso não tinha um termo, não faltava calibração

A onda 3 aplicou o limiar de roteamento de manual ao score do classificador desta conta, achou-o **12,5%**
pior que o número único varrido, e concluiu que **calibração era o passo que faltava**. Era uma afirmação
sem controle atrás. O controle existe agora — a probabilidade que o gerador realmente usa — e o
diagnóstico não sobrevive a ele.

- **Calibração é real, e não é o passo que falta.** Ajustado em três quintos do mês e julgado nos
  **12.709** contatos restantes, o erro de calibração da margem crua é **0,1618** contra **0,0061** do
  controle — **26,68 vezes** — e no bin em que o score diz **0,6502**, **0,9078** dos rótulos estão
  certos. Calibrá-lo corta a penalidade da fórmula **3,59 vezes**, de **17,04%** para **4,74%**. Mas sobre
  a probabilidade perfeitamente calibrada a penalidade ainda é **7,33%**, e ali não resta calibração
  alguma a fazer.
- **O que faltava é a razão de o bot existir.** A forma fechada precifica um rótulo errado e uma
  postergação e trata um rótulo **certo** como gratuito — quando um contato corretamente rotulado que o
  bot resolve *economiza* os segundos humanos que ele teria consumido. Carregue esse termo e a regra passa
  a ser `(erro − postergar) / (erro + benefício)`, que é exatamente a fórmula original quando o benefício
  é zero. O benefício corre no sentido **oposto** ao custo do erro — **142,68** segundos no rastreio
  contra **23,32** na reclamacao — então a fórmula que só precifica erros está mais errada onde o bot é
  mais útil: ela exige 0,6667 de confiança no rastreio onde **0,1974** basta. A penalidade cai para
  **1,96%** na margem crua e **0,19%** na calibrada. **E 342,14 segundos na margem não calibrada vencem
  367,54 na probabilidade que o gerador realmente usou** — corrigir o modelo venceu corrigir o insumo, e a
  onda 3 apontou para o insumo.
- **O score melhor calibrado é o pior ordenador.** O controle tem o menor erro de calibração da tabela e o
  **maior** custo varrido, **342,4383** contra **335,5655** da margem crua, porque é o único score que não
  sabe o que o classificador de fato viu. Calibração e discriminação são propriedades diferentes — o
  instrumento não viesado e inútil da onda 2, num segundo cenário.
- **O otimismo é um décimo do achado, e o limiar nunca foi a coisa aprendida.** Um limiar varrido nos
  primeiros três quintos custa **1,5076** segundo por contato mais no período posterior do que o melhor
  daquele próprio período: **0,45%** da conta e **13,05%** dos 11,5552 segundos que a onda 3 publicou. Ele
  concentra onde o erro é caro e a amostra é rala — **4,1790** no reembolso e **3,2614** na reclamacao, os
  dois menores grupos e os dois erros mais custosos. E os cortes se movem muito mais que o custo: rastreio
  de **0,10** para **0,24**, prazo-de-entrega de 0,22 para 0,38, por **0,1116** de segundo. **A curva de
  custo é plana perto do ótimo, então o custo foi aprendido e o corte não** — uma operação discutindo a
  segunda decimal de um limiar está discutindo ruído de amostragem.
- **E o rótulo que um roteador realmente consegue ler é o melhor para chavear.** A regra por intenção da
  onda 3 pedia o limiar de reclamacao num contato que *é* uma reclamação, o que nenhuma implantação pode
  fazer. O roadmap previu que o ganho encolheria. Ele cresce: chaveada no próprio rótulo do classificador
  a regra economiza **11,9210** segundos por contato contra **10,9487** chaveada na verdade, com **75
  erros de rota menos**, porque um rótulo errado é o evento de que o custo é feito — então o rótulo
  reportado carrega informação sobre o classificador estar errado e o rótulo verdadeiro não carrega
  nenhuma. **Condicionar no que você sabe vence condicionar no que é verdade, quando o que você sabe é
  aquilo de que o erro é feito.** Fora da amostra e chaveada no rótulo legível, a economia da onda 3 passa
  a ser **11,9210** contra os 11,5552 publicados — uma razão de **1,0317**, **105,31** horas no volume
  tratado do mês. Duas correções, sinais opostos, quase se cancelando: a cifra sobrevive por uma razão que
  a onda 3 não nomeou.

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
| [`svclab.chain`](src/svclab/chain/README.md) | O que custa um contato que volta duas vezes, quão longa é de fato uma cadeia de retornos e a forma fechada que diz por quê, e o terceiro ranking das políticas — dias até resolver, que nenhuma taxa contém. |
| [`svclab.planning`](src/svclab/planning/README.md) | Que headcount um conjunto de tetos declarados compra em vez do que uma meta única reporta, qual dos tetos de fato decidiu, como isso muda com o tamanho da fila, e a que distância de furar o plano escolhido está. |
| [`svclab.calibration`](src/svclab/calibration/README.md) | Se a forma fechada de um limiar de roteamento recebeu o insumo errado ou está sem um termo, o que um limiar ajustado num período custa no seguinte, e em qual rótulo uma regra que uma implantação consegue rodar precisa ser chaveada. |
| [`svclab.workforce`](src/svclab/workforce/README.md) | O que uma ocupação custa em pessoas em vez do que um teto proíbe: a folha atrás de uma contagem de atendentes, a taxa de câmbio entre ocupação e contratação, e se o laço de rotatividade que ela fecha alguma vez escapa. |

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
| [`examples/06_the_contact_that_came_back_twice.py`](examples/06_the_contact_that_came_back_twice.py) | A cauda que cinco ondas truncaram, rodada até seu fim declarado: quantas tentativas um contato leva, a série geométrica que diz quando isso importa, o que a cadeia custa a cada política, e o ranking que tem tempo dentro. |
| [`examples/07_the_constraint_nobody_declared.py`](examples/07_the_constraint_nobody_declared.py) | Os três tetos declarados em vez de reportados: o que cada um compra sozinho, no que a fila estável da onda 3 falha, onde a economia de escala para, e quanto espaço sobra no plano escolhido. |
| [`examples/09_the_threshold_fitted_on_the_answer.py`](examples/09_the_threshold_fitted_on_the_answer.py) | A forma fechada recebendo o insumo que ela assume e depois o termo que lhe faltava: a confiabilidade do score, as quatro versões dele precificadas contra uma varredura, o que um limiar custa num período que nunca viu, e a regra chaveada no rótulo que um roteador consegue ler. |
| [`examples/08_the_payroll_behind_the_plan.py`](examples/08_the_payroll_behind_the_plan.py) | O teto de ocupação precificado em pessoas: a folha que cada plano de fato exige, o que um ponto de ocupação compra em contratação, a fila onde não há o que trocar, e quão mais forte a curva de rotatividade teria de ser para espiralar. |

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
python examples/06_the_contact_that_came_back_twice.py
python examples/07_the_constraint_nobody_declared.py
python examples/08_the_payroll_behind_the_plan.py
python examples/09_the_threshold_fitted_on_the_answer.py
```

## Como as afirmações são mantidas honestas

**433 testes, 100% de cobertura de linhas e de ramos.** 361 deles rodam em segundos e liberam cada push.
Os 72 restantes re-derivam, a partir do gerador, toda cifra citada em todo README deste repositório, e
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

**E defeitos são registrados em vez de corrigidos em silêncio.** Trinta e oito até aqui, em
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
