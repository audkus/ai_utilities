from __future__ import annotations

import os
from typing import Any, Dict

import pytest

from ai_utilities.demo.model_registry import MODEL_ID_PLACEHOLDER, ModelDef, ProviderId
from ai_utilities.demo.validation import ModelStatus, validate_model


def test_validate_model_needs_key_for_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AI_API_KEY", raising=False)
    model = ModelDef(
        provider=ProviderId.OPENAI,
        display_name="OpenAI (cloud)",
        model="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        requires_env="AI_API_KEY",
        is_local=False,
        endpoint_id="openai",
    )

    validated = validate_model(model)
    assert validated.status == ModelStatus.NEEDS_KEY


def test_validate_model_unreachable_for_local(monkeypatch: pytest.MonkeyPatch) -> None:
    model = ModelDef(
        provider=ProviderId.OPENAI_COMPAT_LOCAL,
        display_name="LM Studio (local)",
        model="some-model",
        base_url="http://localhost:1234/v1",
        requires_env=None,
        is_local=True,
        endpoint_id="lmstudio",
    )

    # Force server check to fail by removing requests.get via env? Instead rely on actual unreachable.
    validated = validate_model(model)
    assert validated.status in {ModelStatus.UNREACHABLE, ModelStatus.ERROR, ModelStatus.INVALID_MODEL}


def test_validate_model_placeholder_is_invalid_model() -> None:
    model = ModelDef(
        provider=ProviderId.OPENAI_COMPAT_LOCAL,
        display_name="LM Studio (local)",
        model=MODEL_ID_PLACEHOLDER,
        base_url="http://localhost:1234/v1",
        requires_env=None,
        is_local=False,
        endpoint_id="lmstudio",
    )

    validated = validate_model(model)
    assert validated.status == ModelStatus.INVALID_MODEL
