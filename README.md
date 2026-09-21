# service-automation

*[Português](README.pt-BR.md)*

**A containment rate is the number every customer service automation is judged on, and it is a
correct calculation of the wrong quantity.**

It counts sessions the customer abandoned as successes. It counts contacts the customer would have
resolved alone. It ignores the second conversation an unresolved contact produces tomorrow. And the
headcount case built on top of it multiplies a queue by a proportion, when a queue is Erlang.

This repository is that exercise, with the bots actually running. `svclab` is a Python package
containing a seeded contact centre, a deployable bot policy that meets it, the four defensible
readings of what that bot contained, and the queue arithmetic that prices what the operation received.
Every tool here **refuses to return a number when the assumption behind it does not hold** — a
deflection rate with no control arm comes back with a reason attached rather than as a figure that
reads like evidence.

Every table comes from `svclab.synth`, a seeded generator whose parameters are written down, including
the two columns no real contact centre has: **how hard each contact actually was, and whether the
customer would have got there with no help at all.** Those columns are why the claims here can be
checked against the truth instead of against another containment rate. No employer, client, customer,
vendor or platform data is used anywhere, and there is no language model in the repository — see
[`DISCLAIMER.md`](DISCLAIMER.md).

## The finding, in one table

Four bot policies meet the same 31,802 contacts. Ranked by containment, best first:

| Policy | Session containment | Needed containment | Resolution rate | Repeats per contact | Human hours |
| --- | --- | --- | --- | --- | --- |
| patient | **0.8169** | **0.2187** | **0.4476** | **0.3211** | 2,316.78 |
| three-turns | 0.6065 | 0.2145 | 0.6355 | 0.2099 | 2,730.43 |
| guarded | 0.4886 | 0.2029 | **0.7271** | 0.1410 | 2,861.54 |
| human-only | 0.0000 | 0.0000 | 0.9305 | 0.0436 | 3,645.64 |

**The containment ranking is the exact reverse of the resolution ranking.** The policy that looks best
on the KPI resolves 44.76% of contacts against 72.71% for the policy that looks worst, and it does it
by abandoning a third of the customers — who then come back. All four containment definitions,
including the strictest one, prefer it.

So the answer is not a stricter numerator. Containment is a statement about what the bot did;
resolution is a statement about what happened to the customer. **No definition of the first can rank
the second.**

Three more results from the same account:

- **28% of the quoted containment rate never reached the queue.** Measured against customers who never
  met the bot: `three-turns` quoted 0.6065 and deflected 0.4377 per contact. The more a policy
  contains, the more it overstates — `patient` quoted 0.8169 and deflected 0.5370.
- **The automation that contained the most raised total conversations by 26.6%**, from 33,190 sessions
  to 42,015. A contained contact that comes back was a deferred contact.
- **The residue is 1.58 times harder than what the bot resolved.** Volume through the human queue fell
  39% and the mean handling time of what remains rose 17%, because a bot does not take a random sample
  of a queue. And **21.98% of what the bot resolved would have resolved itself.**

## And the headcount case was built on the first column

| Step | Agents | Movement |
| --- | --- | --- |
| the promise, as a multiplication | 5.51 | — |
| volume only, through Erlang | 7.00 | **+1.49** |
| plus the harder residue | 8.00 | **+1.00** |
| plus the repeat stream | 11.00 | **+3.00** |

The case promised **8.49 agents** of saving against a baseline of 14. The queue gives back **3** — the
promise overstates it by **2.83 times**. Three effects compound, and the largest is the repeat stream,
which is the one no business case models at all: a model that counts contained sessions has no way to
represent a contact arriving twice.

The other two are at least arguable from the model that was used. **1.49 agents of the gap is pure
non-linearity** — Erlang on the same reduced volume at the same handling time, no behavioural
assumption in it whatever.

## And the meter you would replace it with was never qualified

