"""
Validation and Formatting a row by specifying how each column should look like.

A column definition is either a list of CellDefinition objects or a string which can be parsed to such a list.

The column definition can contain the following letters:
's': string column
'f': float column
'i': int column
'b': bool column: per default accepts true, t, 1 as True and false, f, 0 as False
'd': date column: default format (both input and output) is %Y-%m-%d
'&': add_on_column column: needs a value as the default which should be added in that place
'x': dont_include this column in the table (column is dropped)
'c': counter column: counts up from 0 (or the supplied start value) for each new row

Any column followed by a '!' is required (=needs to contain a non-empty value after formatting).
A column can take arguments (e.g. 'i(lower=2, upper=4, ignore_non_numeric=t)' means the integer has to be
between 2 and 4 (including) and any non-numeric chars (0-9,.) are removed prior to the validation and formatting).


"""

import re
import csv
from time import strptime, strftime
import typing as t

__all__ = ['CellDefinition', 'parse_column_definition', 'COLUMN_DEFINITION_TYPE']

COLUMN_DEFINITION_TYPE = t.TypeVar('COLUMN_DEFINITION_TYPE', str, t.List[t.Callable[[str], str]])


class CellDefinition():
    """Base class for cell definitions

    Args:
        unparsed_args: str, unparsed raw string which contains the arguments for this cell definition
        required: bool = False, whether or not this cell must contain a non-empty value
        parsed_args: already parsed arguments for this cell definition (overwrite unparsed ones)
    """
    # args which can be passed in -> all other will fail
    _arguments: t.List[str] = []

    def __init__(self, unparsed_args: t.Optional[str] = None, required: bool = False, **parsed_args):
        self.required = required
        self.init_defaults()
        self._parse_arguments(unparsed_args)
        for name, value in parsed_args.items():
            self._validate_and_set_argument(name, value)
        self.finalize_arguments()

    ### Methods which setup the internal state needed to validate and format values (overwrite as needed)

    def validate_argument(self, name: str, value: str) -> t.Tuple[str, t.Any]:
        """Validates a possible argument for this cell definition and returns the value converted to the proper type"""
        return name, value

    def init_defaults(self):
        """Inits a default argument this cell definition has"""
        pass

    def finalize_arguments(self):
        """Called after a argument parsing and assignment was done"""
        pass

    ### Methods which validate values (overwrite as needed)

    def validate_and_format_value(self, value: t.Optional[str]) -> str:
        """Validates and formats the value so it can be outputted

        Raises a ValueError, if the value doesn't validate
        """
        raise NotImplementedError("Need to implement the validate_and_format_value method")

    def __call__(self, value: t.Any) -> t.Optional[str]:
        """Outputs a validated and formatted value as str or raises a ValueError"""
        if isinstance(value, str) and value.strip() == '':
            ret = ''
        else:
            # None has to go through or the add-on columns will complain..
            stringified_value = str(value) if value is not None else None
            ret = str(self.validate_and_format_value(stringified_value))
        if ret == '' and self.required:
            raise ValueError("Value required, but was empty after validation and formatting")
        else:
            return ret

    ### Internal helper methods

    def _parse_arguments(self, arguments: t.Optional[str]):
        """Parses the raw arguments and assigns them to the instance (internal)"""
        if not arguments:
            return
        _args = arguments.split(',')
        for arg in _args:
            name, value = arg.split('=')
            self._validate_and_set_argument(name, value)

    def _validate_and_set_argument(self, name, value):
        """Validates an argument"""
        if name not in self._arguments:
            raise ValueError(f"Not a possible argument: {name}")
        try:
            name, value = self.validate_argument(name, value)
        except:
            raise ValueError(f"Invalid value for argument '{name}': {value}")
        setattr(self, name, value)

    def __repr__(self):
        """Representation of this CellDefinition"""
        a = []
        for name in self._arguments:
            val = getattr(self, name, None)
            if val:
                a.append(f'{name}={repr(val)}')
        if a:
            args_arg = f", args={','.join(a)}"
        else:
            args_arg = ""
        return f"{self.__class__}(required={self.required}{args_arg})"

    def __eq__(self, other):
        """Whether or not a CellDefinition is equal to this one"""
        must_be_equal = ['__class__', 'required'] + self._arguments
        for attr in must_be_equal:
            if getattr(self, attr, None) != getattr(other, attr, None):
                return False
        return True


class str_(CellDefinition):
    """A string/text cell
    """

    def validate_and_format_value(self, input: t.Optional[str]) -> str:
        if input is None:
            input = ''
        return input.strip()


_NUMERIC_REMOVE_NON_NUMERIC_CHARS = re.compile(r'[^0-9,.]')


