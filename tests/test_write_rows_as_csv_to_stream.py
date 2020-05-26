import pytest
import io
from mara_google_sheet_downloader.columns_definition import write_rows_as_csv_to_stream

def test_happy_case():
    rows = [['1','2','3'],['1.0','2,0','3.0']]
    stream = io.StringIO()
    nrows = write_rows_as_csv_to_stream(rows, columns_definition='fff', stream=stream)
    assert nrows == 2
    actual = stream.getvalue().replace('\r\n', '\n')
    assert actual == '1.0\t2.0\t3.0\n1.0\t20.0\t3.0\n'
