# Official Challenge Basis

## Authoritative links

- DCT Abu Dhabi challenge statement: https://challengeon.atrc.ae/en/challenges/atp2026/pages/dct-challenge-statement?lang=en
- Competition rules: https://challengeon.atrc.ae/en/challenges/atp2026/agreements?lang=en
- ATRC announcement: https://atrc.gov.ae/news/advanced-technology-pioneers-competition-opens-applications-putting-real-uae-industry
- DCT Tourism Strategy 2030: https://dct.gov.ae/en/who.we.are/tourism.strategy.2030.aspx

The online pages are authoritative if this summary becomes stale.

## Problem to solve

Build an interactive scenario simulator that predicts how aviation changes affect Abu Dhabi hotel demand. The planner should be able to vary routes, frequency, capacity, load factor, market mix, season, events, transfer/transit share, and stay assumptions, then see hotel-demand effects by market and time of year.

The core semantic problem is that flight data identifies departure country while hotel data identifies guest nationality. These are not equivalent. Aggregate data cannot reveal individual passenger journeys, so any bridge between them must be described as a predictive allocation or effective conversion—not directly observed truth.

## Official evaluation weights

- Technical accuracy and modelling rigour: 40%
- Creativity and originality: 20%
- Practicality and realism: 20%
- Explanation and presentation: 20%

## Seven official success criteria

1. A working simulator, not a static report.
2. A transparent seats → passengers → visitors → hotel guest nights conversion chain with visible assumptions.
3. Historical validation on held-out periods using an honest error metric such as WMAPE.
4. Sensitivity analysis that identifies which factors matter most.
5. Useful source-market and seasonal granularity.
6. A short, non-technical explanation of what a DCT planner should do differently.
7. Reproducible, documented code with stated assumptions and acknowledged limitations.

## Expected conversion chain

```text
scheduled seats
× expected load factor
= arriving passengers
× expected P2P share
= passengers ending their journey in Abu Dhabi
× origin-to-nationality / visitor / hotel-capture allocation
= hotel arrivals by guest market
× stay profile
= hotel guest nights or guest stock
```

Realized passengers, P2P traffic, and hotel arrivals may be valid historical targets or stage diagnostics. They are not known for a future route decision and must not leak into planning-mode evaluation.

## Stakeholder lens

The primary owner and likely user is DCT Abu Dhabi. Operational users and affected stakeholders plausibly include tourism and aviation planners, Abu Dhabi Airports, airlines, hotels, destination-marketing teams, and event planners. Treat this broader list as an inference, not an official list.

The product should support decisions such as route pursuit, airline partnerships, seasonal capacity, hotel readiness, staffing, campaigns, and events. A technically accurate answer that does not change a planning decision is incomplete.

## Competition constraints to remember

- The expected outcome is a functional digital prototype, simulation, or proof of concept rather than a concept deck alone.
- Competition data is aggregated and is restricted to competition use.
- Assumptions and uncertainty should be explicit.
- Submission and eligibility requirements may change; verify the live rules when relevant.
