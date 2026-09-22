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

**If you decide rather than verify, read [`docs/FINDINGS.md`](docs/FINDINGS.md) instead.** It states the
same eight findings as decisions — what each one lands on, what a competent operation would have decided
without it, and what to do instead — and quotes no figure this README does not publish.

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
  contacts to avoid 2,414 misroutes. Wave 3 concluded that calibration was the missing step. It is
  **not** — wave 9 gave the formula the probability the generator actually used and it was still 7.33%
  off, because what the formula omits is a term rather than a calibration. See below.
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

## And every plan above staffed to one target and reported the rest

Wave 3's sharpest line was a queue **perfectly stable** at six agents — with 29.23% of the customers
abandoning and the survivors' agents at 89.45% occupancy. Both were outputs. No real plan treats them
that way: an occupancy ceiling is what stops attrition and an abandonment ceiling is what the brand or
the regulator asks for. So the arithmetic is inverted — declare the ceilings, take whatever headcount
satisfies all of them, and **say which one decided it**.

- **An occupancy ceiling on its own is satisfied by understaffing.** Eight agents hold occupancy at
  0.8121 — and answer **17.51%** of contacts inside the target while **14.34% of customers give up**.
  The customers who abandon are what keeps the occupancy down, so an occupancy target chased alone
  rewards a queue for losing people. Meanwhile the service level and the abandonment ceiling reach the
  same **11 agents** by independent routes and then bind **together**: at ten, both fail.
- **Which settles what wave 3 left open: six agents fails all three ceilings.** Service level 0.0000
  against 0.80, occupancy 0.8945 against 0.85, abandonment 0.2923 against 0.05. Stability means the
  queue has a steady state — it does, with one customer in three walking away. **Stability is not a
  plan.**
- **And the napkin is short by 18%.** `load / occupancy ceiling` gives 9 agents where the queue needs
  **11** — wave 1's headcount error in a new costume: the promise there multiplied a queue by a
  proportion, and this divides one by a proportion. Neither is a queue.
- **Which ceiling binds depends on how big the queue is, and that is the case for consolidation — with
  an end.** Agents per erlang falls from **3.00** at one erlang to **1.18** at four hundred, a 61%
  drop. But the binding constraint is the service level up to about 35 erlangs and **the occupancy
  ceiling alone from 45 upward**: past that point the queue is limited by the agent's tolerance rather
  than the customer's, and those two are negotiated with different people.
- **And "compliant" and "one absence from breaching" are the same sentence.** At eleven agents the
  slack is +0.0368 on service level, +0.1828 on occupancy and **+0.0176 on abandonment** — the
  thinnest of the three. A plan that reports "all constraints met" and one that reports the margins
  are the same plan, and only the second says which number moves first when somebody calls in sick.

## And every headcount above was an agent count, not a payroll

Wave 7 declared occupancy a **ceiling**: 0.84 fine, 0.86 forbidden. What a ceiling stands in for is a
**curve** — attrition rises with how hard the work is — and a curve turns a constraint into a price.
Pricing it closes a loop every operations manager knows and no staffing model contains: **occupancy
raises attrition → attrition empties seats → an empty seat is not an agent → fewer agents raise
occupancy.** So the headcount that produces the work and the headcount on the payroll are two numbers
joined by a fixed point rather than by a margin.

- **Wave 7's eleven agents cost twelve people, and at a hundred erlangs 119 agents cost 130** — with
  **7.13 seats empty** and **9.51 people ramping** at any moment. The premium is not a buffer somebody
  chose; it is the solution of the loop. And it is **not monotone in the size of the queue** — 1.3333 at
  one erlang, 1.0800 at twenty, 1.1017 at fifty — because integer arithmetic dominates a small queue and
  attrition dominates a large one.
- **Which prices the efficiency wave 7 celebrated.** The large queue that needed only 1.18 agents per
  erlang runs at 0.84 occupancy, loses **36.1% of its staff a year** and hires **57 people a year to
  stand still**. A consolidation case that counts the agents saved and not the recruiting it commits to
  has counted one side.
- **The exchange rate is 1.01: twenty-seven more people on the payroll buys 27.39 fewer hires a year.**
  That is the number a manager asks for and a staffing model never prints — and because this repository
  has no money in it, the rate can be read in its own currency. A departure wastes 2.30 person-months,
  so an extra agent costs **12 person-months a year** and returns **2.33**: a ratio of **0.19**. **On
  the queue's own books, loosening the occupancy loses by a factor of five** — which does not make it
  wrong, it means the case rests entirely on what a departure costs *outside* the queue, and naming
  that missing number is the deliverable.
- **On wave 1's queue there is no trade at all.** Every ceiling from 0.90 down to 0.70 needs the same
  twelve people, because the service level already delivers 0.6411 occupancy — under the knee, where
  attrition sits at its floor. The rate comes back `nan` rather than zero: zero would say the trade was
  free. **The occupancy-attrition problem is a large-queue problem**, the same boundary wave 7 found.