Wave 1's conclusion is to judge a policy on resolution rather than containment. An operation measures
that by grading sessions — so the quality panel becomes the instrument, and **a panel is a gauge that
gets qualified before it is used.** That is ordinary practice for a caliper and almost unheard of for a
quality rubric.

- **The panel does not agree with itself.** Reading the same session twice, each grader contradicts
  their earlier verdict on **17% to 23%** of them. Between graders, raw agreement is 76% to 78% at a
  kappa of **0.54 to 0.57** — and the pass rate reported on the identical sessions runs from **0.3815
  to 0.5683** depending on who was on the rota. A factor of 1.49 on the headline number.
- **And measurement error does not add noise to a comparison, it shrinks it — by a factor with a
  closed form.** A binary assessor turns a true pass rate `p` into `p·se + (1−p)·(1−sp)`, so a
  difference between two groups comes out multiplied by `se + sp − 1`: the Youden index, **towards
  zero, always**. The true gap between the arms is 0.5459 acceptable sessions. This panel's index is
  0.6945, so it reports **0.3791 — 69.45% of the real difference.** Exactly, not approximately.
- **A gauge whose sensitivity and specificity sum to one reports exactly zero**, however large the
  real difference. Below that it reverses the sign: not noisy, inverted, and the report says the
  opposite with the same confidence.
- **Attenuation is paid for in sample size.** Detecting this gap takes 10.07 sessions per arm with a
  perfect gauge and **25.03** with this panel — an inflation of 2.49×, worse than the 2.07 the square
  of the Youden index predicts, because the attenuated rates also sit closer to 0.5 where a
  proportion's variance is largest. Sample size is the lever everybody pulls *before* checking whether
  the instrument works.
- **And the automated judge is more accurate than every individual grader, and would be validated
  against them.** It agrees with the declared standard 0.8850 of the time against the best grader's
  0.8675. Validated against one grader it scores anywhere from **0.5450 to 0.7121** of kappa — a
  spread of 0.17 decided by whose week it was. "Agreement with our human reviewers" is a measurement
  of the reviewers as much as of the judge. The honest counterweight, in the same breath: the panel as
  a **committee** beats the judge, 0.7979 against 0.7826 — averaging three moderate assessors recovers
  most of what each one loses, which is an argument for a panel and not for any member of it.

## And three numbers the first two waves never priced

Wave 1's `guarded` policy refused two intents on the strength of a label and never asked what the label
was worth. Every capacity figure above assumes nobody gives up waiting. And both waves compared
policies on the whole account, as though contacts were independent. Three decisions taken by default,
priced:

- **Tuning the router's threshold on accuracy rather than on cost costs 7.51 human hours a month.** The
  accuracy-maximising cut is 0.45 and the cost-minimising one is 0.48 — three hundredths, 0.8506 seconds
  per contact, across 31,802 contacts. Sweeping one threshold per intent instead of one for all five
  saves a further **11.5552 seconds per contact**: 102.1 hours over the same month, because a single
  threshold is a compromise between five intents that wanted very different answers.
- **And the closed form for that threshold, applied to this score, is 12.5% worse than the single number
  it was meant to improve on.** Deferring below `1 − defer_cost / misroute_cost` is exactly optimal on a
  score that *is* the probability the label is right. This score is a margin, so the formula's
  **ranking** of the five intents survives intact and its **levels** do not — it defers 23,304 of 31,802
  contacts to avoid 2,414 misroutes. Calibration is the missing step, and the formula assumes it
  silently.
- **The promised headcount is reachable, if 29% of the customers give up.** Erlang C has nothing to say
  below eight agents at this load: the queue grows without bound, and the service level is reported as
  zero because there is no wait to report. Erlang A does have an answer — at **six** agents the queue is
  perfectly stable, with **29.23% abandonment** and the remaining agents at **89.45% occupancy**. The
  business case's 5.51 agents was never impossible. It was an unstated decision to answer seven contacts
  in ten.
