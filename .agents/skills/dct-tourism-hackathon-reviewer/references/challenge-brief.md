# Official Challenge Basis

## Authoritative links

- DCT Abu Dhabi challenge statement: https://challengeon.atrc.ae/en/challenges/atp2026/pages/dct-challenge-statement?lang=en
- Competition rules: https://challengeon.atrc.ae/en/challenges/atp2026/agreements?lang=en
- ATRC announcement: https://atrc.gov.ae/news/advanced-technology-pioneers-competition-opens-applications-putting-real-uae-industry
- DCT Tourism Strategy 2030: https://dct.gov.ae/en/who.we.are/tourism.strategy.2030.aspx

The online pages override this summary if it goes stale.

## Problem to solve

An interactive scenario simulator predicting how aviation changes affect Abu Dhabi hotel demand. Planners vary routes, frequency, capacity, load factor, market mix, season, events, transfer/transit share, and stay assumptions, and see hotel-demand effects by market and time of year.

Flight data gives departure country; hotel data gives guest nationality. They are not equivalent and aggregate data cannot link journeys, so any bridge must be described as a predictive allocation or effective conversion, never observed truth.

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

Realized passengers, P2P traffic, and hotel arrivals may serve as historical targets or stage diagnostics; they are unknown for a future route decision and must not enter planning-mode evaluation.

## Stakeholder lens

- Primary owner and user: DCT Abu Dhabi. Other plausible users (tourism/aviation planners, Abu Dhabi Airports, airlines, hotels, destination marketing, event planners) are an inference, not an official list.
- The product must support decisions: route pursuit, airline partnerships, seasonal capacity, hotel readiness, staffing, campaigns, events. An accurate answer that changes no planning decision is incomplete.

## Competition constraints to remember

- Expected outcome: a functional prototype, simulation, or proof of concept, not a concept deck alone.
- Competition data is aggregated and restricted to competition use.
- Assumptions and uncertainty must be explicit.
- Submission and eligibility rules may change; verify the live rules when relevant.
