from tokens import token, PyOwm
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import requests, httplib2
from bs4 import BeautifulSoup, SoupStrainer
from pyowm import OWM
from pyowm.utils.config import get_default_config
from pyowm.commons.exceptions import NotFoundError
from models import *
categories = {"известные люди":"rpf", "мультфильмы":"cartoons", "книги":"books", "аниме и манга":"anime_and_manga", "игры":"games", "фильмы и сериалы":"movies_and_tv_series", "другое":"other","комиксы":"comics","мюзиклы":"musicals"}
vk_session = vk_api.VkApi(token=token)
session_api = vk_session.get_api()
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()


def weather(place):
    config_dict = get_default_config()
    config_dict['language'] = 'ru'
    owm = OWM(PyOwm)
    mgr = owm.weather_manager()
    try:
        observation = mgr.weather_at_place(place)
        w = observation.weather
        temp = w.temperature('celsius')["temp"]
        degree_sign = u'\N{DEGREE SIGN}'
        if temp > 0:
            return f"В городе {place.title()} сейчас {w.detailed_status} \n Температура: +{round(temp)}{degree_sign}С"
        else:
            return f"В городе {place.title()} сейчас {w.detailed_status} \n Температура: {round(temp)}{degree_sign}С"

    except NotFoundError:
        return f'Не найден город: {place.title()}'



def get_fanfiction(f, ca, v):
    fandom = f[:v]
    category = categories[f[v + 2:]]

    url = "https://ficbook.net/fanfiction/" + category + "/" + fandom.replace(" ", "_") + "?premium=0&filterDirection="+str(ca)+"&rating="
    fanfictions = []
    http = httplib2.Http()
    status, response = http.request(url)
    for link in BeautifulSoup(response, 'html.parser', parse_only=SoupStrainer('a')):
        if link.has_attr('href'):
            if "/readfic/" in link['href']:
                fanfictions.append("http://ficbook.net" + link['href'])
    fanfictions = fanfictions[:3]
    r = []
    for f in fanfictions:
        url = f
        status, response = http.request(url)
        for link in BeautifulSoup(response, 'html.parser', parse_only=SoupStrainer('h1')):
            soup = BeautifulSoup(str(link), 'html.parser')
            r.append(f + ' --> ' + soup.h1.text + '\n')
    result = " ".join(r)
    return result

def _clean_all_tag_from_str(string_line):
    result = ""
    not_skip = True
    for i in list(string_line):
        if not_skip:
            if i == "<":
                not_skip = False
            else:
                result += i
        else:
            if i == ">":
                not_skip = True
    return result


def add_user(user_vkId, user_name, user_lastname):
    with db:
        try:
            Users.get(Users.vkId == user_vkId)
        except DoesNotExist:
            Users(vkId=user_vkId, name=user_name, lastname=user_lastname).save()




for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
        text = event.text.lower()
        request = requests.get("https://vk.com/id" + str(event.user_id))
        bs = BeautifulSoup(request.text, "html.parser")
        user_name = _clean_all_tag_from_str(bs.findAll("title")[0])
        your_name = str(user_name.split()[0])
        your_lastname = str(user_name.split()[1])
        your_id = int(event.user_id)

        add_user(your_id, your_name, your_lastname)

        if text[:16] == 'погода в городе ':
            if event.from_user:
                vk.messages.send(user_id=event.user_id, message=weather(text[16:]), random_id=0)
            elif event.from_chat:
                vk.messages.send(chat_id=event.chat_id, message=weather(text[16:]), random_id=0)

        elif text[:11] == 'фанфики по ':

            if event.from_user:
                try:
                    i = Users.get(Users.vkId == event.user_id).id
                    cat = Preferences.get(Preferences.userId == i).genreId
                    vk.messages.send(user_id=event.user_id, message=get_fanfiction(text[11:].lower(), cat, text[11:].find(",")), random_id=0)
                except DoesNotExist:
                    vk.messages.send(user_id=event.user_id, message=get_fanfiction(text[11:].lower(), 0, text[11:].find(",")),
                                     random_id=0)
                    u_id = Users.get(Users.vkId == event.user_id).id
                    vk.messages.send(user_id=event.user_id, message="Какая направленность Вам больше нравится?(1 - джен\n2 - гет\n3 - слэш\n4 - фемслэш\n5 - статья\n6 - смешанная\n7 - другие виды отношений\n8 - любая)", random_id=0)
                    for e in longpoll.listen():
                        if e.type == VkEventType.MESSAGE_NEW and e.to_me and e.text:
                            Preferences(userId=u_id, genreId=e.text).save()


        elif text == "пока" or text == "бай":
            if event.from_user:
                vk.messages.send(user_id=event.user_id, message=f"Пока-пока, {your_name}!", random_id=0)
            elif event.from_chat:
                vk.messages.send(user_id=event.chat_id, message="Пока-пока, ребята!", random_id=0)

        elif text == 'привет' or text == 'хай':
            if event.from_user:
                vk.messages.send(user_id=event.user_id, message=f'Привет-привет, {your_name}!', random_id=0)
            elif event.from_chat:
                vk.messages.send(chat_id=event.chat_id, message='Привет-Привет, ребята!', random_id=0)

        else:
            if event.from_user:
                vk.messages.send(user_id=event.user_id, message='Я Вас не понимаю((...', random_id=0)
            elif event.from_chat:
                vk.messages.send(chat_id=event.chat_id, message='Я вас не понимаю((...', random_id=0)