- **And an understaffed queue manufactures its own extra work.** Abandoned contacts come back and the
  return is load, so the settled load is a fixed point: 9.1886 erlangs against a base of 7.5845, which
  is **+21.1% of load and abandonment rising from 29.23% to 38.45%**. At eleven agents the identical
  feedback adds 2.0% and settles at 3.56% — a rounding error at adequate staffing, which is the case for
  the eleven agents stated in the currency the abandonment is paid in.
- **A test of two policies that believes it runs at five per cent is really running at 8.43%.** Customers
  repeat, so contacts are clustered, and a per-contact test divides by a standard error too small by the
  square root of the design effect. Detecting wave 1's 0.0916 gap takes 405 contacts per arm if contacts
  are independent and **523** at a correlation of 0.30. The honest half of this result: **this
  generator's own measured correlation is approximately zero**, because every trait is drawn per
  contact. That is a limitation of the simulator, published as one — the scenarios above are declared
  correlations, not measured ones.

## And the customer in all of it was a label

Every figure above was measured on a generator that draws each trait per contact. A customer id is
therefore a label on a row rather than somebody with a history — which is why wave 3, when it went to
measure the clustering it had just warned about, found an intracluster correlation of approximately
**zero** and had to price *declared* correlations instead.

So the account now exists twice. The **independent** world is the one above. The **correlated** world
gives every customer a difficulty and a patience of their own, and is built from the **identical
noise**: a trait's percentile is mixed with its customer's through a Gaussian copula, which leaves
every marginal distribution exactly where it was and changes only the dependence between two contacts
of one person. The independent world is therefore a **control**, not a baseline.

- **Nothing that was published moves.** Session containment 0.6065 against 0.6046, resolution 0.6355
  against 0.6357, and **two human hours out of 2,730**. The largest relative movement across eight
  published metrics is **0.89%**. That is the precondition rather than the result: it is what makes
  everything below a statement about dependence and about nothing else. **A correlation does not
  change what happened — it changes what you can conclude from it.**
- **A correlation between people is not a correlation between outcomes, and the gap is a factor of
  5.6.** Declared at **0.2500** between customers, the correlation measures 0.2535 on the latent
  scale, 0.2463 on the difficulty itself and **0.0448 on the resolution a test is actually run on**. A
  resolution is a coin whose bias is correlated, not a correlated coin, and at a resolution rate near
  0.64 the coin is most of the variance. The rule that follows is short: **estimate the correlation of
  the outcome you are testing, never of the trait you believe drives it.**
- **Which makes wave 3's own alarm four times too loud on this account.** The measured design effect
  is **1.0693** — 6.93% more sample, and a nominal 5% test really running at **5.80%** — against the
  1.2891 and 8.43% wave 3 priced at a declared 0.30. At wave 3's sizing of 405 contacts per arm the
  power is 0.8026 if contacts are independent, **0.7759** at the measured effect and 0.6970 at the
  declared one: **2.7 points of power, not 11.** The effect is real, measurable and modest, because a
  design effect is a product of two factors and this account's clusters average two contacts.
- **And the KPI is blind to the thing the operation feels.** Among customers with exactly two
  contacts, the share failed **both** times rises from 0.1219 to **0.1406** — 98 more people, on the
  same volume, while the resolution rate moves by 0.0002. A resolution rate is contact-weighted; a
  complaint, a churn and a regulator's letter are customer-weighted. The two agree exactly when a
  customer is a label.
- **The correction most analysts reach for costs twelve times the error it corrects.** Averaging
  each customer's average inflates the standard error by **13.3% in the independent world** — where
  there is no correlation at all to correct — because weighting unequal clusters equally discards
  information. The correlation's own contribution to the same standard error is **1.1%**. The
  independent world's row is the only reason that is visible, which is the argument for keeping a
  control world rather than a better story.

## And the customer who contacted most was busy by accident

The world above gives every customer a difficulty and a patience of their own, and leaves their
**rate** alone: each contact still picks a customer uniformly, so contact counts are Poisson with a
mean below two and the busiest customer in the account is busy by luck. A real account breaks that
twice over — its volume is **concentrated**, and the minority generating it is **not random**, because
the people who contact most are on average the people whose problems are hardest.