- **And the loop does not run away.** At the declared curve the fixed point is unique and the iteration
  reaches it from either end; the slope has to be **12.5 times steeper** before the plan's payroll can
  collapse. Two people short of the plan it splits at **five times** — so **robustness is a property of
  the payroll, not only of the curve**, which is a second and independent argument for funding the plan.
  And where two regimes exist, the one reached from crisis has *lower* occupancy and *lower* attrition:
  the abandonment is the escape valve. **That is the third time in this repository that abandonment is
  what stops something from diverging**, and it is the thing the business is trying not to do.

## And the formula that priced all of it was missing a term, not a calibration

Wave 3 applied the textbook routing threshold to this account's classifier score, found it **12.5%**
worse than the single swept number, and concluded that **calibration was the missing step**. That was an
assertion with no control behind it. The control exists now — the probability the generator actually uses
— and the diagnosis does not survive it.

- **Calibration is real, and it is not the missing step.** Fitted on three fifths of the month and judged
  on the remaining **12,709** contacts, the raw score's calibration error is **0.1618** against the
  control's **0.0061** — **26.68 times** — and in the bin where the score says **0.6502**, **0.9078** of
  the labels are right. Calibrating it cuts the formula's penalty **3.59 times**, from **17.04%** to
  **4.74%**. But on the perfectly calibrated probability the penalty is still **7.33%**, and there is no
  calibration left to do there.
- **What was missing is the reason the bot exists.** The closed form prices a wrong label and a deferral
  and treats a **right** label as free — when a correctly labelled contact the bot resolves *saves* the
  human seconds it would have taken. Carry that term and the rule becomes `(misroute − defer) /
  (misroute + benefit)`, which is the original formula exactly at a benefit of zero. The benefit runs the
  **opposite way** to the misroute cost — **142.68** seconds on rastreio against **23.32** on reclamacao —
  so the formula that prices only mistakes is most wrong where the bot is most useful: it demands 0.6667
  confidence on rastreio where **0.1974** is enough. The penalty falls to **1.96%** on the raw margin and
  **0.19%** on the calibrated one. **And 342.14 seconds on the uncalibrated margin beats 367.54 on the
  probability the generator actually used** — fixing the model beat fixing the input, and wave 3 pointed
  at the input.
- **The best-calibrated score is the worst ranker.** The control has the lowest calibration error in the
  table and the **highest** swept cost, **342.4383** against the raw margin's **335.5655**, because it is
  the only score that does not know what the classifier actually saw. Calibration and discrimination are
  different properties — wave 2's gauge that is unbiased and useless, in a second setting.
- **Optimism is a tenth of the finding, and the threshold was never the thing that was learned.** A
  threshold swept on the first three fifths costs **1.5076** seconds per contact more in the later period
  than that period's own best: **0.45%** of the bill and **13.05%** of the 11.5552 seconds wave 3
  published. It concentrates where the mistake is expensive and the sample is thin — **4.1790** on
  reembolso and **3.2614** on reclamacao, the two smallest groups and the two dearest misroutes. And the
  cuts move far more than the cost does: rastreio from **0.10** to **0.24**, prazo-de-entrega from 0.22 to
  0.38, for **0.1116** of a second. **The cost curve is flat near its optimum, so the cost was learned and
  the cut was not** — an operation arguing about a threshold's second decimal is arguing about sampling
  noise.
- **And the label a router can actually read is the better one to key on.** Wave 3's per-intent rule asked
  for the reclamacao threshold on a contact that *is* a complaint, which no deployment can do. The roadmap
  predicted the gain would shrink. It grows: keyed on the classifier's own label the rule saves
  **11.9210** seconds per contact against **10.9487** keyed on the truth, with **75 fewer** misroutes,
  because a wrong label is the event the cost is made of — so the reported label carries information about
  the classifier being wrong and the true label carries none. **Conditioning on what you know beats
  conditioning on what is true, when what you know is what the mistake is made of.** Out of sample and
  keyed on the readable label, wave 3's saving becomes **11.9210** against its published 11.5552 — a ratio
  of **1.0317**, **105.31** hours at the month's treated volume. Two corrections, opposite signs, nearly
  cancelling: the figure survives for a reason wave 3 did not name.

## And the thing that stopped every model from diverging was the customer leaving

Three waves leaned on the same relief valve without pricing it. Erlang A reaches a steady state
**because** customers give up; an occupancy ceiling is satisfied by understaffing **because** the
customers who abandon are what keeps occupancy down; the attrition loop's second regime is reached **by
losing customers**. Each time the note was that abandonment is the thing the business is trying not to
do. There was no currency to say how much of it happened, so there is one now.

- **A churn rate is a gauge, and this one reports 6% of what it flags.** Nobody can see a customer
  leave; an operation sees **silence**. Ten days of it, on 16,195 customers of whom **775** actually
  left, flags 8,040 people at a sensitivity of **0.6477** and a specificity of **0.5112**. So
  **93.76% of the customers the dashboard flags did not leave** — and because the Youden index is the
  exact factor a binary assessor multiplies a difference by, a comparison of two policies on this churn
  rate reports **15.89%** of the real gap, its index being **0.1589**. Wave 2 found a quality panel transmitting 69.45% and called
  it an instrument problem. This is the same identity at **a fifth** of that transmission.
