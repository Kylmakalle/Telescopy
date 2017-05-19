# -*- coding: utf-8 -*-
import os
import telebot
from botan import track

token = os.environ['TELEGRAM_TOKEN']
botan_token = os.environ['APPMETRICA_TOKEN']
bot = telebot.TeleBot(token)


def lang(message):
    if message.from_user.language_code is not None:
        if 'ru' in message.from_user.language_code:
            return 'ru'
        else:
            return 'en'
    else:
        return 'en'


strings = {'ru': {'start': 'Приветствую, {}!\nЯ Telescopy и я умею преобразовывать Видео и Гифки в круглые'
                           ' <i>Видеосообщения</i>, просто отправь мне медиафайл.\n\n'
                           'Не забудь <a href="{}">обновить</a> приложение, или ты не сможешь просматривать'
                           ' <i>Видеосообщения!</i>',
                  'error': 'Ой, что-то пошло не так, попоробуй другой файл',
                  'content_error': 'Я поддерживаю только Видео или Гифики!',
                  'text_handler': 'Отправь мне Видео или Гифку',
                  'video_note_handler': 'Это и так <i>Видеосообщение!</i>'},
           'en': {'start': 'Greetings, {}!\nI am Telescopy and i can convert your Video or GIF to a round'
                           ' <i>Video Message</i>, just send me your media.\n\n'
                           'Remember to <a href="{}">update</a> an app first, or you will not be able'
                           ' to see <i>Video Messages</i>!',
                  'error': 'Ooops, something went wrong, try another file',
                  'content_error': 'I support only Videos and GIFs!',
                  'text_handler': 'Send me Video or GIF',
                  'video_note_handler': "It's already a <i>Video message!</i>"}}


@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, strings[lang(message)]['start'].format(
        message.from_user.first_name, 'https://telegram.org/update'),
                     parse_mode='HTML', disable_web_page_preview=True)
    track(botan_token, message.from_user.id, message, '/start')
    track(botan_token, message.from_user.id, message, lang(message))


@bot.message_handler(content_types=['video', 'document'])
def converting(message):
    if message.content_type is 'video':
        try:
            videonote = bot.download_file(bot.get_file(message.video.file_id).file_path)
            bot.send_chat_action(message.chat.id, 'record_video_note')
            bot.send_video_note(message.chat.id, videonote)
            track(botan_token, message.from_user.id, message, 'Convert')
        except:
            bot.send_message(message.chat.id, strings[lang(message)]['error'])
            track(botan_token, message.from_user.id, message, 'Error')

    elif message.content_type is 'document' and \
            (message.document.mime_type == 'image/gif' or message.document.mime_type == 'video/mp4'):
        try:
            videonote = bot.download_file(bot.get_file(message.document.file_id).file_path)
            bot.send_chat_action(message.chat.id, 'record_video_note')
            bot.send_video_note(message.chat.id, videonote)
            track(botan_token, message.from_user.id, message, 'Convert')
        except:
            bot.send_message(message.chat.id, strings[lang(message)]['error'])
            track(botan_token, message.from_user.id, message, 'Error')
    else:
        bot.send_message(message.chat.id, strings[lang(message)]['content_error'])


@bot.message_handler(content_types=['text'])
def text_handler(message):
    if message.content_type is 'text' and message.text != '/start':
        bot.send_message(message.chat.id, strings[lang(message)]['text_handler'])


@bot.message_handler(content_types=['video_note'])
def video_note_handler(message):
    if message.video_note is not None:
        bot.send_message(message.chat.id, strings[lang(message)]['video_note_handler'], parse_mode='HTML')


bot.polling(none_stop=True)
