# 0012: Phase 5 plan, heat-insurance basis risk

Date: 2026-11-01. Status: accepted, 2026-11-01: my plan for Phase 5, checked by the Phase 5
review.

Goal: an environment that asks what a parametric heat policy pays and where it misses the
heat a policyholder had (basis risk), with every answer computed exactly from station data by
reference code that first reproduces published NWS Phoenix heat counts.

Context (docs/radar.md, 2026-11-01): the heat triggers found in real programs count days at
or above a temperature threshold and runs of consecutive such days; the VimoSEWA 2024 pilot,
for one, used ERA5 above 43.2 C on at least 7 days from April to July. No benchmark found covers
parametric triggers or basis risk.

Stage 1: the published number first.

- Data: GHCN-Daily `by_station/USW00023183.csv.gz` (Phoenix Sky Harbor), 1,479,584 bytes,
  anonymous HTTPS, Last-Modified Sun, 01 Nov 2026 00:01:02 GMT. NCEI publishes no checksum and
  rewrites the file daily, so I pin my own sha256 with the size and Last-Modified at first
  fetch, keep the copy under data/ (not in git), and fail on any mismatch. NOAA names no
  licence, only citations (doi:10.7289/V5D21VHZ).
- Reader: the standard library `gzip` and `csv` modules. TMAX is stored in tenths of a degree
  C, converted from whole degrees F, so thresholds go the same way: 110 F is 433, 100 F is
  378, 90 F is 322 (round((F - 32) * 50 / 9)). Values with a quality flag are dropped.
- Anchors, checked on the live pages on 2026-11-01: NWS Phoenix's 2023 climate summary
  (weather.gov/psr/yearinreview2023): "DAYS MAX >= 110 55", "DAYS MAX >= 100 133", "DAYS MAX
  >= 90 185", highest 119 on 07/19. NWS Phoenix's extreme temperatures page
  (weather.gov/psr/ExtremeTemps, Phoenix column): "Greatest number of 110° F or greater days 70
  (2024)", "Longest stretch of 110°F or greater days 31 (30 Jun 2023 - 30 Jul 2023)", "Longest
  stretch of 100° F or greater days 113 (27 May 2024 - 16 Sep 2024)", "Greatest number of 100°
  F or greater days 145 (2020)".

Stage 2, designed in its own decision once stage 1 passes: per-season policy questions with
exact answers over pairs of stations, one the index and one the insured site: trigger days,
payouts by events of consecutive days, and days the insured site was hot while the index was
not; a verifiers taskset and an Inspect task tested on mockllm; then a Claude Sonnet 5.5
baseline within the cap.

Out: Indian data (IMD names no licence, the GSOD readme bars passing on non-US derived
products, ERA5 daily statistics need a Copernicus account: those calls are mine to make later),
anything over 100 MB, heat index and wet-bulb formulas (on the radar for later).

Tests: inline rows with hand-computed counts; the reproduction tests run when the pinned file
is on disk and are skipped otherwise, so CI stays offline.