class NumericCellDefinition(CellDefinition):
    """A numeric cell

    Args:
        lower: numeric: the lower bound of the cell
        upper: numeric: the upper bound of the cell
        thousands_separator: [',' or '.']: if '.' will treat '.' as thousands separator, else ','
        ignore_non_numeric: ignore non-numeric chars (e.g. $%). Accepts "t", "true", True, or 1 as True value,
                            everything else is interpreted as False
    """

    _arguments = ['lower', 'upper', 'thousands_separator', 'ignore_non_numeric']
    lower = None
    upper = None
    thousands_separator = None
    ignore_non_alpha = None

    def converter(self, input: t.Optional[str]) -> t.Union[float, int]:
        raise NotImplementedError("Need to supply a converter")

    def validate_argument(self, name: str, value: str):
        if name == 'ignore_non_numeric':
            if isinstance(value, bool):
                return name, value
            if value.lower() in ['t', 'true', 1, "1", True]:
                return name, True
            else:
                return name, False
        if name == 'thousands_separator':
            if value == '.':
                return name, '.'
            else:
                return name, ','
        return name, self.converter(value)

    def validate_and_format_value(self, input: t.Optional[str]) -> str:
        if input is None:
            return ''
        if getattr(self, 'ignore_non_numeric', False):
            input = _NUMERIC_REMOVE_NON_NUMERIC_CHARS.sub('', input)

        input = input.replace(self.thousands_separator or ',', '')
        # if we still have a comma we have a dot as a thousands separator...
        input = input.replace(',', '.')
        val = self.converter(input)
        if self.lower is not None:
            if self.lower > val:
                raise ValueError(f'value out of range {self.lower}<={val}')
        if self.upper is not None:
            if val > self.upper:
                raise ValueError(f'value out of range {val}<={self.upper}')
        return str(val)


class int_(NumericCellDefinition):
    def converter(self, input):
        try:
            return int(float(input))
        except:
            raise ValueError(f'Not parseable as int: {input}')


int_.__doc__ = NumericCellDefinition.__doc__.replace('numeric', 'int')


class float_(NumericCellDefinition):
    def converter(self, input):
        try:
            return float(input)
        except:
            raise ValueError(f'Not parseable as float: {input}')


float_.__doc__ = NumericCellDefinition.__doc__.replace('numeric', 'float')


class bool_(CellDefinition):
    """A integer cell

    Per default these values are converted to bool:
    * true: 'true', 't', 1
    * false: 'false', 'f', 0

    Args:
        true: str: additional value treated as true value
        false: str: additional value treated as false value
    """
    _arguments = ['true', 'false']

    def init_defaults(self):
        self._valid_str_values = {
            'true': True, 't': True, '1': True,
            'false': False, 'f': False, '0': False,
        }

    def finalize_arguments(self):
        if getattr(self, 'true', None):
            self._valid_str_values[getattr(self, 'true').lower()] = True
        if getattr(self, 'false', None):
            self._valid_str_values[getattr(self, 'false').lower()] = False

    def validate_and_format_value(self, value: t.Optional[str]) -> str:

        ## shouldn't be possible
        if isinstance(value, bool):
            return str(value)

        if isinstance(value, (int, float)):
            if int(value) == 1:
                return str(True)
            elif int(value) == 0:
                return str(False)
            else:
                raise ValueError('invalid literal for boolean. numeric, but not 1 or 0.')

        if not isinstance(value, str):
            raise ValueError('invalid literal for boolean. not numeric and not string.')

        lower_value = value.lower()
        try:
            return str(self._valid_str_values[lower_value])
        except:
            raise ValueError('invalid literal for boolean: "%s"' % value)


class date_(CellDefinition):
    """A date cell

    Args:
        in_format: str='%Y-%m-%d': format string the input corresponds to (strptime format)
        out_format: str='%Y-%m-%d': format string the output should corresponds to (strftime format)
    """

    _arguments = ['in_fmt', 'out_fmt']

    def init_defaults(self):
        self.out_format = '%Y-%m-%d'
        self.in_format = '%Y-%m-%d'

    def validate_and_format_value(self, value: t.Optional[str]) -> str:
        return strftime(self.out_format, strptime(value, self.in_format))


class add_on_(CellDefinition):
    """An add-on column

    Inserting this will add an addition column in the place where this cell definition is inserted.

    Args:
        value: str, the value which will be inserted in every cell of the column
    """
    _arguments = ['value']

    def init_defaults(self):
        self.value = ''

    def validate_and_format_value(self, value: t.Optional[str]) -> str:
        if value is not None:
            raise ValueError(f'Add-on columns cannot be used with a cell value, got {value}!')
        return str(self.value)


