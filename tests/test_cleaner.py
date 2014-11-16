__author__ = 'Stephan'

import calendar
import datetime
import time
import unittest
from easybackup.backups import Cleaner


class TestCleaner(unittest.TestCase):
    def setUp(self):
        # Basic settings.
        cleaner = Cleaner()
        cleaner.days_to_keep = 7
        cleaner.weeks_to_keep = 4
        cleaner.months_to_keep = 12
        cleaner.day_of_week_to_keep = 5
        cleaner.day_of_month_to_keep = 1

        self.cleaner = cleaner

        #  Compare to date.
        self.compare_date = datetime.datetime(2014, 11, 11, 0, 0, 0)
        self.compare_date_unix = calendar.timegm(self.compare_date.timetuple())

        # List of dates to test against (550 days, i.e. about 1,5 years).
        self.date_list = [calendar.timegm(
            (self.compare_date - datetime.timedelta(days=x)).timetuple())
                          for x in range(0, 550)]

    def test_remove_older_than_months_to_keep(self):
        """All dates marked for removal are older than months_to_keep."""
        to_remove = self.cleaner._filter_older_than_months_to_keep(
            self.date_list, self.compare_date)

        for val,idx in enumerate(to_remove):
            self.assertEqual(True, self.date_list[idx] < self.compare_date_unix)
            self.assertEqual(True, len(to_remove) == 184)

    def test_months_to_keep(self):
        """Removed dates are between weeks_to_keep and months_to_keep."""
        to_remove = self.cleaner._filter_level_months_to_keep(
            self.date_list, self.compare_date)

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
        to_remove = self.cleaner._filter_level_weeks_to_keep(
            self.date_list, self.compare_date)

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



if __name__ == '__main__':
    unittest.main()
