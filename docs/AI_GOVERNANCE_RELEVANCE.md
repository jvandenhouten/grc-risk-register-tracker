# AI Governance Relevance

This repository is a **cybersecurity GRC** artifact. It is relevant to AI governance because the same controls an organization needs for models, vendors, and human-in-the-loop decisions already live in a risk register: ownership, inherent vs residual scoring, evidence, exceptions, and accountable approval.

## What transfers from this register to AI risk

| GRC object in this repo | AI-governance analogue |
|---|---|
| Risk owner | Named human who accepts residual model or vendor-AI risk |
| Observed control status | Logging, access control, evaluation, human review — things that were actually checked |
| Residual score + rationale | Why this use case may proceed despite remaining uncertainty |
| Remediation action | Exception expiry, additional review, vendor contract clause, monitoring |
| NIST CSF mapping | Crosswalk to NIST AI RMF Govern / Map / Measure / Manage |

## What this repo does **not** claim

- It is not a formal ISO/IEC 42001 implementation.
- It does not report a measured accuracy improvement from multi-model review.
- It does not treat model consensus as proof of truth.
- Joel is not positioned here as a machine-learning engineer.

## Worked example

See [AI_RISK_EXAMPLE.md](AI_RISK_EXAMPLE.md) for one generative-AI vendor risk written in the same schema language as the Atlas register: owner, controls, residual-risk rationale, exception handling, and remediation.
