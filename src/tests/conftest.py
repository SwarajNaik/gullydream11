"""Test fixtures and configuration."""

import pytest


@pytest.fixture
def sample_player_score():
    """Sample player score data for testing scoring engine."""
    return {
        "runs": 45,
        "balls": 30,
        "fours": 4,
        "sixes": 2,
        "overs": 0,
        "wickets": 0,
        "runs_conceded": 0,
        "maidens": 0,
        "catches": 1,
        "stumpings": 0,
        "run_outs": 0,
        "is_starting_xi": True,
    }
