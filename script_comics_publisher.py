import os
import random
import shutil
from pathlib import Path
from urllib.parse import urlparse, unquote

import requests
from environs import Env


def get_random_number_comics():
    api_url = 'https://xkcd.com/info.0.json'
    response = requests.get(api_url)
    response.raise_for_status()
    comics_id = random.randint(1, response.json()['num'])
    return comics_id


def extract_extension(url):
    url_path = urlparse(url).path
    return os.path.splitext(unquote(url_path, encoding='utf-8',
                                    errors='replace'))[1]


def download_image(url, path):
    response = requests.get(url)
    response.raise_for_status()
    with open(path, 'wb') as file:
        file.write(response.content)


def download_random_image(comics_id):
    comics_url = f'https://xkcd.com/{comics_id}/info.0.json'
    response = requests.get(comics_url)
    response.raise_for_status()
    decoded_response = response.json()
    extension = extract_extension(decoded_response['img'])
    message = decoded_response['alt']
    filepath = Path(os.getcwd(), 'image',
                    f'python_comics_{comics_id}{extension}')
    download_image(decoded_response['img'], filepath)
    return filepath, message


def get_upload_server_url(group_id, token, api_version):
    api_url = 'https://api.vk.com/method/photos.getWallUploadServer'
    params = {'group_id': group_id,
              'access_token': token,
              'v': api_version}
    response = requests.get(api_url, params=params)
    response.raise_for_status()
    wall_upload_server_info = response.json()
    return wall_upload_server_info['response']['upload_url']


def send_photo(url, filepath):
    with open(filepath, 'rb') as file:
        files = {
            'photo': file,
        }
        response = requests.post(url, files=files)
    response.raise_for_status()
    return response.json()

def save_photo(params_from_save, group_id, token, api_version):
    api_url = 'https://api.vk.com/method/photos.saveWallPhoto'
    params = {'group_id': group_id,
              'access_token': token,
              'photo': params_from_save['photo'],
              'server': params_from_save['server'],
              'hash': params_from_save['hash'],
              'v': api_version}
    response = requests.post(api_url, params=params)
    response.raise_for_status()
    return response.json()


def post_comics(params_upload_image, group_id, token, message, api_version):
    api_url = 'https://api.vk.com/method/wall.post'
    attachments = f'photo{params_upload_image["response"][0]["owner_id"]}_' \
                  f'{params_upload_image["response"][0]["id"]}'
    params = {'owner_id': f'-{group_id}',
              'access_token': token,
              'from_group': 1,
              'attachments': attachments,
              'message': message,
              'v': api_version}
    response = requests.post(api_url, params=params)
    response.raise_for_status()


def main():
    env = Env()
    env.read_env()
    token = env.str("VK_TOKEN")
    group_id = env.str("VK_GROUP_ID")
    api_version = 5.131
    Path(os.getcwd(), 'image').mkdir(parents=True, exist_ok=True)
    try:
        comics_id = get_random_number_comics()
        filepath, message = download_random_image(comics_id)
        upload_server_url = get_upload_server_url(group_id, token, api_version)
        params_from_save = send_photo(upload_server_url, filepath)
        params_upload_image = save_photo(params_from_save, group_id, token, api_version)
        post_comics(params_upload_image, group_id, token, message, api_version)
    finally:
        shutil.rmtree(Path(os.getcwd(), 'image'))


if __name__ == '__main__':
    main()
