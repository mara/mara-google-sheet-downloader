import shlex
import sys
from mara_pipelines import pipelines
from mara_pipelines.logging import logger
import mara_db.shell

from .columns_definition import COLUMN_DEFINITION_TYPE
from mara_google_sheet_downloader import config as c

__all__ = ['DownloadGoogleSpreadsheet']


class DownloadGoogleSpreadsheet(pipelines.Command):
    def __init__(self,
                 spreadsheet_key: str,
                 worksheet_name: str,
                 columns_definition: COLUMN_DEFINITION_TYPE,
                 target_table_name: str,
                 target_db_alias: str = 'dwh',
                 skip_rows: int = 1,
                 use_flask_command: bool = False,
                 fail_on_no_data: bool = False
                 ) -> None:
        """
        Downloads a google spreadsheet to a table

        Args:
            spreadsheet_key: str, found in url https://docs.google.com/a/.../d/<spreadsheet_key>/
            worksheet_name: str, the name of the worksheet in the spreadsheet
            columns_definition: string or a list of cell definition objects which describes the columns in the
                                worksheet. Only columns in this list are loaded. If a value can't be validated or
                                formatted by the definition for that cell the import fails.
            target_table_name: str, the schema qualified table name on the db_alias where the data should be inserted.
                               The table needs to exist.
            target_db_alias: str='dwh', the mara db alias where this data should be inserted
            skip_rows: int=1 number of leading rows to skip
            use_flask_command: bool=False, if true uses the downloader via flask, which needs an import to the main
                               module in the app.py import path to make the command available (any print() in that path
                               will fail the download). If True, the credentials needed in the downloader itself are
                               directly taken from the config, not passed in via commandline arguments.
            fail_on_no_data: bool=True, if true fail on no data rows received

        """
        self.spreadsheet_key = spreadsheet_key
        self.worksheet_name = worksheet_name
        self.columns_definition = columns_definition
        self.target_table_name = target_table_name
        self.target_db_alias = target_db_alias
        self.skip_rows = skip_rows
        self.delimiter_char = '\t'
        self.use_flask_command = use_flask_command
        self.fail_on_no_data = fail_on_no_data

    def run(self) -> bool:
        logger.log(
            f'Loading google sheet {self.spreadsheet_key} into {self.target_db_alias}.{self.target_table_name}...')
        if not super().run():
            logger.log(f'Error while loading google sheet {self.spreadsheet_key}.')
            return False
        logger.log(f'Finished loading google sheet {self.spreadsheet_key}.')
        return True

    def shell_command(self):
        return (gs_downloader_shell_command(self.spreadsheet_key, self.worksheet_name, self.columns_definition,
                                            skip_rows=self.skip_rows, delimiter_char=self.delimiter_char,
                                            use_flask_command=self.use_flask_command,
                                            fail_on_no_data=self.fail_on_no_data)
                + f'{_shell_linebreak_escape}| '
                + mara_db.shell.copy_from_stdin_command(self.target_db_alias, target_table=self.target_table_name,
                                                        null_value_string='', csv_format=True,
                                                        delimiter_char=self.delimiter_char))

    def html_doc_items(self) -> [(str, str)]:
        from mara_page import _
        from html import escape
        return [
            ('spreadsheet key', _.pre[escape(self.spreadsheet_key)]),
            ('worksheet name', _.pre[escape(self.worksheet_name)]),
            ('columns definition', _.pre[escape(self.columns_definition)]),
            ('target table name', _.pre[escape(self.target_table_name)]),
            ('target db', _.pre[escape(self.target_db_alias)]),
            ('Number of rows to skip', _.pre[str(self.skip_rows)]),
            ('Invocation', _.pre[_invocation(self.use_flask_command)]),
            ('Fail on no data', _.pre[str(self.fail_on_no_data)]),
        ]


def _invocation(use_flask):
    # import mara_google_sheet_downloader
    import mara_google_sheet_downloader.__main__
    main_module = mara_google_sheet_downloader.__name__
    flask_command_name = mara_google_sheet_downloader.__main__.gs_download_to_csv.callback.__name__.replace('_', '-')
    python = sys.executable
    invocation = f'flask {main_module}.{flask_command_name}' if use_flask else f'{python} -m {main_module}'
    return invocation


_shell_linebreak_escape = ' \\\n'
_indentions = ' ' * 5  # similar to what copy_from_stdin_command() does after a linebreak within the command


def gs_downloader_shell_command(spreadsheet_key: str,
                                worksheet_name: str,
                                columns_definition: COLUMN_DEFINITION_TYPE,
                                skip_rows: int = 1,
                                delimiter_char: str = '\t',
                                use_flask_command: bool = True,
                                fail_on_no_data: bool = True,
                                ):
    """
    Downloads a google spreadsheet to a table

    Args:
        spreadsheet_key: str, found in url https://docs.google.com/a/.../d/<spreadsheet_key>/
        worksheet_name: str, the name of the worksheet in the spreadsheet
        columns_definition: string, cell definitions which describe the columns in the worksheet.
                            Only columns in this list are loaded. If a value can't be validated or
                            formatted by the definition for that cell, the import fails.
        skip_rows: int=1, number of leading rows to skip
        delimiter_char: str='\t', a character that delimits the output fields.
        use_flask_command: bool=False, if true uses the downloader via flask, which needs an import in the flask app path
                           to make the command available and this can potentially print something which would make
                           the import fail. If True, the credentials are directly taken from the config,
                           not passed in via commandline arguments.
        fail_on_no_data: bool=True, if true fail on no data rows received
    """
    command = []
    command.extend([
        _invocation(use_flask_command),
        _shell_linebreak_escape,
        _indentions,
        f" --spreadsheet-key='{spreadsheet_key}'",
        f" --worksheet-name='{worksheet_name}'",
        f" --columns-definition='{columns_definition}'",
        f' --skip-rows={skip_rows}',
        f" --delimiter-char='{delimiter_char}'",
        f' --fail-on-no-data' if fail_on_no_data else f' --no-fail-on-no-data'
    ])
    if not use_flask_command:
        if c.gs_service_account_client_id():
            command.extend([
                _shell_linebreak_escape,
                _indentions,
                f" --service-account-client-id='{c.gs_service_account_client_id()}'",
                f" --service-account-private-key-id='{c.gs_service_account_private_key_id()}'",
                f" --service-account-private-key='{c.gs_service_account_private_key()}'",
                f" --service-account-client-email='{c.gs_service_account_client_email()}'",
            ])
        elif c.gs_user_account_client_id():
            command.extend([
                _shell_linebreak_escape,
                _indentions,
                f" --user-account-client-id='{c.gs_user_account_client_id()}'",
                f" --user-account-client-secret='{c.gs_user_account_client_secret()}'",
                f" --user-account-refresh-token='{c.gs_user_account_refresh_token()}'",
            ])
        else:
            raise RuntimeError("Need either credentials for a google user account or for a google service account")

    return ''.join(command)
