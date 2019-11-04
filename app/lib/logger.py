import itertools
import json
import logging
import traceback
from logging import handlers
from uuid import UUID

import flask

PROD_LOG_FORMAT = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
DEBUG_LOG_FORMAT = (
    '-' * 80 + '\n' +
    '%(levelname)s in %(module)s [%(pathname)s:%(lineno)d]:\n' +
    '%(message)s\n' +
    '-' * 80
)

def init_logger(app):

    logging.setLoggerClass(UbiomeLogger)

    # Log SQLAlchemy on DEBUG mode
    if app.config['DEBUG'] == 'True':
        logging.captureWarnings(True)
        sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
        sqlalchemy_logger.addHandler(logging.StreamHandler())

        log_handler = logging.StreamHandler()
        log_handler.setLevel(app.config.get('LOGGING_LEVEL'))
        log_handler.setFormatter(logging.Formatter(DEBUG_LOG_FORMAT))
        app.logger.addHandler(log_handler)
    else:
        werkzeug_log = logging.getLogger('werkzeug')
        werkzeug_log.disabled = True
        del app.logger.handlers[:]

        log_handler = handlers.RotatingFileHandler(maxBytes=app.config.get('LOGGING_MAXBYTES', 100000000),
                                                   backupCount=app.config.get('LOGGING_BKP_COUNTS', 10),
                                                   filename=app.config['TEXT_LOGGING_LOCATION'])
        log_handler.setLevel(app.config.get('LOGGING_LEVEL'))
        log_handler.setFormatter(logging.Formatter(PROD_LOG_FORMAT))
        app.logger.addHandler(log_handler)

        json_handler = handlers.RotatingFileHandler(maxBytes=app.config.get('LOGGING_MAXBYTES', 100000000),
                                                    backupCount=app.config.get('LOGGING_BKP_COUNTS', 10),
                                                    filename=app.config['JSON_LOGGING_LOCATION'])
        json_handler.setLevel(app.config.get('LOGGING_LEVEL'))
        json_handler.setFormatter(JSONFormatter(app.config['LOGGING_APP_NAME']))
        app.logger.addHandler(json_handler)


class JSONFormatter(logging.Formatter):
    def __init__(self, app_name):
        logging.Formatter.__init__(self)
        self.app_name = app_name

    def format(self, record):
        msg = {"name": self.app_name,
            "asctime": self.formatTime(record, self.datefmt),
            "levelname": record.levelname,
            "levelno": record.levelno,
            "message": record.getMessage(),

            "msecs": record.msecs,

            "filename": record.filename,
            "funcname": record.funcName,
            "lineno": record.lineno
        }

        if hasattr(record, 'extra'):
            msg["extra"] = record.extra

        return json.dumps(msg, cls=UUIDEncoder)

    def _formatException(self, ei, strip_newlines=True):
        lines = traceback.format_exception(*ei)
        if strip_newlines:
            lines = [itertools.ifilter(lambda x: x, line.rstrip().splitlines())
                     for line in lines]
            lines = list(itertools.chain(*lines))
        return lines


class UbiomeLogger(logging.Logger):

    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
        """
        We only check if any key in extra dict is duplicated with the keys that exist already in the record.
        Otherwise we append the extra parameter as a new entry in the dictionary
        Also we add the user id and request id to the log message if they exist in flask.g local thread
        """
        if isinstance(msg, dict):
            msg = json.dumps(msg)

        rv = logging.LogRecord(name, level, fn, lno, msg, args, exc_info, func)
        if extra is not None:
            for key in list(extra):
                if (key in ["message", "asctime"]) or (key in rv.__dict__):
                    raise KeyError("Attempt to overwrite %r in LogRecord" % key)
                if extra.get(key) is None:
                    extra.pop(key)
        else:
            extra = dict()

        # TODO: Should we move this to a more accurate place ??
        try:
            if hasattr(flask.g, 'user'):
                extra['user_id'] = flask.g.user.id
                msg = "User %s :: %s" % (flask.g.user.id, msg)
            if hasattr(flask.g, 'request_id'):
                extra['request_id'] = flask.g.request_id
                msg = "Request ID %s :: %s" % (flask.g.request_id, msg)
            if flask.request:
                    extra['path'] = flask.request.path
            if hasattr(flask.g, 'headers'):
                for header in flask.g.headers:
                    if header.log_enabled:
                        extra[header.log_name] = header.value
        except Exception as e:
            pass

        rv.msg = msg
        rv.extra = extra
        return rv


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return obj.hex
        return json.JSONEncoder.default(self, obj)
