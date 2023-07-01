# импорты
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
import re
from datetime import datetime
from config import community_token, access_token
from main import Main

from dbface import check_user, add_user, engine
# отправка сообщений


class BotInterface:
    def __init__(self, community_token, access_token):
        self.vkapi = vk_api.VkApi(token=community_token)
        self.longpoll = VkLongPoll(self.vkapi)
        self.main = Main(access_token)
        self.searchlists = []
        self.keys = []
        self.prm = {}
        self.offset = 0

    def sendmsg(self, user_id, message, attachment=None):
        self.vkapi.method('messages.send',
                       {'user_id': user_id,
                        'message': message,
                        'attachment': attachment,
                        'random_id': get_random_id()}
                       )

    def _bdatereform(self, bdate):
        user_year = bdate.split('.')[2]
        now_year = datetime.now().year
        years = now_year - int(user_year)
        return years

    def photos_for_send(self, searched):
        photos = self.main.search_photos(searched['profile_id'])
        photo_string = ''
        for photo in photos:
            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'

        return photo_string

    # k - отличительный параметр, что именно None
    def new_message(self, k):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if k == 0:
                    # Проверка на числа
                    contains_digit = False
                    for i in event.text:
                        if i.isdigit():
                            contains_digit = True
                            break  # Прерываем цикл, если найдена цифра
                    if contains_digit:
                        self.sendmsg(event.user_id, 'Пожалуйста, введите имя и фамилию без чисел:')
                    else:
                        return event.text

                if k == 1:
                    if event.text == "1" or event.text == "2":
                        return int(event.text)
                    else:
                        self.sendmsg(event.user_id, 'Неверный формат ввода пола. Введите 1 или 2:')

                if k == 2:
                    # Проверка на числа
                    contains_digit = False
                    for i in event.text:
                        if i.isdigit():
                            contains_digit = True
                            break  # Прерываем цикл, если найдена цифра
                    if contains_digit:
                        self.sendmsg(event.user_id, 'Неверно указан город. Введите название города без чисел:')
                    else:
                        return event.text

                if k == 3:
                    pattern = r'^\d{2}\.\d{2}\.\d{4}$'
                    if not re.match(pattern, event.text):
                        self.sendmsg(event.user_id, 'Пожалуйста, введите вашу дату '
                                                         'рождения в формате (дд.мм.гггг):')
                    else:
                        return self._bdate_toyear(event.text)

    def send_mes_exc(self, event):
        if self.prm['Name'] is None:
            self.sendmsg(event.user_id, 'Введите ваше имя и фамилию:')
            return self.new_message(0)

        if self.prm['Sex'] is None:
            self.sendmsg(event.user_id, 'Введите свой пол (1-м, 2-ж):')
            return self.new_message(1)

        elif self.prm['City'] is None:
            self.sendmsg(event.user_id, 'Введите город:')
            return self.new_message(2)

        elif self.prm['Year'] is None:
            self.sendmsg(event.user_id, 'Введите дату рождения (дд.мм.гггг):')
            return self.new_message(3)

    def get_profile(self, searchlists, event):
        while True:
            if searchlists:
                searched = searchlists.pop()

                'проверка анкеты в бд в соотвествии с event.user_id'
                if not check_user(engine, event.user_id, searched['profile_id']):
                    'добавить анкету в бд в соотвествии с event.user_id'
                    add_user(engine, event.user_id, searched['profile_id'])

                    yield searched

            else:
                searchlists = self.main.search_list(
                    self.prm, self.offset)

# обработка событий / получение сообщений
    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'привет':
                    '''Логика для получения данных о пользователе'''
                    self.prm = self.main.get_user_info(event.user_id)
                    self.sendmsg(
                        event.user_id, f'Привет друг, {self.prm["Name"]}')

                    # обработка данных, которые не получили
                    self.keys = self.prm.keys()
                    for i in self.keys:
                        if self.prm[i] is None:
                            self.prm[i] = self.send_mes_exc(event)

                    self.sendmsg(event.user_id, 'Вы успешно зарегистрировались!')

                elif event.text.lower() == 'поиск':
                    '''Логика для поиска анкет'''
                    self.sendmsg(
                        event.user_id, 'Начинаем поиск...')

                    msg = next(iter(self.get_profile(self.searchlists, event)))
                    if msg:

                        photo_string = self.photos_for_send(msg)
                        self.offset += 10

                        self.sendmsg(
                            event.user_id,
                            f'имя: {msg["name"]} ссылка: vk.com/id{msg["profile_id"]}',
                            attachment=photo_string
                        )

                elif event.text.lower() == 'пока':
                    self.sendmsg(
                        event.user_id, 'До новых встреч')
                else:
                    self.sendmsg(
                        event.user_id, 'Неизвестная команда')


if __name__ == '__main__':
    bot_interface = BotInterface(community_token, access_token)
    bot_interface.event_handler()
