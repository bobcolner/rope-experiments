import flask
import flask_caching
import sqlalchemy
# from boomtrain.config import load_flask
import main
# import boomtrain.flask.service

# app = boomtrain.flask.service.APIService(__name__)
app = flask.Flask()
# CONFIG = load_flask()
DB_URL = os.env

cache_config = {
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': '/var/cache/flask',
    'CACHE_DEFAULT_TIMEOUT': 900,
    'CACHE_THRESHOLD': 999
}
cache = flask_caching.Cache(app, config=cache_config)


def debug_mode():
    """Debug mode callable to disable cache in dev"""
    return app.debug


def full_cache_key():
    """Cache key callable that includes GET parameters."""
    return flask.request.full_path


@app.route('/')
@cache.cached(unless=debug_mode)
def index():
    db_conn = get_db()
    data = main.index(db_conn)
    return flask.render_template('table.html', data=data)


@app.route('/client/')
@app.route('/client/<string:site_id>')
@cache.cached(unless=debug_mode)
def client_exps(site_id='all'):
    db_conn = get_db()
    graphs, names = main.client_exps(db_conn, site_id)
    if len(graphs) > 0:
        return flask.render_template('plots.html', graphs=graphs, names=names)
    else:
        return flask.render_template('noexps.html', title='No Experiments',
                                     subtitle='Client on old rec-route?')


@app.route('/client/<string:site_id>/<string:namespace>/<string:experiment>/')
@cache.cached(key_prefix=full_cache_key, unless=debug_mode)
def exp_timeseries(site_id, namespace, experiment):
    db_conn = get_db()
    precision = float(flask.request.args.get('precision', 0.01))
    rope_width = float(flask.request.args.get('rope', 0.005))
    alpha = float(flask.request.args.get('alpha', 0.95))
    graph, results = main.exp_timeseries(db_conn, site_id, namespace, experiment,
                                         precision, rope_width, alpha)
    if graph:
        return flask.render_template('plot.html', html=graph, results=results)
    else:
        return flask.render_template('noexps.html', title='No Experiments')


@app.route("/clear_cache")
def clear_cache():
    try:
        cache.clear()
        return flask.render_template('noexps.html', title="Cleared Cache")
    except:
        return flask.render_template('noexps.html', title="Cleared Cache Fail")


def connect_db():
    """Connects to the database."""
    # http://oddbird.net/2014/06/14/sqlalchemy-postgres-autocommit/
    return sqlalchemy.create_engine(DB_URL, isolation_level='AUTOCOMMIT').connect()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(flask.g, 'pg_db'):
        flask.g.pg_db = connect_db()
    return flask.g.pg_db


@app.teardown_appcontext
def teardown_db(exception):
    """Cose the DB connection after the application context ends."""
    db = getattr(flask.g, 'pg_db', None)
    if db is not None:
        db.close()
