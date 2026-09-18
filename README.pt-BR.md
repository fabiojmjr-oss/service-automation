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

## Módulos

| Módulo | O que decide |
| --- | --- |
| [`svclab.synth`](src/svclab/synth/README.md) | Contra quais dados testar sem tocar numa operação real, e quais duas colunas tornam o resto verificável. |
| [`svclab.bot`](src/svclab/bot/README.md) | Por quanto tempo o bot deve tentar, o que deve se recusar a tentar, e se a diferença entre duas políticas é a política — o que exige os mesmos contatos nos dois lados e uma linha entre o que uma política pode ver e o que o mundo sabe. |
| [`svclab.containment`](src/svclab/containment/README.md) | Qual número de contenção está sendo mostrado, entre os quatro que estão todos corretos; quanto dele chegou à fila, contra clientes que nunca encontraram o bot; e quais contatos o bot ficou. |
| [`svclab.capacity`](src/svclab/capacity/README.md) | Quantos atendentes a fila precisa no seu nível de serviço, quantos a taxa de contenção prometeu, e de onde veio a diferença. |
| [`svclab.quality`](src/svclab/quality/README.md) | Se a nota de qualidade é uma medição ou um hábito, quanto de uma diferença real este painel vai reportar, e o que um instrumento não qualificado custa em sessões. |

Todo README de módulo é bilíngue e traz uma seção **Premissas e limitações**, porque uma cifra sem suas
premissas não é um resultado.

## Exemplos

| Exemplo | O que mostra |
| --- | --- |
| [`examples/01_the_containment_that_wasnt.py`](examples/01_the_containment_that_wasnt.py) | Quatro políticas numa conta: as quatro taxas de contenção e o ranking que cada uma produz, quais contatos o bot ficou, o que a fila recebeu contra o que foi afirmado, e o business case de headcount decomposto nos seus três erros. |
| [`examples/02_the_meter_that_was_noise.py`](examples/02_the_meter_that_was_noise.py) | O estudo do instrumento rodado antes da comparação: repetibilidade, reprodutibilidade, viés contra um padrão declarado, o fator exato pelo qual o painel encolhe toda diferença, o que isso custa em sessões, e contra o que um juiz automático seria validado. |

## Instalar e rodar

```bash
python -m pip install -e ".[dev]"
make check       # lint, tipos e a suíte rápida - o que libera um push
make check-all   # o acima mais toda cifra documentada re-derivada
python examples/01_the_containment_that_wasnt.py
python examples/02_the_meter_that_was_noise.py
```

## Como as afirmações são mantidas honestas

**152 testes, 100% de cobertura de linhas e de ramos.** 129 deles rodam em segundos e liberam cada push.
Os 23 restantes re-derivam, a partir do gerador, toda cifra citada em todo README deste repositório, e
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

**E defeitos são registrados em vez de corrigidos em silêncio.** Nove até aqui, em
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
