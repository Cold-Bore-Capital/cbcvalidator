from datetime import date, datetime, timedelta
from dateutil.parser import parse
from typing import Union, Tuple

import pandas as pd
from pandas.api.types import is_datetime64_ns_dtype
from pytz import timezone
from tabulate import tabulate

today = date.today()


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
            {'col': 'numeric_ex', 'min_val': 2, 'max_val': 7, 'action': 'null'},
            {'col': 'string_ex_trim', 'max_len': 5, 'action': 'trim'},
            {'col': 'string_ex_null', 'min_len': 2, 'action': 'null'},
            {'col': 'date_ex_max', 'max_date': 'today', 'max_date_offset': -2, 'tz': 'America/Chicago', 'action': 'null'},
            # {'col': 'date_ex_min', 'min_date': '2020-01-01', 'action': 'null'},
        ]

        # Actions
        ## Possible action name values:
            raise. Default. Raises an exception.
            print. Prints an output to stdout.
            trim. For max string length, the string will be trimmed.
            null. Sets the value to None.

        # Dates
        ## Min and Max Date
        Date limits can be passed in as either a string `'2022-03-04'` or as a datetime `datetime(2022-03-04)`. Limits
        can also be set to relative values as described below

        ###  Possible date offsets:
            today. Not greater than or less than current date.
            yesterday. current date - 1
            tomorrow. current date + 1

        ## Date Offset:
            Allows an addition or subtraction of days from a relative date. You can enter any integer. For example, if
            a max date value was set to `tomorrow` and a max_dates_offset value was set to 1, the max limit would be
            the day after tomorrow.

        ## Timezone:
            Default is timezone unaware, user can specify any pytz acceptable timezone. If the series is tz aware, a
            timezone value must be passed in, or the date limit values must be tz aware. Passing in a timezone value
            will not convert the date limit, only make the limit tz aware.

        :return:
           The processed dataframe and a string message with the details of out of range items or None.

        """
        original_df = df.copy()
        output_str = ""
        for config in validation_rules:
            col = config['col']
            config_elements = config.keys()
            action = config.get('action')

            min_len = config.get('min_len')
            max_len = config.get('max_len')
            min_val = config.get('min_val')
            max_val = config.get('max_val')
            min_date = config.get('min_date')
            max_date = config.get('max_date')
            max_date_offset = config.get('max_date_offset')
            min_date_offset = config.get('min_date_offset')
            tz = config.get('tz')

            self._check_rule_config(col, config_elements)

            if col in df.columns:
                series = df[col]
                if len(series) > 0 and series.notna().sum() > 0:
                    if 'min_val' in config_elements or 'max_val' in config_elements:
                        # Numeric limit checks
                        mask = self._validate_numeric(series, min_val, max_val)
                    elif 'min_len' in config_elements or 'max_len' in config_elements:
                        mask = self._validate_string(series, min_len, max_len, col)
                    elif 'min_date' in config_elements or 'max_date' in config_elements:
                        mask = self._validate_date(series, min_date, max_date, min_date_offset, max_date_offset, tz, col)
                    else:
                        raise BadConfigurationError('No min or max values were set.')
                else:
                    mask = pd.Series([0])
            else:
                print(f'Column {col} not found in dataframe. Bypassing column.')
                mask = None

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
    def _check_rule_config(col: str, config_elements: list) -> None:
        """
         Checks for config errors in validation rules
        Args:
            col:
            config_elements:

        Returns: None

        """
        # Check for bad configuration
        numeric_check = 1 if ('min_val' in config_elements or 'max_val' in config_elements) else 0
        string_check = 1 if ('min_len' in config_elements or 'max_len' in config_elements) else 0
        date_check = 1 if ('min_date' in config_elements or 'max_date' in config_elements) else 0
        if numeric_check + string_check + date_check > 1:
            raise BadConfigurationError(f'Error in configuration for column {col}. You cannot set both numeric, '
                                        f'string, and/or date values for a single column.')

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
            mask = series > max_val
        elif min_val is not None or min_val == 0:
            mask = series < min_val

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
        mask = None
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

    def _validate_date(self,
                       series: pd.Series,
                       min_date: Union[datetime, str],
                       max_date: Union[datetime, str],
                       min_date_offset: int,
                       max_date_offset: int,
                       tz: str,
                       col: str) -> pd.Series.mask:
        """
       Validates date columns based on parameters

        Args:
            series: series of dates
            min_date: minimum date
            max_date: maximum date
            min_date_offset: offset value either +ve or -ve for minimum date
            max_date_offset: offset value either +ve or -ve for maximum date
            tz: time zone
            col: the name of the column

        Returns:
            A mask of values outside range
        """
        mask = None

        if not is_datetime64_ns_dtype(series):
            # Return as an empty mask if not a datetime series
            print(f'The column {col} was processed as a datetime, but was not a datetime datatype.')
            return pd.Series([0])

        # deal with relative dates and offsets
        rel_date = ['today', 'yesterday', 'tomorrow']
        if isinstance(min_date, str):
            if min_date in rel_date:
                min_date = self._convert_rel_date(min_date)
                if min_date_offset:
                    min_date = min_date + timedelta(days=min_date_offset)
            else:
                # assume a date was passed in that needs converting
                try:
                    min_date = parse(min_date)
                except:
                    raise BadConfigurationError(
                        f'The min_date value {min_date} is not a valid relative date measure or limit')

        if isinstance(max_date, str):
            if max_date in rel_date:
                max_date = self._convert_rel_date(max_date)
                if max_date_offset:
                    max_date = max_date + timedelta(days=max_date_offset)
            else:
                # assume a date was passed in that needs converting
                try:
                    max_date = parse(max_date)
                except:
                    raise BadConfigurationError(
                        f'The max_date value {max_date} is not a valid relative date measure or limit')

        # deal with timezones
        if tz:
            _tz = timezone(tz)
            if min_date:
                min_date = min_date.replace(tzinfo=_tz)
            if max_date:
                max_date = max_date.replace(tzinfo=_tz)


        if min_date is not None and max_date is not None:
            mask = (series < min_date) | (series > max_date)
        elif max_date is not None:
            mask = series > max_date
        elif min_date is not None:
            mask = series < min_date
        return mask

    @staticmethod
    def _convert_rel_date(rel_str: str) -> datetime:
        """
         Converts a relative date like today to an actual date
        Args:
            rel_str: relative date options are today, tomorrow, yesterday

        Returns:
            A datetime

        """

        now = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
        if rel_str == 'today':
            pass
        elif rel_str == 'tomorrow':
            now = now + timedelta(days=1)
        elif rel_str == 'yesterday':
            now = now - timedelta(days=1)
        else:
            raise BadConfigurationError(f'The relative date value {rel_str} is invalid')
        return now

    @staticmethod
    def _apply_action(action: str,
                      col: str,
                      mask: pd.Series.mask,
                      series: pd.Series,
                      min_len: Union[int,None],
                      max_len: Union[int,None],
                      min_val: Union[int,None],
                      max_val: Union[int,None],
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
            series.loc[mask] = series.loc[mask].str.slice(0,max_len)
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
            df: dataframe to be validated
            mask: mask of value indicating out of range
            col: column name
            action: action to be taken, 'null', 'print' or 'raise'
            min_val: minimum value
            max_val: maximum value
            min_len: minimum length
            max_len: maximum length

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
