# Draft: a Hugging Face dataset card for the four item sets

Not published. Field rules read on 2026-11-02 from huggingface/hub-docs at `d086ec6`
(`datasetcard.md`, `docs/hub/repositories-licenses.md`, `docs/hub/datasets-cards.md`) and
huggingface_hub at `5077876` (`repocard_data.py`).

## The heat items and their terms

The card carries the heat items (decision 0027). Each one shows two GHCN-Daily stations' daily
maxima for a season, so publishing the card would publish data derived from GHCN-Daily. The raw
station files are not published (decision 0018). The card states two facts about their terms and
claims nothing more:

- NCEI's metadata page for GHCN-Daily (gov.noaa.ncdc:C00861) names no licence and asks for two
  citations. It also disclaims any warranty. The citations and the disclaimer are in
  `environments/heat_basis_v1/heat_basis_v1/NOTICE`.
- NOAA's NODD entry in the Registry of Open Data on AWS (`awslabs/open-data-registry`,
  `datasets/noaa-ghcn.yaml`) lists GHCN-Daily as CC0-1.0. Whether that covers files fetched from
  NCEI directly, as these were, is unknown.

## The card

```yaml
---
pretty_name: earthgym
license: other
license_name: per-config
license_link: LICENSE.md
configs:
  - config_name: climaqa
    data_files:
      - split: test
        path: climaqa/climaqa_clean_v1.jsonl
  - config_name: era5
    data_files:
      - split: test
        path: era5/era5_forecast_v1.jsonl
  - config_name: ibtracs
    data_files:
      - split: test
        path: ibtracs/ibtracs_storm_v1.jsonl
  - config_name: heat
    data_files:
      - split: test
        path: heat/heat_basis_v1.jsonl
task_categories:
  - question-answering
size_categories:
  - n<1K
tags:
  - rl-environment
  - verifiers
  - climate
  - weather
---
```

`license: other` with `license_link: LICENSE.md`, since each config keeps its source's terms,
spelled out in that file: ClimaQA-derived items under Apache-2.0 (the source dataset's card);
ERA5-derived items under CC BY 4.0 with the Copernicus attribution; IBTrACS-derived items under
IBTrACS's terms ("open for distribution to contribute to global tropical cyclone research", WMO
Resolution 40 for commercial use); heat with the two facts above and both citations. The hub docs:
"In case of `license: other` please add the license's text to a `LICENSE` file inside your repo ...
and set a name for it in `license_name`". The `rl-environment` and `verifiers` tags are the ones the
hub docs added on 2026-10-13. `config_name` "is required even if you have a single subset".

The card's text, below the metadata: what each set asks and how it is graded (from each
environment's README), the held-out split by group (decision 0017), the gold check (decision
0021), the results with links to the reports, and the citations: ClimaQA (arXiv 2410.16701),
ERA5 and WeatherBench 2, IBTrACS (doi:10.25921/82ty-9e16) and GHCN-Daily (doi:10.7289/V5D21VHZ).
