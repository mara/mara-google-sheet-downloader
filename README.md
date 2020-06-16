# Mara Google Sheet Downloader

[![Build Status](https://travis-ci.org/mara/mara-google-sheet-downloader.svg?branch=master)](https://travis-ci.org/mara/mara-google-sheet-downloader)
[![PyPI - License](https://img.shields.io/pypi/l/mara-google-sheet-downloader.svg)](https://github.com/mara/mara-google-sheet-downloader/blob/master/LICENSE)
[![PyPI version](https://badge.fury.io/py/mara-google-sheet-downloader.svg)](https://badge.fury.io/py/mara-google-sheet-downloader)
[![Slack Status](https://img.shields.io/badge/slack-join_chat-white.svg?logo=slack&style=social)](https://communityinviter.com/apps/mara-users/public-invite)


This package contains a google sheet downloader to be used with the mara ETL framework:

- Download a Google sheet to a database table
- Cells can be validated and formatted during download

&nbsp;

## Installation

To use the library directly, use pip:

```
pip install mara-google-sheet-downloader
```

or

```
pip install git+https://github.com/mara/mara-google-sheet-downloader.git
```

&nbsp;

## Example

Here is a pipeline "gs_demo" which downloads to a table. This assumes you have a spread sheet under the
URL https://docs.google.com/spreadsheets/d/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/edit. This sheet must be shared with the
email address for which you configured the credentials (see below).

The spreadsheet contains a worksheet 'test' which contains the following colums:

|city | some_date | amount | already paid? | price | comments |
|---|---|---|---|---| --- |
|Berlin | 01.01.2020 | 3 | ja | 2.3 | added by JK on 2020-03-12 |

Note that it doesn't contain an id column at the start!

```python
from mara_pipelines.pipelines import Pipeline, Task
from mara_pipelines.commands.sql import ExecuteSQL
from mara_google_sheet_downloader.mara_integration import DownloadGoogleSpreadsheet

pipeline = Pipeline(
    id='gs_demo',
    description='A small pipeline that demonstrates the a google sheet download')

pipeline.add(Task(
    id='download_', description='Download a google sheet',
    commands=[
        ExecuteSQL(
            sql_statement=f"""
-- Creates the table where the google sheet data should end up in
DROP TABLE IF EXISTS public.gs_test;
CREATE TABLE public.gs_test (
id BIGINT PRIMARY KEY,
city TEXT,
some_date DATE,
amount INTEGER,
is_paid BOOLEAN,
price DOUBLE PRECISION,
comments TEXT
)
""",
            echo_queries=False,
        ),
        DownloadGoogleSpreadsheet(
            spreadsheet_key='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',  # from the URL
            worksheet_name='test',  # worksheet
            # Validators:
            # c: counter (additional column, will start at 1 and count each row),
            # s: string,
            # d(in_fmt=%d.%m.%Y): date in YYYY.mm.dd format,
            # i: integer,
            # b(true:ja,false=nein): boolean with ja/nein interpreted as True/False,
            # f: float,
            # s: string
            # any cell which does not confirm to this spec will fail the import!
            columns_definition='csd(in_fmt=%d.%m.%Y)ib(true:ja,false=nein)fs',
            target_table_name='public.gs_test', # table where the data should end up
            target_db_alias='dwh', # alias of the DB where the data should end up
            skip_rows=1), # how many rows at the top should be skipped
    ]),
)
```

## Config

The downloader needs OAuth2 credentials, either use a service account or a user account.
* For service accounts, see https://gspread.readthedocs.io/en/latest/oauth2.html. All required information is in the
  downloaded json file.
* For user account credentials, see https://developers.google.com/sheets/api/quickstart/python, Step 1.
  For getting the initial refresh token, you can use
  `flask mara_google_sheet_downloader.generate-user-refresh-token /path/to/downloaded/credential.json`

Credentials will need the scopes `'https://www.googleapis.com/auth/spreadsheets.readonly', 'https://www.googleapis.com/auth/drive.readonly'`.

Example with OAuth2 credentials for a user account:

```python
from mara_app.monkey_patch import patch
import mara_google_sheet_downloader.config
patch(mara_google_sheet_downloader.config.gs_user_account_client_id)(lambda:"....client_id...")
patch(mara_google_sheet_downloader.config.gs_user_account_client_secret)(lambda:"...client_secret...")
patch(mara_google_sheet_downloader.config.gs_user_account_refresh_token)(lambda:"...initial_refresh_token...")
```

## Setup access to sheets to be downloaded

All sheets which should be accessed by the downloader must be shared with the email address associated with these
credentials. This email address is:

* for user account credentials: the email address of the user who created the credentials.
* for service accounts: the email address of the service account itself (e.g. "*@*.iam.gserviceaccount.com").
  This email address is e.g. included in the json file you can download.

## CLI

This package contains a small cli app which downloads a google sheet and outputs it as csv.

You can use it stand alone, see `python -m mara_google_sheet_downloader --help ` for how to use it.
