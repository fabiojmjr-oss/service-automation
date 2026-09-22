# Roadmap

What is built, what is deliberately absent, and what is still open. One wave at a time, each one
ending in a state where every published figure is asserted by a test.

## Wave 1 — the containment that wasn't *(complete)*

A seeded contact centre, a bot that actually runs against it, the four defensible readings of its
containment rate, and the queue arithmetic its headcount case skipped.

| Delivered | Where |
| --- | --- |
| A seeded contact centre with a declared `difficulty` and the self-service counterfactual no operation has | `src/svclab/synth/` |
| Every draw an inverse transform of the uniform stream, enforced against the source | `synth._draws`, `tests/test_synth.py` |
| A control arm assigned per **customer**, so a repeat cannot cross the line | `CentreProfile.holdout_share` |
| A deployable bot policy that can see the predicted intent and the turn number, and nothing else | `svclab.bot.policy` |
| A session runtime that is a deterministic function of the contacts, with the repeat stream as rows | `svclab.bot.session` |
| Four containment definitions returned together, and the one that needs the counterfactual | `containment.containment_table` |
| Deflection against the control arm, clustered by customer, refusing when there is no arm | `containment.deflection` |
| Which contacts the bot kept, by the truth it cannot see | `containment.selection_profile` |
| Erlang B and C the numerically safe way, the staffing search, and the promise as a multiplication | `svclab.capacity.queue` |

**The thread running through it:** at every step the figure an automation programme reports is a
correct calculation of a quantity nobody chose deliberately — and each substitution flatters the
automation. Containment counts abandoned customers as successes. It counts contacts that needed
nobody. It ignores the second conversation an unresolved contact produces. And the headcount case
multiplies a queue by a proportion when a queue is Erlang.

The result I did not expect is Result 1 of
[`svclab.containment`](../src/svclab/containment/README.md). I built four containment definitions
expecting the strict ones to rank the policies correctly and the loose one to flatter. All four rank
`patient` first, and `patient` resolves 44.76% against `guarded`'s 72.71%. The answer is not a
stricter numerator: containment is a statement about the bot, resolution is a statement about the
customer, and no definition of the first can rank the second.

### Defects found and recorded

Each was found by connecting the modules, by a control case, or by writing a sentence — not by reading
code. They are documented rather than quietly fixed, because the class of mistake is the point.

1. **The first version of the session charged a repeat as extra seconds on the original contact.**
   Arithmetically tidier, and it destroyed the wave's central finding: with repeats folded into
   seconds, the human-handled share per contact is exactly one minus the containment rate, so
   deflection and containment are the same number *by construction*. The measurement said the
   containment rate was 99.89% honest, which is what a tautology looks like when you mistake it for a
   result. Repeats are now rows. Found by computing deflection and not believing the answer.
2. **A truth-column test that grepped the file text and failed on the docstring explaining the rule.**
   The policy module may not *reach* `difficulty`; it is entitled to *discuss* it. The test now parses
   the syntax tree and checks string literals, attributes and names, which is the difference between
   testing the rule and testing the prose.
3. **A test asserting the control arm produces no repeat sessions.** It produces one: a human who does
   not resolve the contact is a return too. My test demanded a property the design does not have —
   the design was right, and the arm is a fair comparison rather than a perfect one.
4. **A claim in one paragraph computed on two different denominators.** The bot README quoted
   escalation and abandonment shares from the full dataset and resolution shares from the treated arm,
   in the same sentence. Both were correct; the comparison between them was not. Found by verifying a
   sentence I had already written.
5. **Two dead draw functions carrying the package's coverage from 100% to 99%.** `normal` and
   `order_of` were written because the sibling repository has them, and nothing here consumes either.
   Deleted. Dead code in a portfolio repository is a liability, not a spare part.

## Wave 2 — the meter that was noise *(complete)*

Wave 1 ended with resolution as the quantity a bot policy should be judged on. Grading sessions is how
an operation measures that, so this wave qualifies the gauge before using it — and then prices what the
answers do to the comparison the panel exists to make.

| Delivered | Where |
| --- | --- |
| A quality panel with declared bias and spread per grader, and a second reading of every session | `synth.GRADERS`, `synth.quality_noise` |
| An automated assessor with its own bias and spread, reading everything once | `synth.JUDGE` |
| A session's quality as a declared function of its outcome and difficulty, against a declared standard | `quality.latent_quality` |
| Cohen's kappa, with the two corners and the constant-rater case named rather than guessed | `quality.kappa` |
| The attribute agreement analysis: repeatability, then sensitivity and specificity against the standard | `quality.agreement_table` |
| Reproducibility between every pair, on one replicate so the two problems stay apart | `quality.reproducibility` |
| The attenuation identity in closed form, and the Youden index that is its factor | `quality.attenuation`, `quality.youden` |
| What an unqualified gauge costs in sessions | `quality.sessions_for_difference` |

**The thread from wave 1.** Wave 1: the containment rate is a correct calculation of the wrong
quantity, and resolution is the right one. Wave 2: the instrument you would measure resolution quality
with was never qualified, and an unqualified binary gauge does not merely add noise — it multiplies
every difference by its Youden index, **towards zero, always**. This panel reports 69.45% of the real
gap between the arms. Nobody cheated; the instrument attenuates.

The result I did not expect is Result 5. I built the automated judge to be worse than the panel and it
came out better than every individual grader — and then the way it would actually be validated, against
the graders, scores it anywhere from 0.5450 to 0.7121 of kappa depending on which colleague was free.
The honest counterweight arrived with it: the panel as a **committee** beats the judge, 0.7979 against
0.7826. Averaging three moderate assessors recovers most of what each one loses, which is an argument
for a panel and not for any member of it.

### Defects found and recorded

1. **A repeat session's id was unique only within one call of `run`.** It was numbered from one past
   the largest contact *in that call*, so pooling the treated and control arms — which is exactly what a
   quality study does — produced two different sessions sharing an id, and the arrays stopped lining up.
   Ids are now derived from the contact id plus a declared offset, which makes them unique across any
   set of runs over disjoint contacts. **Found two waves after it was written, by connecting wave 2 to
   wave 1** — the defect was invisible to everything wave 1 did, because wave 1 never pooled two runs.
