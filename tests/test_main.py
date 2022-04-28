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
        v = Validate()
        dates = []
        for i in range(5):
            dates.append(f'2022-01-{i + 1}')
        series = pd.Series(dates)
        series = pd.to_datetime(series)
        # max_date = datetime(2022, 1, 3)
        max_date = pd.Timestamp(2022, 1, 3)

        timezone_str = 'America/Chicago'
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
