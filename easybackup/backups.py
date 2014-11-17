# -*- coding: utf-8 -*-
"""
      Title: easybackup
     Author: Stephan Herzog (sthzg@gmx.net)
       Date: November 2014
      Usage: $ easybackups_start
             $ easybackups_ship
             $ easybackups_clean
  Platforms: Developed on MacOS X and Cent OS

Description:
    Naive and simple app to backup directories and databases. Backup targets
    need to be configured in a config file in INI format. By default, the
    file is expected to live in ~/etc/easybackups_conf.ini. Use the ``--conf``
    flag to pass a file.

    Type ``easybackups_start --help`` to learn about command line options.

    The tool is not daemonized and can be scheduled with cron jobs.

Dependencies:
    * click
    * colorama

Improvements:
    Experimental. Needs testing.

"""
from __future__ import absolute_import, unicode_literals
import calendar
import click
import os
import subprocess
import tarfile
from ConfigParser import ConfigParser, NoOptionError
from datetime import datetime, timedelta


# >>>>> Global Todos <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# TODO(sthzg) Refactor to use subcommands like $ easybackups start.
# TODO(sthzg) Split to multiple modules and a command package.
# TODO(sthzg) Add option to encrypt backups.
# TODO(sthzg) Decide about refactoring utils into classes.
# TODO(sthzg) Add logging.


# >>>>> Strings <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
HELP_CONF = '''
Location of easybackup configuration file.'''''

HELP_GROUP = '''
Specify section names to only backup one or more specific groups. Separate
section names with ,'''

HELP_ROUTINES = '''
Specify the routines that should be run for this backup. Separate routines
with comma (,), e.g. --routines=dir,db.'''

HELP_DRYRUN = '''
By default easybackups_clean will only list the files that would be deleted
from the file system. To actually delete them, pass --dryrun=False.'''

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
@click.option('--routines', default=None, help=HELP_ROUTINES)
def start(conf, groups, routines):
    """Starts the backup process."""
    backup = Backup(conf, groups, routines)

    for group in backup.backup_groups:
        if group.dirs:
            do_file_backups_for_group(group)

        if group.dbs:
            do_database_backups_for_group(group)


@click.command()
@click.option('--conf', default='~/etc/easybackup_conf.ini', help=HELP_CONF)
@click.option('--groups', default=None, help=HELP_GROUP)
def ship(conf, groups):
    """Starts shipping the backups via rsync.

    If shipper settings are present in the INI file this command rsyncs
    each group folder to the configured target destination.
    """
    backup = Backup(conf, groups)

    with click.progressbar(backup.backup_groups,
                           length=(len(backup.backup_groups)+1),
                           label="Groups") as bg:
        for group in bg:
            group.ship()


@click.command()
@click.option('--conf', default='~/etc/easybackup_conf.ini', help=HELP_CONF)
@click.option('--groups', default=None, help=HELP_GROUP)
@click.option('--dryrun', default=True, type=bool, help=HELP_DRYRUN)
def clean(conf, groups, dryrun):
    """Starts cleaning backups according to cleaner configuration.

    Note that to actually delete the outdated files from the file system, the
    command needs to be invoked with --dryrun=False.

    Due to the support of weeks_to_keep and months_to_keep, there will
    usually be one additional backup in the timespan between days_to_keep
    and weeks_to_keep. This is because the backup according to
    day_of_month_to_keep will not be deleted, even though in most cases
    it will not fall on day_of_week_to_keep.
    """
    backup = Backup(conf, groups)

    with click.progressbar(backup.backup_groups,
                           length=(len(backup.backup_groups) + 1),
                           label="Groups") as bg:
        for group in bg:
            group.clean(dry_run=dryrun)


