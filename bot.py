from glob import glob
import logging
import os
from random import choice

from clarifai.rest import ClarifaiApp
from emoji import emojize
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, RegexHandler, Filters 

import settings


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename='Bot.log'
                    )


def greet_user(bot, update, user_data):
    emo = emojize(choice(settings.USER_EMOJI), use_aliases=True)
    user_data['emo'] = emo
    text = 'Привет  {}'.format(emo)
    update.message.reply_text(text, reply_markup=get_keyboard())


def check_user_photo(bot, update, user_data):
    update.message.reply_text("Погодика")
    os.makedirs('downloads', exist_ok=True)
    photo_file = bot.getFile(update.message.photo[-1].file_id)
    filename = os.path.join('downloads', '{}.jpg'.format(photo_file.file_id))
    photo_file.download(filename)
    if is_frog(filename):
        update.message.reply_text("Обнаружена лягушка, теперь у нас на 1 больше.")
        new_filename = os.path.join('images', 'frog_{}.jpg'.format(photo_file.file_id))
        os.rename(filename, new_filename)
    else:
        update.message.reply_text("Это определенно не лягушка!")
        os.remove(filename)


def talk_to_me(bot, update, user_data):
    user_text = "Привет {} {}! Ты написал: {}, но зачем?".format(update.message.chat.first_name, user_data['emo'],
                update.message.text)
    logging.info("User: %s, Chat ud: %s, Message: %s", update.message.chat.username,
                update.message.chat.id, update.message.text)
    update.message.reply_text(user_text, reply_markup=get_keyboard())

def send_frog_picture(bot, update, user_data):
    frog_list = glob('images/frog*.jpg')
    frog_pic = choice(frog_list)
    bot.send_photo(chat_id=update.message.chat.id, photo=open(frog_pic, 'rb'), reply_markup=get_keyboard())


def change_avatar(bot, update, user_data):
    if 'emo' in user_data:
        del user_data['emo']
    emo = get_user_emo(user_data)
    update.message.reply_text('Теперь ты: {}'.format(emo), reply_markup=get_keyboard())


def get_contact(bot, update, user_data):
    print(update.message.contact)
    update.message.reply_text('Готово: {}'.format(get_user_emo(user_data)), reply_markup=get_keyboard())

def get_location(bot, update, user_data):
    print(update.message.location)
    update.message.reply_text('Готово: {}'.format(get_user_emo(user_data)), reply_markup=get_keyboard())


def get_user_emo(user_data):
    if 'emo' in user_data:
        return user_data['emo']
    else:
        user_data['emo'] = emojize(choice(settings.USER_EMOJI), use_aliases=True)
        return user_data['emo']

def get_keyboard():
    #contact_button = KeyboardButton('Прислать контакты', request_contact=True)
    #location_button = KeyboardButton('Прислать координаты', request_location=True)
    my_keyboard = ReplyKeyboardMarkup([
                                        ['Лягушку мне!', 'Сменить аватарку'],
                                        #[contact_button, location_button]
                                    ], resize_keyboard=True
                                )
    return my_keyboard


def is_frog(file_name):
    image_has_frog = False
    app = ClarifaiApp(api_key=settings.CLARIFAI_API_KEY)
    model = app.public_models.general_model
    response = model.predict_by_filename(file_name, max_concepts=5)
    if response['status']['code'] == 10000:
        for concept in response['outputs'][0]['data']['concepts']:
            if concept['name'] == 'frog':
                image_has_frog = True
    return image_has_frog
    

def main():
    mybot = Updater(settings.API_KEY)

    logging.info('Bot start')

    dp = mybot.dispatcher
    dp.add_handler(CommandHandler("start", greet_user, pass_user_data=True))
    dp.add_handler(CommandHandler('frog', send_frog_picture, pass_user_data=True))
    dp.add_handler(RegexHandler('^(Лягушку мне!)$', send_frog_picture, pass_user_data=True))
    dp.add_handler(RegexHandler('^(Сменить аватарку)$', change_avatar, pass_user_data=True))
    #dp.add_handler(MessageHandler(Filters.contact, get_contact, pass_user_data=True))
    #dp.add_handler(MessageHandler(Filters.location, get_location, pass_user_data=True))
    dp.add_handler(MessageHandler(Filters.photo, check_user_photo, pass_user_data=True))

    dp.add_handler(MessageHandler(Filters.text, talk_to_me, pass_user_data=True))

    mybot.start_polling()
    mybot.idle()


main()
