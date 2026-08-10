# Solo Business Startup Positioning Interview

`interview-solo-business-startup-positioning` is an Agent Skill for a person
who needs to form and compare possible directions for a solo business,
independent project, or side business before commercial validation.

It uses a one-question-at-a-time interview to turn lived experience,
capabilities, resources, interests, constraints, and reachable people into two
or three positioning hypotheses. It does not replace commercial validation.

The Chinese mirror, [README.zh-CN.md](README.zh-CN.md), covers the same
user-facing scope, including guidance corresponding to `适合谁`, `如何开始`,
`会得到什么`, and `能力边界`. Its core interview rule is `一次只问一个问题`,
and its next stage is `商业化验证`.

## Who it is for

Use this Skill when you have no direction, too many directions, or a vague
direction that needs formation and comparison. If you already have a clear
project and need to test demand, payment, acquisition, or delivery economics,
use [solo-business-validation-skill](https://github.com/muujaa1000-jack/solo-business-validation-skill)
instead.

## Install

Install this repository using the mechanism provided by your Agent Skills host.
The repository root is the Skill directory; its invocation name and frontmatter
name are both `interview-solo-business-startup-positioning`.

For host-specific installation, consult the host's own documentation. This
repository contains a standard `SKILL.md` and supporting references; it does
not claim that installation or runtime behavior has been verified on every
host.

## Start an interview

Ask your host to use the Skill, for example:

```text
Use the solo-business startup positioning interview. Ask one question at a time
and help me find a direction to validate first.
```

You can also invoke it by name where your host supports named Skills:

```text
$interview-solo-business-startup-positioning
```

## What the interview produces

- A bounded view of experience, capabilities, resources, interests, reachable
  people, and constraints.
- Two or three candidate positioning hypotheses to compare.
- An explicit user choice to select, combine, or retain candidates.
- A seven-section final handoff, including a card for the next validation
  stage.

See the [complete fictional positioning example](examples/complete-positioning.md)
and the [insufficient-evidence example](examples/insufficient-evidence.zh-CN.md).
Public fresh-context prompts and their review method are in the
[evaluation cases](evals/README.md). These are written examples and static
evaluation specifications, not proof of model behavior.

## Commercialization validator

The handoff card is a `待验证假设` (hypothesis to validate), not proof of a
market. Pass it to [solo-business-validation-skill](https://github.com/muujaa1000-jack/solo-business-validation-skill)
to test demand, payment, acquisition, and delivery economics. This Skill does
not approve full development, outreach, publication, charging, or spending.

## Compatibility and verification

The repository follows the public Agent Skills directory pattern: `SKILL.md`,
an optional `agents/` metadata file, and referenced instructions. It is
intended for Codex, Claude Code, and other hosts that choose to interpret this
pattern. Directory-level similarity is not a claim of live installation,
model behavior, or compatibility for any particular host or version.

Read the current host guidance before installation: [Codex Skills](https://developers.openai.com/codex/skills/),
[Claude Code](https://docs.anthropic.com/en/docs/claude-code), and the
[Agent Skills specification](https://agentskills.io/specification).

Static repository contracts can be run with:

```text
python -X utf8 -m unittest discover -s tests -p "test_*.py" -v
```

Those contracts check written rules and repository artifacts only. Dated model
and host observations, when available, belong in `docs/validation.md`; they do
not prove multi-turn stability, cross-model behavior, or commercial outcomes.

## Evidence boundaries

The five information states are `材料已核实`, `用户陈述`, `外部推断`,
`待验证假设`, and `未知`. The Skill must not invent customers, market demand,
prices, channels, results, or personal advantages. A completed positioning
interview is not market validation and does not promise income or fit.

## Develop and release

Contributions should preserve the first-turn single-question contract, the five
information states, the candidate-decision paths, and the seven-section final
handoff. Add or update a contract or evaluation before changing behavior. See
[CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and
[CHANGELOG.md](CHANGELOG.md). The current source version is in [VERSION](VERSION).

Build the deterministic release artifacts and verify them against a fresh
canonical build from the source files:

```text
python -X utf8 scripts/package.py --output-dir dist
python -X utf8 scripts/verify_artifacts.py dist/interview-solo-business-startup-positioning-0.1.0.zip dist/interview-solo-business-startup-positioning-0.1.0.skill
```

### Release artifacts

The release workflow is configured to publish exactly these three assets for
`v0.1.0`:

- `interview-solo-business-startup-positioning-0.1.0.zip`
- `interview-solo-business-startup-positioning-0.1.0.skill`
- `SHA256SUMS`

Do not describe the Release as complete until the remote GitHub Release and
all three downloaded assets have been verified.

## License

[MIT](LICENSE)