2. **A published sample size that counted the wrong unit.** The quality README said "1,200 sampled
   sessions ... 7,200 readings". The panel samples 1,200 **contacts**, which are 1,434 **sessions** once
   the repeats those contacts generated are counted, and therefore 8,604 readings. Both numbers were in
   the table directly below the sentence. Found by writing the claims test for a figure I had already
   published — the fourth time in this family of repositories that the test for a claim is what
   disproved it.
3. **A control case whose arithmetic I got wrong on paper.** A test asserted that two raters passing 95
   of 100 and agreeing on 90 have agreement above 0.90; it is exactly 0.90. Recomputing it properly
   improved the case: chance agreement at those margins is 0.905, so kappa is **−0.053**. Two raters who
   look like a working gauge agree slightly *less* than two coins weighted the same way. The corrected
   case is a better demonstration than the one I intended.
4. **Two draw functions deleted in wave 1 as dead code, needed again in wave 2.** `normal` went because
   nothing consumed it and coverage said so; the grader noise needs it. Restored, and the lesson is not
   that deleting it was wrong — it is that "dead code is a liability" and "this will be needed next
   wave" are both true, and coverage settles the argument rather than judgement.

## Wave 3 — the three numbers nobody priced *(complete)*

Waves 1 and 2 took three decisions by default: the router's threshold, the assumption that nobody
abandons a queue, and the comparison of two policies on the whole account. This wave prices all three,
each one on its own front.

| Delivered | Where |
| --- | --- |
| A classifier score per contact, the generator's accuracy margin rescaled and blurred once | `synth.routing_scores` |
| The cost-sensitive threshold in closed form, and what it assumes about the score it is given | `routing.calibrated_threshold` |
| The cost of a routing rule in human seconds, swept over a threshold or over a threshold per intent | `routing.cost_of`, `routing.cost_curve` |
| Erlang A as the birth-death chain with impatience, and the abandonment it implies where Erlang C has no answer | `capacity.abandonment`, `capacity.impatience_table` |
| The repeat feedback solved as a fixed point rather than as one pass | `capacity.load_with_repeats` |
| The Kish design effect, the ANOVA estimator of the intracluster correlation, and the significance level a clustered test really runs at | `experiment.design_effect`, `experiment.intracluster_correlation`, `experiment.actual_alpha` |
| Sample size for the comparison wave 1 made, at declared correlations | `experiment.sizing_table` |

**The thread from waves 1 and 2.** Wave 1: the reported quantity was the wrong one. Wave 2: the
instrument that would measure the right one was never qualified. Wave 3: the three numbers *inside* both
arguments — a threshold, a patience, a sample size — were never chosen at all, and each one moves the
conclusion by more than the modelling choices that were debated.

The result I did not expect is Result 3 of [`svclab.routing`](../src/svclab/routing/README.md). I wrote
the module expecting the closed-form threshold to beat the swept single number, because it is the
textbook answer and it is correct. Applied to this score it is **12.5% worse** than the number it was
meant to improve on. What survives is its ranking of the five intents, which is exact; what fails is
every level, because the formula's input has to be a probability and this score is a margin. The
finding is the one the documentation now carries, and it is the opposite of the sentence I first wrote.

The second thing I did not expect is Result 2 of
[`svclab.experiment`](../src/svclab/experiment/README.md): the measured intracluster correlation of this
account is approximately **zero**, because the generator draws every trait per contact, so a customer is
a label rather than a person. That is a limitation of my own simulator and it is published as one, with
the estimator verified against constructed corners instead. The alternative was to present a modelling
shortcut as a property of contact centres.

### Defects found and recorded

1. **Three published figures computed on one population and asserted against another.** The routing
   README quoted the mean score where the label is right, where it is wrong, and the label accuracy,
   from a probe that joined the scores to all 40,000 contacts; every table around them is computed on the
   31,802-contact treated arm. Corrected to the treated arm, they are 0.6975, 0.4293 and 0.7771. This is
   the third defect of exactly this class in this family of repositories, and the second in this one —
   which says the discipline that catches it is the claims test, not care.
2. **A module docstring claiming a result the measurement contradicted.** I wrote that per-intent
   *calibrated* thresholds beat the best single threshold before running them; they cost 388.89 seconds
   per contact against 345.63. The sentence was drafted from the theory and would have shipped as a
   finding. It was replaced by the true one — the ranking survives, the levels do not — which is a better
   result than the one I claimed.
3. **A numerical guard that did not guard.** The birth-death product form in `_queue_distribution`
   overflows at large agent counts; the tail tolerance was compared against a weight that had already
   reached infinity, the comparison became `nan`, and the function returned `nan` instead of refusing.
   A tolerance test is not a bound. It now rescales inside the loop and checks that every term is
   finite.
4. **Two branches that could not be reached, both found by the coverage report and neither by reading
   the code.** A literal `if False` left from drafting, and a degrees-of-freedom guard in
   `intracluster_correlation` that the caller's own validation had already made impossible. Branch
   coverage is the only reason either was noticed.
5. **A test that assumed a threshold of 1.0 defers every contact.** The score is clipped into the unit
   interval, so contacts sitting exactly at the ceiling survive the cut. The test was wrong and the code
   was right; the test now uses 1.5 and records why.
6. **A type error that only the matrix could see.** `best_by` took the winning threshold through
   `Series.idxmax()` and `.loc`, which type-checks against the pandas stubs my interpreter resolved and
   not against the newer ones the 3.12 job installed — `idxmax` returns a `Hashable`, and `.loc` has no
   overload for one. The gate was green locally and red on the first push. It now selects positionally
   through NumPy, which is version-independent and says what it means: take the first best row. **The
   second time in this family of repositories that a figure or a check held on one machine and moved on
   a clean install** — which is the reason the matrix exists and the reason the CI gate is not optional.

