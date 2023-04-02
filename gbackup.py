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
        with open('token.json', 'w', encoding='utf-8') as token:
            token.write(creds.to_json())

    next_page_token = ""
    try:
        service = build(API_NAME, API_VERSION, credentials=creds)

        # Call the Drive v3 API
        results = get_google_files(service, next_page_token)
        print('Files:')
        print_google_page(service, results)
        next_page_token = results.get('nextPageToken', None)
        i=0
        while next_page_token and i < 3:
            print_google_page(service, results)
            next_page_token = results.get('nextPageToken', None)
            results = get_google_files(service, next_page_token)
            i=i+1
        return

    except HttpError as error:
        print(f'An error occurred: {error}')

def print_google_page(service, this_results):
    """Prints the files returned by results
    """
    items = this_results.get('files', [])
    if not items:
        print('No files found.')
        return
    for item in items:
        if 'parents' in item:
            folder_name = '/'
            for parent in item['parents']:
                folder = service.files().get(fileId=parent, fields="id, name, parents").execute()
                folder_name = folder_name + folder.get('name') + '/'
        else:
            folder_name = '/'
        if 'size' in item:
            print(f"{item['name']:<60}\t{item['id']}\t{item['mimeType']:<30}\t{folder_name:<20}")
        else:
            #is a directory?
            print(f"{item['name']:<60}\t{item['id']}\t{item['mimeType']:<30}\t{folder_name:<20}")
    return

def get_google_files(this_service, this_next_page_token):
    """Gets the files using NextPageToken
    """
    results = this_service.files().list(
        pageSize=1000,
        corpora='user',
        pageToken=this_next_page_token,
        q="'me' in owners",
        fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, parents, ownedByMe)"
        ).execute()
    return results

if __name__ == '__main__':
    main()

# vim: tabstop=4 shiftwidth=4 expandtab
