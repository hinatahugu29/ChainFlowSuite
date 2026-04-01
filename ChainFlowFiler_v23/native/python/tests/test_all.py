import pytest
import native


def test_sum_as_string():
    assert native.sum_as_string(1, 1) == "2"