## Wave 4 — the customer who was a label *(complete)*

Wave 3 warned about clustering, went to measure it, and found nothing to measure: the generator drew
every trait per contact, so a customer was a label on a row. This wave builds the account a second
time with customers who are people, from the identical noise, and prices what the independence
assumption was worth.

| Delivered | Where |
| --- | --- |
| The uniforms behind every outcome kept in the contact table, so a second world can replay them | `synth.contacts`, `synth.outcomes_from_difficulty` |
| A per-customer percentile of difficulty and of patience, drawn last so no earlier figure moves | `synth.customer_components` |
| The Gaussian copula that adds the correlation and leaves every marginal distribution untouched | `synth.blend`, `synth.correlated_contacts` |
| The second dataset, assembled without redrawing anything | `synth.correlated_dataset` |
| Whether the correlation moved anything already published | `population.world_table` |
| The attenuation chain: declared, latent, observed on the trait, and on the outcome a test runs on | `population.correlation_table` |
| The measured design effect and the error rate a per-contact test really runs at | `population.design_table` |
| The power a sizing actually had, as the other side of wave 3's error rate | `population.power_at` |
| How often the same person was failed twice, against the independent world as a control | `population.pair_failures` |
| Three standard errors on one difference: naive, cluster-mean, and design-effect corrected | `population.error_table` |

**The thread from wave 3.** Wave 3's last open item was its own limitation: it priced design effects
at correlations it had to declare, because the world it measured had none. Wave 4 gives the world a
correlation and measures the whole chain — and the chain is the finding. A quarter of a contact's
difficulty belonging to the customer arrives as **4.5%** of the resolution a test is run on, which is
a design effect of 1.0432 rather than the 1.2891 wave 3 treated as its serious case. The alarm was
right in shape and seven times too loud in size.

The result I did not expect is Result 1 of [`svclab.population`](../src/svclab/population/README.md),
and it is the one that took the longest to earn. **Nothing already published moves** — eight metrics,
largest relative movement 0.89%, two human hours out of 2,730 — and every claims test from waves 1 to
3 passes unchanged against the new generator. That is not a null result. It is the precondition that
makes the rest of the wave a statement about dependence rather than about two things at once, and the
first version of the module did not have it.

The second thing I did not expect is Result 5. I built the standard-error table to show what the
correlation costs an interval, and the independent world's row says that **averaging each customer's
average inflates the standard error by 13.3% on data with no correlation in it at all** — nineteen
times the 0.7% the correlation itself is worth. The correction an analyst reaches for because it needs
no correlation estimate is more expensive than the problem. Only the control world makes that legible.

### Defects found and recorded

1. **The first construction changed two things at once.** The customer effect began as a convex
   combination of two draws — tidy, closed-form, and it multiplies the trait's variance by
   ``w**2 + (1 - w)**2``. At the declared weight that is 0.545, so the correlated world had a
   difficulty spread 26% narrower than the independent one, and the resolution rate moved from
   **0.6355 to 0.7166** for a reason that had nothing to do with customers. Replaced by a Gaussian
   copula, which holds the marginal distribution exactly and changes only the dependence. Found by
   building the table whose only job was to check that nothing moved — a table I nearly did not write,
   because the construction "obviously" preserved the mean.
2. **I measured the correlation of the trait and nearly published it as the design effect.** The first
   numbers out of this wave were the intracluster correlations of `difficulty` and `patience_turns`,
   0.2463 and 0.0740, and the design effect that follows from them is about 1.22. The quantity a test
   is sized on is the **outcome**, whose correlation is 0.0448 and whose design effect is 1.0432. Both
   numbers are in the module now, as the two ends of the attenuation chain, which is a better result
   than the one I was about to assert — but the mistake is exactly the one the module warns readers
   about, made first by its author.
3. **A refusal working correctly looked like a bug.** `design_table` crashed on the independent world:
   the measured design effect is 0.9879, and wave 3's `actual_alpha` refuses an effect below one
   rather than clipping a negative correlation estimate to nothing. My first instinct was that the
   guard was in the way. It was right, and the table now reports no error rate for that row, which is
   more honest than the 0.05 it would otherwise have printed.
4. **The truth-blindness test would have passed while protecting nothing.** Keeping the uniforms in the
   contact table added four columns that are truth by another route: a uniform plus the curve it was
   compared against **is** the answer. The AST test that stops `svclab.bot.policy` reaching a truth
   column knew only the old names, so it would have gone green while a policy read `u_self_serve`.
   Found by asking what the new columns mean rather than by a failure. A rule that does not grow with
   the table protects a shape the data no longer has.
5. **A published figure mis-rounded in transcription.** The pair-failure ratio is 1.067660 and the
   README quoted **1.0678**. Caught by the claims test the same hour it was written, for the fifth time
   in this family of repositories. The lesson has stopped being about care: transcription by hand is
   the defect, and the test is the control that makes it survivable.
6. **Two draw functions went dead the moment the transforms were separated, and only coverage said
   so.** Splitting `exponential` and `bernoulli` into a drawing half and a transforming half left the
   drawing halves with no callers at all - the contact table now draws its own uniforms and applies the
   transform itself. Coverage fell to 99% and named the two lines. Deleted, with the memorylessness
   note moved to the half that survived. **This is wave 1's fifth defect again, in a new costume**, and
   the repeat is the useful part: a refactor that makes a function's job smaller is exactly when a
   wrapper becomes ornamental, and judgement did not notice either time.

## Wave 5 — the frequent caller who was busy by accident *(complete)*

Wave 4 gave a customer traits and left their contact **rate** alone. Every contact still picked a
customer uniformly, so counts were Poisson with a mean below two and the busiest customer in the
account was busy by luck. This wave regroups the identical contacts into customers who do not all
contact equally often, with the heavy users correlated with the difficult ones.

