from unittest import TestCase

import pandas as pd

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
