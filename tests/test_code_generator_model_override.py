import importlib
import sys
import types

from zstar.llm.models import StrategyGeneration


def test_get_strategy_code_uses_model_override_and_restores_original(monkeypatch):
    fake_ollama_module = types.SimpleNamespace(chat=lambda *args, **kwargs: None)
    monkeypatch.setitem(sys.modules, "ollama", fake_ollama_module)

    code_generator_module = importlib.import_module("zstar.llm.code_generator")
    code_generator_module = importlib.reload(code_generator_module)
    code_generator = code_generator_module.CodeGenerator(model="default-model")

    used_models: list[str] = []

    def fake_generate_code(user_prompt: str) -> StrategyGeneration:
        used_models.append(code_generator.model)
        return StrategyGeneration(
            name="Generated",
            summary="Summary",
            assumptions=[],
            code="print('ok')",
        )

    monkeypatch.setattr(code_generator, "generate_code", fake_generate_code)
    monkeypatch.setattr(code_generator.validate_strategy, "validate", lambda _: [])

    result = code_generator.get_strategy_code(
        user_prompt="Generate strategy",
        model="override-model",
    )

    assert result.code == "print('ok')"
    assert used_models == ["override-model"]
    assert code_generator.model == "default-model"


def test_get_strategy_code_emits_progress_events(monkeypatch):
    fake_ollama_module = types.SimpleNamespace(chat=lambda *args, **kwargs: None)
    monkeypatch.setitem(sys.modules, "ollama", fake_ollama_module)

    code_generator_module = importlib.import_module("zstar.llm.code_generator")
    code_generator_module = importlib.reload(code_generator_module)
    code_generator = code_generator_module.CodeGenerator(model="default-model")

    first_generation = StrategyGeneration(
        name="Generated-1",
        summary="Summary",
        assumptions=[],
        code="print('first')",
    )
    second_generation = StrategyGeneration(
        name="Generated-2",
        summary="Summary",
        assumptions=[],
        code="print('second')",
    )

    monkeypatch.setattr(code_generator, "generate_code", lambda _: first_generation)
    monkeypatch.setattr(code_generator, "retry_generation", lambda *_: second_generation)

    validation_results = [["error"], []]

    def fake_validate(_: str) -> list[str]:
        return validation_results.pop(0)

    monkeypatch.setattr(code_generator.validate_strategy, "validate", fake_validate)

    progress_events: list[tuple[str, str, str]] = []
    code_generator.get_strategy_code(
        user_prompt="Generate strategy",
        progress_callback=lambda step_id, label, state: progress_events.append((step_id, label, state)),
    )

    assert ("generate_code", "Generating code...", "running") in progress_events
    assert ("generate_code", "Generating code...", "done") in progress_events
    assert ("validate_syntax_1", "Validating syntax...", "running") in progress_events
    assert ("validate_syntax_1", "Validating syntax...", "done") in progress_events
    assert ("retry_generation_1", "Validation failed (1). Retrying (1/2)...", "running") in progress_events
    assert ("retry_generation_1", "Validation failed (1). Retrying (1/2)...", "done") in progress_events
    assert ("validate_syntax_2", "Validating syntax...", "running") in progress_events
    assert ("validate_syntax_2", "Validating syntax...", "done") in progress_events
