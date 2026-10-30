# 0007: what a Phase 3 task asks

Date: 2026-10-30. Status: proposed. Stage 2 starts only after Aswani chooses.

Context: stage 1 gave a grader that reproduces two published WeatherBench 2 scores exactly
(IFS HRES MSLP at 72 h, 2020: RMSE 133.890547 Pa and ACC 0.981878;
`reports/era5/2026-10-30-wb2-reproduction.md`). The README says Phase 3 is "graded against
weatherbench2", which fits two task designs. The radar found no environment that scores
forecasts with the WB2 rules; numeric question answering over ERA5 already exists (Zephyrus,
TerraBench; `docs/radar.md`).

Options:

1. Forecast-answer tasks. A prompt gives a 64x32 grid cell, a variable (MSLP or 2 m
   temperature), an init time in 2020, a lead of 24, 48 or 72 h, the cell's ERA5 values over
   the three days before the init and the climatology at the valid time. The reply is a
   forecast value on a last line `ANSWER: <number>`. The eval reports WB2-graded RMSE and ACC
   over all items, next to persistence, climatology and HRES at the same cells. The RL reward
   per item is a bounded function of the error scaled per variable. This measures forecasting
   and gives RL a graded signal; the per-item scale is a choice to make and test.
2. Score-computation tasks. A prompt gives a small crop of HRES forecasts, ERA5 truth and
   climatology and asks for the area-weighted RMSE, bias or ACC under the WB2 rules. The reply
   is checked against the grader within a relative tolerance. This is exact and simple, but it
   mostly tests arithmetic and knowledge of the conventions, close to existing numeric QA.

Proposal: option 1. Both options reuse the stage 1 grader, and the data for option 1 (ERA5,
climatology and HRES for MSLP and 2 m temperature, 2020, three leads) fits under 100 MB by the
radar's sizes. No paid run: tests use mockllm, and a baseline needs Aswani's yes.

Consequences: option 1 adds a per-variable error scale and a persistence baseline to the
grader, each test-first; option 2 adds only a tolerance.