# >>>>> Utils <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
def do_file_backups_for_group(group):
    """Creates tar.gz compressed backups for all backup target directories.

    :param group: Instance of ``BackupGroup``
    :type group: BackupGroup
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

        subprocess.call(['chmod', '0400', target_path])


def do_database_backups_for_group(group):
    """Creates compressed backups for all backup target databases.

    :param group: Instance of ``BackupGroup``
    :type group: BackupGroup
    """
    group.check_or_create_base_path()
    dbs = group.dbs

    label = "Dumping DBs in group {}".format(group.group_title)
    with click.progressbar(dbs, label=click.style(label, fg='yellow')) as dbs:
        for item in dbs:
            if item.db_type == 'postgres':
                target_path = '{}/{}__{}_{}.dump'.format(
                    group.base_path,
                    group.filename_prefix,
                    item.db_type.lower(),
                    item.db_name.lower())

                cmd = 'pg_dump -Fc -U {} {} > {}'.format(
                    item.db_user,
                    item.db_name,
                    target_path)

                subprocess.call(cmd, shell=True)
                subprocess.call(['chmod', '0400', target_path])


def extract_dirs(val):
    """Returns a list of paths extracted from the config ``dir`` value."""
    items = list()
    for d in [x.strip() for x in val.split(',')]:
        item = FileBackupItem()
        item.dir = d
        items.append(item)

    return items


def extract_databases(val):
    """Returns a list of db connection strings."""
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


def monthdelta(date, delta):
    m, y = (date.month+delta) % 12, date.year + ((date.month)+delta-1) // 12
    if not m: m = 12
    d = min(date.day, [31,
        29 if y%4==0 and not y%400==0 else 28,31,30,31,30,31,31,30,31,30,31][m-1])

    return date.replace(day=d,month=m, year=y)


# >>>>> Data objects <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
class Backup(object):
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


class Shipper(object):
    def __init__(self):
        self.ssh_port = 22
        self.user = None
        self.host = None
        self.source_dir = None
        self.target_dir = None

    def get_rsync_cmd(self):
        """Builds rsync command from Shipper configuration."""
        # TODO(sthzg) Create as list.
        cmd = "rsync -rvz -e 'ssh -p {}' --progress --ignore-existing {} {}@{}:{}"  # NOQA
        return cmd.format(
            self.ssh_port,
            self.source_dir,
            self.user,
            self.host,
            self.target_dir)

    def ship(self):
        """Ships current group to target location via rsync."""
        cmd = self.get_rsync_cmd()
        subprocess.call(cmd, shell=True)


class Cleaner(object):
    def __init__(self):
        self.days_to_keep = None
        self.weeks_to_keep = None
        self.months_to_keep = None
        self.day_of_week_to_keep = None
        self.day_of_month_to_keep = None
        self.storage_dir = None
        self.files = []
        self.file_index_to_delete = []
        self.compare_time = datetime.now()

    def clean(self, storage_dir, dry_run=True):
        """Analyzes outdated files and deletes them from the file system.

        By default this command will only output the names of the files
        that will be deleted. To really issue deletion from the file system,
        it needs to be invoked with ``dry_run`` set to False.

        :param storage_dir: Directory of files to be analyzed and deleted.
        :param dry_run: Flag that indicates whether files will be deleted.
        :return:
        """
        self.storage_dir = storage_dir
        self.files = self._get_files_and_dates()
        file_dates = [x[1] for x in self.files]
        self.file_index_to_delete = self._get_file_indexes_to_delete(file_dates)
        if not dry_run:
            self._delete_outdated()
        else:
            self._print_outdated()

    def _delete_outdated(self):
        """Deletes files marked for deletion from the file system."""
        self._print_outdated()
        for outdated in sorted(self.file_index_to_delete, reverse=True):
            os.remove(self.files[outdated][0])
            pass

    def _print_outdated(self):
        """Prints all files marked for removal to stdout."""
        for outdated in sorted(self.file_index_to_delete, reverse=True):
            print "Marked for removal: {}".format(self.files[outdated][0])

    def _get_files_and_dates(self):
        """Returns a list of tuples with file path and mtime."""
        return [(os.path.join(self.storage_dir, f),
                 os.stat(os.path.join(self.storage_dir, f)).st_mtime)
                for f in os.listdir(self.storage_dir)]

    def _get_file_indexes_to_delete(self, file_dates):
        """Returns indexes of files to be deleted.

        :param file_dates: A list of dates in unix timestamp format.
        :return:
        """
        cleanup_old = self._filter_older_than_months_to_keep(file_dates)
        cleanup_months = self._filter_level_months_to_keep(file_dates)
        cleanup_weeks = self._filter_level_weeks_to_keep(file_dates)

        # To ensure unique indexes we return list(set(...)).
        return list(set(cleanup_old + cleanup_months + cleanup_weeks))

    def _filter_older_than_months_to_keep(self, file_dates):
        """Returns indexes of dates that exceed months_to_keep.

        :param file_dates: A list of dates in unix timestamp format.
        :param compare_time:  A datetime object to compare against.
        :return: A list of indexes.
        """
        latest_date_to_keep = calendar.timegm(monthdelta(
            self.compare_time, self.months_to_keep * -1).timetuple())

        to_remove = [idx for idx,val in enumerate(file_dates)
                     if val < latest_date_to_keep]

        return to_remove

    def _filter_level_months_to_keep(self, file_dates):
        """Returns indexes of dates between weeks_to_keep and months_to_keep
        leaving one backup per month according to day_of_month_to_keep.

        :param file_dates: A list of dates in unix timestamp format.
        :param compare_time:  A datetime object to compare against.
        :return: A list of indexes.
        """
        latest_date_to_compare = calendar.timegm(monthdelta(
            self.compare_time, self.months_to_keep * -1).timetuple())

        youngest_date_to_compare = calendar.timegm(
            (self.compare_time - timedelta(weeks=self.weeks_to_keep))
            .timetuple())

        to_remove = list()
        for idx,file_date in enumerate(file_dates):
            dt = datetime.fromtimestamp(file_date)

            cond1 = file_date <= youngest_date_to_compare
            cond2 = file_date >= latest_date_to_compare
            cond3 = dt.day != self.day_of_month_to_keep

            if cond1 and cond2 and cond3:
                to_remove.append(idx)

        return to_remove

    def _filter_level_weeks_to_keep(self, file_dates):
        """Returns indexes of dates between days_to_keep and weeks_to_keep
        leaving one backup per week according to day_of_week_to_keep.

        Additionally ensures that the backup according to
        day_of_month_to_keep will not be deleted.

        :param file_dates: A list of dates in unix timestamp format.
        :param compare_time:  A datetime object to compare against.
        :return: A list of indexes.
        """
        latest_date_to_compare = calendar.timegm(
            (self.compare_time - timedelta(weeks=self.weeks_to_keep))
            .timetuple())

        youngest_date_to_compare = calendar.timegm(
            (self.compare_time - timedelta(days=self.days_to_keep))
            .timetuple())

        to_remove = list()
        for idx,file_date in enumerate(file_dates):
            dt = datetime.fromtimestamp(file_date)

            cond1 = file_date <= youngest_date_to_compare
            cond2 = file_date >= latest_date_to_compare
            cond3 = dt.day != self.day_of_month_to_keep
            cond4 = dt.weekday() != self.day_of_week_to_keep

            if cond1 and cond2 and cond3 and cond4:
                to_remove.append(idx)

        return to_remove
