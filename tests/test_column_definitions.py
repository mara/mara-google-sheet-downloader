from mara_google_sheet_downloader.columns_definition import parse_column_definition, str_, int_, float_
import pytest


def test_parse_column_definition():
    assert parse_column_definition('s!') == [str_(required=True)]
    assert parse_column_definition('s') != [str_(required=True)]
    assert parse_column_definition('s()') == [str_(required=False)], f'returned: {parse_column_definition("s()")}'
    assert parse_column_definition('s()!') == [str_(required=True)]
    assert parse_column_definition('i') == [int_()]
    assert parse_column_definition('i!') == [int_(required=True)]
    assert parse_column_definition('i(lower=1,upper=2)') == [int_(lower=1, upper=2)]
    assert parse_column_definition('i(lower=1,upper=2)') == [int_(unparsed_args='lower=1,upper=2')]
    assert parse_column_definition('i(lower=1,upper=2)!') == [int_(unparsed_args='lower=1,upper=2', required=True)]
    assert parse_column_definition('f(lower=1,upper=2)') == [float_(lower=1, upper=2)]
    assert parse_column_definition('f(lower=1,upper=2)') == [float_(unparsed_args='lower=1,upper=2')]
    assert parse_column_definition('f(lower=1,upper=2)') == [float_(lower=1, upper=2)]
    assert parse_column_definition('f(lower=1,upper=2)!') == [
        float_(unparsed_args='lower=1,upper=2', required=True)]

    try:
        parse_column_definition('f!()!')
        assert False
    except RuntimeError:
        pass
    try:
        parse_column_definition('f(')
        assert False
    except RuntimeError:
        pass


def test_string_formatting():
    assert str_()('') == ''
    assert str_()(None) == ''
    assert str_()(' ') == ''
    assert str_()(' a ') == 'a'


def test_numeric_formatting():
    assert float_()(None) == ''

    assert float_(lower=1, upper=200)('1.23') == '1.23'
    assert float_(lower=1, upper=200)('1.23 ') == '1.23'
    assert float_(lower=1, upper=2000)('123,4') == '1234.0'
    assert float_(lower=1, upper=2000)('1.23,4') == '1.234'

    with pytest.raises(ValueError):
        float_(lower=1, upper=200)('1.23.4')

    assert float_()('1,23.4') == '123.4'
    assert float_(thousands_separator='.')('1,23.4') == '1.234'

    # https://github.com/mara/mara-google-sheet-downloader/pull/7
    assert float_()('1,234') == '1234.0'
    assert float_(thousands_separator='.')('1.234') == '1234.0'
    assert int_()('1,234') == '1234'
    assert int_(thousands_separator='.')('1.234') == '1234'

    with pytest.raises(ValueError):
        float_(lower=1, upper=2)('1.23€')

    assert int_(lower=1, upper=200, ignore_non_numeric=True)('1.23,0%') == '1'
    assert int_(lower=1, upper=200, ignore_non_numeric=True)('1,23.0%') == '123'
    assert int_(lower=1, upper=200, ignore_non_numeric=True)('1,§$%§%$2,$%&(/§&%(3.0%')
    assert float_(lower=1, upper=200, ignore_non_numeric=True)('1.23,4%') == '1.234'
    assert float_(lower=1, upper=200, ignore_non_numeric=True)('1,§$%§%$2,$%&(/§&%(3.4%') == '123.4'

    with pytest.raises(ValueError):
        float_()('1 23')

    assert float_()('1.23') == '1.23'
    with pytest.raises(ValueError):
        float_(upper=2)('2.23')
    with pytest.raises(ValueError):
        float_(lower=3)('2.23')


if __name__ == '__main__':
    test_parse_column_definition()
    test_string_formatting()
    test_numeric_formatting()
    print("Done.")
