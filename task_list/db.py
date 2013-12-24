from trac.core import *
from trac.db import Table, Column, Index, DatabaseManager
from trac.env import IEnvironmentSetupParticipant

SCHEMA_VERSION = 1

class TaskListSetup(Component):
    implements(IEnvironmentSetupParticipant)

    # IEnvironmentSetupParticipant
    def environment_created(self):
        """ Called when a new environment is created. Procedure is similar to
        an environment upgrade, but we also need to commit the changes
        ourselves. """
        return False
        with self.env.db_transaction as db:
            self.upgrade_environment()

    def environment_needs_upgrade(self, db):
        return False
        current_version = self._get_version(db) or -1
        return current_version < SCHEMA_VERSION

    def upgrade_environment(self, db):
        """ Upgrade our part of the database to the latest version. Note that
        we don't commit the changes here, as this is done by the common upgrade
        procedure instead. """
        current_version = self._get_version(db) or -1
        for version in range(current_version + 1, SCHEMA_VERSION + 1):
            self.env.log.debug("version=%d", version)
            for function in self.VERSION_MAP.get(version, []):
                function(self, db)
                self.log.info('Done.')

        """ Reget version, since it may have changed during the update
        update procedure above (when upgrading from v1 to v2) """
        current_version = self._get_version(db)
        cursor = db.cursor()
        try:
            cursor.execute("UPDATE system SET value=%s WHERE "
                           "name='task_list_version'", (SCHEMA_VERSION,))
        except Exception, e:
            self.env.log.error(e, exc_info=1)
            raise TracError(str(e))
        
    # private methods

    def _create_tables(self, db):
        table = Table('task_list_ticket', key='id')[
            Column('id', auto_increment=True),
            Column('tasklist', type='int'),
            Column('ticket', type='int'),
            Index(['tasklist', 'ticket']),
            ]
        cursor = db.cursor()
        backend, __ = DatabaseManager(self.env)._get_connector()
        for stmt in backend.to_sql(table):
            cursor.execute(stmt)

    def _set_version(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO system VALUES ('task_list_version',1)")
        except Exception, e:
            self.env.log.error(e, exc_info=1)
            raise TracError(str(e))

    VERSION_MAP = {
        1: [_create_tables, _set_version],
        }

    def _get_version(self, db):
        """ Determine the version of the database scheme for this plugin
        that is currently used.
        system table. """
        cursor = db.cursor()

        stmt = "SELECT value FROM system WHERE name='task_list_version'"
        try:
            cursor.execute(stmt)
            row = cursor.fetchone()
            if row:
                return int(row[0])
        except Exception:
            pass
