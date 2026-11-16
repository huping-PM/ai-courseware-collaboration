---
name: grill-with-docs
description: A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go.
---

# Grill with Docs

## Purpose

This skill runs a `/grilling` session — a structured, relentless interview that pressure-tests a plan or design. It systematically probes for:

- **Hidden assumptions** — what's being taken for granted?
- **Missing context** — what stakeholders, constraints, or risks haven't been named?
- **Weak reasoning** — are the causal links sound?
- **Gaps** — what's not covered?
- **Unresolved trade-offs** — what hard choices were glossed over?

As the grilling progresses, the session produces two living documents:

- **ADR (Architecture Decision Record)** — captures each decision, its context, options considered, and the rationale for the chosen approach.
- **Glossary** — defines domain terms as they surface, ensuring shared vocabulary.

## How to Invoke

When the user types `/grilling`, begin the grilling session:

1. Ask what plan, design, or proposal they want to grill.
2. If they already stated it (in the conversation or selected text), use that as the target.
3. If nothing is provided, ask: "What plan or design would you like me to grill?"

## Grilling Protocol

For each round of questioning:

1. **State what you hear** — summarize the relevant part of the plan before questioning it.
2. **Probe** — ask 1-3 sharp questions about that part (not a flood).
3. **Document** — if the user's answer reveals a decision, capture it as an ADR entry; if a term needs defining, add it to the glossary.
4. **Proceed** — move to the next aspect or follow the thread.

Focus on one thread at a time. Don't jump around. Let the conversation breathe.

### Dimensions to cover (over the full session, not all at once)

- **Goal clarity**: Is the problem correctly defined? Is success measurable?
- **Stakeholders**: Who benefits? Who loses? Who needs to consent?
- **Constraints**: Time, budget, regulation, technology, skill, capacity.
- **Risks**: What could go wrong? What's the worst-case scenario?
- **Alternatives considered**: Was this chosen over something else? Why?
- **Causal logic**: Does A actually lead to B? What's the mechanism?
- **Dependencies**: What must be true for this to work?
- **Scalability**: Does this work at 1×? 10×? 100×?
- **Exit criteria**: When would you abandon this approach?

## ADR Format

When a decision surfaces, document it inline:

```
## ADR-{n}: {Title}

**Context**: {what prompted this decision}
**Decision**: {what was chosen}
**Options considered**: {what else was explored}
**Rationale**: {why this option won}
**Consequences**: {what this decision implies}
```

## Glossary Format

When a term needs defining:

```
**{Term}**: {definition}
```

## Completion

When the user is satisfied or says "stop", summarize:

1. All ADRs created (with links if saved)
2. All glossary entries
3. The top 1-3 action items or open questions

If the session was done on a file, offer to save the ADRs and glossary alongside it (e.g. `docs/adr/` and `docs/glossary.md`).
