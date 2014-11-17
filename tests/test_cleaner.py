# -*- coding: utf-8 -*-
import calendar
import datetime
import os
import shutil
import subprocess
import unittest
from esbckp.backups import Cleaner


def create_testfiles(file_dates):
    """Creates test files with atime and mtime according to ``file_dates``."""
    base_path = os.path.abspath(os.path.dirname(__file__))
    test_path = os.path.join(base_path, 'testfiles')
    try:
        os.mkdir(test_path)
    except OSError:
        shutil.rmtree(test_path)
        os.mkdir(test_path)

    for file_date in file_dates:
        dt = datetime.datetime.fromtimestamp(file_date)
        fname = os.path.join(test_path, "test_{}.txt".format(dt))
        with open(fname, "w") as f:
            f.write("test file with date {}".format(dt))

        os.utime(fname, (file_date, file_date))
        subprocess.call(['chmod', '0400', fname])


class TestCleaner(unittest.TestCase):
    def setUp(self):
        #  Compare to date.
        self.compare_date = datetime.datetime(2014, 11, 11, 0, 0, 0)
        self.compare_date_unix = calendar.timegm(self.compare_date.timetuple())

        # Basic settings.
        cleaner = Cleaner()
        cleaner.days_to_keep = 7
        cleaner.weeks_to_keep = 4
        cleaner.months_to_keep = 12
        cleaner.day_of_week_to_keep = 5
        cleaner.day_of_month_to_keep = 1
        cleaner.compare_time = self.compare_date
        cleaner.storage_dir = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), 'testfiles')
        self.cleaner = cleaner

        # List of dates to test against (550 days, i.e. about 1,5 years).
        self.date_list = [calendar.timegm(
            (self.compare_date - datetime.timedelta(days=x)).timetuple())
                          for x in range(0, 550)]

    def test_remove_older_than_months_to_keep(self):
        """All dates marked for removal are older than months_to_keep."""
        to_remove = self.cleaner._filter_older_than_months_to_keep(
            self.date_list)

        for val,idx in enumerate(to_remove):
            self.assertEqual(True, self.date_list[idx] < self.compare_date_unix)
            self.assertEqual(True, len(to_remove) == 184)

    def test_months_to_keep(self):
        """Removed dates are between weeks_to_keep and months_to_keep."""
        to_remove = self.cleaner._filter_months_to_keep(
            self.date_list)

        youngest_date_to_compare = 1413244800  # i.e. 2014-10-14 02:00:00
        latest_date_to_compare = 1384128000    # i.e. 2013-11-11 01:00:00

        for val,idx in enumerate(to_remove):
            cond1 = self.date_list[idx] <= youngest_date_to_compare
            cond2 = self.date_list[idx] >= latest_date_to_compare
            cond3 = datetime.datetime.fromtimestamp(
                self.date_list[idx]).day != self.cleaner.day_of_month_to_keep

            self.assertEqual(True, cond1 and cond2 and cond3)
            self.assertEqual(True, len(to_remove) == 327)

    def test_weeks_to_keep(self):
        """Removed dates are between days_to_keep and weeks_to_keep."""
        to_remove = self.cleaner._filter_weeks_to_keep(
            self.date_list)

        youngest_date_to_compare = 1415059200  # i.e. 2014-11-04 01:00:00
        latest_date_to_compare = 1413244800    # i.e. 2014-10-14 02:00:00

        for val,idx in enumerate(to_remove):
            cond1 = self.date_list[idx] <= youngest_date_to_compare
            cond2 = self.date_list[idx] >= latest_date_to_compare
            cond3 = datetime.datetime.fromtimestamp(
                self.date_list[idx]).weekday() != self.cleaner.day_of_week_to_keep
            cond4 = datetime.datetime.fromtimestamp(
                self.date_list[idx]).day != self.cleaner.day_of_month_to_keep

            self.assertEqual(True, cond1 and cond2 and cond3 and cond4)
            self.assertEqual(True, len(to_remove) == 19)

    def test_get_file_indexes_to_delete(self):
        """List of indexes sum up to the correct amount."""
        to_remove = self.cleaner._get_file_indexes_to_delete(self.date_list)
        self.assertEqual(True, len(to_remove) == 529)

    def test_file_deletion(self):
        """Expected number of files remain on the file system after deltion."""
        create_testfiles(self.date_list)
        self.cleaner.files = self.cleaner._get_files_and_dates()
        file_dates = [x[1] for x in self.cleaner.files]
        self.cleaner.file_index_to_delete = self.cleaner._get_file_indexes_to_delete(file_dates)
        self.cleaner._delete_outdated()

        self.assertEqual(True, len(os.listdir(self.cleaner.storage_dir)) == 21)

if __name__ == '__main__':
    unittest.main()
