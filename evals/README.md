# Evaluation cases

`cases.json` is a public, fictional behavior-evaluation specification for this
Skill. It does not record a model run and does not prove any host or model
implements the behavior.

## Method

For each case, run two fresh contexts: one without the Skill and one with the Skill available.
Complete five repetitions per case for each condition. Use manual review for
every response against `expected_behaviors`, including reply shape, evidence
labels, decision path, and whether a final handoff was allowed.

Every case must be runnable by itself in a fresh context. A later-stage case
must carry a self-contained fictional prior state in its own prompt, including
the fictional prior answers, candidates, and explicit user decision needed for
that stage. This synthetic state is test input; it does not prove that a multi-turn interview occurred.

Record the date, model, host, model or host version if available, invocation
method, prompt, raw response, reviewer, and result. A dated record is evidence
only for the tested model-host combination and prompt set; do not generalize it
to other hosts, models, versions, or multi-turn conversations.

## Boundaries

Static repository tests check this JSON schema and written contracts. They do
not run models. All prompts and expected behaviors are fictional and are
designed to reveal overreach, not to validate demand, payment, acquisition, or
delivery economics.
