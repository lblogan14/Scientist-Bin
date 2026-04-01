"""Tests for the metrics bridge (results JSON parsing)."""

from scientist_bin_backend.execution.metrics_bridge import parse_results_json


def test_parse_results_json_valid():
    stdout = (
        "Some training output...\n"
        "===RESULTS===\n"
        '{"results": [{"algorithm": "RF", "metrics": {"accuracy": 0.95}}], '
        '"best_model": "RF", "errors": []}'
    )
    result = parse_results_json(stdout)
    assert result is not None
    assert result["best_model"] == "RF"
    assert len(result["results"]) == 1
    assert result["results"][0]["metrics"]["accuracy"] == 0.95


def test_parse_results_json_with_trailing_output():
    stdout = (
        "Training...\n"
        "===RESULTS===\n"
        '{"results": [], "best_model": "LR", "errors": []}\n'
        "Some extra output after JSON\n"
    )
    result = parse_results_json(stdout)
    assert result is not None
    assert result["best_model"] == "LR"


def test_parse_results_json_no_marker():
    stdout = "Just some training output without results marker"
    result = parse_results_json(stdout)
    assert result is None


def test_parse_results_json_invalid_json():
    stdout = "===RESULTS===\nnot valid json at all"
    result = parse_results_json(stdout)
    assert result is None


def test_parse_results_json_empty():
    result = parse_results_json("")
    assert result is None
