import ast
from typing import List, Tuple, Optional
import numpy as np
import pandas as pd
from zstar.core.strategy.core_strategy import CoreStrategy


class CodeValidation:
    def sample_data(self, rows: int = 200) -> pd.DataFrame:
        dates = pd.date_range(start="2020-01-01", periods=rows, freq="D")
        rng = np.random.default_rng(seed=42)

        data = {
            "open": rng.random(rows) * 100,
            "high": rng.random(rows) * 100,
            "low": rng.random(rows) * 100,
            "close": rng.random(rows) * 100,
            "volume": rng.integers(1, 1000, size=rows),
        }

        return pd.DataFrame(data, index=dates)

    
    def has_strategy_assignment(self, tree: ast.AST) -> bool:
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "strategy":
                        return True
                    
        return False

    
    def has_corestrategy_subclass(self, tree: ast.AST) -> bool:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == "CoreStrategy":
                        return True
                    
        return False
    

    def run_static_validation(self, code: str) -> List[str]:
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return[f"SyntaxError: line {e.lineno}, col {e.offset}: {e.msg}"]
        
        errors = []
        
        if not self.has_strategy_assignment(tree):
            errors.append("FormatError: No variable named 'strategy' assigned in the code.")

        if not self.has_corestrategy_subclass(tree):
            errors.append("FormatError: No class found that inherits from 'CoreStrategy'.")

        return errors

    
    def run_load_validation(self, code: str) -> Tuple[Optional[CoreStrategy], List[str]]:
        scope = {
            "__builtins__": __builtins__,
            "CoreStrategy": CoreStrategy,
            "pd": pd,
            "np": np,
        }

        try:
            exec(code, scope, scope)
            strategy = scope.get("strategy")
        except Exception as e:
            return None, [f"ExecutionError: {str(e)}"]

        return strategy, []


    def run_runtime_validation(self, strategy: CoreStrategy) -> List[str]:
        df = self.sample_data()

        try:
            df = strategy.calculate_indicators(df)
            df = strategy.long_entry_signals(df)
            df = strategy.short_entry_signals(df)
            df = strategy.long_exit_signals(df)
            df = strategy.short_exit_signals(df)
        except Exception as e:
            return [f"RuntimeError: {str(e)}"]

        required = ["long_entry", "short_entry", "long_exit", "short_exit"]

        errors = []
        for col in required:
            if col not in df.columns:
                errors.append(f"RuntimeError: Missing required signal column '{col}'")

        try:
            size = strategy.position_size(10000, 100)
            if size <= 0:
                errors.append("RuntimeError: position_size must return > 0")
        except Exception as e:
            errors.append(f"RuntimeError in position_size: {str(e)}")

        return errors
    

    def validate_strategy_code(self, code: str) -> List[str]:
        errors = self.run_static_validation(code)
        if errors:
            return errors
        
        strategy, load_errors = self.run_load_validation(code)
        if load_errors:
            return load_errors
        
        runtime_errors = self.run_runtime_validation(strategy)
        return runtime_errors
