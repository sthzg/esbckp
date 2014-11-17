# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import click
import esbckp
from .constants import *
from .utils import do_file_backups_for_group, do_database_backups_for_group


@click.group()
@click.option('--debug/--no-debug', default=False)
def cli(debug):
    """Naive and simple app to backup directories and databases.

    Backup targets need to be configured in a config file in INI format. By
    default, the file is expected to live in ~/etc/easybackups_conf.ini.
    Use the ``--conf`` flag to pass a file.

    See further help for the available subcommands start, ship and clean.
    """
    pass

@cli.command()
@click.option('--conf', default='~/etc/easybackup_conf.ini', help=HELP_CONF)
@click.option('--groups', default=None, help=HELP_GROUP)
@click.option('--routines', default=None, help=HELP_ROUTINES)
def start(conf, groups, routines):
    """Start backups."""
    backup = esbckp.Backup(conf, groups, routines)

    for group in backup.backup_groups:
        if group.dirs:
            do_file_backups_for_group(group)

        if group.dbs:
            do_database_backups_for_group(group)


@cli.command()
@click.option('--conf', default='~/etc/easybackup_conf.ini', help=HELP_CONF)
@click.option('--groups', default=None, help=HELP_GROUP)
def ship(conf, groups):
    """Ship backups via rsync.

    If shipper settings are present in the INI file this command rsyncs
    each group folder to the configured target destination.
    """
    backup = esbckp.Backup(conf, groups)

    with click.progressbar(backup.backup_groups,
                           length=(len(backup.backup_groups)+1),
                           label="Groups") as bg:
        for group in bg:
            group.ship()


@cli.command()
@click.option('--conf', default='~/etc/easybackup_conf.ini', help=HELP_CONF)
@click.option('--groups', default=None, help=HELP_GROUP)
@click.option('--dryrun', default=True, type=bool, help=HELP_DRYRUN)
def clean(conf, groups, dryrun):
    """Clean outdated backups.

    Note that to actually delete the outdated files from the file system, the
    command needs to be invoked with --dryrun=False.

    Due to the support of weeks_to_keep and months_to_keep, there will
    usually be one additional backup in the timespan between days_to_keep
    and weeks_to_keep. This is because the backup according to
    day_of_month_to_keep will not be deleted, even though in most cases
    it will not fall on day_of_week_to_keep.
    """
    backup = esbckp.Backup(conf, groups)

    with click.progressbar(backup.backup_groups,
                           length=(len(backup.backup_groups) + 1),
                           label="Groups") as bg:
        for group in bg:
            group.clean(dry_run=dryrun)
