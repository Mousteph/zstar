from pathlib import Path
from typing import Annotated

import typer

STRATEGY_FILE_OPTION = typer.Option(
    ...,
    "--strategy-file",
    exists=True,
    file_okay=True,
    dir_okay=False,
    readable=True,
    resolve_path=True,
    help="Path to a Python strategy file defining `strategy`.",
)

CONFIG_FILE_OPTION = typer.Option(
    ...,
    "--config-file",
    exists=True,
    file_okay=True,
    dir_okay=False,
    readable=True,
    resolve_path=True,
    help="Path to the backtest JSON config file.",
)

StrategyFileOption = Annotated[Path, STRATEGY_FILE_OPTION]
ConfigFileOption = Annotated[Path, CONFIG_FILE_OPTION]
