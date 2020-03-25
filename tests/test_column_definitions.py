from mara_google_sheet_downloader.columns_definition import parse_column_definition, str_, int_, float_


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
    assert float_(lower=1, upper=200)('123,4') == '123.4'
    assert float_(lower=1, upper=200)('1.23,4') == '123.4'
    assert float_(lower=1, upper=200)('1.23.4') == '123.4'

    try:
        float_(lower=1, upper=2)('1.23€')
        assert False
    except ValueError:
        pass

    assert int_(lower=1, upper=200, ignore_non_numeric=True)('1.23,0%') == '123'
    assert int_(lower=1, upper=200, ignore_non_numeric=True)('1.§$%§%$2,$%&(/§&%(3.0%') == '123'
    assert float_(lower=1, upper=200, ignore_non_numeric=True)('1.23,4%') == '123.4'
    assert float_(lower=1, upper=200, ignore_non_numeric=True)('1.§$%§%$2,$%&(/§&%(3.4%') == '123.4'

    try:
        float_()('1 23')
        assert False
    except ValueError:
        pass

    assert float_()('1.23') == '1.23'
    try:
        float_(upper=2)('2.23')
        assert False
    except ValueError:
        pass
    try:
        float_(lower=3)('2.23')
        assert False
    except ValueError:
        pass


if __name__ == '__main__':
    test_parse_column_definition()
    test_string_formatting()
    test_numeric_formatting()
    print("Done.")
