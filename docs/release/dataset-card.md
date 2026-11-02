# Draft: a Hugging Face dataset card for the four item sets

Not published. Field rules read on 2026-11-02 from huggingface/hub-docs at `d086ec6`
(`datasetcard.md`, `docs/hub/repositories-licenses.md`, `docs/hub/datasets-cards.md`) and
huggingface_hub at `5077876` (`repocard_data.py`).

## A licence question to settle first

The heat items carry GHCN-Daily values: each one shows both stations' daily maxima for a
season. NOAA names no licence for GHCN-Daily, and for that reason I did not publish the raw
station files (decision 0018). Publishing the heat items, here or by making the repository
public, publishes data derived from them. The same question applies to the bundled items in
`environments/heat_basis_v1/` whenever the repository goes public. It needs my decision first:
leave heat out of the card, or publish on a stated basis.

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
Resolution 40 for commercial use); heat as settled above. The hub docs: "In case of `license:
other` please add the license's text to a `LICENSE` file inside your repo ... and set a name for
it in `license_name`". The `rl-environment` and `verifiers` tags are the ones the hub docs added
on 2026-10-13. `config_name` "is required even if you have a single subset".

The card's text, below the metadata: what each set asks and how it is graded (from each
environment's README), the held-out split by group (decision 0017), the gold check (decision
0021), the results with links to the reports, and the citations: ClimaQA (arXiv 2410.16701),
ERA5 and WeatherBench 2, IBTrACS (doi:10.25921/82ty-9e16) and GHCN-Daily (doi:10.7289/V5D21VHZ).
