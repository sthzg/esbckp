# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import click
import esbckp
import os
import subprocess
import tarfile


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
        item = esbckp.FileBackupItem()
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
            items.append(esbckp.DatabaseBackupItem(db))
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
