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

    def sendphotos(self, searched):
        photos = self.main.search_photos(searched['profile_id'])
        photostr = ''
        for photo in photos:
            photostr += f'photo{photo["owner_id"]}_{photo["id"]},'

        return photostr

    # Выявляем нехватку данных, соотносим через служебную nn, проверяем и исправляем в случае неверного ввода
    def killgaps(self, nn):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if nn == 0:
                    # Проверка на наличие цифр
                    contains_digit = False
                    for i in event.text:
                        if i.isdigit():
                            contains_digit = True
                            break
                    if contains_digit:
                        self.sendmsg(event.user_id, 'Имя и фамилия не должны содержать цифры, введите еще раз:')
                    else:
                        return event.text

                if nn == 1:
                    if event.text == "1" or event.text == "2":
                        return int(event.text)
                    else:
                        self.sendmsg(event.user_id, 'Неверно ввели пол. Введите 1 или 2 (1-М, 2-Ж):')

                if nn == 2:
                    # Проверяем наличие цифр в назввании города:
                    contains_digit = False
                    for i in event.text:
                        if i.isdigit():
                            contains_digit = True
                            break
                    if contains_digit:
                        self.sendmsg(event.user_id, 'Название города содержит цифры. Введите название города еще раз:')
                    else:
                        return event.text

                if nn == 3:
                    pattern = r'^\d{2}\.\d{2}\.\d{4}$'
                    if not re.match(pattern, event.text):
                        self.sendmsg(event.user_id, 'Дата рождения должна быть в формате дд.мм.гггг, введите еще раз:')
                    else:
                        return self._bdatereform(event.text)

    def gaplooking(self, event):
        if self.prm['Name'] is None:
            self.sendmsg(event.user_id, 'Ваше имя и фамилия? Введите пожалуйста.')
            return self.killgaps(0)

        if self.prm['Sex'] is None:
            self.sendmsg(event.user_id, 'Укажите Ваш пол (1-м, 2-ж):')
            return self.killgaps(1)

        elif self.prm['City'] is None:
            self.sendmsg(event.user_id, 'Из какого Вы города? Напиште название:')
            return self.killgaps(2)

        elif self.prm['Year'] is None:
            self.sendmsg(event.user_id, 'Укажите Вашу дату рождения (дд.мм.гггг):')
            return self.killgaps(3)

    # Проверяем профиль на наличии его в БД, фиксация его в БД и передача пользователю, либо составление нового листа профилей
    def findprofile(self, searchlists, event):
        while True:
            if searchlists:
                searched = searchlists.pop()
                if not check_user(engine, event.user_id, searched['profile_id']):
                    add_user(engine, event.user_id, searched['profile_id'])
                    yield searched
            else:
                searchlists = self.main.search_list(
                    self.prm, self.offset)

# Обработка событий / получение сообщений
    def cmd_events(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'привет':
                    # Получение данных о пользователе:
                    self.prm = self.main.get_user_info(event.user_id)
                    self.sendmsg(
                        event.user_id, f'Привет друг, {self.prm["Name"]}')

                    # Обработка недостающих данных о пользователе:
                    self.keys = self.prm.keys()
                    for i in self.keys:
                        if self.prm[i] is None:
                            self.prm[i] = self.gaplooking(event)

                    self.sendmsg(event.user_id, 'Вы успешно зарегистрировались!')

                elif event.text.lower() == 'поиск':
                    # поиск анкет:
                    self.sendmsg(
                        event.user_id, 'Начинаем поиск...')

                    msg = next(iter(self.findprofile(self.searchlists, event)))
                    if msg:

                        photo_string = self.sendphotos(msg)
                        self.offset += 10

                        self.sendmsg(
                            event.user_id,
                            f'имя: {msg["name"]} ссылка: vk.com/id{msg["profile_id"]}',
                            attachment=photo_string
                        )

                elif event.text.lower() == 'пока':
                    self.sendmsg(
                        event.user_id, 'Всего Вам наилучшего!')
                else:
                    self.sendmsg(
                        event.user_id, 'Не знаю такой директивы!')


if __name__ == '__main__':
    bot_interface = BotInterface(community_token, access_token)
    bot_interface.cmd_events()

