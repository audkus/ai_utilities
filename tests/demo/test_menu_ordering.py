from __future__ import annotations

from ai_utilities.demo.menu import sort_models_alphabetically
from ai_utilities.demo.validation import ModelStatus, ValidatedModel
from ai_utilities.demo.model_registry import ModelDef, ProviderId


def _vm(text: str, status: ModelStatus) -> ValidatedModel:
    model_def = ModelDef(
        provider=ProviderId.OPENAI,
        display_name=text.split(" – ")[0],
        model=text.split(" – ")[1],
        base_url="https://example.com/v1",
        requires_env=None,
        is_local=False,
        endpoint_id="x",
    )
    return ValidatedModel(
        model_def=model_def,
        status=status,
        status_detail=status.value,
        fix_instructions="",
        menu_line_text=text,
    )


def test_sort_models_is_case_insensitive_and_status_independent() -> None:
    models = [
        _vm("Ollama (local) – llama3.2:latest", ModelStatus.UNREACHABLE),
        _vm("openai (cloud) – <default>", ModelStatus.NEEDS_KEY),
        _vm("FastChat (local) – vicuna", ModelStatus.READY),
    ]

    sorted_models = sort_models_alphabetically(models)
    assert [m.menu_line_text for m in sorted_models] == [
        "FastChat (local) – vicuna",
        "Ollama (local) – llama3.2:latest",
        "openai (cloud) – <default>",
    ]