So the same 31,802 contacts are regrouped into customers whose contact rate is log-normal and
correlated with their own difficulty at a declared 0.40. The regrouping reuses the uniform that chose
the customer in the first place and never crosses an arm, so **every per-contact figure stays
identical, bit for bit** — asserted exactly, not to a tolerance. The control is the same regrouping at
**equal rates**, because reassigning contacts among the customers an account actually saw enlarges the
clusters on its own.

- **The same volume arrives from 10,640 people instead of 13,087, and the mean barely notices.** Mean
  contacts per customer rise 23%, from 2.43 to 2.99. The **effective** cluster size — the
  size-weighted mean, which is the quantity a design effect is computed from — rises **78%**, from
  3.23 to **5.75**. Concentration is a statement about the variance of the cluster sizes.
- **Which is where wave 3's alarm comes back: the design effect is 1.2246, or 95% of the 1.2891 wave 3
  declared as its serious case.** Wave 4 measured 1.0693 and called that alarm four times too loud — in
  a world where everybody contacts at the same rate, which it had assumed rather than chosen. Two wrong
  assumptions in opposite directions whose product was close to right, and a nominal 5% test here is
  really running at **7.65%**.
- **The cost concentrates faster than the volume.** Heavy users — four contacts or more in the month,
  a declared count rather than a decile — are 2,643 people in the control, and they generate 38.75% of
  the contacts, 38.97% of the failures and 39.01% of the human hours: one number, because being heavy
  says nothing about being difficult. Concentrated, 2,885 people generate **58.1% of the volume, 59.9%
  of the failures and 61.2% of the hours**. The separation is the finding — volume and hours differ by
  0.3 of a point in the control and by **3.1 points** here, because heavy users do not merely contact
  more, each of their contacts costs more. And the population failed three times or more goes from 794
  customers to **1,305**.
- **The resolution rate falls 1.53 points with no change of policy at all.** The distribution of
  difficulty **per customer** is unchanged; the distribution **per contact** is not, because the
  difficult customers now send more contacts each. Mean difficulty per contact rises 9.9%. The queue's
  mix of difficulty is a property of who calls, not only of who they are — and no business case models
  it.
- **And wave 1's central estimate loses a third of its precision.** Deflection per customer is not
  comparable across worlds that disagree about how many customers there are, so its rise from 1.5484
  to 1.7845 is a denominator rather than a finding. What is comparable is the error: **+66% relative,
  a 91% wider interval**, on the same contacts, the same arms and the same bot. A per-customer number
  is only as stable as the assumption about who a customer is.

## And the contact that came back came back only once

Everything above allows an unresolved contact **one** return. Every wave said so, and every wave named
it as the reason its figures were an underestimate — wave 1 wrote that a containment rate becomes a
permanent queue through the geometric tail, and then truncated the tail at one term. So the runtime now
runs the chain: up to four attempts, a customer 15% less likely to return each time, a human 15% more
likely to resolve it. The default is still one return, and `run(contacts, policy)` and
`run(contacts, policy, chain=SINGLE_RETURN)` produce the **identical frame** — asserted by equality,
not by tolerance.

- **The chain is real and it is short.** 720 contacts need a third attempt and seven need a fourth. It
  adds 727 sessions, **4.88% of the month's human hours**, and lifts eventual resolution from 0.8067 to
  **0.8291** — 2.24 points five waves were not counting.
- **Because a tail needs an operation that keeps failing.** A contact reopens only if the customer
  returns **and** the human failed again, so the sessions one unresolved contact generates are a
  geometric series in `r = P(return) × P(human fails)`. Here `r = 0.6174 × 0.0695 = 0.0429`, and the
  series is **1.0448 sessions however many attempts are allowed**. Truncating at one return cost
  **0.18%** — at a reopen rate of 0.5 it would have cost **a third**, and at 0.7 the single-return model
  reports half the sessions that happen. **The geometric tail is not a property of customers who
  return; it is a property of an operation that keeps failing them**, and the lever is the human's
  first-contact resolution rather than the customer's return rate.
