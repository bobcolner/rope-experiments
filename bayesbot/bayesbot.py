import pandas as pd
from scipy import stats


def bernoulli_update(trials: int, success: int, prior: stats.beta) -> stats.beta:
    a_hat = prior.args[0] + success
    b_hat = prior.args[1] + trials - success
    posterior = stats.beta(a_hat, b_hat)
    return posterior


def compute_stats(data: pd.Series, prior: stats.beta,
                  trials_col: str, success_col: str) -> pd.Series:

    trials = data[trials_col]
    success = data[success_col]
    posterior = bernoulli_update(trials, success, prior)

    posterior_stats = {
        'trials': trials,
        'success': success,
        'ratio': safe_divide(success, trials),
        'p01': posterior.ppf(0.01),
        'p05': posterior.ppf(0.05),
        'p25': posterior.ppf(0.25),
        'p50': posterior.ppf(0.50),
        'p75': posterior.ppf(0.75),
        'p95': posterior.ppf(0.95),
        'p99': posterior.ppf(0.99),
        'precision50': posterior.ppf(0.75) - posterior.ppf(0.25),
        'precision90': posterior.ppf(0.95) - posterior.ppf(0.05),
        'prior_beta_a': prior.args[0],
        'prior_beta_b': prior.args[1],
        'posterior_beta_a': posterior.args[0],
        'posterior_beta_b': posterior.args[1]
    }
    return pd.Series(posterior_stats)


def safe_divide(numerator: int, denominator: int):
    if denominator == 0:
        return None
    else:
        return float(numerator / denominator)


def append_stats(data: pd.DataFrame, trials_col: str, success_col: str,
                 prior=stats.beta(1, 1)) -> pd.DataFrame:
    bayes_stats = data.apply(compute_stats, axis=1, prior=prior,
                             trials_col=trials_col, success_col=success_col)
    return data.join(bayes_stats)
