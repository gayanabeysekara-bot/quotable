from evaluation.metrics import accumulate, false_alerts_per_camera_per_day, match_events, match_frame, percentile


def test_perfect_match():
    c = match_frame([((0, 0, 1, 1), 0.9)], [(0, 0, 1, 1)])
    assert (c.tp, c.fp, c.fn) == (1, 0, 0) and c.precision == 1 and c.recall == 1


def test_fp_and_fn_counted():
    c = match_frame([((0, 0, 0.1, 0.1), 0.9), ((0.5, 0.5, 0.6, 0.6), 0.8)], [(0.5, 0.5, 0.6, 0.6), (0.8, 0.8, 0.9, 0.9)])
    assert (c.tp, c.fp, c.fn) == (1, 1, 1)


def test_duplicate_predictions_are_false_positives():
    c = match_frame([((0, 0, 1, 1), 0.9), ((0, 0, 1, 1), 0.8)], [(0, 0, 1, 1)])
    assert (c.tp, c.fp) == (1, 1)


def test_accumulate_and_empty_metrics():
    c = accumulate([([], []), ([], [(0, 0, 1, 1)])])
    assert c.fn == 1 and c.precision is None and c.recall == 0


def test_event_matching_with_tolerance():
    c = match_events([1.0, 10.0, 30.0], [1.5, 11.9, 50.0], tolerance_s=2.0)
    assert (c.tp, c.fp, c.fn) == (2, 1, 1)


def test_helpers():
    assert percentile([1, 2, 3, 4], 0.5) == 2.5
    assert false_alerts_per_camera_per_day(6, 3, 48) == 1.0
    assert false_alerts_per_camera_per_day(1, 0, 24) is None
