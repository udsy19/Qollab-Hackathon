"""The problem instance: expected returns and covariance for a small universe of liquid US ETFs.

THE NUMBERS ARE SYNTHETIC. They are drawn from a seeded random generator whose volatilities and
correlations were chosen by hand to look like liquid US ETFs; they are not market data, they are not
estimated from any price history, and nothing here predicts any real return.

The project reads them from a JSON file (`data/etf_stats_synthetic.json`) so that a file of DERIVED
statistics (annualised mu and cov, no raw prices) can replace it later without touching the solvers:
write a JSON with the same keys and change the one path literal in `main.py`. The file was produced by
`synthetic_etf_stats()` below, and `load_stats()` falls back to calling it if the file cannot be read.
"""
from __future__ import annotations

import json

import numpy as np

# Hand-chosen, plausible annual figures (NOT estimates): drift, volatility, and one correlation matrix.
TICKERS = ["SPY", "QQQ", "IWM", "DIA", "TLT", "GLD", "EFA", "HYG"]
_DRIFT = np.array([0.075, 0.095, 0.070, 0.070, 0.035, 0.045, 0.060, 0.050])
_VOL = np.array([0.17, 0.22, 0.24, 0.16, 0.15, 0.15, 0.18, 0.08])
_CORR = np.array([
    #  SPY   QQQ   IWM   DIA   TLT   GLD   EFA   HYG
    [1.00, 0.93, 0.86, 0.95, -0.25, 0.05, 0.85, 0.70],  # SPY
    [0.93, 1.00, 0.80, 0.85, -0.20, 0.05, 0.78, 0.62],  # QQQ
    [0.86, 0.80, 1.00, 0.84, -0.22, 0.07, 0.78, 0.68],  # IWM
    [0.95, 0.85, 0.84, 1.00, -0.24, 0.04, 0.84, 0.69],  # DIA
    [-0.25, -0.20, -0.22, -0.24, 1.00, 0.30, -0.15, 0.05],  # TLT
    [0.05, 0.05, 0.07, 0.04, 0.30, 1.00, 0.15, 0.10],  # GLD
    [0.85, 0.78, 0.78, 0.84, -0.15, 0.15, 1.00, 0.66],  # EFA
    [0.70, 0.62, 0.68, 0.69, 0.05, 0.10, 0.66, 1.00],  # HYG
])
TRADING_DAYS = 252


def synthetic_etf_stats(seed: int = 2026, days: int = 756, shrink: float = 0.5) -> dict:
    """Simulate `days` of daily returns from the hand-chosen figures and estimate annualised mu and cov.

    The sample mean of three years of returns is very noisy (standard error ~ vol / sqrt(3)), so mu is
    shrunk halfway toward the hand-chosen drift, as a practitioner would. Deterministic for a given seed.
    """
    rng = np.random.default_rng(seed)
    cov_true = np.outer(_VOL, _VOL) * _CORR
    daily = rng.multivariate_normal(_DRIFT / TRADING_DAYS, cov_true / TRADING_DAYS, size=days)
    mu_sample = daily.mean(axis=0) * TRADING_DAYS
    mu = shrink * _DRIFT + (1 - shrink) * mu_sample
    cov = np.cov(daily, rowvar=False) * TRADING_DAYS
    return {
        "synthetic": True,
        "label": "SYNTHETIC: seeded simulation, not market data",
        "generator": f"qctrade.instance.synthetic_etf_stats(seed={seed}, days={days}, shrink={shrink})",
        "units": "annualised arithmetic return and covariance",
        "tickers": list(TICKERS),
        "mu": [round(float(x), 8) for x in mu],
        "cov": [[round(float(x), 8) for x in row] for row in cov],
    }


def validate_stats(stats: dict) -> None:
    """Refuse a stats file that would make the benchmark meaningless: wrong shapes, asymmetric or non-PSD cov."""
    for key in ("tickers", "mu", "cov", "synthetic"):
        if key not in stats:
            raise ValueError(f"stats file lacks the key {key!r}")
    n = len(stats["tickers"])
    mu, cov = np.asarray(stats["mu"], float), np.asarray(stats["cov"], float)
    if mu.shape != (n,) or cov.shape != (n, n):
        raise ValueError(f"stats shapes: {n} tickers, mu {mu.shape}, cov {cov.shape}")
    if not np.allclose(cov, cov.T, atol=1e-10):
        raise ValueError("cov is not symmetric")
    if np.linalg.eigvalsh(cov).min() < -1e-10:
        raise ValueError("cov is not positive semi-definite")


def load_stats(path: str) -> tuple[dict, str]:
    """Read and validate a stats JSON; if it cannot be read, regenerate the synthetic one. Returns (stats, origin)."""
    try:
        with open(path) as fh:
            stats = json.load(fh)
        origin = f"file {path}"
    except OSError as err:
        stats = synthetic_etf_stats()
        origin = f"regenerated in code (could not read {path}: {err.__class__.__name__})"
    validate_stats(stats)
    return stats, origin


def select_universe(stats: dict, n_assets: int) -> tuple[list[str], np.ndarray, np.ndarray]:
    """The first `n_assets` tickers of the file, in file order."""
    n_all = len(stats["tickers"])
    if not 2 <= n_assets <= n_all:
        raise ValueError(f"n_assets must be between 2 and {n_all} (the stats file has {n_all} tickers)")
    mu = np.asarray(stats["mu"], float)[:n_assets]
    cov = np.asarray(stats["cov"], float)[:n_assets, :n_assets]
    return list(stats["tickers"][:n_assets]), mu, cov
