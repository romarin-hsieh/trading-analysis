from pathlib import Path

import yaml

from trading_analysis.config import AppConfig, load_config


def test_load_config_with_inline_universe(tmp_path: Path):
    cfg_yaml = {
        "universe": {"name": "tiny", "symbols": ["aapl", "MSFT", "msft"]},
        "data": {"source": "yahoo", "start": "2024-01-01", "bar": "1d"},
    }
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg_yaml), encoding="utf-8")
    cfg = load_config(cfg_path)
    assert isinstance(cfg, AppConfig)
    assert cfg.universe.symbols == ["AAPL", "MSFT"]


def test_load_config_with_universe_path(tmp_path: Path):
    universe_path = tmp_path / "universe.yaml"
    universe_path.write_text(
        yaml.safe_dump({"name": "tiny", "symbols": ["AAPL", "GOOG"]}), encoding="utf-8"
    )
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(
        yaml.safe_dump({"universe": str(universe_path)}), encoding="utf-8"
    )
    cfg = load_config(cfg_path)
    assert cfg.universe.symbols == ["AAPL", "GOOG"]
