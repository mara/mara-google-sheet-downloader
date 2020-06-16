from mara_google_sheet_downloader import mara_integration as mi
import pytest


@pytest.fixture
def mock_mara_pipelines_config(monkeypatch):
    """Setups the mara_pipelines.config so that it's usable for us"""
    import mara_db.dbs
    import mara_db.config

    def mock_databases():
        return {'dwh': mara_db.dbs.PostgreSQLDB(host='localhost', database='mock_db')}

    monkeypatch.setattr(mara_db.config, "databases", mock_databases)


@pytest.fixture
def mock_mara_google_sheet_downloader_config(monkeypatch):
    """Setups the mara_google_sheet_downloader.config so that it's usable for us"""
    import mara_google_sheet_downloader.config
    prefix = 'gs_user_account_'
    for name in ['client_id', 'client_secret', 'refresh_token']:
        monkeypatch.setattr(mara_google_sheet_downloader.config, prefix + name, lambda x=name: "mock_" + x)


spreadsheet_key = 'xxx'
worksheet_name = 'yyy'
columns_definition = 'b(true=ja)'
target_table_name = 'public.target_table'
skip_rows = 3


def test_DownloadGoogleSpreadsheet_command_with_flask(mock_mara_pipelines_config):
    command = mi.DownloadGoogleSpreadsheet(spreadsheet_key=spreadsheet_key,
                                           worksheet_name=worksheet_name,
                                           columns_definition=columns_definition,
                                           target_table_name=target_table_name,
                                           skip_rows=skip_rows,
                                           use_flask_command=True
                                           )
    shell_command = command.shell_command()
    assert target_table_name in shell_command # more a test of mara_db
    assert f"--worksheet-name='{worksheet_name}'" in shell_command
    assert f"--columns-definition='{columns_definition}'" in shell_command
    assert f"--skip-rows={skip_rows}" in shell_command
    assert shell_command.startswith('flask')


def test_DownloadGoogleSpreadsheet_command_with_python(mock_mara_pipelines_config,
                                                       mock_mara_google_sheet_downloader_config):
    command = mi.DownloadGoogleSpreadsheet(spreadsheet_key=spreadsheet_key,
                                           worksheet_name=worksheet_name,
                                           columns_definition=columns_definition,
                                           target_table_name=target_table_name,
                                           skip_rows=skip_rows,
                                           use_flask_command=False
                                           )
    shell_command = command.shell_command()
    print(shell_command)
    assert target_table_name in shell_command # more a test of mara_db
    assert f"--worksheet-name='{worksheet_name}'" in shell_command
    assert f"--columns-definition='{columns_definition}'" in shell_command
    assert f"--user-account-client-id='mock_client_id'" in shell_command
    assert f"--user-account-client-secret='mock_client_secret'" in shell_command
    assert f"--user-account-refresh-token='mock_refresh_token'" in shell_command
    assert f"--skip-rows={skip_rows}" in shell_command
    assert 'python' in shell_command


def test_DownloadGoogleSpreadsheet_command_with_python_without_credentials(mock_mara_pipelines_config):
    command = mi.DownloadGoogleSpreadsheet(spreadsheet_key=spreadsheet_key,
                                           worksheet_name=worksheet_name,
                                           columns_definition=columns_definition,
                                           target_table_name=target_table_name,
                                           skip_rows=skip_rows,
                                           use_flask_command=False
                                           )
    with pytest.raises(RuntimeError, match='credentials'):
        # missing credentials
        command.shell_command()
