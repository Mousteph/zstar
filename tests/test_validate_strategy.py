from zstar.core.strategy.validate_strategy import ValidateStrategy, ValidationIssue, Severity, Category


def test_validate_strategy_reports_syntax_error_with_line_number():
    validator = ValidateStrategy(strategy_filename="broken.py")
    _, result = validator.validate_result("class Broken(\n") 

    assert result.total_errors == 1
    issue = result.issues[0]
    assert issue.category == "syntax"
    assert issue.file == "broken.py"
    assert issue.line == 1


def test_validate_strategy_reports_missing_corestrategy_subclass():
    validator = ValidateStrategy(strategy_filename="missing.py")
    _, result = validator.validate_result("value = 1")

    assert result.total_errors == 1
    assert result.issues[0].category == "template"


def test_validate_strategy_reports_multiple_subclasses():
    validator = ValidateStrategy(strategy_filename="multiple.py")
    code = """
class OneStrategy(CoreStrategy):
    def position_size(self, balance, entry_price):
        return 1

class TwoStrategy(CoreStrategy):
    def position_size(self, balance, entry_price):
        return 1
"""
    _, result = validator.validate_result(code)

    assert result.total_errors == 1
    assert result.issues[0].category == "template"


def test_validate_strategy_reports_missing_required_signal_columns():
    validator = ValidateStrategy(strategy_filename="missing_signals.py")
    code = """
class MissingSignalsStrategy(CoreStrategy):
    def short_entry_signals(self, data):
        if "short_entry" in data.columns:
            data = data.drop(columns=["short_entry"])
        return data

    def position_size(self, balance, entry_price):
        return 1.0
"""
    _, result = validator.validate_result(code)

    assert result.total_errors > 0
    categories = {issue.category for issue in result.issues}
    assert "template" in categories


def test_validate_strategy_reports_position_size_type_mismatch():
    validator = ValidateStrategy(strategy_filename="type_mismatch.py")
    code = """
class TypeMismatchStrategy(CoreStrategy):
    def position_size(self, balance, entry_price):
        return "one"
"""
    _, result = validator.validate_result(code)

    assert result.total_errors == 1
    assert result.issues[0].category == "type"


def test_validate_strategy_reports_position_size_logic_issue():
    validator = ValidateStrategy(strategy_filename="bad_logic.py")
    code = """
class BadLogicStrategy(CoreStrategy):
    def position_size(self, balance, entry_price):
        return 0
"""
    _, result = validator.validate_result(code)

    assert result.total_errors == 1
    assert result.issues[0].category == "logic"


def test_validate_strategy_reports_runtime_exception():
    validator = ValidateStrategy(strategy_filename="runtime.py")
    code = """
class RuntimeStrategy(CoreStrategy):
    def calculate_indicators(self, data):
        raise RuntimeError("boom")

    def position_size(self, balance, entry_price):
        return 1
"""
    _, result = validator.validate_result(code)

    assert result.total_errors == 1
    assert result.issues[0].category == "logic"


def test_validate_strategy_sorts_errors_before_warnings():
    validator = ValidateStrategy(strategy_filename="sorted.py")
    code = """
class WarningAndErrorStrategy(CoreStrategy):
    def long_entry_signals(self, data):
        data["long_entry"] = [None] * len(data)
        return data

    def short_entry_signals(self, data):
        data["short_entry"] = [0] * len(data)
        return data

    def long_exit_signals(self, data):
        data["long_exit"] = [0] * len(data)
        return data

    def short_exit_signals(self, data):
        data["short_exit"] = [0] * len(data)
        return data

    def position_size(self, balance, entry_price):
        return "bad"
"""
    _, result = validator.validate_result(code)

    assert result.total_errors >= 1
    assert result.total_warnings >= 1
    severities = [issue.severity for issue in result.issues]
    first_warning = severities.index("warning")
    assert all(severity == "error" for severity in severities[:first_warning])


def test_validate_strategy_message_length_and_actionable_text():
    long_message = "x" * 400
    issue = ValidationIssue(
        severity=Severity.ERROR.value,
        category=Category.LOGIC.value,
        file="strategy.py",
        message=f"Fix this issue now: {long_message}",
    )

    assert len(issue.message) > 200
    assert "Fix" in issue.message
    assert "something went wrong" not in issue.message.lower()


def test_validate_strategy_file_supports_relative_imports(tmp_path):
    strategy_dir = tmp_path / "strategies"
    strategy_dir.mkdir()
    (strategy_dir / "helper.py").write_text(
        """
def my_size():
    return 1.0
""",
        encoding="utf-8",
    )
    main_file = strategy_dir / "multi.py"
    main_file.write_text(
        """
from .helper import my_size

class MultiFileStrategy(CoreStrategy):
    def position_size(self, balance, entry_price):
        return my_size()
""",
        encoding="utf-8",
    )
    
    validator = ValidateStrategy(strategy_path=main_file)

    _, result = validator.validate_file()

    assert result.total_errors == 0