| Delivered | Where |
| --- | --- |
| The uniform that chose a customer kept in the contact table, so the choice can be replayed | `synth.contacts` |
| A per-customer contact propensity, log-normal and correlated with that customer's own difficulty | `synth.propensity` |
| The regrouping itself, arm by arm, with every trait and every arm preserved | `synth.reassign_customers`, `synth.concentrated_dataset` |
| The declared control: the same regrouping at equal rates | `synth.EQUAL_RATES` |
| The size-weighted mean cluster size, which is the one a design effect is computed from | `experiment.effective_cluster_size` |
| How unequal the account is, and whether its heavy users are its difficult ones | `concentration.concentration_table` |
| Who pays: the top decile's share of volume, of failures and of human hours | `concentration.burden_table` |
| What a per-customer estimate loses in precision | `concentration.precision_table` |

**The thread from wave 4.** Wave 4 concluded that wave 3's clustering alarm was four times too loud on
this account. It measured that in a world where everybody contacts at the same rate — an assumption it
inherited rather than chose. Relax it and the design effect is **1.2246**, which is 95% of the 1.2891
wave 3 declared as its serious case. Two wrong assumptions in opposite directions, and their product
was close to right. The lesson is not that wave 3 was vindicated; it is that a design effect has two
inputs and this family of repositories had been arguing about one of them.

The result I did not expect is Result 3 of
[`svclab.concentration`](../src/svclab/concentration/README.md). The regrouping is exactly invariant
per contact — asserted as an identity, not a tolerance — and yet the resolution rate falls **1.53
points** once the traits are correlated within the new customers. The distribution of difficulty per
*customer* does not move; the distribution per *contact* does, because the difficult customers now send
more contacts each. A queue's mix of difficulty is a property of who calls, not only of who they are,
and I had published the invariance one wave earlier without noticing it had a boundary.

### Defects found and recorded

1. **Waves 3 and 4 put the wrong cluster size into the design effect.** Kish's inflation is
   ``1 + (m - 1) * rho`` for clusters of one size; with unequal sizes the quantity that belongs in it is
   the **size-weighted** mean, ``sum(m^2) / sum(m)``, because a randomly chosen contact sits in a
   cluster of that expected size. Wave 4 passed the plain mean and published a design effect of
   **1.0432**; the corrected figure is **1.0693**, the actual error rate moves from 0.0550 to 0.0580,
   the power at wave 3's sizing from 0.7859 to 0.7759, and the standard-error comparison's headline
   from nineteen times to twelve. In the concentrated world the same mistake would report 9.41% of
   extra sample where the answer is 22.46% — **less than half**, in the direction that lets a test
   ship. `population.design_table` now carries both columns so the size of the error stays visible, and
   `experiment.effective_cluster_size` is the correction. Found by writing a concentration measure,
   which forced the question "which m?" that four waves had not asked.
2. **My first control was the world waves 1 to 4 published, which would have credited an artefact to
   concentration.** Reassigning contacts among the customers an account actually saw raises the mean
   cluster size from 1.96 to 2.43 with **no concentration at all**, because a customer who was seen once
   can be seen twice while one who was never seen cannot enter. Comparing against the published world
   would have attributed that entire jump to the log-normal rate. The control is now the same
   regrouping at equal rates. Found by running the dispersion-zero case and not believing the customer
   count.
3. **I published an invariance one wave before finding its boundary.** Wave 4's headline is that
   nothing already measured moves; wave 5's regrouping is invariant per contact as an exact identity,
   and the combination of regrouping **and** correlated traits moves the resolution rate by 1.53
   points. The two statements are both true and the second one is the interesting one, but the first
   was published in a form that invited the wrong generalisation. The distinction is now Result 3
   rather than a footnote.
4. **A per-customer estimate compared across worlds with different customer counts.** Deflection per
   customer rises from 1.5484 to 1.7845 in the concentrated world and my first note called that a 15%
   rise in what the bot deflects. It is a denominator: the same volume divided among fewer people. The
   comparable quantity is the relative error, which rises 66%. Caught by asking where the rise came
   from before writing it down — the one habit that has caught more defects in this repository than any
   test.
5. **"The top decile of customers" is not a set, and two published figures moved because of it.**
   Contact counts are small integers and most customers tie, so ranking by count and taking the top
   tenth leaves the membership of the group to whatever order the sort happened to produce - and
   `sort_values` is not stable by default. The shares of unresolved contacts and of human hours
   therefore differed between this machine and the CI runner in the third decimal, while the share of
   *volume* did not, because a sum over tied counts is the same whichever tied customers are picked.
   **The gate caught it on the push, not before**: the fast suite compared worlds and the claims suite
   compared numbers, and only the second one crosses machines. The group is now defined by a declared
   contact count - four or more in the month - which is the same set everywhere, is comparable between
   two worlds that group the same contacts differently, and is how an operation would describe it
   anyway. The figures moved with the definition: 31.6% of volume became 58.1%, because a threshold
   catches more people than a tenth. **Third time in this family of repositories that a figure held on
   one machine and moved on another**, and the first where the cause was a definition rather than a
   draw. The defect also bought a search: every ranking primitive in the package was re-read, and the
   quality panel's sample now sorts its uniform keys stably. Two identical uniforms are vanishingly
   unlikely, so nothing moved - but the hazard is the same one and it is cheaper to close than to
   argue about.

## Wave 6 — the contact that came back twice *(complete)*

Every wave so far allowed an unresolved contact one return, and every wave named that as the reason its
figures were an underestimate. Wave 1 wrote that a containment rate becomes a permanent queue through
the geometric tail, and then truncated the tail at one term. This wave runs the chain.

| Delivered | Where |
| --- | --- |
| A declared chain: attempts, a decay on returning, a lift on being resolved | `synth.ChainProfile`, `synth.CHAIN` |
| The earlier waves' world kept as the default, so nothing published moves | `synth.SINGLE_RETURN` |
| Two uniforms per contact per further attempt, drawn last of everything | `synth.return_draws` |
| A session runtime that runs the chain, with the two-attempt case bit-identical | `bot.run(chain=..., draws=...)` |
| What each attempt held, and the resolution it accumulated | `chain.attempt_table` |
| The reopen rate, and the sessions one unresolved contact generates in closed form | `chain.reopen_rate`, `chain.sessions_per_unresolved` |
| What truncating the tail at one return costs, across the rates an operation might have | `chain.tail_table` |
| What the chain costs each policy | `chain.chain_table` |
| Days to resolution, which is the third ranking of the four policies | `chain.time_table` |

