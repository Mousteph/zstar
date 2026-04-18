from zstar.llm.models import StrategyGeneration
from zstar.core.strategy import ValidateStrategy
from ollama import chat
from typing import Callable, List, Optional
import json


class CodeGenerator:
    def __init__(self, model: str = "gemma4:e4b"):
        self.model = model
        self.schema = StrategyGeneration.model_json_schema()
        self.validate_strategy = ValidateStrategy()

        self.system_prompt = f"""
        You generate valid JSON only.

        Return exactly one JSON object that matches this JSON Schema:
        {json.dumps(self.schema, indent=2)}

        Rules:
        - Output valid JSON only
        - Do not use markdown fences
        - Do not add explanations before or after the JSON
        - The "code" field must be raw Python source as a string
        - The code must define a subclass of CoreStrategy
        - The code must create a global variable named strategy
        - The code may use pandas as pd and numpy as np
        - The code must not import arbitrary libraries unless explicitly allowed
        """.strip()

    
    def generate_code(self, user_prompt: str) -> StrategyGeneration: 
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = chat(
            model=self.model,
            messages=messages,
            think=False,
            stream=False,
            options={"temperature": 0.5},
            format=StrategyGeneration.model_json_schema()
        )

        return StrategyGeneration.model_validate_json(response.message.content)


    def retry_generation(self, user_prompt: str, code_generated: StrategyGeneration, errors: List[str]) -> StrategyGeneration:
        retry_message = f"""
        The previous code generated failed validation steps:

        Original user prompt:
        {user_prompt}

        Code generated:
        {code_generated.code}

        Validation errors:
        {json.dumps(errors, indent=2)}

        Return a full corrected JSON object matching the required schema exactly.

        Rules:
        - Output valid JSON only
        - No markdown fences
        - No explanation
        - The python code must define a subclass of CoreStrategy
        - The python code must create a global variable named strategy
        - Fix all the listed errors in the code
        """
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": retry_message}
        ]
        
        response = chat(
            model=self.model,
            messages=messages,
            think=False,
            stream=False,
            options={"temperature": 0.0},
            format=StrategyGeneration.model_json_schema()
        )

        return StrategyGeneration.model_validate_json(response.message.content)


    def get_strategy_code(
        self,
        user_prompt: str,
        max_nb_errors: int = 2,
        model: Optional[str] = None,
        progress_callback: Optional[Callable[[str, str, str], None]] = None,
    ) -> StrategyGeneration:
        def emit_progress(step_id: str, label: str, state: str) -> None:
            if progress_callback is None:
                return

            try:
                progress_callback(step_id, label, state)
            except Exception:
                # Keep generation flow resilient if UI logging callback fails.
                return

        original_model = self.model
        if model and model.strip():
            self.model = model.strip()

        try:
            print("Generating code...")
            emit_progress("generate_code", "Generating code...", "running")
            strategy_generation = self.generate_code(user_prompt)
            print("Code generation complete.")
            emit_progress("generate_code", "Generating code...", "done")

            print("Validating syntax...")
            validation_attempt = 1
            validation_step_id = f"validate_syntax_{validation_attempt}"
            emit_progress(validation_step_id, "Validating syntax...", "running")
            list_error = self.validate_strategy.validate(strategy_generation.code)
            emit_progress(validation_step_id, "Validating syntax...", "done")
            nb_error = 0

            while len(list_error) > 0 and nb_error < max_nb_errors:
                nb_error += 1
                print(f"Validation failed with {len(list_error)} error(s). Attempting retry {nb_error}...")
                retry_step_id = f"retry_generation_{nb_error}"
                retry_label = f"Validation failed ({len(list_error)}). Retrying ({nb_error}/{max_nb_errors})..."
                emit_progress(retry_step_id, retry_label, "running")
                strategy_generation = self.retry_generation(user_prompt, strategy_generation, list_error)
                emit_progress(retry_step_id, retry_label, "done")
                validation_attempt += 1
                validation_step_id = f"validate_syntax_{validation_attempt}"
                emit_progress(validation_step_id, "Validating syntax...", "running")
                list_error = self.validate_strategy.validate(strategy_generation.code)
                emit_progress(validation_step_id, "Validating syntax...", "done")

            if len(list_error) > 0:
                print("Validation of the generated code failed, please fix the code manually.")
            else:
                print("Code validated successfully!")

            return strategy_generation
        finally:
            self.model = original_model
