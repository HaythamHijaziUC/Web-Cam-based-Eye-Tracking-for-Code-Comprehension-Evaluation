import tempfile, os, math, pytest
from unittest.mock import patch

def make_file(tmp_path, content):
    f = tmp_path / "data.txt"
    f.write_text(content)
    return str(f)

def test_load_data_basic(tmp_path):
    path = make_file(tmp_path, "1.0\n2.5\n3.0\n")
    result = load_data(path)
    assert result == [1.0, 2.5, 3.0]

def test_load_data_empty(tmp_path):
    path = make_file(tmp_path, "")
    assert load_data(path) == []

def test_load_data_invalid_raises(tmp_path):
    path = make_file(tmp_path, "1.0\nnot_a_float\n")
    with pytest.raises(ValueError):
        load_data(path)

def test_normalize_sum_to_one():
    assert abs(sum(normalize([1.0, 2.0, 3.0, 4.0])) - 1.0) < 1e-9

def test_normalize_zero_total_raises():
    with pytest.raises(ZeroDivisionError):
        normalize([0.0, 0.0, 0.0])

def test_compute_statistics_known():
    mean, std = compute_statistics([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
    assert abs(mean - 5.0) < 1e-9
    assert abs(std - 2.0) < 1e-9

def test_compute_statistics_uniform():
    mean, std = compute_statistics([3.0, 3.0, 3.0])
    assert mean == 3.0 and std == 0.0

def test_main_high_variance():
    with patch("__main__.load_data", return_value=[0.1, 0.9, 0.1, 0.9]), \
         patch("builtins.print") as mock_print:
        main()
    output = " ".join(str(c) for c in mock_print.call_args_list)
    assert "High variance detected" in output

def test_main_low_variance():
    with patch("__main__.load_data", return_value=[0.5, 0.5, 0.5]), \
         patch("builtins.print") as mock_print:
        main()
    output = " ".join(str(c) for c in mock_print.call_args_list)
    assert "Variance is normal" in output

def test_main_above_average_index():
    with patch("__main__.load_data", return_value=[1.0, 3.0]), \
         patch("builtins.print") as mock_print:
        main()
    output = " ".join(str(c) for c in mock_print.call_args_list)
    assert "Value 1 is above average" in output
    assert "Value 0 is above average" not in output