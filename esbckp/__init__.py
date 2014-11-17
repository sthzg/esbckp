# -*- coding: utf-8 -*-
"""
      Title: esbckp
     Author: Stephan Herzog (sthzg@gmx.net)
       Date: November 2014
      Usage: $ esbckp
             $ esbckp start --help
             $ esbckp ship --help
             $ esbckp clean --help
  Platforms: Developed on MacOS X and Cent OS

Description:
    Naive and simple app to backup directories and databases. Backup targets
    need to be configured in a config file in INI format. By default, the
    file is expected to live in ~/etc/easybackups_conf.ini. Use the ``--conf``
    flag to pass a file.

    Type ``esbckp --help`` to learn about command line options.

    The tool is not daemonized and can be scheduled with cron jobs.

Dependencies:
    * Click
    * colorama

Improvements:
    Experimental. Needs testing.

"""
from __future__ import absolute_import, unicode_literals
from .backups import Backup, FileBackupItem, DatabaseBackupItem
from .shipper import Shipper
from .cleaner import Cleaner


# >>>>> Global Todos <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# TODO(sthzg) Add option to encrypt backups.
# TODO(sthzg) Decide about refactoring utils into classes.
# TODO(sthzg) Make backup actions pluggable and extendable.
# TODO(sthzg) Add logging.


total_num_files = 0
current_file_number = 0
