import os
import datetime
import sqlalchemy
import pandas as pd
import bayesbot as bb


def run_sql_file(db_conn, sql_file, **kwargs):
    sql_tempate = open(sql_file).read()
    sql = sql_tempate.format(**kwargs)
    results = pd.read_sql_query(sql, db_conn)
    print('query done: ' + sql_file + ' at: ' + now())
    return results


def enrich_and_move_data(source_conn, dest_conn, dest_table, sql, trials_col, success_col, stats=True):
    results = pd.read_sql_query(sql, source_conn)
    print('query done: ' + sql + ' at: ' + now())
    if stats:
        results = bb.append_stats(data=results, prior=bb.stats.beta(1.2, 2),
                                  trials_col=trials_col, success_col=success_col
                                  )
        print('stats done: ' + sql + ' at: ' + now())
    results.to_sql(name=dest_table, con=dest_conn, if_exists='replace', index=False)
    print('insert done: ' + sql + ' at: ' + now())
    return results


def now() -> str:
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


update_events = True
update_exp_metrics = False
update_campaign_metrics = False
update_recent = False
update_rollup = False
update_timeseries = False

try:
    BTDW_CONN = sqlalchemy.create_engine(os.getenv('BTDW_CONN'), isolation_level="AUTOCOMMIT").connect()
    BB_CONN = sqlalchemy.create_engine(os.getenv('BB_CONN'), isolation_level="AUTOCOMMIT").connect()
    # BB_CONN = sqlalchemy.create_engine(os.getenv('LOCAL_CONN'), isolation_level="AUTOCOMMIT").connect()
    print('dbs connected')

    if update_events:
        run_sql_file(db_conn=BTDW_CONN, sql_file="sql/rec_events.psql", days_ago=30)

    if update_exp_metrics:
        run_sql_file(db_conn=BTDW_CONN, sql_file="sql/exp_metrics.psql")

    if update_campaign_metrics:
        run_sql_file(db_conn=BTDW_CONN, sql_file="sql/campaign_metrics.psql")

    if update_recent:
        enrich_and_move_data(source_conn=BTDW_CONN, dest_conn=BB_CONN, dest_table='exp_recent',
                             sql="SELECT * FROM bi.exp_recent;", stats=False,
                             trials_col='unique_view', success_col='unique_click'
                             )
    if update_rollup:
        enrich_and_move_data(source_conn=BTDW_CONN, dest_conn=BB_CONN, dest_table='exp_rollup',
                             sql="SELECT * FROM bi.exp_rollup;", stats=True,
                             trials_col='unique_view', success_col='unique_click'
                             )
    if update_timeseries:
        enrich_and_move_data(source_conn=BTDW_CONN, dest_conn=BB_CONN, dest_table='exp_timeseries',
                             sql="SELECT * FROM bi.exp_timeseries;", stats=True,
                             trials_col='cumulative_viewed', success_col='cumulative_clicked'
                             )
finally:
    BTDW_CONN.close()
    BB_CONN.close()
    print('dbs disconnected')