**The thread from wave 1.** Wave 1's finding was that containment ranks the policies in the exact
reverse of resolution. Wave 6 adds a third ranking, **days to resolution**, which agrees with
resolution and is steeper: `patient` takes 8.4 times as long as `human-only` to resolve a contact, and
40.5% of what it eventually resolves is resolved on a later attempt. A rate has no time in it, and the
customer pays in time.

The result I did not expect is Result 2 of [`svclab.chain`](../src/svclab/chain/README.md). I built the
chain expecting to find that five waves of figures had understated the queue, and the closed form says
they understated it by **0.18%**. A contact reopens only if the customer returns *and* the human failed
again, so the tail is a geometric series in the **product** - 0.6174 times 0.0695 here - and at a
reopen rate of 0.0429 there is no tail to find. The geometric tail wave 1 feared is not a property of
customers who come back. It is a property of an operation that keeps failing them: the same repeat rate
against a human who resolves 70% instead of 93% would double the queue's own workload. That is a
sharper and more actionable statement than the warning it replaces, and it arrived by measuring
something I expected to confirm.

Wave 3 deserves a note here rather than a defect. Its repeat feedback solved
`load = base x (1 + repeat x abandonment(load))` by iterating to a fixed point, and iterating that map
**is** summing the geometric series - so wave 3 was never truncating anything. The truncation lived in
the session runtime, and the two models now agree by construction rather than by coincidence.

### Defects found and recorded

1. **The second attempt reused the first attempt's human draw, and that is load-bearing rather than
   lazy.** A human who failed a contact once fails it again on the second attempt by construction,
   because `human_resolves` is one column. Keeping that is what makes the two-attempt world identical
   to the published one, so it stays - but it means the second attempt's resolution rate of 0.8157 is a
   property of **who was still open**, not a fresh trial, and reading it as "a human resolves 82% of
   returns" would be wrong. Documented in the module's limitations after I nearly quoted it that way in
   the README.
2. **My first chain never terminated for the hardest contacts, and the fix hid the problem.** With the
   human draw reused at every attempt, a contact whose human failed once could never be resolved, so
   every such contact used every attempt the chain allowed. Giving later attempts their own draw fixed
   it; compounding the declared lift then made the probability **clip at one**, which means a long
   enough chain here always terminates. That is now stated in `ChainProfile` and in the module's
   limitations, because it is a property of the parameter rather than of contact centres - an operation
   whose escalation path does not actually improve has no such guarantee, and it is the case this model
   cannot represent.
3. **A hand-built control case I got wrong on paper, again, and again it improved the test.** I wrote a
   test asserting that a contact nobody can help stays unresolved through four attempts. It resolves on
   the fourth: `reclamacao`'s human curve at difficulty 0.5 is 0.80, the lift compounds to 1.0576, and
   that clips to certainty. The test now asserts the saturation instead, which is a better thing to
   pin than the claim I intended - and it is the third time in this repository that recomputing a
   control case by hand produced a more interesting fact than the one I was reaching for.
4. **A dead constant survived the rewrite.** `MAX_REPEATS = 1` documented the truncation the chain
   replaced, and nothing imported it except the package's own `__all__`. Removed. Coverage does not
   catch an unused constant, which is why this one needed a grep rather than a report.
5. **A guard for something already refused upstream, for the second time in four waves.** The helper
   that aligns a return draw to the open contacts checked for missing draws, and `run` had already
   refused a long chain without them - so the line could not execute. Branch coverage named it, as it
   named wave 3's unreachable degrees-of-freedom guard. The helper now takes a frame rather than an
   optional one and an empty stand-in covers the case that can occur, which is the same lesson twice:
   **a guard written from imagination rather than from a path is dead code that looks like care.**

## Wave 7 — the constraint nobody declared *(complete)*

Every plan in waves 1 to 6 staffed to a service level and then reported the occupancy and the
abandonment it landed on. Wave 3's sharpest line was a queue "perfectly stable" at six agents, with
29.23% abandoning and the rest handled at 89.45% occupancy - both of them outputs. This wave declares
all three as ceilings and asks which one decides the headcount.

| Delivered | Where |
| --- | --- |
| A plan stated as constraints rather than as a target, refusing to be empty | `planning.Constraints` |
| The three measures at a staffing level, with occupancy on the **effective** load | `planning.metrics_at` |
| The smallest headcount that satisfies every declared ceiling | `planning.agents_for_constraints` |
| Which ceiling one fewer agent would have failed, joined when several bind at once | `planning.binding_constraint` |
| Every declared plan priced side by side | `planning.plan_table` |
| The same ceilings against queues from one erlang to four hundred | `planning.scale_table` |
| How much room each ceiling has left at the chosen headcount | `planning.headroom` |
| The napkin an occupancy ceiling implies with no queueing model at all | `planning.agents_at_ceiling` |

**The thread from wave 3.** Wave 3 found six agents stable and declined to call it a plan; wave 7
settles it - six agents **fails all three ceilings**, and "stable" only ever meant the queue has a
steady state. Wave 1's headcount error also reappears: the promise there multiplied a queue by a
proportion, and `load / occupancy ceiling` divides one by a proportion. The napkin gives 9 where the
queue needs 11, short by 18% of the requirement. Neither operation is a queue.

The result I did not expect is the middle row of Result 1. **An occupancy ceiling on its own is
satisfied by understaffing**: eight agents hold occupancy at 0.8121 while answering 17.51% of contacts
inside the target and losing 14.34% of customers, because the customers who abandon are exactly what
keeps the occupancy down. A humane-sounding ceiling, pursued alone, rewards a queue for losing people.
It is the same shape as wave 1's central finding in a place I was not looking: a correct calculation
of a quantity nobody chose deliberately.

