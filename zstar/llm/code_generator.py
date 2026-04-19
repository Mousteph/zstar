from zstar.llm.models import StrategyGeneration
from zstar.core.strategy import ValidateStrategy
from ollama import chat
from typing import Callable, List, Optional, Dict, Tuple
import json
import os


class Response:
    def __init__(self, strategy_generation: Optional[StrategyGeneration], error_message: str, raw_response: str):
        self.strategy_generation = strategy_generation
        self.error_message = error_message
        self.raw_response = raw_response


class CodeGenerator:


    def _load_prompt(self, filename: str) -> str:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_dir, filename), "r") as f:
            return f.read()


    def _generate(self, messages: List[Dict[str, str]]) -> Tuple[Optional[StrategyGeneration], str, str]:
        response = chat(
            model=self.model,
            messages=messages,
            think=False,
            stream=False,
            options={"temperature": 0.0},
            format=StrategyGeneration.model_json_schema()
        )

        return self._parse_response(response.message.content)

    
    def _parse_response(self, response: str) -> Response:
        try:
            strategy_generation = StrategyGeneration.model_validate_json(response)
            return Response(strategy_generation, "", response)
        except Exception as exc:
            print(f"Error parsing response: {exc}")
            return Response(None, f"Error parsing response: {str(exc)}", response)


    def _emit_progress(self, progress_callback: Optional[Callable[[str, str, str], None]], step_id: str, label: str, state: str) -> None:
        print(f"Emitting progress: {step_id} - {label} - {state}")
        
        if progress_callback is None:
            return

        try:
            progress_callback(step_id, label, state)
        except Exception as exc:
            print(f"Failed to emit progress: {step_id} - {label} - {state}")
            print(f"Error: {exc}")
            return


    def __init__(self, model: str = "gemma4:e4b"):
        self.model = model
        self.schema = StrategyGeneration.model_json_schema()
        self.validate_strategy = ValidateStrategy()
        self.system_prompt = self._load_prompt("prompts/system_code_generator.txt")
        self.retry_prompt = self._load_prompt("prompts/retry_code_generator.txt")

    
    def _validate_strategy_progress(self,
            nb: int,
            code: str,
            progress_callback: Optional[Callable[[str, str, str], None]] = None
    ) -> List[str]:
        id_step = f"validate_syntax_{nb}"
        self._emit_progress(progress_callback, id_step, "Validating syntax generated code...", "running")
        
        list_error = self.validate_strategy.validate(code)[1]
        if len(list_error) == 0:
            self._emit_progress(progress_callback, id_step, "Code generated is valid.", "done")
        else:
            self._emit_progress(progress_callback, id_step, "Error while validating syntax.", "done")

        return list_error

    
    def _generate_code_progress(self, user_prompt: str, progress_callback: Optional[Callable[[str, str, str], None]] = None) -> Response:
        id_step = "generate_code"
        
        self._emit_progress(progress_callback, id_step, "Generating code...", "running")
        
        response = self.generate_code(user_prompt)

        if response.strategy_generation is None:
            self._emit_progress(progress_callback, id_step, "Failed to generate code.", "done")
        else:
            self._emit_progress(progress_callback, id_step, "Code generation complete.", "done")

        return response

    
    def generate_code(self, user_prompt: str) -> Response:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        return self._generate(messages)


    def _retry_generation_progress(self,
        nb: int,
        user_prompt: str,
        code: str,
        errors: List[str],
        max_nb_errors: int,
        progress_callback: Optional[Callable[[str, str, str], None]] = None
    ) -> Response:
        id_step = f"retry_generation_{nb}"
        retry_label = f"{len(errors)} found, fixing errors. Retrying {nb}/{max_nb_errors})..."
        self._emit_progress(progress_callback, id_step, retry_label, "running")
        
        response = self.retry_generation(user_prompt, code, errors)
        if response.strategy_generation is None:
            retry_label_done = f"Retry generation failed ({nb}/{max_nb_errors})."
            self._emit_progress(progress_callback, id_step, retry_label_done, "done")
        
        else:
            retry_label_done = f"Retry generation complete ({nb}/{max_nb_errors})."
            self._emit_progress(progress_callback, id_step, retry_label_done, "done")

        return response


    def retry_generation(self, user_prompt: str, code: str, errors: List[str]) -> Response:
        retry_message = self.retry_prompt.format(
            user_prompt=user_prompt,
            code=code,
            errors=json.dumps(errors, indent=2)
        )
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": retry_message}
        ]

        return self._generate(messages)
        

    def generate_strategy_code(
        self,
        user_prompt: str,
        max_nb_errors: int = 2,
        progress_callback: Optional[Callable[[str, str, str], None]] = None,
    ) -> StrategyGeneration:
        try:
            nb_error = 0
            
            response = self._generate_code_progress(user_prompt, progress_callback)
            if response.strategy_generation is not None:
                if not response.strategy_generation.can_answer:
                    return response.strategy_generation

                list_error = self._validate_strategy_progress(nb_error, response.strategy_generation.code, progress_callback)
                code = response.strategy_generation.code
            else:
                list_error = [response.error_message]
                code = response.raw_response

            while len(list_error) > 0 and nb_error < max_nb_errors:
                nb_error += 1

                response = self._retry_generation_progress(nb_error, user_prompt, code, list_error, max_nb_errors, progress_callback)
                if response.strategy_generation is not None:
                    list_error = self._validate_strategy_progress(nb_error, response.strategy_generation.code, progress_callback)
                    code = response.strategy_generation.code
                else:
                    list_error = [response.error_message]
                    code = response.raw_response


            if response.strategy_generation is not None:
                return response.strategy_generation
            else:
                return StrategyGeneration(
                    name="Error: Unable to generate valid strategy code",
                    summary=f"Error: Unable to generate valid strategy code\n\n{response.error_message}",
                    code="",
                    can_answer=False
                )

        except Exception:
            pass
