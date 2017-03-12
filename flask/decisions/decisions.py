import pandas as pd
from scipy import stats


def experiment_stop(exp_hourly: pd.DataFrame, precision: float):
    try:
        # individual configs stop times
        config_stop_times = [config_hourly[config_hourly.precision90 < precision].iloc[1]['event_time']
                             for name, config_hourly in exp_hourly.groupby(['config'])]
    except:
        # not all configs have reached precision threshold
        return False
    return max(config_stop_times)


def beta_comparision(beta1: stats.beta, beta2: stats.beta, rope_width: float,
                     two_sided: bool=True, num_sim: int=20000) -> float:
    '''
    This is a function for comparing two random variables beta1 and beta2, each following beta distributions.
    The output is a probability, prob(|beta1-beta2| > rope_width) [two_side = True], OR
    prob(beta1-beta2 > rope_width) [two_side = False], where rope_width is a threshold.
    '''
    prob_dif = beta1.rvs(size=num_sim) - beta2.rvs(size=num_sim)
    if two_sided:
        prob = sum(abs(prob_dif) > rope_width) / num_sim
    else:
        prob = sum(prob_dif > rope_width) / num_sim
    return prob


def pairwise_beta_compare(exp_final: pd.DataFrame, rope_width: float, alpha: float) -> list:
    sig_results = []
    for _, config_a in exp_final.iterrows():
        for _, config_b in exp_final.iterrows():
            if config_a.config == config_b.config:
                continue
            prob_a_over_b = beta_comparision(
                beta1=stats.beta(config_a.posterior_beta_a, config_a.posterior_beta_b),
                beta2=stats.beta(config_b.posterior_beta_a, config_b.posterior_beta_b),
                rope_width=rope_width,
                two_sided=False
            )
            if prob_a_over_b > alpha:
                result_text = "{a_name}[{a_value}] > {b_name}[{b_value}] p={prob}".format(
                    a_name=config_a.config,
                    a_value=round(config_a.p50, 3),
                    b_name=config_b.config,
                    b_value=round(config_b.p50, 3),
                    prob=round(prob_a_over_b, 5)
                )
                sig_results.append(result_text)
    if len(sig_results) > 0:
            return sig_results
    else:
        return ['No Meaningful Difference']
