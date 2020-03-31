import click


@click.command()
@click.argument('filename', required=True)
def generate_user_refresh_token(filename: str):
    """Helper to generate the necessary user credentials for using the mara Google Sheet Downloader

    You need the credentials.json file downloaded from https://developers.google.com/sheets/api/quickstart/python
    "step 1".
    """
    from google_auth_oauthlib.flow import InstalledAppFlow
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly', 'https://www.googleapis.com/auth/drive.readonly']

    flow = InstalledAppFlow.from_client_secrets_file(filename, SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n\nUser credentials:")
    print(f'client_id:     {creds.client_id}')
    print(f'client_secret: {creds.client_secret}')
    print(f'refresh_token: {creds.refresh_token}')


if __name__ == '__main__':
    generate_user_refresh_token()
