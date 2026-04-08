import typer

from zstar.core.backtest import BacktesterEngine
from zstar.core.data_loader import YahooData
from zstar.core.core_strategy import load_strategy_from_code
from zstar.utils import read_yaml_file
from .options import ConfigFileOption, StrategyFileOption
from .runner import CliRunner
from .utils import read_strategy_code
from .models import BacktestCliConfig

app = typer.Typer(add_completion=False, help="ZStar command line interface.")


@app.callback()
def cli_main() -> None:
    """ZStar command line interface."""


@app.command("backtest")
def backtest_command(strategy_file: StrategyFileOption, config_file: ConfigFileOption) -> None:
    print("Starting backtest...")
    try:
        strategy_code = read_strategy_code(strategy_file)
        config_data = read_yaml_file(config_file)
        config = BacktestCliConfig.model_validate(config_data)

        strategy = load_strategy_from_code(strategy_code)
        yahoo_data = YahooData(config.data)
        backtest_engine = BacktesterEngine(strategy, yahoo_data, config.backtest_config)

        report = backtest_engine.run_backtest()
        kpis_output_path, equity_output_path = CliRunner.write_backtest_outputs(config, report)

        typer.echo("Backtest completed successfully")
        typer.echo(f"Number of bars processed: {len(yahoo_data.data)}")
        typer.echo(f"Output KPIs path: {kpis_output_path}")
        typer.echo(f"Output equity curve path: {equity_output_path}")

    except RuntimeError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        
        raise typer.Exit(code=1) from exc
