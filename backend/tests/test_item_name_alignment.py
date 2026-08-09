import pytest

from app.core.config import Settings
from app.workflows.querying.item_name_alignment import ItemNameAligner


def align_with(matches: list[dict[str, object]]) -> tuple[list[str], list[str]]:
    aligner = ItemNameAligner(
        Settings(_env_file=None),
        matcher=lambda _names: [
            {
                "extracted_name": "RS-12",
                "matches": matches,
            }
        ],  # type: ignore[arg-type]
    )
    return aligner.align(["RS-12"])


def test_exact_name_match_is_confirmed_even_when_score_is_below_threshold() -> None:
    confirmed, options = align_with([{"item_name": "RS-12", "score": 0.55}])

    assert confirmed == ["RS-12"]
    assert options == []


def test_unique_high_confidence_candidate_is_confirmed() -> None:
    confirmed, options = align_with(
        [
            {"item_name": "RS-12 数字万用表", "score": 0.81},
            {"item_name": "RS-13 数字万用表", "score": 0.52},
        ]
    )

    assert confirmed == ["RS-12 数字万用表"]
    assert options == []


def test_clear_score_gap_confirms_first_of_multiple_high_candidates() -> None:
    confirmed, options = align_with(
        [
            {"item_name": "RS-12 数字万用表", "score": 0.92},
            {"item_name": "RS-13 数字万用表", "score": 0.74},
        ]
    )

    assert confirmed == ["RS-12 数字万用表"]
    assert options == []


def test_close_high_candidates_require_user_clarification() -> None:
    confirmed, options = align_with(
        [
            {"item_name": "RS-12 数字万用表", "score": 0.82},
            {"item_name": "RS-13 数字万用表", "score": 0.78},
        ]
    )

    assert confirmed == []
    assert options == ["RS-12 数字万用表", "RS-13 数字万用表"]


def test_middle_confidence_candidates_become_options_and_low_scores_are_dropped() -> None:
    confirmed, options = align_with(
        [
            {"item_name": "RS-12 数字万用表", "score": 0.66},
            {"item_name": "RS-13 数字万用表", "score": 0.59},
        ]
    )

    assert confirmed == []
    assert options == ["RS-12 数字万用表"]


def test_invalid_matcher_result_is_rejected() -> None:
    aligner = ItemNameAligner(
        Settings(_env_file=None),
        matcher=lambda _names: [{"extracted_name": "RS-12", "matches": None}],  # type: ignore[list-item]
    )

    with pytest.raises(Exception, match="候选结果格式无效"):
        aligner.align(["RS-12"])
