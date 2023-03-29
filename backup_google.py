'''Python file to backup ajo's document
'''
from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

#from googleapiclient.http import MediaIoBaseDownload

CLIENT_SECRET_FILE = 'client_secret_file.json'
API_NAME = 'drive'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/drive']


def main():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    next_page_token = ""
    try:
        service = build(API_NAME, API_VERSION, credentials=creds)

        # Call the Drive v3 API
        results = get_google_files(service, next_page_token)
        items = results.get('files', [])
        next_page_token = results.get('nextPageToken', None)
        if next_page_token:
            print('NEXT-TOKEN:', next_page_token)

        if not items:
            print('No files found.')
            return
        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')

def get_google_files(this_service, this_next_page_token):
    """Gets the files using NextPageToken
    """
    results = this_service.files().list(
        pageSize=10,
        pageToken=this_next_page_token,
        fields="nextPageToken, files(id, name, modifiedTime)").execute()
    return results

if __name__ == '__main__':
    main()
