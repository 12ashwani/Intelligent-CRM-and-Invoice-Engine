import mysql.connector
from flask import g

from comman_db.crm_core import MYSQL_CONFIG

class MySQLConnection:

    def __init__(self, app=None):
        self.app = app

    def init_app(self, app):
        self.app = app
        self.app.teardown_appcontext(self._close_connection)

    def _close_connection(self, exception=None):

        if hasattr(g, 'mysql_connection'):

            try:
                g.mysql_connection.close()

            except Exception:
                pass

            delattr(g, 'mysql_connection')

    def _get_connection(self):

        if not hasattr(g, 'mysql_connection'):

            g.mysql_connection = mysql.connector.connect(
                **MYSQL_CONFIG,
                autocommit=False
            )

        return g.mysql_connection

    @property
    def connection(self):
        return self._get_connection()


mysql_db = MySQLConnection()