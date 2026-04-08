import pytest
from pydantic import ValidationError

from zstar.core.backtest.backtest_config_model import BacktestConfigModel


def test_backtest_config_model_defaults():
    config = BacktestConfigModel()

    assert config.initial_balance == pytest.approx(10000.0)
    assert config.entry_fee_pct == 0
    assert config.exit_fee_pct == 0
    assert config.slippage_pct == 0
    assert config.slippage_seed is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("initial_balance", -1),
        ("entry_fee_pct", -0.01),
        ("entry_fee_pct", 100.01),
        ("exit_fee_pct", -0.01),
        ("exit_fee_pct", 100.01),
        ("slippage_pct", -0.01),
        ("slippage_pct", 100.01),
    ],
)
def test_backtest_config_model_rejects_out_of_range_values(field, value):
    with pytest.raises(ValidationError):
        BacktestConfigModel(**{field: value})
