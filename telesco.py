# -*- coding: utf-8 -*-
import os
import telebot
import cloudconvert
import ujson
import requests
from botan import track

token = os.environ['TELEGRAM_TOKEN']
botan_token = os.environ['APPMETRICA_TOKEN']
cloud_convert_token = os.environ['CLOUD_CONVERT_TOKEN']
me = os.environ['CREATOR_ID']

bot = telebot.AsyncTeleBot(token)


def lang(message):
    if message.from_user.language_code is not None:
        if 'ru' in message.from_user.language_code:
            return 'ru'
        else:
            return 'en'
    else:
        return 'en'


strings = {'ru': {'start': 'Приветствую, {}!\nЯ Telescopy и я умею преобразовывать квадратные Видео в круглые'
                           ' <i>Видеосообщения</i>, просто отправь мне медиафайл.\n\n'
                           'Используй команду /help если у тебя есть вопросы.',
                  'error': 'Ой, что-то пошло не так, попоробуй другой файл',
                  'content_error': 'Я поддерживаю только квадратные Видео!',
                  'text_handler': 'Отправь мне квадратное Видео',
                  'video_note_handler': 'Это и так <i>Видеосообщение!</i>',
                  'size_handler': 'Файл слишком большой!\nМаксимальный размер файла *8 MB!*',
                  'converting': '<i>Конвертирую</i> <code>{0:.2f}%</code>',
                  'downloading': '<i>Скачиваю файл...</i>',
                  'uploading': '<i>Колдую...</i>',
                  'webm': 'WebM формат пока не поддерживается 😓',
                  'help': '<a href="http://telegra.ph/Telescopy-FAQ-Ru-05-21-3">FAQ</a>',
                  'not_square': 'Это видео не квадратное (соотношение сторон 1:1)!'},
           'en': {'start': 'Greetings, {}!\nI am Telescopy and i can convert your square Video to a round'
                           ' <i>Video Message</i>, just send me your media.\n\n'
                           'Use /help command if you have any questions.',
                  'error': 'Ooops, something went wrong, try another file',
                  'content_error': 'I support only square Videos!',
                  'text_handler': 'Send me square Video',
                  'video_note_handler': "It's already a <i>Video message!</i>",
                  'size_handler': 'File is too big!\nMaximum file size is *8 MB*',
                  'converting': '<i>Converting</i> <code>{0:.2f}%</code>',
                  'downloading': '<i>Downloading file...</i>',
                  'uploading': '<i>Doing some magic stuff...</i>',
                  'webm': 'WebMs are currently unsupported 😓',
                  'help': '<a href="http://telegra.ph/Telescopy-FAQ-En-05-21-2">FAQ</a>',
                  'not_square': "It's not a square video (1:1 Aspect ratio)!"}}


def check_size(message):
    if message.video.file_size < 8000001:
        return 1
    else:
        bot.send_message(message.chat.id, strings[lang(message)]['size_handler'], parse_mode='Markdown').wait()
        return 0


def check_dimensions(message):
    if abs(message.video.height - message.video.width) in {0, 1}:
        return 1
    else:
        bot.send_message(message.chat.id, strings[lang(message)]['not_square']).wait()
        return 0


@bot.message_handler(commands=['start'])
def welcome(message):
    task = bot.send_message(message.chat.id, strings[lang(message)]['start'].format(
        message.from_user.first_name, 'https://telegram.org/update'),
                            parse_mode='HTML', disable_web_page_preview=True)
    track(botan_token, message.from_user.id, message, '/start')
    track(botan_token, message.from_user.id, message, lang(message))
    task.wait()


@bot.message_handler(commands=['help'])
def welcome(message):
    task = bot.send_message(message.chat.id, strings[lang(message)]['help'],
                            parse_mode='HTML', disable_web_page_preview=False)
    track(botan_token, message.from_user.id, message, '/help')
    task.wait()