The second thing I did not expect is where the economy of scale ends. Agents per erlang falls 61% from
one erlang to four hundred, which is the whole case for consolidating queues - and the binding
constraint moves from the service level to the occupancy ceiling at about 45 erlangs. Past that point a
bigger queue does not buy a cheaper plan; it buys a plan whose constraint has changed from an external
promise into an internal limit, and those are negotiated with different people.

### Defects found and recorded

1. **The same gap quoted on two different bases inside one wave.** The README said the napkin
   understates the requirement by **18%** and the example said **22%**: `(11 - 9) / 11` against
   `11 / 9 - 1`. Both are arithmetically true and they are different quantities, so a reader comparing
   the two artefacts would have found the wave contradicting itself. Standardised on the share of the
   requirement, with the reason written into the example beside the line. **Third defect in this family
   about a denominator**, and the first where both numbers were correct.
2. **A monotonicity the search depends on and nothing had checked.** `agents_for_constraints` searches
   upward and returns the first satisfying headcount, which is only the *smallest* one if all three
   measures are weakly monotone in agents. That held, and it was an assumption rather than an assertion
   until the test that walks the whole search range existed. The habit worth keeping is not the test -
   it is asking what a search silently assumes before trusting what it returns.

## Wave 8 — the payroll behind the plan *(complete)*

Wave 7 declared occupancy a ceiling. What a ceiling stands in for is a curve, and a curve turns a
constraint into a price. This wave prices it, which closes a loop none of the earlier waves contained:
occupancy raises attrition, attrition empties seats, an empty seat is not an agent, fewer agents raise
occupancy.

| Delivered | Where |
| --- | --- |
| An attrition curve with a declared base, knee and slope | `synth.WorkforceProfile`, `synth.WORKFORCE` |
| The producing share of a payroll: the vacancies and the ramp the attrition implies | `workforce.available_share` |
| The fixed point of the loop, iterated from a declared starting occupancy | `workforce.settle` |
| The death spiral reported as a **state** rather than raised as an error | `Settlement.collapsed` |
| The smallest payroll whose settled state satisfies wave 7's ceilings | `workforce.staffed_for_constraints` |
| The payroll behind each of wave 7's plans, with its empty and ramping seats | `workforce.payroll_table` |
| What a point of occupancy costs in people and buys in hires | `workforce.trade_table`, `workforce.exchange_rate` |
| Whether the loop has one resting place or two, across a range of slopes | `workforce.regime_table` |

**The thread from wave 7.** Wave 7 said the occupancy ceiling binds on large queues and left the ceiling
as a rule. Wave 8 prices it: twenty-seven more people on a hundred-erlang payroll buys 27.39 fewer hires
a year, an exchange rate of 1.01. And because this repository has no money in it, the rate reads in its
own currency - a departure wastes 2.30 person-months, so an extra agent costs 12 person-months a year
and returns 2.33, a ratio of 0.19. **On the queue's own books, loosening the occupancy loses by a factor
of five.** That is not an argument against doing it. It is a precise statement of the number a plan is
implicitly asserting when it does, and the repository declines to invent that number rather than hiding
the gap.

The result I did not expect is Result 3. I built the loop expecting a death spiral and the declared curve
does not have one: the fixed point is unique and the iteration reaches it from either end. The slope has
to be **12.5 times steeper** before the plan's payroll can collapse - and two people short of the plan,
only **five times**. So robustness to the spiral is a property of the **payroll**, not only of the
curve, which is a second and independent argument for funding a plan and one no queueing model makes.

The second thing I did not expect is what the second regime looks like where it exists. It is not a
collapse: it has *lower* occupancy and *lower* attrition than the healthy one, reached by losing
customers rather than by keeping agents, with the identical 21.0% abandonment. **Abandonment is the
escape valve, for the third time in this repository** - wave 3's Erlang A has a steady state exactly
where Erlang C has none because people leave; wave 7's occupancy ceiling on its own is satisfied by
understaffing because the customers who abandon keep occupancy down; wave 8's attrition loop finds its
second resting place the same way. Every model in this family is stabilised by the thing the business is
trying not to do, and noticing that three times is what made it worth writing down.

### Defects found and recorded

1. **A trade table whose exchange rate could not exist, and reporting zero would have hidden it.** On
   wave 1's 7.58-erlang queue every occupancy ceiling from 0.90 to 0.70 needs the same twelve people,
   because the service level already delivers 0.6411 occupancy - below the attrition curve's knee. The
   first version divided by a payroll change of zero and the test caught a rate of `nan` I had not
   planned for. Keeping the `nan` is the fix: zero would say the trade is free, and the truth is that
   **there is no trade to make**. Now stated in the function, tested as a property, and published as
   the boundary it is - the occupancy-attrition problem is a large-queue problem, the same boundary
   wave 7 found for its binding ceiling.

## Wave 9 — the threshold that was fitted on the answer *(complete)*

Wave 3 applied the textbook routing threshold to a margin, found it 12.5% worse than sweeping, and
published the reason: the formula wants a probability. That was an assertion with no control behind it,
and the roadmap recorded three of wave 3's defaults as open — the calibration, the in-sample fit, and the
rule keyed on the true label — predicting that each made the published saving an upper bound.

`svclab.calibration` closes all three and the prediction survives only one of them.

