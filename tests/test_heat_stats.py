from earthgym.heat import stats

# 110 F is 433 tenths of a degree C, 112 F is 444
SERIES = {
    "20230629": 428,
    "20230630": 433,
    "20230701": 444,
    "20230702": 433,
    "20230703": 428,
    "20230704": 433,
}


def test_whole_degrees_f_map_to_tenths_of_a_degree_c_as_ghcn_stores_them():
    assert [stats.tenths(f) for f in (110, 100, 90)] == [433, 378, 322]
    assert [stats.fahrenheit(stats.tenths(f)) for f in range(-40, 130)] == list(range(-40, 130))


def test_days_at_or_above_count_within_the_year():
    assert stats.days_at_or_above(SERIES, 2023, 110) == 4
    assert stats.days_at_or_above(SERIES, 2023, 111) == 1
    assert stats.days_at_or_above(SERIES, 2024, 110) == 0


def test_longest_run_needs_consecutive_dates_and_a_missing_day_breaks_it():
    assert stats.longest_run(SERIES, 2023, 110) == (3, "2023-06-30", "2023-07-02")
    gap = {"20230630": 444, "20230702": 444}
    assert stats.longest_run(gap, 2023, 110) == (1, "2023-06-30", "2023-06-30")
    assert stats.longest_run(SERIES, 2023, 120) == (0, None, None)


def test_highest_is_the_whole_degree_value_and_its_first_date():
    assert stats.highest(SERIES, 2023) == (112, "2023-07-01")
