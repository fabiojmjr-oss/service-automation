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

Every module README is bilingual and carries an **Assumptions and limitations** section, because a
figure without its assumptions is not a result.

## Examples

| Example | What it shows |
| --- | --- |
| [`examples/01_the_containment_that_wasnt.py`](examples/01_the_containment_that_wasnt.py) | Four policies on one account: the four containment rates and the ranking each produces, which contacts the bot kept, what the queue actually received against what was claimed, and the headcount case decomposed into its three errors. |
| [`examples/02_the_meter_that_was_noise.py`](examples/02_the_meter_that_was_noise.py) | The gauge study run before the comparison: repeatability, reproducibility, bias against a declared standard, the exact factor by which the panel shrinks every difference, what that costs in sessions, and what an automated judge would be validated against. |
| [`examples/03_three_numbers_nobody_priced.py`](examples/03_three_numbers_nobody_priced.py) | The three defaults priced: the routing threshold swept against both objectives and against its closed form, the queue with impatience and with the repeat feedback solved to its fixed point, and what a real test of two policies costs once customers are allowed to repeat. |

## Install and run

```bash
python -m pip install -e ".[dev]"
make check       # lint, types and the fast suite - what gates a push
make check-all   # the above plus every documented figure re-derived
python examples/01_the_containment_that_wasnt.py
python examples/02_the_meter_that_was_noise.py
python examples/03_three_numbers_nobody_priced.py
```

## How the claims are kept honest

**216 tests, 100% statement and branch coverage.** 183 of them run in seconds and gate every push. The
remaining 33 re-derive, from the generator, every figure quoted in every README on this repository,
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

**And defects are recorded rather than quietly fixed.** Fourteen so far, in
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
