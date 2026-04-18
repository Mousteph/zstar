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