- **And the rule is useless at both ends, for opposite reasons.** The index is not monotone in how often
  somebody contacts: **0.1008** at one contact, 0.1063 at two, **0.2678** at three, **0.0928** at four
  or more. At one contact it cannot see the stayers — being silent is what one contact means, so
  specificity is 0.3368. At four or more it cannot see the leavers — a frequent customer who leaves late
  still has a recent contact, so sensitivity collapses to 0.2791. **A silence window is a statement
  about contact frequency before it is a statement about leaving**, and one window for a whole book of
  customers is two instruments wearing one name.
- **Losing customers reduces the bill, and the KPI cannot see it.** The policy that drives away the most
  people books the largest reduction in human hours: `patient` loses **1,123** customers and saves
  **59.49** hours, against **257** and 24.49 for the human queue — monotone across all four policies,
  and every one of those hours arrives on the report as efficiency. The ranking by customers lost **is
  wave 1's containment ranking, exactly**: a fourth ranking of the same four policies, the second that
  agrees with the KPI while disagreeing with resolution and with time. And containment, recomputed on
  the contacts that survive, moves by **0.00017** — the numerator and the denominator fall together,
  which is what a ratio does when you remove the people it is a ratio over. The exchange rate, read out
  loud: on the containment-maximising policy **one saved hour costs 18.88 customers**.
- **The valve three waves used, priced in people.** Wave 3's "perfectly stable" six agents at 29.23%
  abandonment spend **557.74** customers a month; wave 7's eleven agents at 3.56% spend **67.93**. So
  stability costs **489.81 more customers a month** than compliance, and wave 7's humane-sounding
  occupancy target pursued alone costs **205.70 more**. Five agents buy that back: **97.96 customers a
  month per agent.** Which closes what wave 8 left open — it priced an extra agent at 12 person-months
  against 2.33 returned and said the case rests entirely on what a departure costs *outside* the queue.
  That is the quantity. There is still no money in this repository, so the price stays with the reader.
- **And the unit was wrong for nine waves.** Only **590** contacts disappear — 1.86% of the month —
  because a customer who leaves on day three loses twenty-seven days here and the rest of their life in
  an operation. Seconds, sessions, agents and hours are monthly quantities, and a month is the window
  every wave here measured in. Customers are not monthly. **Nine waves built an increasingly careful
  account in a unit that cannot express the loss at all**, and the only reason it took ten to notice is
  that the unit was never wrong about anything else.

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
| [`svclab.planning`](src/svclab/planning/README.md) | What headcount a set of declared ceilings buys rather than what one target reports, which of the ceilings actually decided it, how that changes with the size of the queue, and how close to breaching the chosen plan sits. |
| [`svclab.calibration`](src/svclab/calibration/README.md) | Whether the closed form for a routing threshold was given the wrong input or is missing a term, what a threshold fitted on one period costs in the next, and which label a rule a deployment can run has to be keyed on. |
| [`svclab.churn`](src/svclab/churn/README.md) | What an automation costs in customers rather than in seconds: whether the churn rate an operation can measure is an instrument at all, which policies lose the most people, and what the abandonment three waves used as relief spends. |
| [`svclab.workforce`](src/svclab/workforce/README.md) | What an occupancy costs in people rather than what a ceiling forbids: the payroll behind an agent count, the exchange rate between occupancy and hiring, and whether the attrition loop it closes ever runs away. |

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
| [`examples/07_the_constraint_nobody_declared.py`](examples/07_the_constraint_nobody_declared.py) | The three ceilings declared instead of reported: what each buys on its own, what wave 3's stable queue fails, where the economy of scale stops, and how much room the chosen plan has left. |
| [`examples/10_the_customer_who_stopped_calling.py`](examples/10_the_customer_who_stopped_calling.py) | The relief valve priced in people: what the month left its customers with, the silence rule measured as a gauge and split by contact frequency, what each policy costs in customers beside what it costs in hours, and the retention an extra agent buys. |
| [`examples/09_the_threshold_fitted_on_the_answer.py`](examples/09_the_threshold_fitted_on_the_answer.py) | The closed form given the input it assumes and then the term it was missing: the reliability of the score, the four versions of it priced against a sweep, what a threshold costs in a period it never saw, and the rule keyed on the label a router can read. |
| [`examples/08_the_payroll_behind_the_plan.py`](examples/08_the_payroll_behind_the_plan.py) | The occupancy ceiling priced in people: the payroll each plan actually needs, what a point of occupancy buys in hiring, the queue where there is nothing to trade, and how much steeper the attrition curve would have to be to spiral. |

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
python examples/07_the_constraint_nobody_declared.py
python examples/08_the_payroll_behind_the_plan.py
python examples/09_the_threshold_fitted_on_the_answer.py
python examples/10_the_customer_who_stopped_calling.py
```

## How the claims are kept honest

**471 tests, 100% statement and branch coverage.** 392 of them run in seconds and gate every push. The
remaining 79 re-derive, from the generator, every figure quoted in every README on this repository,
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

**And defects are recorded rather than quietly fixed.** Forty so far, in
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