- `score.py` — the calendar split (`fit_period`), two calibrators fitted rather than assumed (`isotonic`
  by pool-adjacent-violators, `platt` by Newton's method), the reliability table and its expected
  calibration error, and the control: `true_probability`, the accuracy curve the generator actually uses.
- `selection.py` — `price` and `swept` (wave 3's pricing, on any subset and any key), `resolve_benefit`
  and `amended_threshold` (the closed form carrying the term wave 3's omits), `formula_table`,
  `optimism_table` and `key_table`.
- One parameter added elsewhere: `svclab.routing.defer_below` now takes a `key`, so a per-intent rule can
  be keyed on `predicted_intent`. The default is the true intent, which is what wave 3 priced, so no
  published figure moves. And `svclab.bot.classifier_labels` lifts the predicted label out of `run` so a
  router can read it without running the bot — the outcome frames are asserted unchanged.

**Result 1 — calibration is real and is not the missing step.** Raw calibration error 0.1618 against the
control's 0.0061; in the bin where the score says 0.6502, 0.9078 of the labels are right. Calibrating
cuts the formula's penalty 3.59 times, 17.04% to 4.74%. On the perfectly calibrated probability it is
still 7.33%.

**Result 2 — the missing piece is a term.** The closed form prices a wrong label and a deferral and
treats a right label as free. Carrying the benefit, `(misroute − defer) / (misroute + benefit)`, the
penalty falls to 1.96% on the raw margin — and 342.14 seconds there beats 367.54 from the naive formula on
the probability the generator uses. Fixing the model beat fixing the input by roughly four to one.

**Result 3 — the best-calibrated score is the worst ranker.** The control's swept cost is 342.4383 against
the raw margin's 335.5655, because it is the only score that does not know what the classifier saw.

**Result 4 — optimism is 1.5076 seconds per contact**, 0.45% of the bill and 13.05% of wave 3's saving,
concentrated in the two smallest and dearest intents. The thresholds move much further than the cost
does, so the cost was learned and the cut was not.

**Result 5 — the deployable key wins.** 11.9210 seconds per contact saved keyed on the classifier's label
against 10.9487 keyed on the truth, with 75 fewer misroutes.

### Defects found and recorded

1. **A published diagnosis that a control case refutes.** Wave 3 wrote "calibration is the missing step,
   and the closed form assumes it silently" in the root READMEs, the routing module's docstring, its
   package docstring and its README — four places, one unverified claim. The diagnosis is half right: the
   input really is wrong, and fixing it leaves 7.33% of the penalty standing, because the formula also
   omits the benefit of a correct label. What made it wrong was the missing control, not the missing
   measurement: there was nothing in wave 3 on which the formula was expected to be *exactly* optimal, so
   nothing could fail. All four statements are now corrected in place rather than deleted, and the
   correction points here.
2. **A prediction about the deployable rule that is backwards.** This file recorded that keying the rule
   on the predicted label would leave the direction intact and shrink the size of the gain. It grows it,
   from 10.9487 to 11.9210 seconds per contact, with 75 fewer misroutes. The reasoning behind the
   prediction treated the reported label as a noisy proxy for the true one, when for *this* decision it is
   the better conditioning variable: a wrong label is the event the cost is made of, so the reported
   label carries information about the classifier being wrong and the true label carries none. The
   corollary is recorded too — the three corrections do not all point the same way, and the two that
   matter nearly cancel, so wave 3's headline survives for a reason wave 3 did not name.
3. **A docstring describing a different function from the one that produced the figures.**
   `svclab.routing.defer_below` documented its per-intent mapping as keyed on the "**predicted** intent",
   noting that per intent is "the harder one to deploy, because the rule has to be keyed on what the
   classifier thinks" — while the code mapped the true `intent` column. Every per-intent figure in wave 3
   was therefore produced by the oracle rule and described as the deployable one. Nothing in wave 3 could
   catch it: the two readings differ only where the classifier is wrong, and no test asked which of them
   had run. Found by needing the deployable rule badly enough to go and read the code.

4. **A type that is only wrong on the Python the local gate did not run, for the second time in nine
   waves.** `GRID` was built as `tuple(round(value, 2) for value in np.arange(...))`. `round` on a
   numpy scalar returns a numpy scalar, so the constant's type is `tuple[floating[Any], ...]`, and
   every default argument annotated `tuple[float, ...]` is an assignment error. Locally mypy inferred
   `float` and the gate passed; on the 3.10 leg of the matrix it inferred `floating[Any]` and four
   functions failed. Wave 1's `Series.idxmax` defect was the same shape - a annotation that depends on
   which version of a stub is installed - and the lesson repeated is that a local gate is a sample of
   one environment. Fixed by making the values builtin floats, and pinned by a test that asserts the
   element **type** rather than its value, because equality cannot tell a numpy scalar from a float.
   The same spelling survives in the tests and the examples, where mypy does not look and the values
   are identical either way; it is left there rather than tidied, because a change no check can fail
   is churn.

One more thing was caught by its own test before publication and is recorded here only because the class
of mistake is worth naming: the first isotonic fit ran pool-adjacent-violators over individual points
rather than over pooled ties, so contacts sharing one score could be given different probabilities
depending on the order they happened to be stored in. A unit test asserting the fitted value at a
repeated score failed on the first run. It moved no published figure on this account, which is the part
worth noticing — the account's scores are nearly all distinct, so the defect was invisible in every
aggregate and visible only in a four-point example.

## The executive brief — `FINDINGS.md` *(complete)*

Eight waves of findings were readable only in the order they were built, next to the arithmetic that
produced them. The reader who has to *decide* needs the other cut: what each finding lands on, what a
competent operation would have decided without it, and what to do instead.

- [`FINDINGS.md`](FINDINGS.md) and [`FINDINGS.pt-BR.md`](FINDINGS.pt-BR.md) — one numbered finding per
  example, each in four movements (the decision, what the case said, what the account says, what to do
  instead), plus a closing section on what none of it says.
- **It derives nothing**, which is the risk: a second copy of a figure is a second place for it to go
  stale, and the claim tests cannot see a file they do not parse. So the coupling is asserted instead.
  `tests/test_findings_meta.py` extracts every quantity from the brief — decimals, percentages and
  counts of a hundred or more — and fails unless each one appears in the root README of the same
  language, which the slow suite re-derives from the generator. A third test compares the two editions
  to each other after normalising the decimal separator, because a figure corrected in one language and
  not the other is the defect this repository keeps making.
- The coupling test earned itself immediately: the first draft advised measuring the reopen rate and
  said a tail model is not worth building "below roughly 0.1". That threshold was **invented in the act
  of writing the sentence** — no test derives it, and nothing in the repository supports it. The build
  refused the figure before the commit existed. It was replaced by the two anchors wave 6 actually
  publishes: one return captures this queue to within 0.18%, and at a reopen rate of 0.5 it misses a
  third. The lesson generalises past this file — **prose is where unverified numbers enter a repository
  whose code is fully tested**, because prose is the only part nobody compiles.

## What is deliberately not here

- **No language model, and no API call to one.** The bot is a policy plus a declared response curve.
  A generated reply would make every figure in this repository unreproducible — a model version bump
  silently falsifies the text — and would need secrets in the repository. What is measured here is a
  policy, and a policy is arithmetic. This is the single most consequential exclusion in the file and
  it is a measurement decision, not a technical limitation.
- **No prompt engineering, no retrieval, no tool-calling agent loop.** All three are the subject of a
  later wave and none of them changes any conclusion in this one: a bot that resolves more of the easy
  end still leaves the residue, still generates the repeats, and still gets measured with the wrong
  numerator.
- **No industry containment benchmarks.** Every number here comes from the seeded generator. A
  benchmark quoted from memory cannot be put under test, and this repository's only real discipline is
  that its figures are asserted.
- **No cost in money.** Every cost here is a queue cost — sessions, seconds, agents. Licence fees,
  token costs and build effort all fall on the automation's side of the ledger, so a complete case
  would be worse for the bot than these figures, not better.
- **No dashboards.** The output is tables and a decision, which is what survives being pasted into a
  document.

## Still open

- **A benefit conditioned on more than the intent.** Wave 9's amended threshold uses one benefit per
  intent, averaged over contacts whose resolvability differs, which is why it lands within a fraction of
  a per cent of the sweep instead of on it. A benefit conditioned on the score itself would close more of
  that gap and needs its own held-out fit.
- **A period that actually drifts.** Wave 9's calendar split measures pure fitting noise, because nothing
  in this generator changes over the month. Distribution shift is the failure a held-out period is
  usually defended as testing, and it is the one this repository cannot yet exhibit.
- **A classifier whose confidence does not know the outcome.** The score here is built from the realised
  classification, which makes it a better ranker than any deployed confidence and is the mechanism behind
  wave 9's Result 3. A score built only from features the classifier could see would separate calibration
  from discrimination on honest levels rather than on this account's optimistic ones.

- **Attrition that depends on more than occupancy.** Wave 8's curve knows about how hard the work is
  and nothing else. Pay, management, commute, the labour market and the season all matter more in most
  operations, and a curve fitted to one operation's leavers is the first thing worth measuring before
  any of wave 8's arithmetic is trusted.
- **The transition rather than the steady state.** Every figure in wave 8 is a fixed point, which
  assumes the load, the curve and the hiring pipeline have been stable long enough to settle. The pain
  of a spiral lives in the months on the way there, and nothing here models them.
- **A hiring pipeline that can fail.** A departure is replaced immediately and always. No freeze, no
  role that cannot be filled, no candidate queue that empties - and each of those makes the payroll
  premium worse than the numbers published here.
- **A plan per interval, and shrinkage.** Every headcount in wave 7 staffs one steady state. A real
  plan solves each half hour and then loses agents to breaks, training and absence, which multiplies
  every figure here without changing any of the arguments.
- **A return that arrives on a distribution rather than on a grid.** Every return in wave 6 lands
  exactly one repeat window later, so days to resolution is a multiple of three days. Real returns
  arrive the same afternoon or three weeks later, and the ordering would survive while the levels
  gained the spread they are missing.
- **A return the bot is allowed to attempt.** A repeat goes straight to a human here, always. A
  deployment routes it to a bot that can see the previous conversation, which is a different policy
  question and the one wave 6's Result 3 would move under.
- **An escalation path that does not improve.** Wave 6's lift compounds and clips at one, so its chains
  always end. An operation whose second line is no better than its first has an unbounded tail, and
  that is the case the closed form in Result 2 prices and the simulation cannot reach.
- **Churn as an outcome.** A chain that ends because the customer left looks identical here to one that
  ends because the customer was helped. The difference is the only one the business cares about, and
  nothing in this repository can tell them apart.
- **More volume, not the same volume rearranged.** Wave 5 redistributes 31,802 contacts among fewer
  people, so every figure in it is the pure regrouping effect. An account whose frequent callers are
  difficult has *more* contacts than one whose are not, and that second effect is additive to
  everything wave 5 measured.
- **A rate that changes within the period.** A customer's propensity is constant here. Real escalation
  looks like a month of silence, a failure, and then nine contacts in a fortnight - which is a hazard
  model rather than a rate, and it would put the repeat chain and the concentration in the same
  mechanism.
- **A true heavy tail.** A log-normal rate has no outliers worth naming. The customer an operation
  discusses by name - two hundred contacts in a month - is a different distribution, and it moves the
  burden table further than it moves the design effect.
- **Tail dependence rather than a shifted mean.** A Gaussian copula gives a customer who is difficult
  a uniformly higher chance of being difficult again. Real escalations look like a heavy tail: mostly
  ordinary, occasionally catastrophic. A copula with tail dependence is the honest shape and it is a
  different parameter, not a different number.
- **Correcting for the attenuation rather than measuring it.** Wave 2's factor is measurable, so
  dividing the observed difference by it is available and is deliberately not offered: a correction
  applied to a gauge study this uncertain buys a point estimate and loses the interval. Propagating the
  gauge study's own uncertainty into the corrected difference is the honest version and is real work.
- **A grader who knows which arm the transcript came from.** Wave 2's attenuation identity assumes the
  two error rates are the same in both arms. Differential misclassification is the case that
  *exaggerates* a difference instead of hiding it, and it is the more likely failure in an operation
  where the reviewer can tell a bot transcript at a glance.
- **The value the queue cannot see.** A bot that answers at three in the morning, in a channel a
  customer prefers, has a value none of these tables contain. The honest statement is that it is
  absent, not that it is zero.
