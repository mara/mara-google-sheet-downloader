"""Google Sheet Download to to CSV on stdout

The csv is formatted as csv.excel dialect suitable for e.g. CSV loads into DBs.

No header is written.

Mainly to be used with mara to import a Google Sheet to a database table.
"""

import click
import sys
import random

import time
import gspread

from mara_google_sheet_downloader import config as c
from .columns_definition import write_rows_as_csv_to_stream


@click.command()
@click.option('--spreadsheet-key', help='Spreadsheet Key (from URL).',
              required=True)
@click.option('--worksheet-name', help='Worksheet Name.',
              required=True)
@click.option('--columns-definition', help='Column Definition.',
              required=True)
@click.option('--skip-rows', help='How many rows at the top should be skipped',
              required=True,
              default=1,
              show_default=True)
@click.option('--service-account-private-key-id', help='Service Account private_key_id',
              required=False)
@click.option('--service-account-private-key', help='Service Account private_key',
              required=False)
@click.option('--service-account-client-email', help='Service Account client_email',
              required=False)
@click.option('--service-account-client-id', help='Service Account client_id',
              required=False)
@click.option('--user-account-client-id', help='User Account client_id',
              required=False)
@click.option('--user-account-client-secret', help='User Account client_secret',
              required=False)
@click.option('--user-account-refresh-token', help='User Account refresh_token',
              required=False)
@click.option('--delimiter-char', help='A character that delimits the output fields.',
              default='\t',
              show_default="\\t",
              required=False)
@click.option('--fail-on-no-data/--no-fail-on-no-data',
              help='Toggle to fail if no data is received.',
              default=True,
              required=False)
def gs_download_to_csv(spreadsheet_key: str, worksheet_name: str, columns_definition: str,
                       skip_rows: int,
                       delimiter_char: str = '\t',
                       service_account_private_key_id: str = None,
                       service_account_private_key: str = None,
                       service_account_client_email: str = None,
                       service_account_client_id: str = None,
                       user_account_client_id: str = None,
                       user_account_client_secret: str = None,
                       user_account_refresh_token: str = None,
                       fail_on_no_data: bool = True
                       ):
    """Download a google sheet as CSV to stdout

    Needs google credentials, either from a service account or from a user account.

    The csv is formatted as csv.excel dialect suitable for e.g. CSV loads into DBs. No header is written.
    """
    if not worksheet_name:
        raise RuntimeError("Need a worksheet_name")
    if not spreadsheet_key:
        raise RuntimeError("Need a spreadsheet_key")
    if not columns_definition:
        raise RuntimeError("Need a columns_definition")

    # TODO: make sure we only get a single credential config overall and warn/abort if we have more than one
    #       (warn: no print to stdout allowed!)

    # add a fallback to the config if no value are given
    # config is only set if this command is invoked via flask with a MaraApp
    service_account_private_key_id = service_account_private_key_id or c.gs_service_account_private_key_id()
    service_account_private_key = service_account_private_key or c.gs_service_account_private_key()
    service_account_client_email = service_account_client_email or c.gs_service_account_client_email()
    service_account_client_id = service_account_client_id or c.gs_service_account_client_id()
    user_account_client_id = user_account_client_id or c.gs_user_account_client_id()
    user_account_client_secret = user_account_client_secret or c.gs_user_account_client_secret()
    user_account_refresh_token = user_account_refresh_token or c.gs_user_account_refresh_token()

    if user_account_client_id:
        credentials = _google_sheet_credentials_from_user_credentials(
            client_id=user_account_client_id,
            client_secret=user_account_client_secret,
            refresh_token=user_account_refresh_token,
        )
    elif service_account_client_id:
        credentials = _google_sheet_credentials_from_service_account_credentials(
            private_key_id=service_account_private_key_id,
            private_key=service_account_private_key,
            client_email=service_account_client_email,
            client_id=service_account_client_id,
        )
    else:
        raise RuntimeError("Need either credentials for a google user account or for a google service account")

    overall_tries = 0
    api_errors = 0
    while True:
        try:
            # Connect to google sheets
            client = gspread.authorize(credentials)
            spreadsheet = client.open_by_key(spreadsheet_key)
            worksheet = spreadsheet.worksheet(worksheet_name)
            rows = iter(worksheet.get_all_values())

            for _ in range(skip_rows):
                # just pop the rows without outputting them!
                try:
                    next(rows)
                except StopIteration:
                    raise ValueError(f"Expected {skip_rows} header rows, but not all were there.")
            break
        except gspread.exceptions.APIError as apie:
            # these happen when the API got too many requests with this credentials in 100 seconds
            # 10 times might be a bit much but this is better than failing just because you have a lot of
            # gs downloads or some local dev loads at the same time
            # if it has a NOT_FOUND in it it's something else...
            # apie.response is a response object...
            if apie.response.status_code in (404,):
                # 404: the spreadsheet doesn't exist
                print(f'Aborting: {apie!r}', file=sys.stderr, flush=True)
                raise apie
            if api_errors > 10:
                raise apie
            api_errors += 1
            print(f'Got API Error, but will retry again: {apie!r}', file=sys.stderr, flush=True)
            # google measures activity in a 100s window, so wait a bit more on average
            # add a bit of random to get multiple parallel downloads spread out a bit
            sleep_seconds = 80 + (80 * random.random())
        except Exception as e:
            # some API down or so -> wait a bit and try again
            if overall_tries > 3:
                raise e
            print(f'Got exception, but will retry again: {e!r}', file=sys.stderr, flush=True)
            overall_tries += 1
            sleep_seconds = 20 * (overall_tries + 1)
        time.sleep(sleep_seconds)
        continue

    stream = sys.stdout
    nrows = write_rows_as_csv_to_stream(rows,
                                        columns_definition=columns_definition,
                                        stream=stream,
                                        delimiter_char=delimiter_char)
    stream.flush()

    if fail_on_no_data and nrows == 0:
        raise ValueError("Received no data rows, failing")


SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly', 'https://www.googleapis.com/auth/drive.readonly']


# The next version of gspread will probably support google_auth_oauthlib instead of oauth2client but will
# still support the old credentials: https://github.com/burnash/gspread/pull/711
# but lets keep this functions private for now
def _google_sheet_credentials_from_service_account_credentials(
    private_key_id: str,
    private_key: str,
    client_email: str,
    client_id: str
):
    '''Returns the credentials for a service account

    The credentials have the scope set to ['https://spreadsheets.google.com/feeds']

    https://gspread.readthedocs.io/en/latest/oauth2.html

    '''
    import oauth2client
    from oauth2client.service_account import ServiceAccountCredentials
    from oauth2client import crypt

    # adapted from ServiceAccountCredentials._from_parsed_json_keyfile()
    service_account_email = client_email
    private_key_pkcs8_pem = private_key
    private_key_id = private_key_id
    client_id = client_id
    token_uri = oauth2client.GOOGLE_TOKEN_URI
    revoke_uri = oauth2client.GOOGLE_REVOKE_URI

    signer = crypt.Signer.from_string(private_key_pkcs8_pem)
    credentials = ServiceAccountCredentials(service_account_email, signer, scopes=SCOPES,
                                            private_key_id=private_key_id,
                                            client_id=client_id, token_uri=token_uri,
                                            revoke_uri=revoke_uri)
    credentials._private_key_pkcs8_pem = private_key_pkcs8_pem

    return credentials


def _google_sheet_credentials_from_user_credentials(
    client_id: str,
    client_secret: str,
    refresh_token: str
):
    '''Returns the credentials from user authenticated client_id, client_secret, refresh_token

    The credentials need to have the scope set to ['https://spreadsheets.google.com/feeds']

    See https://developers.google.com/sheets/api/quickstart/python for how to get such credentials including the
    initial refresh token
    '''
    # https://stackoverflow.com/a/42230541/1380673
    import oauth2client
    import oauth2client.client as client

    credentials = client.OAuth2Credentials(
        access_token=None,  # set access_token to None since we use a refresh token
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        token_expiry=None,
        token_uri=oauth2client.GOOGLE_TOKEN_URI,
        user_agent=None,
        revoke_uri=oauth2client.GOOGLE_REVOKE_URI,
        scopes=SCOPES)
    return credentials


if __name__ == '__main__':
    gs_download_to_csv(prog_name='mara_google_sheet_downloader')