@bot.message_handler(content_types=['video', 'document'])
def converting(message):
    if message.content_type is 'video':
        if check_size(message):
            if check_dimensions(message):
                try:
                    action = bot.send_chat_action(message.chat.id, 'record_video_note')
                    videonote = bot.download_file((((bot.get_file(message.video.file_id)).wait()).file_path)).wait()
                    if message.video.height < 640:
                        bot.send_video_note(message.chat.id, videonote, length=message.video.height).wait()
                    else:
                        bot.send_video_note(message.chat.id, videonote).wait()
                    action.wait()
                    track(botan_token, message.from_user.id, message, 'Convert')
                except Exception as e:
                    bot.send_message(me, '`{}`'.format(e), parse_mode='Markdown').wait()
                    bot.forward_message(me, message.chat.id, message.message_id).wait()  # some debug info
                    bot.send_message(message.chat.id, strings[lang(message)]['error']).wait()
                    track(botan_token, message.from_user.id, message, 'Error')

        else:
            return

    elif message.content_type is 'document' and \
            (message.document.mime_type == 'image/gif' or message.document.mime_type == 'video/mp4'):
        bot.send_message(message.chat.id, strings[lang(message)]['content_error'])
        return
        """if check_size(message):
            try:
                videonote = bot.download_file((((bot.get_file(message.document.file_id)).wait()).file_path)).wait()
                bot.send_chat_action(message.chat.id, 'record_video_note').wait()
                bot.send_video_note(message.chat.id, videonote).wait()
                track(botan_token, message.from_user.id, message, 'Convert')
            except:
                bot.send_message(message.chat.id, strings[lang(message)]['error']).wait()
                track(botan_token, message.from_user.id, message, 'Error')
        else:
            return"""

    elif message.content_type is 'document' and message.document.mime_type == 'video/webm':
        if str(message.from_user.id) == me:
            if check_size(message):
                try:
                    status = bot.send_message(message.chat.id, strings[lang(message)]['downloading'],
                                              parse_mode='HTML').wait()
                    api = cloudconvert.Api(cloud_convert_token)
                    process = api.convert({
                        'inputformat': 'webm',
                        'outputformat': 'mp4',
                        'input': 'download',
                        'save': True,
                        'file': 'https://api.telegram.org/file/bot{}/{}'.format(token,
                         (((bot.get_file(message.document.file_id)).wait()).file_path))
                    })
                    bot.edit_message_text(message.chat.id, strings[lang(message)]['converting'].format(0),
                                          status.chat.id,
                                          status.message_id,
                                          parse_mode='HTML').wait()
                    while True:
                        r = requests.get('https:{}'.format(process['url']))
                        percentage = ujson.loads(r.text)['percent']
                        bot.edit_message_text(strings[lang(message)]['converting'].format(percentage), status.chat.id,
                                              status.message_id,
                                              parse_mode='HTML').wait()
                        if percentage == 100:
                            break
                    bot.edit_message_text(strings[lang(message)]['uploading'].format(percentage), status.chat.id,
                                          status.message_id,
                                          parse_mode='HTML').wait()
                    process.wait()
                    bot.send_chat_action(message.chat.id, 'record_video_note').wait()
                    file = '{}_{}.mp4'.format(message.from_user.id, message.message_id)
                    process.download(file)
                    videonote = open(file, 'rb')
                    bot.delete_message(status.chat.id, status.message_id).wait()
                    bot.send_video_note(message.chat.id, videonote).wait()
                    videonote.close()
                    os.remove(file)
                except:
                    bot.send_message(message.chat.id, strings[lang(message)]['error']).wait()
                    track(botan_token, message.from_user.id, message, 'Error')
            else:
                return
        else:
            bot.send_message(message.chat.id, strings[lang(message)]['webm'], parse_mode='HTML').wait()

    else:
        bot.send_message(message.chat.id, strings[lang(message)]['content_error']).wait()


@bot.message_handler(content_types=['text'])
def text_handler(message):
    if message.content_type is 'text' and message.text != '/start' and message.text != '/help':
        bot.send_message(message.chat.id, strings[lang(message)]['text_handler']).wait()


@bot.message_handler(content_types=['video_note'])
def video_note_handler(message):
    if message.video_note is not None:
        bot.send_message(message.chat.id, strings[lang(message)]['video_note_handler'], parse_mode='HTML').wait()


bot.polling(none_stop=True)
