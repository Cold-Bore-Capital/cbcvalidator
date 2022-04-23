from typing import Union, Tuple

import pandas as pd
from tabulate import tabulate


class Validate:

    def __init__(self, verbose=False, test_mode=False):
        self._test_mode = test_mode
        self._verbose = verbose

    def validate(self, df: pd.DataFrame, validation_rules: list) -> Tuple[pd.DataFrame, Union[str, None]]:
        """
        Validates field in a dataframe as specified by the validation_dict.

        :param df: A dataframe to validate.
        :param validation_rules: A dict containing validation parameters. All validation params are optional.
        [
            {'col': 'a', 'min_val': 2, 'max_val': 7, 'action': 'null'},
            {'col': 'b', 'max_len': 5, 'action': 'trim'},
            {'col': 'b', 'min_len': 2, 'action': 'null'}
        ]

        Possible action name values:
            raise. Default. Raises an exception.
            print. Prints an output to stdout.
            trim. For max string length, the string will be trimmed.
            null. Sets the value to None.
        :return:
           The processed dataframe and a string message with the details of out of range items or None.

        """
        original_df = df.copy()
        output_str = ""
        for config in validation_rules:
            col = config['col']
            config_elements = config.keys()
            action = config.get('action')
            min_len = None
            max_len = None
            min_val = None
            max_val = None
            # Check for bad configuration
            if ('min_val' in config_elements or 'max_val' in config_elements) and (
                    'min_len' in config_elements or 'max_len' in config_elements):
                raise BadConfigurationError(f'Error in configuration for column {col}. You cannot set both numeric and '
                                            f'string values for a single column.')

            if 'min_val' in config_elements or 'max_val' in config_elements:
                # Numeric limits check
                min_val = config.get('min_val')
                max_val = config.get('max_val')
                series = df[col]
                if len(series) > 0:
                    mask = self._validate_numeric(series, min_val, max_val)
                else:
                    # Create an empty mask
                    mask = pd.Series([0])

            elif 'min_len' in config_elements or 'max_len' in config_elements:
                # String limits check
                min_len = config.get('min_len')
                max_len = config.get('max_len')
                if col in df.columns:
                    series = df[col]
                    if len(series) > 0 and series.notna().sum() > 0:
                        mask = self._validate_string(series, min_len, max_len, col)
                    else:
                        # Create an empty mask
                        mask = pd.Series([0])
                else:
                    print(f'Column {col} not found in dataframe. Bypassing column.')
                    mask = None
            else:
                raise BadConfigurationError('No min or max values were set.')
            if isinstance(mask, pd.Series):
                if mask.sum() > 0:
                    self._apply_action(action, col, mask, series, min_len, max_len, min_val, max_val, self._verbose)
                    current_output = self._build_output_msg(original_df, mask, col, action, min_val, max_val, min_len,
                                                            max_len)
                    output_str = f'{output_str}{current_output}'

        if output_str != "":
            return df, output_str
        else:
            return df, None

    @staticmethod
    def _validate_numeric(series: pd.Series,
                          min_val: Union[int, float],
                          max_val: Union[int, float]) -> pd.Series.mask:
        """
        Validates numeric columns based on validation dict. 
        
        Args:
            series: 
            min_val: 
            max_val: 

        Returns:
            A mask indicating out of range values.
        """
        if (min_val is not None or min_val == 0) and (max_val is not None or max_val == 0):
            mask = (series < min_val) | (series > max_val)
        elif max_val is not None or max_val == 0:
            mask = series >= max_val
        elif min_val is not None or min_val == 0:
            mask = series <= min_val

        return mask

    @staticmethod
    def _validate_string(series: pd.Series,
                         min_len: Union[int, float, None],
                         max_len: Union[int, float, None],
                         col: str) -> pd.Series.mask:
        """
        Validates string columns based on validation dict.

        Args:
            series: Series to process
            min_len: Min len
            max_len: Max len
            col: The name of the column

        Returns:
            A mask of values outside range.
        """
        # Put this try except here to catch non str series processed as string.
        if series.dtype == object:
            if (min_len is not None or min_len == 0) and (max_len is not None or max_len == 0):
                mask = (series.str.len() < min_len) | (series.str.len() > max_len)
            elif max_len is not None or max_len == 0:
                mask = series.str.len() > max_len
            elif min_len is not None or min_len == 0:
                mask = series.str.len() < min_len

            return mask
        else:
            # Return as an empty mask if not a string series
            print(f'The column {col} was processed as a string, but was not a str datatype.')
            return pd.Series([0])

    @staticmethod
    def _apply_action(action: str,
                      col: str,
                      mask: pd.Series.mask,
                      series: pd.Series,
                      min_len: int,
                      max_len: int,
                      min_val: int,
                      max_val: int,
                      verbose: bool = False) -> None:
        """
        Applies the specified action to the series.

        Args:
            action: The action to take on out of range values. Option are raise, print, trim (string only), null.
            col: Name of the column being processed.
            mask:
            series:
            max_len:
            max_val:

        Returns:
            None (series by ref)
        """
        min_val_str = min_len if min_len else min_val
        max_val_str = max_len if max_len else max_val

        msg = f'The column {col} contained out of range numeric values \n' \
              f'Limits - min: {min_val_str}  |  max: {max_val_str} \n' \
              f' {series[mask]} \n'
        if action == 'raise':
            raise ValueOutOfRange(msg)
        elif action == 'print':
            print(msg)
        elif action == 'null':
            series.loc[mask] = None
            if verbose:
                print(msg)
        elif action == 'trim':
            series.loc[mask] = series.loc[mask].str.slice(0, max_len)
            if verbose:
                print(msg)

    @staticmethod
    def _build_output_msg(df: pd.DataFrame,
                          mask: pd.DataFrame.mask,
                          col: str,
                          action: str,
                          min_val: Union[int, float],
                          max_val: Union[int, float],
                          min_len: int,
                          max_len: int) -> str:
        """
        Builds an output message suitable for email alert.

        Args:
            df:
            mask:
            col:
            action:
            min_val:
            max_val:
            min_len:
            max_len:

        Returns:
            A string containing an output message in the format
                Column "A" contained out of range values.
                The limits were min_len: None | max_len: 10
                Rows with out of range values:
                Idx    Name              Age         Active
                3      Areallylongname   23          True
        """
        column_str = f'Column "{col}" had {mask.sum()} values out of range.'
        if min_val or max_val:
            # Numeric based
            limits_str = f'The numeric limits were min: {min_val}  |  max: {max_val}. Action taken: {action}.'
        else:
            limits_str = f'The string limits were min: {min_len}  |  max: {max_len}. Action taken: {action}.'

        df_str = tabulate(df[mask], headers='keys', tablefmt='psql')

        return f'{column_str}\n{limits_str}\n{df_str}\n\n'


class BadConfigurationError(Exception):
    pass


class ValueOutOfRange(Exception):
    pass


class SeriesNotString(Exception):
    pass


class MissingConfiguration(Exception):
    pass