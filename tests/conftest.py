import json
from pathlib import Path

import pytest

from rules.loaders import load_brief, load_catalog, load_profile, load_scoring_config

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def catalog():
    return load_catalog()


@pytest.fixture
def scoring_config():
    return load_scoring_config()


@pytest.fixture
def test_profile():
    return load_profile(FIXTURES_DIR / "profile_test.yaml")


@pytest.fixture
def test_brief():
    return load_brief(FIXTURES_DIR / "brief_test.yaml")


def load_fixture_asset(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


@pytest.fixture
def asset_pass():
    return load_fixture_asset("asset_knowledge_pass.json")


@pytest.fixture
def asset_fail_critical():
    return load_fixture_asset("asset_knowledge_fail_critical.json")


@pytest.fixture
def asset_missing_data():
    return load_fixture_asset("asset_knowledge_missing_data.json")