- **And the chain charges the policy containment rewarded.** Extra hours rise with containment:
  `human-only` pays +3.86%, `guarded` +4.72%, `three-turns` +4.88%, `patient` **+5.74%** — 1.5 times
  what the human queue pays, because a policy that contains more leaves more unresolved, and an
  unresolved contact is the only thing a chain can act on.
- **Which produces a third ranking of the same four policies, and it is the steepest.** Days to
  resolution: `human-only` **0.16**, `guarded` 0.52, `three-turns` 0.78, `patient` **1.31** — and
  **40.5% of what `patient` eventually resolves is resolved on a later attempt**, against 2.6% for the
  human queue. `patient` takes **8.4 times** as long as `human-only` and 2.5 times as long as
  `guarded`.

| Ranked best first by | Order |
| --- | --- |
| containment | patient, three-turns, guarded, human-only |
| resolution | human-only, guarded, three-turns, patient |
| **days to resolution** | human-only, guarded, three-turns, patient |

**Containment is the exact reverse of both of the others.** Wave 1 said no definition of containment
can rank resolution. Wave 6 adds that resolution is not the whole of what the customer experiences
either: a problem fixed after two returns and three days was fixed **and** the customer waited three
days. A rate has no time in it — and three days is not a rounding error on a KPI, it is the complaint.

## Modules

| Module | What it decides |
| --- | --- |
| [`svclab.synth`](src/svclab/synth/README.md) | What data to test against without touching a real operation, and which two columns make the rest checkable. |
| [`svclab.bot`](src/svclab/bot/README.md) | How long the bot should try, what it should refuse to attempt, and whether the difference between two policies is the policy — which needs the same contacts on both sides and a line between what a policy may see and what the world knows. |
| [`svclab.containment`](src/svclab/containment/README.md) | Which containment number is being shown, out of the four that are all correct; how much of it reached the queue, against customers who never met the bot; and which contacts the bot kept. |
| [`svclab.capacity`](src/svclab/capacity/README.md) | How many agents the queue needs at its service level, how many the containment rate promised, and where the difference came from. |
| [`svclab.quality`](src/svclab/quality/README.md) | Whether the quality score is a measurement or a habit, how much of a real difference this panel will report, and what an unqualified gauge costs in sessions. |
| [`svclab.routing`](src/svclab/routing/README.md) | Where to cut the classifier's score when the two mistakes cost different numbers of human seconds, what the closed form for that cut assumes about the score, and which objective the cut is being tuned on. |
| [`svclab.experiment`](src/svclab/experiment/README.md) | How many contacts a test of two policies needs once customers repeat, and what significance level a test that ignores the clustering is really running at. |
| [`svclab.population`](src/svclab/population/README.md) | What the independence assumption was worth: how much of a correlation between customers survives into the outcome a test is run on, what the surviving part costs, and what the usual correction for it costs instead. |
| [`svclab.concentration`](src/svclab/concentration/README.md) | What grouping decides once customers do not all contact equally often: how unequal the clusters really are, which of the two cluster sizes belongs in a design effect, who pays for the failures, and how much precision a per-customer estimate loses. |
| [`svclab.chain`](src/svclab/chain/README.md) | What a contact that comes back twice costs, how long a return chain really is and the closed form that says why, and the third ranking of the policies — days to resolution, which no rate contains. |

Every module README is bilingual and carries an **Assumptions and limitations** section, because a
figure without its assumptions is not a result.

## Examples

