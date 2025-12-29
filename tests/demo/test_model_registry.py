from __future__ import annotations

from typing import Any, Dict

import pytest

from ai_utilities.demo.model_registry import MODEL_ID_PLACEHOLDER, build_catalog


def test_build_catalog_contains_curated_local_endpoints() -> None:
    catalog = build_catalog()
    names = {f"{m.display_name} – {m.model}" for m in catalog}

    assert any(name.startswith("LM Studio (local) –") for name in names)
    assert any(name.startswith("FastChat (local) –") for name in names)
    assert any(name.startswith("text-generation-webui (local) –") for name in names)


def test_placeholder_used_when_no_models_discovered() -> None:
    catalog = build_catalog()
    assert any(m.model == MODEL_ID_PLACEHOLDER for m in catalog)
