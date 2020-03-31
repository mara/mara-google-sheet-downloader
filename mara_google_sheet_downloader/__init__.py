def MARA_CONFIG_MODULES():
    from mara_google_sheet_downloader import config
    return [config]

def MARA_CLICK_COMMANDS():
    from mara_google_sheet_downloader.__main__ import gs_download_to_csv
    from mara_google_sheet_downloader.user_credential_helper import generate_user_refresh_token
    return [gs_download_to_csv, generate_user_refresh_token]