| Example | What it shows |
| --- | --- |
| [`examples/01_the_containment_that_wasnt.py`](examples/01_the_containment_that_wasnt.py) | Four policies on one account: the four containment rates and the ranking each produces, which contacts the bot kept, what the queue actually received against what was claimed, and the headcount case decomposed into its three errors. |
| [`examples/02_the_meter_that_was_noise.py`](examples/02_the_meter_that_was_noise.py) | The gauge study run before the comparison: repeatability, reproducibility, bias against a declared standard, the exact factor by which the panel shrinks every difference, what that costs in sessions, and what an automated judge would be validated against. |
| [`examples/03_three_numbers_nobody_priced.py`](examples/03_three_numbers_nobody_priced.py) | The three defaults priced: the routing threshold swept against both objectives and against its closed form, the queue with impatience and with the repeat feedback solved to its fixed point, and what a real test of two policies costs once customers are allowed to repeat. |
| [`examples/04_the_customer_who_was_a_label.py`](examples/04_the_customer_who_was_a_label.py) | The same account built twice from the same noise: whether the correlation moves anything already published, how much of it reaches the outcome, what it costs a comparison, how many people are failed twice, and what three different standard errors say about one difference. |
| [`examples/05_the_frequent_caller.py`](examples/05_the_frequent_caller.py) | The identical contacts regrouped into customers who contact at different rates, with the heavy users correlated with the difficult ones: the shape of the clusters, the design effect that returns, who pays for it, and what it costs the precision of wave 1's estimate. |
| [`examples/06_the_contact_that_came_back_twice.py`](examples/06_the_contact_that_came_back_twice.py) | The tail five waves truncated, run to its declared end: how many attempts a contact takes, the geometric series that says when that matters, what the chain costs each policy, and the ranking with time in it. |

## Install and run

```bash
python -m pip install -e ".[dev]"
make check       # lint, types and the fast suite - what gates a push
make check-all   # the above plus every documented figure re-derived
python examples/01_the_containment_that_wasnt.py
python examples/02_the_meter_that_was_noise.py
python examples/03_three_numbers_nobody_priced.py
python examples/04_the_customer_who_was_a_label.py
python examples/05_the_frequent_caller.py
python examples/06_the_contact_that_came_back_twice.py
```

## How the claims are kept honest

**306 tests, 100% statement and branch coverage.** 255 of them run in seconds and gate every push. The
remaining 51 re-derive, from the generator, every figure quoted in every README on this repository,
and run the example script. A change that moves a published number breaks the build instead of leaving
the text quietly wrong.

**A bot is a deterministic function of the dataset.** Everything random is drawn once per contact
before any bot exists, so two policies meet the identical contacts and any difference between them is
the policy. Running a policy twice returns the identical frame, and a test asserts it.

**A policy cannot see the answer.** `difficulty`, `would_self_serve` and `human_seconds` are truth, and
a test parses `svclab.bot.policy` and fails if the code reaches any of them. Every automation business
case ever written was built by somebody who could see the outcome column; the reason those cases are
wrong is that the bot could not.

**Verification against closed forms and control cases, never against the code's own output.** The
containment rates are checked on ten sessions whose four numerators are countable on fingers; the
deflection estimator against two arms whose difference is exactly one contact per customer with zero
spread; Erlang C against the closed form that makes it equal the offered load at one agent, and
Erlang B against `a / (1 + a)`; the staffing search against its own definition, by asserting that one
fewer agent misses the target.

**Every draw is an inverse transform of the uniform stream, never a rejection sampler**, so the stream
position depends on how many values are asked for and not on which library version answers. That rule
is checked against the source, because a sibling repository published figures that held on one machine
and moved on a clean install.

**And defects are recorded rather than quietly fixed.** Thirty-one so far, in
[`docs/ROADMAP.md`](docs/ROADMAP.md), every one of them found by connecting the modules, by a control
case or by verifying a sentence — none by reading code. Two are worth reading. The original session
charged a repeat contact as extra seconds rather than as a row, which makes deflection arithmetically
identical to containment and hides the entire finding behind a tautology. And a repeat's session id was
unique only within one run, which nothing in wave 1 could expose because wave 1 never pooled two runs —
wave 2 pooled the arms and the arrays stopped lining up.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for what is built, what is deliberately absent — including why
there is no language model here — and what is still open.

## Licence

MIT. See [`LICENSE`](LICENSE).
