from unittest import TestCase
from datetime import datetime, timedelta

import pandas as pd
import pytz

from cbcvalidator.main import Validate, ValueOutOfRange, BadConfigurationError


class TestValidate(TestCase):

    def test_validate(self):
        v = Validate(verbose=True)

        data = {'a': [1, 2, 3, 4, 5, 6, 7, 8],
                'b': ['abcdefg', 'abcdefghijkl', 'a', 'b', 'c', 'd', 'ef', 'ghi']}
        df = pd.DataFrame(data)
        val_dict = [
            {'col': 'a', 'min_val': 2, 'max_val': 7, 'action': 'null'},
            {'col': 'b', 'max_len': 5, 'action': 'trim'},
            {'col': 'b', 'min_len': 2, 'action': 'null'}
        ]

        df, msg = v.validate(df, val_dict)

        test = pd.isnull(df.loc[0, 'a'])
        self.assertTrue(test)

        # Test zero value limit (zero's eval to False)
        data = {'a': [-1, 2, 3, 4, 5, 6, 7, 8],
                'b': ['abcdefg', 'abcdefghijkl', 'a', 'b', 'c', 'd', 'ef', 'ghi']}
        df = pd.DataFrame(data)
        val_dict = [
            {'col': 'a', 'min_val': 0, 'max_val': 7, 'action': 'null'},
            {'col': 'b', 'max_len': 5, 'action': 'trim'},
            {'col': 'b', 'min_len': 2, 'action': 'null'}
        ]

        df, msg = v.validate(df, val_dict)

        test = pd.isnull(df.loc[0, 'a'])
        self.assertTrue(test)

        test = len(df.loc[0, 'b'])
        golden = 5
        self.assertEqual(golden, test)

        data = {'a': [1, 2, 3, 4, 5, 6, 7, 8],
                'b': ['abcdefg', 'abcdefghijkl', 'a', 'b', 'c', 'd', 'ef', 'ghi']}
        df = pd.DataFrame(data)
        val_dict = [
            {'col': 'a', 'max_val': 7, 'action': 'null'},
            {'col': 'a', 'min_val': 3, 'action': 'print'},
            {'col': 'b', 'max_len': 5, 'action': 'print'},
            {'col': 'b', 'min_len': 3, 'action': 'null'}
        ]

        df, msg = v.validate(df, val_dict)

        test = pd.isnull(df.loc[7, 'a'])
        self.assertTrue(test)

        test = pd.isnull(df.loc[2, 'b'])
        self.assertTrue(test)

        # Test value out of range raises
        data = {'a': [1, 2, 3, 4, 5, 6, 7, 8],
                'b': ['abcdefg', 'abcdefghijkl', 'a', 'b', 'c', 'd', 'ef', 'ghi']}
        df = pd.DataFrame(data)
        val_dict = [
            {'col': 'a', 'max_val': 7, 'action': 'raise'},
        ]

        with self.assertRaises(ValueOutOfRange) as context:
            df, msg = v.validate(df, val_dict)

        # Test with no validation criteria matching.
        data = {'a': [1, 2, 3, 4, 5, 6, 7, 8],
                'b': ['abcdefg', 'abcdefghijkl', 'a', 'b', 'c', 'd', 'ef', 'ghi']}
        df = pd.DataFrame(data)
        val_dict = [
            {'col': 'a', 'max_val': 99, 'action': 'null'},
        ]

        df, msg = v.validate(df, val_dict)

        self.assertIsNone(msg)

        # Check that fully empty series works.
        data = {'a': [None, None, None, None, None, None, None, None]}
        df = pd.DataFrame(data)
        val_dict = [
            {'col': 'a', 'max_val': 7, 'action': 'null'}
        ]

        df, msg = v.validate(df, val_dict)
        # So long as this doesn't raise an error it's fine.

        # Test what happens when a numeric column is processed as a string. This should do nothing, but print a
        # warning.
        data = {'a': [1, 2, 3, 4, 5, 6, 7, 8],
                'b': ['abcdefg', 'abcdefghijkl', 'a', 'b', 'c', 'd', 'ef', 'ghi']}
        df = pd.DataFrame(data)
        val_dict = [
            {'col': 'a', 'min_len': 2, 'max_len': 7, 'action': 'trim'}
        ]

        df, msg = v.validate(df, val_dict)
        test = df.loc[0, 'a']
        self.assertEqual(1, test)

        # Test for a missing column
        data = {'a': [1, 2, 3, 4, 5, 6, 7, 8],
                'b': ['abcdefg', 'abcdefghijkl', 'a', 'b', 'c', 'd', 'ef', 'ghi']}
        df = pd.DataFrame(data)
        val_dict = [
            {'col': 'not_a_col_name', 'min_len': 2, 'max_len': 7, 'action': 'trim'}
        ]

        df, msg = v.validate(df, val_dict)
        test = df.loc[0, 'a']
        self.assertEqual(1, test)

        # Test value out of range raises
        data = {'a': [1, 2, 3, 4, 5, 6, 7, 8],
                'b': ['abcdefg', 'abcdefghijkl', 'a', 'b', 'c', 'd', 'ef', 'ghi']}
        df = pd.DataFrame(data)
        val_dict = [
            {'col': 'a', 'action': 'trim'},
        ]

        with self.assertRaises(BadConfigurationError) as context:
            df, msg = v.validate(df, val_dict)

    def test__validate_date(self):
        # ****************
        # Check max dates
        # ****************
        v = Validate()
        dates = []
        for i in range(5):
            dates.append(f'2022-01-{i + 1}')
        series = pd.to_datetime(pd.Series(dates))
        max_date = datetime(2022, 1, 3)
        timezone_str = None
        mask = v._validate_date(series, None, max_date, None, None, timezone_str, '0')
        self.assertTrue(mask[0])
        self.assertFalse(mask[3])


        # unit test to check if time zone aware series is passed
        dates = []
        for i in range(5):
            dates.append(datetime(2022, 1, i + 1, tzinfo=pytz.timezone('US/Central')))
        series = pd.Series(dates)
        max_date = datetime(2022, 1, 3)
        timezone_str = 'US/Central'
        mask = v._validate_date(series, None, max_date, None, None, timezone_str, '0')
        self.assertTrue(mask[0])
        self.assertFalse(mask[3])

        # Check relative dates
        dates = []
        now = datetime.now()
        for i in range(5):
            test_date = now + timedelta(days=i)
            dates.append(test_date)
        series = pd.Series(dates)
        max_date = 'tomorrow'
        timezone_str = None
        mask = v._validate_date(series, None, max_date, None, None, timezone_str, '0')
        self.assertTrue(mask[0])
        self.assertFalse(mask[2])

        # Check relative dates with an offset
        dates = []
        now = datetime.now()
        for i in range(5):
            test_date = now + timedelta(days=i) - timedelta(days=3) # putting it in range of yesterday
            dates.append(test_date)
        series = pd.Series(dates)
        max_date = 'yesterday'
        max_offset = -1
        timezone_str = None
        mask = v._validate_date(series, None, max_date, None, max_offset, timezone_str, '0')
        self.assertTrue(mask[0])
        self.assertFalse(mask[2])

        # ****************
        # Check min dates
        # ****************
        v = Validate()
        dates = []
        for i in range(5):
            dates.append(f'2022-01-{i + 1}')
        series = pd.to_datetime(pd.Series(dates))
        min_date = datetime(2022, 1, 3)
        timezone_str = None
        mask = v._validate_date(series, min_date, None, None, None, timezone_str, '0')
        self.assertFalse(mask[0])
        self.assertTrue(mask[3])

        # unit test to check if time zone aware series is passed
        dates = []
        for i in range(5):
            dates.append(datetime(2022, 1, i + 1, tzinfo=pytz.timezone('US/Central')))
        series = pd.Series(dates)
        min_date = datetime(2022, 1, 3)
        timezone_str = 'US/Central'
        mask = v._validate_date(series, min_date, None, None, None, timezone_str, '0')
        self.assertFalse(mask[0])
        self.assertTrue(mask[2])

        # Check relative dates
        dates = []
        now = datetime.now()
        for i in range(5):
            test_date = now + timedelta(days=i)
            dates.append(test_date)
        series = pd.Series(dates)
        min_date = 'tomorrow'
        timezone_str = None
        mask = v._validate_date(series, min_date, None, None, None, timezone_str, '0')
        self.assertFalse(mask[0])
        self.assertTrue(mask[2])

        # Check relative dates with an offset
        dates = []
        now = datetime.now()
        for i in range(5):
            test_date = now + timedelta(days=i)
            dates.append(test_date)
        series = pd.Series(dates)
        min_date = 'yesterday'
        min_offset = 2
        timezone_str = None
        mask = v._validate_date(series, min_date, None, min_offset, None, timezone_str, '0')
        self.assertFalse(mask[0])
        self.assertTrue(mask[2])

        # ****************
        # Check min and max dates
        # ****************
        v = Validate()
        dates = []
        for i in range(5):
            dates.append(f'2022-01-{i + 1}')
        series = pd.to_datetime(pd.Series(dates))
        min_date = datetime(2022, 1, 2)
        max_date = datetime(2022, 1, 3)
        timezone_str = None
        mask = v._validate_date(series, min_date, max_date, None, None, timezone_str, '0')
        self.assertFalse(mask[0])
        self.assertTrue(mask[1])
        self.assertTrue(mask[2])
        self.assertFalse(mask[3])
        self.assertFalse(mask[4])

        # ****************
        # Check non datetime column
        # ****************
        not_dates = []
        for i in range(5):
            not_dates.append(f'abc-{i}')
        series = pd.Series(not_dates)
        min_date = datetime(2022, 1, 2)
        max_date = datetime(2022, 1, 3)
        timezone_str = None
        mask = v._validate_date(series, min_date, max_date, None, None, timezone_str, '0')
        test = mask.sum()
        self.assertEqual(0, test)

        # ****************
        # Check raises error on bad offset
        # ****************
        dates = []
        now = datetime.now()
        for i in range(5):
            test_date = now + timedelta(days=i)
            dates.append(test_date)
        series = pd.Series(dates)
        min_date = 'a_bad_input'
        min_offset = 2
        timezone_str = None
        with self.assertRaises(BadConfigurationError) as context:
            mask = v._validate_date(series, min_date, None, min_offset, None, timezone_str, '0')



        a = 0

    def test__convert_rel_date(self):
        v = Validate()
        rel_str = 'today'
        test = v._convert_rel_date(rel_str)
        golden = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
        self.assertEqual(golden, test)

        rel_str = 'yesterday'
        test = v._convert_rel_date(rel_str)
        golden = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0) - timedelta(days=1)
        self.assertEqual(golden, test)

        rel_str = 'tomorrow'
        test = v._convert_rel_date(rel_str)
        golden = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0) + timedelta(days=1)
        self.assertEqual(golden, test)

        # Check BadConfigurationError
        with self.assertRaises(BadConfigurationError) as context:
            rel_str = 'abc'
            test = v._convert_rel_date(rel_str)
