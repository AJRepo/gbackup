'''Python file to backup ajo's document
'''
from __future__ import print_function

import os.path
import io
import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

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
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w', encoding='utf-8') as token:
            token.write(creds.to_json())

    # If there are no (valid) credentials available, let the user log in.
    if not creds.valid:
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
        results = list_google_files(service, next_page_token)
        print('Files:')
        tree_google_pages(service, results)
        next_page_token = results.get('nextPageToken', None)
        i=0
        while next_page_token and i < 3:
            tree_google_pages(service, results)
            next_page_token = results.get('nextPageToken', None)
            results = list_google_files(service, next_page_token)
            i=i+1
        return

    except HttpError as error:
        print(f'An error occurred: {error}')

def get_grequest(service, this_item):
    """ get request based on mimeType
    """
    request = None

    if this_item['mimeType'] == 'application/vnd.google-apps.document':
        # print('Google Doc')
        request = service.files().export_media(
            fileId=this_item['id'],
            mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    elif this_item['mimeType'] == 'application/vnd.google-apps.spreadsheet':
        # print('Google Sheet')
        request = service.files().export_media(
            fileId=this_item['id'],
            mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    elif this_item['mimeType'] == 'application/vnd.google-apps.presentation':
        # print('Google Slide')
        request = service.files().export_media(
            fileId=this_item['id'],
            mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation')
    elif this_item['mimeType'] == 'application/vnd.google-apps.form':
        return request
    elif this_item['mimeType'] == 'application/vnd.google-apps.map':
        return request
    elif this_item['mimeType'] == 'application/vnd.google-apps.site':
        return request
    else:
        request = service.files().get_media(fileId=this_item['id'])
    return request

def download_gfile(this_item, request, path):
    """Downloads a file
    Args:
        this_item: item list of the file to download
        request: see get_grequest to get the request var
        extension: see get_grequest for the extension mimeType
    """
    file_name = this_item['name']
    extension = get_extension(this_item['mimeType'])
    debug = 0
    if request is None:
        return 0


    try:
        file_handle = io.BytesIO()
        downloader = MediaIoBaseDownload(file_handle, request)

        # To get download progress for file
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            if debug == 1:
                print(f'Download {int(status.progress() * 100)}.')

        file_handle.seek(0)
        #with open(os.path.join(path, file_name), 'wb') as file:
        with open(os.path.join(path, file_name + extension), 'wb') as file:
            file.write(file_handle.read())
            file.close()
        print(f'Downloaded {file_name}')

    except HttpError as error:
        print(f'An error occurred: {error}')
        file = None

    return 0

def tree_google_pages(service, this_results):
    """Prints the files returned by results
    """
    items = this_results.get('files', [])
    root_dir="./"
    if not items:
        print('No files found.')
        return
    for item in items:
        if 'parents' in item:
            folder_name = '/'
            #Google now only allows one parent per item
            parents = item['parents']
            while parents is not None:
                parent = parents[0]
                folder = service.files().get(fileId=parent,
                                  fields="id, name, parents").execute()
                folder_name = '/' + folder.get('name') + folder_name
                parents = folder.get('parents')
        else:
            folder_name = '/'
        if 'size' in item:
            create_folder(root_dir + folder_name)
            sync_gfile(service, item, root_dir + folder_name)
            print("FILE:")
        else:
            #is a directory?
            create_folder(root_dir + folder_name)
            print("DIRC:")
        print(f"{item['name']:<60}\t"
              #f"{item['id']}\t"
              f"{item['mimeType']:<30}\t"
              f"{item['modifiedTime']:<30}\t"
              f"{root_dir + folder_name:<20}")
    return

def gtime_to_unixtime(this_time):
    """Get gtime of file in unixtime format"""
    return datetime.datetime.timestamp(datetime.datetime.strptime(this_time,
            '%Y-%m-%dT%H:%M:%S.%f%z'))

def get_extension(mime_type):
    """Input: string mime_type
       return: string extension
    """
    extension = ''
    if mime_type == 'application/vnd.google-apps.document':
        # print('Google Doc')
        extension = '.docx'
    elif mime_type == 'application/vnd.google-apps.spreadsheet':
        # print('Google Sheet')
        extension = '.xlsx'
    elif mime_type == 'application/vnd.google-apps.presentation':
        # print('Google Slide')
        extension = '.pptx'

    return extension

def sync_gfile(this_service, this_item, this_path):
    """If the folder does not exist create it"""
    extension = get_extension(this_item['mimeType'])
    if not os.path.isfile(this_path + this_item['name'] + extension):
        print("to Download: not exist")
        request = get_grequest(this_service, this_item)
        download_gfile(this_item, request, this_path)
    else:
        real_file_mtime = os.path.getmtime(this_path + this_item['name'] + extension)
        if gtime_to_unixtime(this_item['modifiedTime']) > \
             real_file_mtime:
            print(f"to Download: {this_item['modifiedTime']} >"
                  f"{real_file_mtime}")
        else:
            print("to skip")

    return 0

def create_folder(this_path):
    """If the folder does not exist create it"""
    if not os.path.exists(this_path):
        os.makedirs(this_path)
        return 0

    return 1

def list_google_files(this_service, this_next_page_token):
    """Gets the files using NextPageToken
    """
    results = this_service.files().list(
        pageSize=2,
        corpora='user',
        pageToken=this_next_page_token,
        q="'me' in owners",
        fields="nextPageToken, files(id, name, mimeType,\
                size, modifiedTime, parents, ownedByMe, md5Checksum)"
        ).execute()
    return results

if __name__ == '__main__':
    main()

# vim: tabstop=4 shiftwidth=4 expandtab
