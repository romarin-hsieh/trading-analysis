"""Layered configuration: YAML file + environment variables, validated by Pydantic."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DataConfig(BaseModel):
    source: str = "yahoo"
    start: date = date(2018, 1, 1)
    end: date | None = None
    bar: str = "1d"
    cache_dir: Path = Path("./data")


class ModelConfig(BaseModel):
    use_kronos: bool = True
    kronos_size: str = Field("mini", pattern=r"^(mini|small|base|large)$")
    lookback: int = 256
    horizon: int = 5
    device: str = "cpu"
    cache_forecasts: bool = True


class StrategyConfig(BaseModel):
    rule: str = "kronos_trend"
    params: dict[str, Any] = Field(default_factory=dict)
    fallback_rule: str | None = "sma_crossover"
    fallback_params: dict[str, Any] = Field(default_factory=dict)


class SizingConfig(BaseModel):
    method: str = Field("fixed_fraction", pattern=r"^(fixed_fraction|vol_target|kelly)$")
    fraction: float = 0.05
    max_positions: int = 10


class RiskConfig(BaseModel):
    max_drawdown_pct: float = 0.20
    max_position_pct: float = 0.15
    max_sector_pct: float = 0.40
    initial_cash: float = 100_000.0


class BacktestConfig(BaseModel):
    fees_bps: float = 5.0
    slippage_bps: float = 5.0
    cash: float = 100_000.0
    freq: str = "1d"
    benchmark: str | None = "SPY"
    output_dir: Path = Path("./data/backtest_reports")


class UniverseConfig(BaseModel):
    name: str
    description: str | None = None
    symbols: list[str]

    @field_validator("symbols")
    @classmethod
    def _dedupe_upper(cls, v: list[str]) -> list[str]:
        return sorted({s.strip().upper() for s in v if s.strip()})


class AppConfig(BaseModel):
    universe: UniverseConfig
    data: DataConfig = DataConfig()
    model: ModelConfig = ModelConfig()
    strategy: StrategyConfig = StrategyConfig()
    sizing: SizingConfig = SizingConfig()
    risk: RiskConfig = RiskConfig()
    backtest: BacktestConfig = BacktestConfig()


class EnvSettings(BaseSettings):
    """Secrets and paths from environment / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    alpha_vantage_api_key: str | None = None
    polygon_api_key: str | None = None
    huggingface_token: str | None = None
    trading_data_dir: Path = Path("./data")
    mlflow_tracking_uri: str = "./mlruns"
    trading_config_path: Path = Path("./configs/mvp.yaml")


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_config(config_path: str | Path | None = None) -> AppConfig:
    """Load and validate the application config.

    The `universe` field can be either a path to a yaml file or an inline dict.
    """
    env = EnvSettings()
    path = Path(config_path) if config_path else env.trading_config_path
    raw = _load_yaml(path)

    universe_field = raw.get("universe")
    if isinstance(universe_field, str):
        raw["universe"] = _load_yaml(Path(universe_field))

    return AppConfig.model_validate(raw)


def get_env() -> EnvSettings:
    return EnvSettings()
