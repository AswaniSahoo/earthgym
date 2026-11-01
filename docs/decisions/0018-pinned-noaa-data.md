# 0018: the pinned IBTrACS build as a release asset; the GHCN-Daily files stay local

Date: 2026-11-02. Status: accepted, 2026-11-02. From the Codex review's finding 1, with my rule
for fix batch 1: publish the pinned NOAA files as a GitHub release asset if their terms allow
redistribution, and if the terms are unclear, do not upload and document the limitation.

Context: NCEI publishes no checksum and overwrites its files in place, so my pins are my own
sha256s, and a stranger can rebuild the items only while NCEI still serves the bytes I pinned.
On 2026-11-02 NCEI served `ibtracs.NA.list.v04r01.csv` with `Last-Modified: Sun, 01 Nov 2026
10:03:22 GMT`, a day after the pinned build (Fri, 30 Oct 2026 04:27:28 GMT), and the bytes were
still the pinned ones; the next change to any storm record will change them. The Phoenix Sky
Harbor station file still had its pinned `Last-Modified` (Sun, 01 Nov 2026 00:01:02 GMT).

Terms, read at the source on 2026-11-02:

- IBTrACS. The "Terms of Use" on NCEI's IBTrACS page
  (https://www.ncei.noaa.gov/products/international-best-track-archive): "IBTrACS was developed
  to support scientific research efforts. The IBTrACS data usage policy follows the World Data
  Center for Meteorology (WDC), which provides full and open access to the data. We have
  agreements from the Regional Specialized Meteorological Centers that provide track data to
  make IBTrACS data open for distribution to contribute to global tropical cyclone research. We
  also use the World Meteorological Organization's Resolution 40 policy as the guide for
  commercial use of IBTrACS data." The ISO metadata (gov.noaa.ncdc:C01552) adds the citation
  and NOAA's distribution and use liability statements.
- GHCN-Daily. NCEI's product page
  (https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily)
  has no terms section. The readme (https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt,
  version 3.35) says how to cite the dataset and nothing about use or redistribution. The ISO
  metadata (gov.noaa.ncdc:C00861) sets the access and use constraints to `otherRestrictions`,
  and its only constraint text is the citation and the same liability statements. No licence is
  named anywhere.

Decision:

- IBTrACS: the terms allow it. Its providers agreed "to make IBTrACS data open for distribution
  to contribute to global tropical cyclone research", and rlenv is research. The pinned build is
  an unmodified asset of the release `data-v1`
  (https://github.com/AswaniSahoo/rlenv/releases/tag/data-v1, tag at commit ed9654c), with the
  terms and both citations in the release notes. GitHub's digest of the asset is the pinned
  sha256, and a download of it with `gh release download` hashed to the same value.
  `rlenv.ibtracs.data.fetch` tries the asset first, then NCEI, and keeps a copy only if its
  sha256 is the pin. Commercial use follows WMO Resolution 40, as the terms say; rlenv makes
  none.
- GHCN-Daily: the terms are unclear. NOAA names no licence for it and says nothing about
  redistribution, so the pinned station files are not uploaded.

Consequences:

- The repository is private, so only accounts with access to it can download the asset:
  anonymously its URL returns 404, and fetch falls back to NCEI. Collaborators and CI use
  `gh release download data-v1 -p ibtracs.NA.list.v04r01.csv -D data/ibtracs`. If the
  repository becomes public, the plain fetch works for anyone.
- heat-basis-v1 can be rebuilt only while NCEI serves the pinned station builds (their sha256s
  are in `rlenv.heat.data.STATIONS`). Once NCEI rewrites a file with new data, the hash check
  refuses it, and the items cannot be rebuilt from public sources. The published heat numbers
  do not need the station files: they can be recomputed from the committed per-item results.
- To lift the limit: a statement from NCEI that GHCN-Daily may be redistributed, or my
  decision to publish the files on another basis.
