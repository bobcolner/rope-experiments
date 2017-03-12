import flask_caching
from server import app, cache_config

cache = flask_caching.Cache()


def main():
    cache.init_app(app, config=cache_config)
    with app.app_context():
        cache.clear()


if __name__ == '__main__':
    main()
