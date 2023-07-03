# Импорт модулей и переменных
from config import access_token
from datetime import datetime
import vk_api
from vk_api.exceptions import ApiError


# Получение пользовательских данных
class Main:
    def __init__(self, access_token):
        self.vkapi = vk_api.VkApi(token=access_token)

    def get_user_info(self, user_id):

        try:
            info, = self.vkapi.method('users.get',
                                      {'user_id': user_id,
                                       'fields': 'city,bdate,sex,relation'}
                                      )
        except ApiError as err:
            info = {}
            print('Выявлена ошибка!')
            print(f'Error = {err}')

        output = {'Name': (info['first_name'] + ' ' + info['last_name']) if
                  'first_name' in info and 'last_name' in info else None,
                  'Sex': info.get('sex'),
                  'City': info.get('city')['title'] if info.get('city') is not None else None,
                  'Year': datetime.now().year - int(info.get('bdate').split('.')[2])
                  if info.get('bdate') is not None else None
                  }
        return output

# Поиск пар по параметрам соответствущим пользователю
    def search_list(self, userinfo, offset):
        try:
            pairs = self.vkapi.method('users.search',
                                      {
                                          'count': 10,
                                          'offset': offset,
                                          'hometown': userinfo['City'],
                                          'sex': 1 if userinfo['Sex'] == 2 else 2,
                                          'has_photo': True,
                                          'age_from': userinfo['Year'] - 3,
                                          'age_to': userinfo['Year'] + 3,
                                      }
                                      )
        except ApiError as err:
            pairs = []
            print('Выявлена ошибка!')
            print(f'Error = {err}')

        output = [{'name': item['first_name'] + ' ' + item['last_name'],
                   'profile_id': item['id']
                   } for item in pairs['items'] if item['is_closed'] is False
                  ]

        return output

# Поиск фотографий у найденных пар
    def search_photos(self, profile_id):
        try:
            photos = self.vkapi.method('photos.get',
                                       {'owner_id': profile_id,
                                        'album_id': 'profile',
                                        'extended': 1
                                        }
                                       )
        except ApiError as err:
            photos = {}
            print('Выявлена ошибка!')
            print(f'Error = {err}')

        output = [{'owner_id': item['owner_id'],
                   'id': item['id'],
                   'likes': item['likes']['count'],
                   'comments': item['comments']['count']
                   } for item in photos['items']
                  ]
# сортировка фото по лайкам и комментариям
        output.sort(key=lambda x: (x['likes'], x['comments']), reverse=True)

        return output[:3]


if __name__ == '__main__':
    user_id = 755150
    prm = Main(access_token)
    userinfo = prm.get_user_info(user_id)
    searchlists = prm.search_list(userinfo, 10)
    searched = (searchlists.pop())['profile_id']
    photos = prm.search_photos(searched)
