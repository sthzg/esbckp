# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from datetime import datetime
import click
import os
import tarfile
from ConfigParser import ConfigParser

help_conf = 'Location of easybackup configuration file.'
help_group = "Specify section names to only backup one or more specific " \
             "groups. Separate section names with ,"

total_num_files = 0
current_file_number = 0


@click.command()
@click.option('--conf', default='~/etc/easybackup_conf.ini', help=help_conf)
@click.option('--groups', default=None, help=help_group)
def filebackup(conf, groups):
    if not os.path.exists(os.path.expanduser(conf)):
        raise click.ClickException('Config file does not exist.')

    cfg = os.path.expanduser(conf)

    parser = ConfigParser()
    parser.read([cfg])

    bsd = os.path.expanduser(parser.defaults().get('backup_storage_dir'))

    if not os.path.exists(bsd):
        raise click.ClickException('Backup storage directory does not exist at '
                                   '{}'.format(bsd))

    fbackup_items = list()
    for section in parser.sections():
        if groups and section not in groups:
            continue

        group = FileBackupGroup()
        group.group_title = section
        group.base_name = parser.get(section, 'base_name')

        for d in [x.strip() for x in parser.get(section, 'dir').split(',')]:
            item = FileBackupItem()
            item.dir = d
            group.items.append(item)

        fbackup_items.append(group)

    for group in fbackup_items:
        base_path = os.path.join(bsd, group.group_title)

        if not os.path.exists(base_path):
            os.makedirs(base_path)

        # Specify the datetime prefix for the backup's file name outside
        # of the loop so that all backup targets within this group get the
        # same filename prefix. (exact timestamps available on the file info).
        prefix = datetime.now().strftime('%Y-%m-%d--%H-%M-%S')

        for item in group.items:
            backup_source = os.path.expanduser(item.dir)

            if not os.path.exists(backup_source):
                continue

            # TODO(sthzg) Find better solution than using globals.
            globals()['current_file_number'] = 0
            globals()['total_num_files'] = len(
                [os.path.join(dp, f) for dp, dn, fn in
                 os.walk(backup_source) for f in fn])

            postfix = backup_source.replace(os.sep, '#')
            fname = "{}__{}.tar.gz".format(prefix, postfix)
            target_path = "{}/{}".format(base_path, fname)

            with tarfile.open(target_path, "w:gz") as tar:
                tar.add(backup_source, filter=tar_add_filter)
                click.echo('\r', nl=False)
                msg = 'Wrote {}'.format(target_path)
                click.echo(click.style(msg, fg='green'))


def tar_add_filter(tarinfo):
    msg = '\r{}/{} files packed.'.format(globals()['current_file_number'],
                                         globals()['total_num_files'])
    click.echo(click.style(msg, fg='yellow'), nl=False)
    if tarinfo.isfile():
        globals()['current_file_number'] += 1

    return tarinfo


class FileBackupGroup(object):
    def __init__(self):
        self.group_title = None
        self.base_name = None
        self.items = []


class FileBackupItem(object):
    def __init__(self):
        self.dir = None

