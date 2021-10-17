from typing import Union

import pandas as pd


class Validate():

    def __init__(self):
        pass

    def validate(self, df: pd.DataFrame, validation_dict: dict) -> pd.DataFrame:
        """
        Validates field in a dataframe as specified by the validation_dict.

        :param df: A dataframe to validate.
        :param validation_dict: A dict containing validation parameters. All validation params are optional.
        {'column_name': {'min_len': 5,
                         'max_len': 10,
                         'min_val': 2,
                         'max_val': 150,
                         'action': 'action_name'}
        }

        Possible action name values:
            raise. Default. Raises an exception.
            print. Prints an output to stdout.
            trim. For max string length, the string will be trimmed.
            null. Sets the value to None.
        :return: The processed dataframe.
        """

        for config in validation_dict:
            col = config['col']
            config_elements = config.keys()
            action = config.get('action')
            alert = config.get('alert')
            max_len = None
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
                mask = self._validate_numeric(series, min_val, max_val)

            elif 'min_len' in config_elements or 'max_len' in config_elements:
                # String limits check
                min_len = config.get('min_len')
                max_len = config.get('max_len')
                series = df[col]
                mask = self._validate_string(series, min_len, max_len)
            else:
                raise BadConfigurationError('No min or max values were set.')

            if mask.sum() > 0:
                self._apply_action_numeric(action, alert, col, mask, series, max_len, max_val)

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
        if min_val and max_val:
            mask = (series < min_val) | (series > max_val)
        elif max_val:
            mask = series >= max_val
        else:
            mask = series <= min_val
        return mask

    @staticmethod
    def _validate_string(series: pd.Series,
                         min_len: Union[int, float],
                         max_len: Union[int, float]) -> pd.Series.mask:
        """
        Validates string columns based on validation dict.

        Args:
            series:
            min_len:
            max_len:

        Returns:

        """
        if min_len and max_len:
            mask = (series.str.len() < min_len) | (series.str.len() > max_len)
        elif max_len:
            mask = series.str.len() > max_len
        else:
            mask = series.str.len() < min_len
        return mask

    @staticmethod
    def _apply_action_numeric(action: str,
                              alert: bool,
                              col: str,
                              mask: pd.Series.mask,
                              series: pd.Series,
                              max_len: int,
                              max_val: int) -> None:
        """
        Applies the specified action to the series.

        Args:
            action: The action to take on out of range values. Option are raise, print, trim (string only), null.
            alert: Flag to indicate if an email alert should be sent about the out of range value.
            col: Name of the column being processed.
            mask:
            series:
            max_len:
            max_val:

        Returns:
            None
        """
        if action == 'raise':
            raise ValueOutOfRange(f'The column {col} contained out of range numeric values \n {series[mask]}')
        elif action == 'print':
            print(f'The column {col} contained out of range numeric values \n {series[mask]}')
        elif action == 'null':
            series.loc[mask] = None
        elif action == 'trim':
            series.loc[mask] = series.loc[mask].str.slice(0, max_len)


class BadConfigurationError(Exception):
    pass


class ValueOutOfRange(Exception):
    pass
