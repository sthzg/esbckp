# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import subprocess


class Shipper(object):
    """Ships backups via rsync to remote destination.

    Mostly a small wrapper around the rsync command that will be invoked
    via ``subprocess.call()``.
    """
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
