# 0027: the heat items are public with the repository; the station files stay unpublished

Date: 2026-11-13. Status: accepted, 2026-11-13. Amends 0018.

Context: decision 0018 kept the GHCN-Daily station files unpublished, because the NCEI sources it
read (the product page, the readme and the ISO metadata) name no licence for GHCN-Daily and say
nothing about redistribution. The heat items still show those stations' values, so making the
repository public would publish data derived from them. The roadmap listed
that as my decision to make, before the repository went public.

Decision: on 2026-11-13 my choice was "flip", and the repository went public that day with the heat
items in it. My choice; the record gives no further reason.

Later on 2026-11-13 I answered the questions that left open with "yes for all": the heat items'
terms are stated as the two facts below and nothing more, and the draft Hugging Face card in
`docs/release/dataset-card.md` carries the heat items. The card stays a draft; nothing is published
to Hugging Face.

The two facts:

- NCEI's metadata page for GHCN-Daily (gov.noaa.ncdc:C00861) names no licence and asks for the two
  citations below.
- NOAA's NODD entry in the Registry of Open Data on AWS lists GHCN-Daily as CC0-1.0 (quoted below).
  Whether that covers files fetched from NCEI directly, as these were, is UNKNOWN.

What is public now, in the tree:

- `environments/heat_basis_v1/heat_basis_v1/heat_basis_v1.jsonl`, 300 items. Each one carries both
  of its stations' daily maximum temperatures (GHCN-Daily TMAX) for one season's cover window, 1 May
  to 30 September (153 days), in whole degrees F, with a gap where GHCN-Daily has no value or a
  quality-flagged one (`src/earthgym/heat/data.py`, `read`). Together the items cover 40
  station-seasons: USW00003192, USW00003184, USW00023183 and USC00028499, each from 2015 to 2024.
  The build checks that every value converts back to GHCN-Daily's tenths of a degree C exactly
  (`src/earthgym/heat/items.py`, `main`), so for those days the items are TMAX in other units, not a
  summary of it.
- Counts computed from the same station data, such as NWS Phoenix's 55 days at 110 F or more in
  2023, in `reports/heat/`, `tests/test_heat_reproduction.py` and
  `docs/reviews/phase-5-heat-basis.md`. The review of this change found no other file with the
  daily series (`docs/reviews/2026-11-13-go-public.md`).
- The citations and NOAA's disclaimer, in `environments/heat_basis_v1/heat_basis_v1/NOTICE`, which
  the root `NOTICE` names (`tests/test_licences.py` checks both).

What is not public: the raw station files, NCEI's `by_station/<station>.csv.gz`. They are not in
git (`data/` is ignored) and not on the `data-v1` release, whose one asset is the IBTrACS CSV.
Their pins stay in `earthgym.heat.data.STATIONS`.

The two citations NOAA asks for, in the ISO metadata for GHCN-Daily (gov.noaa.ncdc:C00861, read
again on 2026-11-13: access constraint `otherRestrictions`, no licence named), as the NOTICE
carries them:

- Menne, Matthew J., Imke Durre, Bryant Korzeniewski, Shelley McNeill, Kristy Thomas, Xungang Yin,
  Steven Anthony, Ron Ray, Russell S. Vose, Byron E. Gleason, and Tamara G. Houston (2012): Global
  Historical Climatology Network - Daily (GHCN-Daily), Version 3. Those four stations. NOAA
  National Climatic Data Center. doi:10.7289/V5D21VHZ. Accessed 2026-11-01.
- Matthew J. Menne, Imke Durre, Russell S. Vose, Byron E. Gleason, and Tamara G. Houston, 2012: An
  Overview of the Global Historical Climatology Network-Daily Database. J. Atmos. Oceanic Technol.,
  29, 897-910. doi:10.1175/JTECH-D-11-00103.1.

Read after the decision, on 2026-11-13: GHCN-Daily is also a NOAA Open Data Dissemination (NODD)
dataset, and its entry in the Registry of Open Data on AWS (`awslabs/open-data-registry`,
`datasets/noaa-ghcn.yaml`, last changed at 16872e9 on 2025-03-19, `ManagedBy` NOAA) says: "NOAA
data disseminated through NODD is made available under the Creative Commons 1.0 Universal Public
Domain Dedication (CC0-1.0) license". It also says: "NOAA requests attribution for the use or
dissemination of unaltered NOAA data. ... If you modify NOAA data, you may not state or imply that
it is original, unaltered NOAA data." The items came from NCEI's own files, not through NODD, and
this statement was read in that registry entry, not on an NCEI page, so whether it covers them is
UNKNOWN.

Consequences:

- 0018's first consequence no longer holds. With the repository public, the `data-v1` asset needs
  no account: on 2026-11-13 an anonymous request for it returned HTTP 206, so
  `earthgym.ibtracs.data.fetch` works for anyone, as 0018 said it would.
- The heat rebuild from public sources stopped by 2026-11-02, when NCEI served another build of a
  pinned station file (`docs/reproduce.md`), and on 2026-11-13 all four files differed from their
  pins (`docs/reviews/2026-11-13-go-public.md`). The published heat numbers do not need a rebuild;
  they can be recomputed from the committed items and per-item results.
- The draft Hugging Face card (`docs/release/dataset-card.md`) carries the heat items, with the
  same two facts and both citations. It is a draft; publishing it is a separate decision.
