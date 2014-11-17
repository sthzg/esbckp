# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import calendar
import datetime
from .utils import *


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
        self.compare_time = datetime.datetime.now()

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
            (self.compare_time - datetime.timedelta(weeks=self.weeks_to_keep))
            .timetuple())

        to_remove = list()
        for idx,file_date in enumerate(file_dates):
            dt = datetime.datetime.fromtimestamp(file_date)

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
            (self.compare_time - datetime.timedelta(weeks=self.weeks_to_keep))
            .timetuple())

        youngest_date_to_compare = calendar.timegm(
            (self.compare_time - datetime.timedelta(days=self.days_to_keep))
            .timetuple())

        to_remove = list()
        for idx,file_date in enumerate(file_dates):
            dt = datetime.datetime.fromtimestamp(file_date)

            cond1 = file_date <= youngest_date_to_compare
            cond2 = file_date >= latest_date_to_compare
            cond3 = dt.day != self.day_of_month_to_keep
            cond4 = dt.weekday() != self.day_of_week_to_keep

            if cond1 and cond2 and cond3 and cond4:
                to_remove.append(idx)

        return to_remove
