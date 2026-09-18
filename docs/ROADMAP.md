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

- **Erlang A, and what impatience in the human queue changes.** Every capacity figure here assumes
  nobody abandons while waiting for an agent, which is false and is the assumption the whole family of
  models is most often wrong about. The direction of every comparison survives; the agent counts do
  not.
- **The classifier as a measurement system, with a cost-sensitive threshold.** The routing classifier
  here has an accuracy curve and no confidence score, so no policy can threshold on one. Misrouting a
  complaint and misrouting a tracking question have wildly different costs, which makes threshold
  selection a Gage R&R problem before it is an F1 problem — and the attribute agreement analysis a
  Master Black Belt would run on human QA graders applies unchanged to an automated judge.
- **Sizing the bot's own A/B test.** The comparison in this wave uses the whole account on both sides.
  A real deployment tests one policy against another on a fraction of the volume, contacts are not
  independent because customers repeat, and the design effect from clustering by customer inflates the
  error rate a per-contact test believes it has.
- **Repeat chains rather than one repeat.** A customer whose second attempt also fails does come back,
  and the geometric tail is what turns a containment rate into a permanent queue.
- **Occupancy as a constraint rather than a report.** The plans here hit a service level and report the
  occupancy they arrive at. Real staffing has a ceiling on occupancy before attrition rises, and a plan
  that ignores it buys the service level with turnover.
- **The value the queue cannot see.** A bot that answers at three in the morning, in a channel a
  customer prefers, has a value none of these tables contain. The honest statement is that it is
  absent, not that it is zero.
