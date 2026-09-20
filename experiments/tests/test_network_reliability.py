from experiments.network_reliability import deterministic_delivery_plan, percentile


def test_percentile_interpolates_sorted_values() -> None:
    assert percentile([40, 10, 20, 30], 0.5) == 25
    assert percentile([1, 2, 3, 4, 5], 0.95) == 4.8


def test_delivery_plan_is_seeded_and_bounded() -> None:
    first = deterministic_delivery_plan(100, 0.2, 42)
    second = deterministic_delivery_plan(100, 0.2, 42)
    assert first == second
    assert 65 <= sum(first) <= 95
    assert all(deterministic_delivery_plan(10, 0, 1))
    assert not any(deterministic_delivery_plan(10, 1, 1))
