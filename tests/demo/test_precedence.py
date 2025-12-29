from __future__ import annotations

import argparse
import os

import pytest

from ai_utilities.demo.app import resolve_initial_selection
from ai_utilities.demo.validation import ModelStatus, ValidatedModel
from ai_utilities.demo.model_registry import ModelDef, ProviderId


def _validated(provider: ProviderId, model: str, base_url: str, status: ModelStatus) -> ValidatedModel:
    model_def = ModelDef(
        provider=provider,
        display_name="X",
        model=model,
        base_url=base_url,
        requires_env=None,
        is_local=provider != ProviderId.OPENAI,
        endpoint_id="x",
    )
    return ValidatedModel(
        model_def=model_def,
        status=status,
        status_detail=status.value,
        fix_instructions="",
        menu_line_text=f"X – {model}",
    )


def test_cli_overrides_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_MODEL", "env-model")

    models = [
        _validated(ProviderId.OPENAI, "cli-model", "https://api.openai.com/v1", ModelStatus.READY),
        _validated(ProviderId.OPENAI, "env-model", "https://api.openai.com/v1", ModelStatus.READY),
    ]

    args = argparse.Namespace(
        provider="openai",
        model="cli-model",
        base_url=None,
        endpoint=None,
        non_interactive=False,
        debug=False,
        list_models=False,
    )

    selected = resolve_initial_selection(models, args)
    assert selected is not None
    assert selected.model_def.model == "cli-model"
