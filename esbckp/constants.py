# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals


HELP_CONF = (
    "Location of configuration file.")

HELP_GROUP = (
    "Specify section names to only backup one or more specific groups. "
    "Separate section names with commas (,).")

HELP_ROUTINES = (
    "Specify the routines that should be run for this backup. Separate "
    "routines with comma (,), e.g. --routines=dir,db.")

HELP_DRYRUN = (
    "By default easybackups_clean will only list the files that would be "
    "deleted  from the file system. To actually delete them, pass "
    "--dryrun=False.")

ERR_CONFIG_FILE_DOES_NOT_EXIST = (
    "Config file does not exist.")

ERR_BACK_STORAGE_DOES_NOT_EXIST = (
    "Backup storage directory does not exist at {}")

ERR_DB_STRING_LENGTH = (
    "Error with db string {}. It needs to have three tokens separated by a "
    "colon (:), e.g. postgres:my_database:my_user. Skipping this particular "
    "db-backup.")
