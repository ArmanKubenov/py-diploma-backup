import time
import requests
from pprint import pprint
import os
import json
import configparser
from tqdm import tqdm
from xmlrpc.client import boolean
import datetime

config = configparser.ConfigParser()
config.read("settings.ini")
TOKEN_VK = config['vk_api']['access_token']
TOKEN_YADISK = input('Введите токен с Яндекс Полигона:')

def save_log_file(save_photos: list):
    data = []
    for photo in tqdm(save_photos):
        file_name = f"{photo['file_name']}.jpg"
        size = f"{photo['size']}"
        download_log = {'file_name': file_name, 'size': size}
        data.append(download_log)
    with open('log_list.json', 'w') as file_log:
        json.dump(data, file_log, indent=2)
        print('Файл log_list.json с информацией о фото записан!')


class VkSaver:
    def __init__(self, user_id, token: str):
        self.user_id = user_id
        self.api_version = config['vk_api']['api_version']
        self.get_photos_url = config['vk_api']['get_photos_url']
        self.download_file_path = config['files_path']['download_file_path']
            
    def get_photos(self, user_id):
        user_id = int(input('Введите Id пользователя:'))
        params = {'owner_id': user_id,
                    'album_id': 'profile',
                    'extended': 1,
                    'rev': 1,
                    'photo_sizes': 1,
                    'count': 5,
                    'access_token': TOKEN_VK,
                    'v':'5.131'}
        response = requests.get(self.get_photos_url, params=params)
        print(response.status_code)
        profile_list = response.json()
        photos = []
        for file in tqdm(profile_list['response']['items']):
            photos.append({'file_name': file['likes']['count'], 'size': file['sizes'][-1]['type'], 'url':file['sizes'][-1]['url']})
        return photos
              
class YaUploader:
    def __init__(self, token: str):
        self.get_upload_url_api = config['yadisk_api']['get_upload_url_api']
        self.mkdir_url = config['yadisk_api']['mkdir_url']
        self.download_file_path = config['files_path']['download_file_path']
          
    def create_folder(self):
        headers = {'Content-Type': 'application/json',
                    'Authorization': TOKEN_YADISK}
        params = {'path': f'{folder_name}',
                    'overwrite': 'false'}
        create_dir = requests.api.put(self.mkdir_url, headers=headers, params=params)
        answer = create_dir.status_code
        if answer == 201:
            print(f"Каталог {folder_name} создан")
        else:
            result = result.json()
            print(f"Ответ {answer}: {create_dir['message']}")
                
    def upload_photo(self, ext_url_file: str, photo: str, folder_name, overwrite=True) -> boolean:
        headers = {'Content-Type': 'application/json',
                    'Authorization': TOKEN_YADISK}
        params = {'path': f'{folder_name}/{photo}', "url": ext_url_file,
                    'overwrite': 'true'}
        response = requests.post(self.get_upload_url_api, headers=headers, params=params)
        print(response.status_code)
        response.raise_for_status()
        if response.status_code == 202:
            print(f"Загрузка выполнена {file_name}")
            return True
        else:
            print(f"Ошибка при загрузке файла! = {response.status_code}")
            return False

if __name__ == '__main__':
    downloader = VkSaver(51620911, TOKEN_VK)
    save_photos = downloader.get_photos(downloader.user_id)
    if len(save_photos) > 0:
        count_photos = int(input(f'В профиле VK найдено {len(save_photos)} фотографий. Сколько фотографий вы хотите загрузить: '))
        if count_photos > len(save_photos) or count_photos < 1:
            count_photos = len(save_photos)
    else:
        print("В профиле VK фотографии не найдены")
    uploader = YaUploader(TOKEN_YADISK)
    folder_name = str(input('Введите имя папки на Яндекс диске, в которую необходимо сохранить фото: '))
    uploader.create_folder()
    i = 0
    for photo in tqdm(save_photos):
        file_name = f"{photo['file_name']}.jpg"
        size = f"{photo['size']}"
        download = uploader.upload_photo(photo['url'], file_name, folder_name)
        if download:
            save_photos[i]['status'] = 'Загружен'
        else:
            save_photos[i]['status'] = 'Ошибка'
        i += 1
        if count_photos == i: 
            break
    
    save_log_file(save_photos)