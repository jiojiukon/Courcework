from distutils.log import error
from gc import freeze
import requests as r
from pprint import pprint
import time
from progress.bar import ChargingBar

class VK:
    def __init__(self, token, id, version='5.131'):
        self.token = token
        self.id = id
        self.version = version
        self.url = 'https://api.vk.com/method/'
        self.params = {'access_token': self.token, 'v': self.version, 'user_ids': self.id}

    def user_info(self): #информация о владельце id
        url = self.url + 'users.get'  
        response = r.get(url, params = self.params)
        return response.json()

    def __get_id(self): #получает id страницы(для того, если в переменную id поступает буквенная замена id пользователя)
        for i in self.user_info()['response']:
            return i['id']

    def get_name(self): # получает имя и фамилию владельца id, на основе этого создается папка на яндекс диске
        for i in self.user_info()['response']:
            first_name = i['first_name']
            last_name = i['last_name']
            return f'{first_name} {last_name}'

    def get_albums_info(self, prnt=False, n=0): # возвращает словарь {'Название' : id} с доступными альбомами пользователя
        url = self.url + 'photos.getAlbums'
        params = {'user_ids': self.__get_id(), 'owner_id': self.__get_id()}
        response = r.get(url,params={**self.params, **params})
        albums = response.json()
        albums_id= {}
        if 'response' in albums.keys():
            albums = albums['response']
            for album in albums['items']:
                n += 1
                id, title, description = album['id'], album['title'], album['description']
                albums_id[title] = id
                if prnt:
                    print(f'{n}. id альболма {id}, Название {title}. Описание:{description}\n')
        else:
            print(f'что-то пошло не так:\n{albums}')
        return albums_id 

    def get_photo(self, album_id): #'wall' — фотографии со стены, 'profile' — фотографии профиля, 'saved' — сохраненные фотографии
        url = self.url + 'photos.get'
        params = {'owner_id': self.__get_id(), 'extended': '1', 'album_id':album_id,}
        u = r.get(url, params = {**self.params, **params})
        response = u.json()
        return response


    def big_size_photo(self, photos_list): # возвращает словарь {количество лайков: url} на все фото, в альбоме. url на самый большой из возможных размеров фото
        max_size_photo = {}
        n = 0
        if 'response' in photos_list.keys():
            items = photos_list['response']['items']
            for photo_info in items:
                amount_of_likes = str(photo_info['likes']['count'])
                sizes = []
                for s in photo_info['sizes']:
                    sizes.append(s['height'])
                for a in photo_info['sizes']:
                    if a['height'] == max(sizes):
                        if amount_of_likes in max_size_photo.keys():
                            amount_of_likes = '0'+ amount_of_likes
                        max_size_photo[amount_of_likes] = a['url']
        else:
            print(f'что-то пошло не так:\n {photos_list}')
        return max_size_photo



class YaUploader:
    def __init__(self,token:str):
        self.token = token
        self.url = 'https://cloud-api.yandex.net/v1/disk/'

    def __get_headers(self):
        return {'Content-Type': 'application/json',
            'Authorization': f'OAuth {self.token}'}
    
    def create_folder(self,folder_name): # создает папку в яндекс диске
        url = self.url +'resources'
        params = {'path': f'{folder_name}'}
        new_folder = r.put(url, headers=self.__get_headers(), params=params)
        return print(f'the folder {folder_name} is created')

    def __upload(self,vk:VK, ph_name, photo_url): # загружает фото
        url, path = self.url + "resources/upload", f'{vk.get_name()}/{ph_name}'
        params = {'path': path, 'url': f'{photo_url}'}
        upload = r.post(url=url, headers=self.__get_headers(), params=params)
        time.sleep(0.33)
        return upload.status_code

    def create_json(self, name, format='.jpg'):
        with open('Photo_list.json', 'a', encoding='utf-8') as j:
            j.write(f'{name}{format}\n')

    def forom_vk_to_yandex(self, photos, photo_count = None): #загрузка количества {photo_count} фотографий 
        if photo_count == None:
            photo_count = len(photos.items())
        bar = ChargingBar('uploading progress', max = photo_count)
        n = 0
        for photo_name, photo_url in photos.items():
            n +=1
            bar.next()
            upld = self.__upload(vk, photo_name, photo_url)
            if n == photo_count:
                self.create_json(str(photo_name)) 
                return print(f'\nPhotos are uploaded')
            if upld == 202:   
                self.create_json(str(photo_name))                 
                continue
            else:
                return print(f'  error {upld}')


if __name__ == '__main__':
    vk_token = ''
    id = '41888006'
    vk: VK =VK(vk_token, id)
    vk_photos = vk.get_photo('wall') #'wall', 'saved', 'profile', or album_id
    bigiest_photo_vk = vk.big_size_photo(vk_photos)
    ya_token = ''
    yandex = YaUploader(ya_token)
    yandex.create_folder(vk.get_name())
    yandex.forom_vk_to_yandex(bigiest_photo_vk,3)
