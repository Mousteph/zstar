import ast
import inspect
from typing import Optional, Tuple, List, Dict, Set
import numpy as np
import pandas as pd
from zstar.core.strategy.core_strategy import CoreStrategy


class ValidateStrategy:
    required_signal_columns = ["long_entry", "short_entry", "long_exit", "short_exit"]

    def sample_data(self, rows: int = 200) -> pd.DataFrame:
        dates = pd.date_range(start="2020-01-01", periods=rows, freq="D")
        rng = np.random.default_rng(seed=42)

        open_prices = rng.random(rows) * 100
        close_prices = rng.random(rows) * 100
        high_noise = rng.random(rows) * 10
        low_noise = rng.random(rows) * 10

        data = {
            "open": open_prices,
            "high": np.maximum(open_prices, close_prices) + high_noise,
            "low": np.minimum(open_prices, close_prices) - low_noise,
            "close": close_prices,
            "volume": rng.integers(1, 1000, size=rows),
        }

        return pd.DataFrame(data, index=dates)
    

    def _base_name(self, base: ast.expr) -> Optional[str]:
        if isinstance(base, ast.Name):
            return base.id

        if isinstance(base, ast.Attribute):
            return base.attr

        return None
    
    
    def get_corestrategy_subclass_names(self, tree: ast.AST) -> List[str]:
        class_bases: Dict[str, Set[str]] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_bases[node.name] = {
                    base_name
                    for base in node.bases
                    if (base_name := self._base_name(base)) is not None
                }

        subclass_names: List[str] = []
        changed = True
        while changed:
            changed = False
            for class_name, base_names in class_bases.items():
                if class_name in subclass_names:
                    continue

                if "CoreStrategy" in base_names or any(base_name in subclass_names for base_name in base_names):
                    subclass_names.append(class_name)
                    changed = True

        return subclass_names


    def run_static_validation(self, code: str) -> List[str]:
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return [f"SyntaxError: line {e.lineno}, col {e.offset}: {e.msg}"]

        strategy_classes = self.get_corestrategy_subclass_names(tree)
        if not strategy_classes:
            return ["FormatError: No class found that inherits from 'CoreStrategy'."]

        if len(strategy_classes) > 1:
            class_names = ", ".join(sorted(strategy_classes))
            return [f"FormatError: Multiple CoreStrategy subclasses found: {class_names}. Define exactly one strategy class."]

        return []


    def _get_strategy_class(self, scope: Dict[str, object]) -> Optional[type[CoreStrategy]]:
        for value in scope.values():
            if inspect.isclass(value) and issubclass(value, CoreStrategy) and value is not CoreStrategy:
                return value

        return None

    
    def run_load_validation(self, code: str) -> Tuple[Optional[CoreStrategy], List[str]]:
        scope = {
            "__builtins__": __builtins__,
            "CoreStrategy": CoreStrategy,
            "pd": pd,
            "np": np,
        }

        try:
            exec(code, scope, scope)
        except Exception as e:
            return None, [f"ExecutionError when loading strategy: {str(e)}"]
        
        strategy_class = self._get_strategy_class(scope)
        if strategy_class is None:
            return None, ["ValidationError: Unable to resolve strategy class after loading. A strategy class must be defined that inherits from CoreStrategy."]
    
        try:
            strategy = strategy_class()
        except Exception as e:
            return None, [f"ExecutionError when instantiating strategy class '{strategy_class.__name__}': {str(e)}"]

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

        errors = []
        try:
            for col in self.required_signal_columns:
                if col not in df.columns:
                    errors.append(f"RuntimeError: Missing required signal column '{col}'")
        except Exception as e:
            errors.append(f"RuntimeError when validating signal columns: {str(e)}")

        try:
            size = strategy.position_size(10000, 100)
            if not isinstance(size, (int, float, np.integer, np.floating)):
                errors.append("RuntimeError: position_size must return a numeric value")
            elif size <= 0:
                errors.append("RuntimeError: position_size must return > 0")
        except Exception as e:
            errors.append(f"RuntimeError in position_size: {str(e)}")

        return errors


    def validate(self, code: str) -> Tuple[Optional[CoreStrategy], List[str]]:
        errors = self.run_static_validation(code)
        if errors:
            return None, errors
        
        strategy, load_errors = self.run_load_validation(code)
        if load_errors:
            return None, load_errors

        runtime_errors = self.run_runtime_validation(strategy)
        if runtime_errors:
            return None, runtime_errors

        return strategy, []
