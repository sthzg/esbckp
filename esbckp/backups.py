# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import click
import os
from ConfigParser import ConfigParser, NoOptionError
from datetime import datetime
from .constants import *
from .utils import extract_dirs, extract_databases
from .shipper import Shipper
from .cleaner import Cleaner


class Backup(object):
    """Main application class for backups.

    Builds the main backup object which all subcommands access to retrieve
    information about ``BackupGroups``.
    """
    def __init__(self, conf, groups, routines=None):
        if not os.path.exists(os.path.expanduser(conf)):
            raise click.ClickException(ERR_CONFIG_FILE_DOES_NOT_EXIST)

        cfg = os.path.expanduser(conf)

        parser = ConfigParser()
        parser.read([cfg])

        bsd = os.path.expanduser(parser.defaults().get('backup_storage_dir'))

        self.backup_groups = list()
        self.backup_storage_dir = bsd

        if not os.path.exists(bsd):
            raise click.ClickException(ERR_BACK_STORAGE_DOES_NOT_EXIST.format(bsd))

        for section in parser.sections():
            if groups and section not in groups:
                continue

            group = BackupGroup()
            group.group_title = section
            group.base_path = os.path.join(bsd, group.group_title)
            group.base_name = parser.get(section, 'base_name')
            group.filename_prefix = datetime.now().strftime('%Y-%m-%d--%H-%M-%S')
            group.backup_storage_dir = bsd

            if not routines or 'dir' in routines:
                group.dirs = extract_dirs(parser.get(section, 'dir'))

            if not routines or 'db' in routines:
                group.dbs = extract_databases(parser.get(section, 'db'))

            group.shipper = group.populate_shipper(parser, section)
            group.cleaner = group.populate_cleaner(parser, section)

            self.backup_groups.append(group)


class BackupGroup(object):
    """Provides functionality and configuration for one ``BackupGroup``.

    Backups are bundled in groups. This allows the app to backup many
    different projects on one server under different namespaces.

    Instead of maintaining one big backup file containing everything on one
    server, it is possible to manage backups in chunks like project_1,
    project_2, server_conf, etc.

    Each group may override app defaults, which allows e.g. for shipping
    different backups to different remote locations or configuring
    different cleaner rules for different groups.
    """
    def __init__(self):
        self.backup_storage_dir = None
        self.group_title = None
        self.base_path = None
        self.base_name = None
        self.dirs = []
        self.dbs = []
        self.shipper = None
        self.cleaner = None
        self.filename_prefix = None

    def check_or_create_base_path(self):
        """Creates ``base_path`` on file system if it does not exist."""
        if self.base_path and not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def populate_shipper(self, parser, section):
        """Returns ``Shipper`` object from ``section`` or leaves it at None."""
        try:
            source_dir = os.path.join(self.backup_storage_dir, self.group_title)
            target_dir = parser.get(section, 'shipper_dir')

            self.shipper = Shipper()
            self.shipper.ssh_port = parser.get(section, 'shipper_ssh_port')
            self.shipper.user = parser.get(section, 'shipper_user')
            self.shipper.host = parser.get(section, 'shipper_host')
            self.shipper.source_dir = source_dir
            self.shipper.target_dir = target_dir

            return self.shipper

        except NoOptionError:
            return None

    def populate_cleaner(self, parser, section):
        """Returns ``Cleaner`` object from ``section`` or leaves it at None."""
        try:
            cl = Cleaner()
            cl.days_to_keep = int(parser.get(section, 'cleaner_days_to_keep'))
            cl.weeks_to_keep = int(parser.get(section, 'cleaner_weeks_to_keep'))
            cl.months_to_keep = int(parser.get(section, 'cleaner_months_to_keep'))
            cl.day_of_week_to_keep = int(parser.get(section, 'cleaner_day_of_week_to_keep'))  # NOQA
            cl.day_of_month_to_keep = int(parser.get(section, 'cleaner_day_of_month_to_keep'))  # NOQA

            self.cleaner = cl
            return self.cleaner

        except NoOptionError:
            return None

    def ship(self):
        """Starts shipping via rsync."""
        self.shipper.ship()

    def clean(self, dry_run=True):
        storage_dir = os.path.join(self.backup_storage_dir, self.group_title)
        self.cleaner.clean(storage_dir, dry_run)


class FileBackupItem(object):
    """Data object for file backups."""
    def __init__(self):
        self.dir = None


class DatabaseBackupItem(object):
    """Data object for database backups.

    The app currently only supports postgres.
    """
    def __init__(self, db_string):
        self.db_string = db_string
        self.db_type = None
        self.db_user = None
        self.db_name = None

        self._extract_db_string()

    def _extract_db_string(self):
        """Validates and extracts the configured database string.

        Database strings look like <db_system>:<db_name>:<db_user>.

        :raises: ValueError
        """
        tokens = self.db_string.split(':')

        if len(tokens) != 3:
            raise ValueError(ERR_DB_STRING_LENGTH.format(self.db_string))
        else:
            self.db_type, self.db_name, self.db_user = tokens