class counter_(add_on_):
    """A counter column

    Inserting this will add an addition column in the place where this cell definition is
    inserted, which increases by 1 per row.

    Args:
        start: int=0 value this counter should start from
    """
    _arguments = ['start']

    def init_defaults(self):
        self.start = 0
        self.current_count = 0

    def validate_argument(self, name: str, value: str) -> t.Tuple[str, t.Any]:
        """Validates a possible argument for this cell definition and returns the value converted to the proper type"""
        return name, int(value)

    def finalize_arguments(self):
        self.current_count = int(self.start)

    def validate_and_format_value(self, value: t.Optional[str]) -> str:
        if value is not None:
            raise ValueError(f'Counter column cannot be used with a value, got {value} (type: {type(value)})!')
        self.current_count += 1
        return str(self.current_count)


class _SkipColumn(Exception):
    pass


class dont_include_(CellDefinition):
    def __call__(self, value: t.Optional[str]):
        # needs to be overwritten to not get the empty str returns of the default implementation
        raise _SkipColumn()

    def validate_and_format_value(self, value: t.Optional[str]) -> str:
        raise _SkipColumn()


_CELLS = {
    # ! is for 'required' and '()' are used for arguments!
    's': str_,
    'f': float_,
    'i': int_,
    'b': bool_,
    'd': date_,
    '&': add_on_,
    'x': dont_include_,
    'c': counter_,
}  # type: t.Dict[str, t.Callable]


def parse_column_definition(definition: str) -> t.List[t.Callable]:
    """Returns a list of CellDefinition for a column definition"""
    res = []
    col = 0
    while col < len(definition):
        try:
            cell = _CELLS[definition[col]]
            col += 1
        except KeyError:
            avail = ','.join(_CELLS.keys())
            msg = f"Can't find a cell definition for '{definition[col]}' at pos {col + 1}, available: {avail}"
            raise RuntimeError(msg)
        args = None
        required = False
        # peek if the next is a '(' or '!'
        # This is not else/elif on purpose and the order is important
        # valid stuff is x! and x()!
        if col < len(definition) and definition[col] == '(':
            # ... and get the stuff until )
            right = definition.find(')', col + 1)
            if right == -1:
                msg = f"Bad column definition: found '(' at pos {col + 1}, but no following ')': {definition}"
                raise RuntimeError(msg)
            args = definition[col + 1:right]
            # swallow the ')'
            col = right + 1
        if col < len(definition) and definition[col] == '!':
            required = True
            # swallow the '!'
            col += 1

        cell_instance = cell(unparsed_args=args, required=required)  # type: t.Callable
        res.append(cell_instance)
    return res


def write_rows_as_csv_to_stream(rows: t.Union[t.Sequence[t.List[str]], t.Iterator[t.List[str]]],
                                columns_definition: COLUMN_DEFINITION_TYPE,
                                stream: t.TextIO,
                                delimiter_char: str = '\t',
                                ):
    """Writes each row (list of strings) as csv to the stream

    The csv is formatted as csv.excel dialect suitable for e.g. CSV loads into DBs

    No header is written.

    Args:
        rows: iterable of list of strings, input data
        columns_definition: either a str with a column definition or a list of CellDefinition instances.
                            If a row has more values than this definition (minus any add-on/counter columns),
                            the rest is omitted.
        stream: t.TextIO, sink where the processed content is written to (in Text mode, so sys.stdout is suitable)
        delimiter_char: str (default: '\t'), A character that delimits the output fields.
    """
    if isinstance(columns_definition, str):
        cell_definitions = parse_column_definition(columns_definition)
    else:
        cell_definitions = columns_definition

    cell_definitions_for_existing_columns = [f for f in cell_definitions if not isinstance(f, add_on_)]

    # only the one we want, without addons
    number_of_columns_to_look_at = len(cell_definitions_for_existing_columns)

    dialect = csv.excel
    dialect.delimiter = delimiter_char

    csv_writer = csv.writer(stream, dialect=dialect)

    n_rows = 0
    for row in rows:
        if len(''.join(row)) > 0:
            buf = []
            col_number = 0
            relevant_cols = row[:number_of_columns_to_look_at]
            try:
                for cell in cell_definitions:
                    # look out for add-on columns!
                    if not isinstance(cell, add_on_):
                        x = relevant_cols[col_number]
                        col_number += 1
                    else:
                        x = None

                    try:
                        val = cell(x)
                        buf.append(str(val))
                    except _SkipColumn:
                        # value should be dropped
                        pass
            except Exception as e:
                raise ValueError(f'Row contains bad data: {row} ({str(e.args)})')

            csv_writer.writerow(buf)
            n_rows += 1
    return n_rows
