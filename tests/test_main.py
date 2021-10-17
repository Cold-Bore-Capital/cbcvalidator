from unittest import TestCase
import pandas as pd
from cbcvalidator.main import Validate


class TestValidate(TestCase):

    def test_validate(self):
        v = Validate()

        data = {'a': [1, 2, 3, 4, 5, 6, 7, 8],
                'b': ['abcdefg', 'abcdefghijkl', 'a', 'b', 'c', 'd', 'ef', 'ghi']}
        df = pd.DataFrame(data)
        val_dict = [
            {'col': 'a', 'min_val': 2, 'max_val': 7, 'action': 'null'},
            {'col': 'b', 'max_len': 5, 'action': 'trim'},
            {'col': 'b', 'min_len': 2, 'action': 'null'}
        ]

        v.validate(df, val_dict)

        test = pd.isnull(df.loc[0, 'a'])
        self.assertTrue(test)

        test = df.loc[0, 'b'].str.len()
        golden = 5
        self.assertEqual(golden, test)