# Disclaimer

*[Português abaixo](#aviso)*

**No data from any employer, client, customer, vendor, platform or third party is used anywhere in
this repository.**

Every table in every example, test and README figure is produced by `svclab.synth`, a seeded generator
whose parameters are written down in `src/svclab/synth/config.py`. Running `generate_dataset()` on the
default seed reproduces every published number exactly. No contact centre was read, exported, queried
or approximated to build it; no ticket, transcript, recording or customer record of any kind was used;
and no platform or helpdesk API is called anywhere in the codebase.

**There is no language model in this repository, and no call to one.** The bot is a policy plus a
declared response curve, not a generated reply. That is a deliberate choice, explained in
[`src/svclab/bot/README.md`](src/svclab/bot/README.md): a model would make every published figure
unreproducible and would require secrets in a repository that has none.

The contact reasons (`rastreio`, `prazo-de-entrega`, `cadastro`, `reembolso`, `reclamacao`) are
**invented Portuguese labels for generic customer service functions**, not the structure of any real
operation's intent taxonomy. So are every handling time, the share of volume behind each reason, the
number of contacts and customers, the staffed hours, the service level target, the handoff cost, the
per-turn cost, the classifier accuracy curves, the human resolution curves and the patience
distribution. None of these are measurements of, or references to, any real contact centre, queue,
team, vendor, product or platform, and any resemblance to one is coincidental.

Two columns deserve naming on their own, because they are the reason this repository can say anything
at all.

The `difficulty` column — how hard each contact actually is — is **invented**. It is drawn from a
declared Beta distribution, and whether a bot can resolve the contact, whether the classifier labels
it correctly, how long a human takes and whether the human succeeds are all declared functions of it.

The `would_self_serve` column — whether the customer would have got there with **no help at all** — is
**invented**, and it is the one no real operation has. It is why containment can be checked against
something rather than against another containment rate. Every claim in these READMEs about an
automation getting credit for work that was never work is a claim against that declared column, not
against an observed one.

The **two worlds** are both invented, and the correlation between them is declared. From wave 4 the
account exists twice: once with every trait drawn per contact, and once with a share of each
customer's difficulty and patience belonging to the person. That share — 0.25 and 0.10 — was chosen to
sit inside the range an earlier wave had to guess at. Nothing here is evidence about how correlated a
real account's contacts are. It is evidence about what a correlation of a declared size does to a
measurement, and about how much of it survives into an outcome.

Everything in the generator was designed to make a particular measurement situation visible — one
contact reason that is mostly answerable and mostly self-serving, one that is neither, a residue whose
handling time rises with difficulty, a repeat stream that an unresolved conversation produces, and a
control arm assigned per customer — not to represent any real operation. The shares, the curves, the
spreads and the sample sizes were chosen for what they demonstrate.

No market statistic, industry benchmark, vendor figure or third-party number is quoted as fact
anywhere in this repository. Where the literature is referenced, it is cited by name in the module's
**Sources** section as the origin of a *method*, never as a source of numbers appearing in these
tables. In particular, no containment rate, deflection rate, automation saving or handling time here
should be read as typical of anything.

This repository is a portfolio of methods. It is not a report about any operation, vendor or market.

---

# Aviso

*[English above](#disclaimer)*

**Nenhum dado de empregador, cliente, consumidor, fornecedor, plataforma ou terceiro é utilizado em
qualquer parte deste repositório.**

Toda tabela em todo exemplo, teste e figura de README é produzida pelo `svclab.synth`, um gerador com
semente cujos parâmetros estão escritos em `src/svclab/synth/config.py`. Rodar `generate_dataset()` na
semente padrão reproduz exatamente todo número publicado. Nenhuma central de atendimento foi lida,
exportada, consultada ou aproximada para construí-lo; nenhum ticket, transcrição, gravação ou registro
de cliente de qualquer tipo foi usado; e nenhuma API de plataforma ou helpdesk é chamada em lugar
algum do código.

**Não existe modelo de linguagem neste repositório, nem chamada a um.** O bot é uma política mais uma
curva de resposta declarada, não uma resposta gerada. É uma escolha deliberada, explicada no
[`src/svclab/bot/README.md`](src/svclab/bot/README.md): um modelo tornaria toda cifra publicada
irreproduzível e exigiria segredos num repositório que não tem nenhum.

As razões de contato (`rastreio`, `prazo-de-entrega`, `cadastro`, `reembolso`, `reclamacao`) são
**rótulos inventados em português para funções genéricas de atendimento**, não a estrutura da taxonomia
de intenções de nenhuma operação real. Também são inventados todos os tempos de atendimento, a fração
de volume de cada razão, o número de contatos e clientes, as horas de operação, o alvo de nível de
serviço, o custo de handoff, o custo por turno, as curvas de acurácia do classificador, as curvas de
resolução humana e a distribuição de paciência. Nada disso é medição de, ou referência a, nenhuma
central, fila, equipe, fornecedor, produto ou plataforma real, e qualquer semelhança é coincidência.

Duas colunas merecem ser nomeadas à parte, porque são a razão pela qual este repositório consegue
afirmar qualquer coisa.

A coluna `difficulty` — o quão difícil cada contato realmente é — é **inventada**. É sorteada de uma
distribuição Beta declarada, e se um bot consegue resolver o contato, se o classificador o rotula
certo, quanto um humano leva e se o humano tem êxito são todas funções declaradas dela.

A coluna `would_self_serve` — se o cliente teria chegado lá **sem ajuda alguma** — é **inventada**, e é
a que nenhuma operação real possui. É por ela que a contenção pode ser confrontada com algo em vez de
com outra taxa de contenção. Toda afirmação nestes READMEs sobre uma automação receber crédito por
trabalho que nunca foi trabalho é uma afirmação contra essa coluna declarada, não contra uma observada.

Os **dois mundos** são ambos inventados, e a correlação entre eles é declarada. A partir da onda 4 a
conta existe duas vezes: uma com todo traço sorteado por contato e outra com uma parcela da
dificuldade e da paciência de cada cliente pertencendo à pessoa. Essa parcela — 0,25 e 0,10 — foi
escolhida para cair dentro da faixa que uma onda anterior teve de supor. Nada aqui é evidência sobre
quão correlacionados são os contatos de uma conta real. É evidência sobre o que uma correlação de
tamanho declarado faz a uma medição, e sobre quanto dela sobrevive até um desfecho.

Tudo no gerador foi desenhado para tornar visível uma situação de medição específica — uma razão de
contato em boa parte respondível e em boa parte autorresolvível, uma que não é nem uma coisa nem outra,
um resíduo cujo tempo de atendimento cresce com a dificuldade, um fluxo de recontatos que uma conversa
não resolvida produz, e um braço de controle atribuído por cliente — e não para representar operação
real alguma. As frações, as curvas, as dispersões e os tamanhos de amostra foram escolhidos pelo que
demonstram.

Nenhuma estatística de mercado, benchmark de indústria, cifra de fornecedor ou número de terceiro é
citado como fato em qualquer parte deste repositório. Onde a literatura é referenciada, ela é citada
nominalmente na seção **Fontes** do módulo como origem de um *método*, nunca como fonte de números que
aparecem nestas tabelas. Em particular, nenhuma taxa de contenção, taxa de desvio, economia de
automação ou tempo de atendimento aqui deve ser lido como típico de nada.

Este repositório é um portfólio de métodos. Não é um relatório sobre operação, fornecedor ou mercado
algum.
