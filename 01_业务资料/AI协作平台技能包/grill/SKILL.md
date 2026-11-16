---
name: grill
description: Critically challenge a business model, product strategy, investment case, or implementation plan. Use when the user asks to grill, interrogate, stress-test, find flaws, red-team, or assess feasibility; do not use for routine proofreading.
metadata:
  short-description: Red-team a business plan and turn risks into validation actions
---

# Grill

Conduct a rigorous but constructive pre-mortem. The aim is to find material objections before real investment, rather than to defend or casually dismiss the plan.

## Evidence and tone

- Be direct, but distinguish facts, supplied evidence, reasonable inference, and unverified assumptions.
- Do not invent market size, customer validation, budgets, regulatory status, or competitor capabilities. Mark missing evidence as `信息不足`.
- Every material challenge must state why it matters and end in a specific improvement, experiment, or decision.
- Use the plan's actual context (industry, customer, delivery model and constraints), rather than generic startup criticism.

## Default review

Unless the user narrows scope, review the plan through all three layers below.

### 1. Structured checks

Rate each item as `通过` / `存在风险` / `存在漏洞` / `信息不足`.

| Dimension | Checks |
| --- | --- |
| Problem reality | Is the problem evidenced, felt by buyers, severe enough to act on, time-sensitive, and prevalent in the target segment? |
| Market | Are TAM, SAM/SOM and their assumptions credible; is the market growing; is there a reachable buyer and a real budget? |
| Defensibility | Is differentiation perceptible and durable; are there data, technology, scale, network effects, or switching costs? |
| Business model | Who pays, how much and how often; are unit economics, costs, margin and path to profit credible? |
| Product and delivery | Is it standardizable and scalable; has customer and technical feasibility been tested; are boundaries clear? |
| Team and resources | Are the required industry, product, technology and sales capabilities, key roles, funding, data and relationships in place? |
| Risk and exit | What single risk could kill the business; what is Plan B; what happens in extreme scenarios; can failure be absorbed? |

### 2. Six-role red team

Challenge the plan from these views and report each one's decisive objections:

- Investor: scale, traction, use of funds, milestones, return path, and 12-month risk.
- Customer: quantified pain, alternatives, adoption cost, time to value, service continuity, security and compliance.
- Competitor: replication time, pricing/channel attack, customer poaching, and shallow moats.
- Regulator: licensing, privacy/data security, grey areas, policy changes, AI accountability, and legal relationships.
- Delivery team: a 90-day deliverable, roles, dependencies, data/technical proof, and Plan B if the first customer declines.
- Partner: value exchange, bypass risk, revenue sharing, dependency, data/brand risk, and alternatives.

### 3. Cautious challenger

1. Rewrite the business logic as a chain of `if → then` premises.
2. Mark each premise as fact, judgment, or assumption; identify its evidence and what would falsify it.
3. Locate the weakest link and estimate the consequence if it fails.
4. Test for common traps: pseudo-demand, project-service trap, platform cold start, subsidy dependence, pseudo-moat, adverse cost scaling, imagined window, and large-customer concentration.
5. Compare best-case, base-case, and worst-case conditions, impacts, triggers, and mitigations.

## Output

Use this compact report unless the user asks for another format:

```markdown
## [Plan name] — Grill report

**Scope:** structured checks + red team + cautious challenger

### 1. Check overview
| Dimension | Passed | Risks | Gaps | Unknowns |
| --- | ---: | ---: | ---: | ---: |
| ... | | | | |

### 2. Findings, sorted by severity
| Severity | Finding | Evidence / missing evidence | Impact | Validation or correction |
| --- | --- | --- | --- | --- |
| Fatal / Major / Moderate / Minor | | | | |

### 3. Six-role objections
State the key objection and the response or experiment for each role.

### 4. Critical assumptions
| Assumption | Type | Evidence strength | Consequence if false | Validation priority |
| --- | --- | --- | --- | --- |

### 5. Decision
- Maturity: high / medium / low
- Recommendation: proceed / proceed with conditions / pause and redesign
- Three highest-priority next validations: ...
```

## Source material

This Codex packaging is distilled from the user's original framework at `D:\G盘\code专属-商业模式\工作流\03-拷问Skill.md`. Read that source when a full 33-item rubric, role-by-role question bank, or feasibility-report template is needed.
