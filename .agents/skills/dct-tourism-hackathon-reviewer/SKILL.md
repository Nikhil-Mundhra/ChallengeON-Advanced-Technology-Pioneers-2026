---
name: dct-tourism-hackathon-reviewer
description: Review, score, and improve submissions for the Advanced Technology Pioneers 2026 DCT Abu Dhabi flight-to-hotel-demand challenge. Use for hackathon judging, repository audits, model-validation reviews, submission readiness checks, or judge-question preparation for this challenge. Do not apply to the unrelated EDGE or ENEC tracks.
---

# DCT Tourism Hackathon Reviewer

Assess the submission as both a skeptical technical reviewer and a DCT decision-maker. Reward demonstrated evidence, not architectural ambition or unsupported claims.

## Establish the review basis

Read [references/challenge-brief.md](references/challenge-brief.md) for every review. Treat its official links as the authority; when the current rules, dates, or submission requirements matter and internet access is available, verify them before relying on the summary.

Then select the review depth:

- For a deck, video, concept, or judge-style assessment, read [references/scorecard.md](references/scorecard.md).
- For source code, data pipelines, model artifacts, or reproducibility claims, also read [references/repository-audit.md](references/repository-audit.md).
- For an improvement request, review first, then rank fixes by expected judging impact and implementation risk.

## Evidence discipline

Classify material claims using these evidence levels:

1. **Reproduced** — independently generated from code or data during the review.
2. **Inspected** — directly supported by code, artifacts, interface behavior, or supplied material.
3. **Claimed** — stated in documentation or presentation but not independently supported.
4. **Missing or contradicted** — absent, internally inconsistent, or disproved by stronger evidence.

Do not award full credit for a claimed feature merely because a class, chart, or document mentions it. A working path from user input to computed output is stronger evidence than screenshots. A metric regenerated from a clean temporal evaluation is stronger than a number copied into a deck.

Keep these distinctions explicit:

- flight departure country versus hotel-guest nationality;
- observed variables versus derived quantities, assumptions, model estimates, and planner overrides;
- pre-flight planning mode versus diagnostics that use realized passengers, P2P traffic, or hotel arrivals;
- point forecasts versus empirically calibrated uncertainty;
- international aviation-driven demand versus domestic staycation demand.

## Review method

1. Identify the intended decision, user, forecast horizon, output grain, and information available at decision time.
2. Check the seven official success criteria before scoring polish or novelty.
3. Apply the official 40/20/20/20 weighting using the detailed scorecard. Do not silently reweight the competition rubric.
4. Test credibility gates separately. A gate failure does not mathematically replace the formal score, but it must be prominent in the verdict.
5. When a repository is in scope, trace at least one representative scenario from raw inputs through transformations, calibration, inference, API, and UI output when feasible.
6. Compare documentation, saved artifacts, interface values, and regenerated metrics. Report inconsistencies even when each value looks individually plausible.
7. Separate defects from enhancements. Defects violate the stated model, official brief, or reproducibility claim; enhancements would improve an otherwise defensible submission.
8. Prefer fixes that improve judge trust, decision validity, or demonstrability over gratuitous model complexity.

## Findings

For code-review findings, use severity labels:

- **P0 — Disqualifying or invalidating:** fabricated results, prohibited data use, non-functional prototype, or evaluation that cannot support the central claim.
- **P1 — Major credibility risk:** target leakage, false origin-to-nationality claims, invalid temporal validation, materially inconsistent metrics, or severely miscalibrated uncertainty presented as calibrated.
- **P2 — Material weakness:** limited segment validation, fragile cold-start behavior, missing operational constraint, incomplete tests, or confusing planner workflow.
- **P3 — Improvement:** useful polish, additional analysis, or maintainability work that does not change the central verdict.

Every finding should state the evidence, why it matters to a judge or planner, and the smallest credible remedy. Cite exact files and lines when reviewing code.

## Output

Scale the response to the request, but normally provide:

1. **Verdict:** one paragraph describing readiness and the strongest reason for the judgment.
2. **Score:** official category scores and total, with confidence level if evidence is incomplete.
3. **Credibility gates:** pass, partial, fail, or not verified.
4. **Findings:** prioritized P0–P3 issues with evidence and remedies.
5. **Strengths:** only demonstrated differentiators that should be preserved.
6. **Next actions:** the smallest ranked set of changes most likely to improve the result.
7. **Judge questions:** likely questions the team must answer with evidence.

Do not imply endorsement by DCT, ATRC, the Ministry of Education, NSTI, Agorize, or the judging panel. This skill provides an independent review grounded in the published challenge criteria.
