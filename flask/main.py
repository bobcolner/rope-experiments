import pandas as pd
from boomtrain.experiment_dashboard.flask.decisions import decisions
from boomtrain.experiment_dashboard.flask.plots import plots


def index(db_conn):
    sql = """
    SELECT *
    FROM exp_recent
    WHERE experiments > 1
    ORDER BY experiments DESC
    """
    recent_exps = pd.read_sql_query(sql, db_conn)
    recent_exps = add_client_names(recent_exps)
    return recent_exps.to_dict('records')


def client_exps(db_conn, site_id, output_type='div'):
    if site_id == 'all':
        exps = pd.read_sql_query(
            sql="SELECT * FROM exp_rollup LIMIT 99;",
            con=db_conn
        )
    else:
        exps = pd.read_sql_query(
            sql="SELECT * FROM exp_rollup WHERE site_id = '{site_id}' LIMIT 99;"
            .format(site_id=site_id),
            con=db_conn
        )
    exps = add_client_names(exps)
    graphs = [plots.plot_boxplot(exp, output_type)
              for name, exp in exps.groupby(['site_id', 'namespace', 'experiment'])]
    names = [name for name, exp in exps.groupby(['site_id', 'namespace', 'experiment'])]
    return graphs, names


def exp_timeseries(db_conn, site_id, namespace, experiment, precision=0.01,
                   rope_width=0.005, alpha=0.95, output_type='div'):
    sql = """
    SELECT *
    FROM exp_timeseries
    WHERE
        site_id = '{site_id}'
        AND namespace = '{namespace}'
        AND experiment = '{experiment}'
    ORDER BY site_id, namespace, experiment, config, exp_hour
    ;""".format(site_id=site_id, namespace=namespace, experiment=experiment)
    exp_hourly = pd.read_sql_query(sql, db_conn)
    exp_hourly = add_client_names(exp_hourly)
    stop_time = decisions.experiment_stop(exp_hourly, precision)
    if stop_time:
        exp_final = exp_hourly[exp_hourly.event_time == stop_time]
        results = decisions.pairwise_beta_compare(exp_final, rope_width, alpha)
    else:
        results = ['Experiment Running']
    graph = plots.plot_timeseries(exp_hourly, stop_time, output_type)
    return graph, results


def add_client_names(input_df):
    clients = {
        'ccc7cf66cbbc9108b54937e139f83841': 'CureJoy',
        '9e622eaef5dcfcd9fbc5c9c469f1b1cb': 'MGOA',
        '24fd0aa5647ab760fba2ebb8e56c71bc': 'Fodors',
        'fe3d1b4f09f60315d2bbfb27557a10e3': 'THG',
        '0eddb34d4eb4be1df2b4160ec047aa73': 'GameSpot',
        '8daa8843f4bdb355641619fc942f6ae6': 'TheStar',
        'c5609ca29fb7f571afa782fca14ebfca': 'DramaFever',
        'dcf561fa8dad7ae0bf96f52ee0826c2b': 'HumbleBundle',
        'ed6e6b11168e3880f61e111016d10d9a': 'MantaMedia',
        'f1957ff5e116f9c1ff0595be82420f31': 'BarkPost',
        '7a0f18a6274829b2e0710f57eea2b6d0': 'UpOut',
        '27d380589c8daa43418dc7f99a4c3ec9': 'BHG'
    }
    df = pd.DataFrame.from_dict(clients, 'index')
    df['site_id'] = df.index
    df.columns = ['client', 'site_id']
    output_df = input_df.merge(df, on='site_id', how='left')
    return output_df.reset_index()
