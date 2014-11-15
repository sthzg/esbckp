# -*- coding: utf-8 -*-
"""
      Title: easybackup
     Author: Stephan Herzog (sthzg@gmx.net)
       Date: November 2014
      Usage: $ easybackups_start

Description:
    Naive and simple app to backup directories and databases. Backup targets
    need to be configured in a config file in INI format. By default, the
    file is expected to live in ~/etc/easybackups_conf.ini. Use the ``--conf``
    flag to pass a file.

    Type ``easybackups_start --help`` to learn about command line options.

Dependencies:
    * click
    * colorama

Improvements:
    Experimental. Needs testing.

"""
from __future__ import absolute_import, unicode_literals
import click
import os
import subprocess
import tarfile
from ConfigParser import ConfigParser
from datetime import datetime

# >>>>> Strings <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
HELP_CONF = '''
Location of easybackup configuration file.'''''

HELP_GROUP = '''
Specify section names to only backup one or more specific groups. Separate
section names with ,'''

ERR_CONFIG_FILE_DOES_NOT_EXIST = '''
Config file does not exist.'''

ERR_BACK_STORAGE_DOES_NOT_EXIST = '''
Backup storage directory does not exist at {}'''

ERR_DB_STRING_LENGTH = '''
Error with db string {}. It needs to have three tokens separated by a colon
(:), e.g. postgres:my_database:my_user. Skipping this particular db-backup.'''

# >>>>> Globals <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
total_num_files = 0
current_file_number = 0


# >>>>> Commands <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
@click.command()
@click.option('--conf', default='~/etc/easybackup_conf.ini', help=HELP_CONF)
@click.option('--groups', default=None, help=HELP_GROUP)
def start(conf, groups):
    """Starts the backup process.

    :param conf: Path of configuration file, default ~/etc/easybackups_conf.ini.
    :param groups: Name of groups to backup. If left out defaults to all.
    :return:
    """
    if not os.path.exists(os.path.expanduser(conf)):
        raise click.ClickException(ERR_CONFIG_FILE_DOES_NOT_EXIST)

    cfg = os.path.expanduser(conf)

    parser = ConfigParser()
    parser.read([cfg])

    bsd = os.path.expanduser(parser.defaults().get('backup_storage_dir'))

    if not os.path.exists(bsd):
        raise click.ClickException(ERR_BACK_STORAGE_DOES_NOT_EXIST.format(bsd))

    backup_groups = list()
    for section in parser.sections():
        if groups and section not in groups:
            continue

        group = FileBackupGroup()
        group.group_title = section
        group.base_path = os.path.join(bsd, group.group_title)
        group.base_name = parser.get(section, 'base_name')
        group.filename_prefix = datetime.now().strftime('%Y-%m-%d--%H-%M-%S')
        group.backup_storage_dir = bsd
        group.dirs = extract_dirs(parser.get(section, 'dir'))
        group.dbs = extract_databases(parser.get(section, 'db'))

        backup_groups.append(group)

    for group in backup_groups:
        if group.dirs:
            do_file_backups_for_group(group)

        if group.dbs:
            do_database_backups_for_group(group)



# >>>>> Utils <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
def do_file_backups_for_group(group):
    """Creates tar.gz compressed backups for all backup target directories.

    :param group: Instance of ``FileBackupGroup``
    :type group: FileBackupGroup
    """
    group.check_or_create_base_path()

    for item in group.dirs:
        backup_source = os.path.expanduser(item.dir)

        if not os.path.exists(backup_source):
            continue

        # TODO(sthzg) Find better solution than using globals.
        globals()['current_file_number'] = 0
        globals()['total_num_files'] = len(
            [os.path.join(dp, f)
             for dp, dn, fn in os.walk(backup_source) for f in fn])

        postfix = backup_source.replace(os.sep, '#')
        fname = "{}__{}.tar.gz".format(group.filename_prefix, postfix)
        target_path = "{}/{}".format(group.base_path, fname)

        with tarfile.open(target_path, "w:gz") as tar:
            tar.add(backup_source, filter=tar_add_filter)
            click.echo('\r', nl=False)
            msg = 'Wrote {}'.format(target_path)
            click.echo(click.style(msg, fg='green'))


def do_database_backups_for_group(group):
    """Creates tar.gz compressed backups for all backup target databases.

    :param group: Instance of ``FileBackupGroup``
    :type group: FileBackupGroup
    """
    group.check_or_create_base_path()
    dbs = group.dbs

    label = "Dumping DBs in group {}".format(group.group_title)
    with click.progressbar(dbs, label=click.style(label, fg='yellow')) as dbs:
        for item in dbs:
            if item.db_type == 'postgres':
                cmd = 'pg_dump -Fc -U {} {} > {}/{}__{}_{}.dump'.format(
                    item.db_user,
                    item.db_name,
                    group.base_path,
                    group.filename_prefix,
                    item.db_type.lower(),
                    item.db_name.lower())

                subprocess.call(cmd, shell=True)


def extract_dirs(val):
    """Returns a list of paths extracted from the config ``dir`` value."""
    items = list()
    for d in [x.strip() for x in val.split(',')]:
        item = FileBackupItem()
        item.dir = d
        items.append(item)

    return items


def extract_databases(val):
    items = list()
    for db in [x.strip() for x in val.split(',')]:
        # Skip when no DBs are configured in group (i.e. db is an empty string)
        if not db:
            continue

        try:
            items.append(DatabaseBackupItem(db))
        except ValueError, e:
            click.echo(click.style(e.message, fg='blue'))

    return items


def tar_add_filter(tarinfo):
    """Outputs a file progress counter while compressing file backups."""
    msg = '\r{}/{} files packed.'.format(globals()['current_file_number'],
                                         globals()['total_num_files'])
    click.echo(click.style(msg, fg='yellow'), nl=False)
    if tarinfo.isfile():
        globals()['current_file_number'] += 1

    return tarinfo


# >>>>> Data objects <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
class FileBackupGroup(object):
    def __init__(self):
        self.backup_storage_dir = None
        self.group_title = None
        self.base_path = None
        self.base_name = None
        self.dirs = []
        self.dbs = []
        self.filename_prefix = None

    def check_or_create_base_path(self):
        if self.base_path and not os.path.exists(self.base_path):
            os.makedirs(self.base_path)


class FileBackupItem(object):
    def __init__(self):
        self.dir = None


class DatabaseBackupItem(object):
    def __init__(self, db_string):
        self.db_string = db_string
        self.db_type = None
        self.db_user = None
        self.db_name = None

        self._extract_db_string()

    def _extract_db_string(self):
        """Validates and extracts the configured database string.

        :raises: ValueError
        """
        tokens = self.db_string.split(':')

        if len(tokens) != 3:
            raise ValueError(ERR_DB_STRING_LENGTH.format(self.db_string))
        else:
            self.db_type, self.db_name, self.db_user = tokens