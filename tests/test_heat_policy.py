from earthgym.heat import policy, stats

T = stats.tenths(110)  # 433
# index: 05-01..05-04 at 110, a gap on 05-05, 05-06..05-07 at 110, 05-08 at 109; outside the
# window on 04-30 and 10-01
INDEX = {
    "20230430": 450,
    "20230501": T,
    "20230502": T,
    "20230503": T + 10,
    "20230504": T,
    "20230506": T,
    "20230507": T,
    "20230508": stats.tenths(109),
    "20231001": 450,
}
# the site: hot where the index is hot, and also on 05-05 (index missing) and 05-08
SITE = INDEX | {"20230505": T, "20230508": T, "20230509": T - 5}


def test_window_runs_from_may_1_to_september_30():
    days = policy.window(2023)
    assert (days[0], days[-1], len(days)) == ("20230501", "20230930", 153)


def test_trigger_days_count_the_window_only_and_never_a_missing_day():
    assert policy.trigger_days(INDEX, 2023, 110) == 6
    assert policy.trigger_days(INDEX, 2023, 111) == 1  # only 05-03 is above 110


def test_an_event_is_a_run_of_at_least_k_trigger_days_and_pays_once():
    assert policy.events(INDEX, 2023, 110, 2) == 2  # 05-01..05-04 and 05-06..05-07
    assert policy.events(INDEX, 2023, 110, 3) == 1  # the gap on 05-05 splits the runs
    assert policy.events(INDEX, 2023, 110, 5) == 0


def test_missed_days_are_hot_at_the_site_but_not_at_the_index():
    assert policy.missed_days(INDEX, SITE, 2023, 110) == 2  # 05-05 (index missing) and 05-08
    assert policy.missed_days(SITE, INDEX, 2023, 110) == 0  # the other way round
