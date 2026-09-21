# Worked example — third-party generative AI in customer operations

**Status:** Demonstration record only. Synthetic organization. Not a production authorization.

This example shows how an AI use case is written into the same objects the Atlas register already uses.

## Risk

| Field | Value |
|---|---|
| Risk code | RISK-AI-001 (illustrative; not loaded into `grc_register.db` in v1.1) |
| Title | Unreviewed generative-AI drafts alter customer commitments |
| Category | Third-Party / Cybersecurity |
| Asset | Customer-operations knowledge base and ticket console |
| Owner | VP Customer Operations (accountable human) |
| Inherent likelihood / impact | 4 / 4 (score 16) |
| Status | Open |

**Description.** Agents paste ticket history into a vendor chat model to draft replies. The model can invent policy exceptions, quote incorrect SLAs, or include another customer’s details from the prompt window. No named reviewer is required before send.

## Observed facts (not judgments)

- Vendor subprocessors and training-use terms were not attached to the intake record.
- No retention limit is configured on the vendor workspace.
- No sample of outbound drafts is independently reviewed.
- Prompt-injection / data-exfiltration testing has not been performed.

## Mapped controls (CSF 2.0)

| Control idea | CSF category | Type | Implementation |
|---|---|---|---|
| Approved-tool inventory and named owner | GV.OC / GV.RR | Preventive | Planned |
| Data-class ban: no regulated or cross-customer text in prompts | PR.DS | Preventive | Partially implemented |
| Human send-authority for concession / legal / safety language | GV.PO | Preventive | Planned |
| Weekly sample review of AI-assisted tickets | DE.CM | Detective | Not implemented |
| Vendor BA / no-train clause | GV.SC | Preventive | Planned |

## Residual assessment (analytical judgment)

| Field | Value |
|---|---|
| Residual likelihood / impact | 3 / 4 (score 12) |
| Analyst | Governance reviewer (portfolio demonstration) |
| Rationale | Inherent risk stays high because the model can still fabricate a commitment. Likelihood is reduced one point only if the data-class ban is actually followed. Impact stays 4 because a single bad send can create a contractual or privacy event. Residual 12 is **not** acceptable for unsupervised send. |

## Exception handling

- **Allowed:** draft generation inside the approved vendor workspace.
- **Not allowed:** sending AI text that grants refunds, legal positions, medical advice, or safety instructions without a named human click.
- **Expiry:** 90 days or first production incident, whichever is first.
- **Rollback:** disable the vendor integration; revert to human-only drafts.

## Remediation

1. Record the tool in the AI-use inventory with data class and owner.
2. Turn on human-release for Amber/Red ticket types.
3. Sample 25 outbound drafts per week for fabricated policy.
4. Close the exception only when sample-review findings are documented.

## NIST AI RMF crosswalk (mapping language only)

| AI RMF function | How this example uses it |
|---|---|
| Govern | Named owner, prohibited uses, exception expiry |
| Map | Use case, data class, vendor, failure mode |
| Measure | Sample review of outbound drafts (not a published accuracy benchmark) |
| Manage | Residual rationale, rollback, dual control on consequential sends |
