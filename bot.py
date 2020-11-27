from glob import glob
import logging
import os
from random import choice

from emoji import emojize
from telegram import ReplyKeyboardRemove, ReplyKeyboardMarkup, InlineKeyboardMarkup,\
    InlineKeyboardButton, ParseMode, error

from clarifai.rest import ClarifaiApp

from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, RegexHandler,\
        CallbackQueryHandler, ConversationHandler, Filters 
from telegram.ext import messagequeue as mq

from db import db, get_or_create_user, get_user_emo, toggle_subscription, get_subscribers
import settings
import facts


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename='Bot.log'
                    )

subscribers = set()

@mq.queuedmessage
def send_updates(bot, job):
    for user in get_subscribers(db):
        try:
            bot.sendMessage(chat_id=user['chat_id'], text="Не ну ты молодец!")
        except error.BadRequest:
            print('Chat {} not found'.format(user['chat_id']))


def greet_user(bot, update, user_data):
    user = get_or_create_user(db, update.effective_user, update.message)
    emo = get_user_emo(db, user)
    user_data['emo'] = emo
    text = 'Привет  {}'.format(emo)
    update.message.reply_text(text, reply_markup=get_keyboard())


def check_user_photo(bot, update, user_data):
    user = get_or_create_user(db, update.effective_user, update.message)
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

#def anketa_start(bot, update, user_data):
   # user = get_or_create_user(db, update.effective_user, update.message)
   # update.message.reply_text("Представься! Введи Имя и Фамилию", reply_markup=ReplyKeyboardRemove())
   # return "name"

#def anketa_get_name(bot, update, user_data):
    #user = get_or_create_user(db, update.effective_user, update.message)
    #user_name = update.message.text
    #if len(user_name.split(" ")) !=2:
        #update.message.reply_text("Ну же, Имя и Фамилию, давай ты сможешь!")
        #return "name"
    #else:
        #user_data['anketa_name'] = user_name
        #reply_keyboard = [["1", "2", "3", "4", "5"]]

        #update.message.reply_text(
            #"Оцени бот от 1 до 5",
            #reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        #)
        #return "rating"

def anketa_rating(bot, update, user_data):
    user = get_or_create_user(db, update.effective_user, update.message)
    user_data['anketa_rating'] = update.message.text
    update.message.reply_text("""Напиши что думаешь или оставь отзыв. 
А если лениво нажми => /cancel""")
    return "comment"

def anketa_comment(bot, update, user_data):
    user = get_or_create_user(db, update.effective_user, update.message)
    user_data['anketa_comment'] = update.message.text
    text = """
<b>Имя Фамилия:</b> {anketa_name}
<b>Оценка:</b> {anketa_rating}
<b>Комментарий:</b> {anketa_comment}""".format(**user_data)
    update.message.reply_text(text, reply_markup=get_keyboard(), parse_mode=ParseMode.HTML)
    return ConversationHandler.END

def dontknow(bot, update, user_data):
    user = get_or_create_user(db, update.effective_user, update.message)
    update.message.reply_text("Не понятно")


def subscribe(bot, update):
    user = get_or_create_user(db, update.effective_user, update.message)
    if not user.get('subscribed'):
        toggle_subscription(db, user)
    update.message.reply_text('Подписка активна')

def unsubscribe(bot, update):
    user = get_or_create_user(db, update.effective_user, update.message)
    if user.get('subscribed'):
        toggle_subscription(db, user)
        update.message.reply_text('Подписка отключена')
    else:
        update.message.reply_text('Подписка не активна, нажмите /subscribe чтобы подписаться')

def show_inline(bot, update, user_data):
    inlinekbd = [[InlineKeyboardButton('Интересный факт', callback_data='1'), 
                    InlineKeyboardButton('Ну такое', callback_data='0')]]

    kbd_markup = InlineKeyboardMarkup(inlinekbd)
    update.message.reply_text(choice(facts.FACT1),
        reply_markup=kbd_markup)

def inlene_button_pressed(bot, update):
    query = update.callback_query
    try:
        user_choice = int(query.data)
        text = "Отлично, дальше больше!" if user_choice > 0 else "Вам не угодить..."
    except TypeError:
        text = "Что-то пошло не так"
    bot.edit_message_text(text=text, chat_id=query.message.chat_id, message_id=query.message.message_id)

def set_alarm(bot, update, args, job_queue):
    try:
        seconds = abs(int(args[0]))
        job_queue.run_once(alarm, seconds, context=update.message.chat_id)
    except (IndexError, ValueError):
        update.message.reply_text("Введите количество секунд после /alarm")


@mq.queuedmessage
def alarm(bot, job):
    bot.sendMessage(chat_id=job.context, text="Сработал будильник")


def anketa_skip_comment(bot, update, user_data):
    user = get_or_create_user(db, update.effective_user, update.message)
    text = """
<b>Фамилия Имя:</b> {anketa_name}
<b>Оценка:</b> {anketa_rating}""".format(**user_data)
    update.message.reply_text(text, reply_markup=get_keyboard(), parse_mode=ParseMode.HTML)
    return ConversationHandler.END


def talk_to_me(bot, update, user_data):
    user = get_or_create_user(db, update.effective_user, update.message)
    emo = get_user_emo(db, user)
    user_text = "Привет {} {}! Ты написал: {}, но зачем?".format(user['first_name'], emo,
                                                                update.message.text)
    logging.info("User: %s, Chat ud: %s, Message: %s", user['username'],
                update.message.chat.id, update.message.text)
    update.message.reply_text(user_text, reply_markup=get_keyboard())

def send_frog_picture(bot, update, user_data):
    user = get_or_create_user(db, update.effective_user, update.message)
    frog_list = glob('images/frog*.jpg')
    frog_pic = choice(frog_list)
    inlinepic = [[InlineKeyboardButton(emojize(":thumbs_up:"), callback_data='frog_good'),
                    InlineKeyboardButton(emojize(":thumbs_down:"), callback_data='frog_bad')]]

    pic_markup = InlineKeyboardMarkup(inlinepic)
    bot.send_photo(chat_id=update.message.chat.id, photo=open(frog_pic, 'rb'), reply_markup=get_keyboard())


def change_avatar(bot, update, user_data):
    user = get_or_create_user(db, update.effective_user, update.message)
    if 'emo' in user:
        del user['emo']
    emo = get_user_emo(db, user)
    update.message.reply_text('Теперь ты: {}'.format(emo), reply_markup=get_keyboard())


def get_contact(bot, update, user_data):
    user = get_or_create_user(db, update.effective_user, update.message)
    print(update.message.contact)
    update.message.reply_text('Готово: {}'.format(get_user_emo(db, user)), reply_markup=get_keyboard())

def get_location(bot, update, user_data):
    user = get_or_create_user(db, update.effective_user, update.message)
    print(update.message.location)
    update.message.reply_text('Готово: {}'.format(get_user_emo(db, user)), reply_markup=get_keyboard())


def get_keyboard():
    #contact_button = KeyboardButton('Прислать контакты', request_contact=True)
    #location_button = KeyboardButton('Прислать координаты', request_location=True)
    my_keyboard = ReplyKeyboardMarkup([
                                        ['Лягушку мне!', 'Факты о лягушках'],
                                        #['Анкета'], 
                                        ['Сменить аватарку']
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
    mybot.bot._msg_queue = mq.MessageQueue()
    mybot.bot._is_messages_queued_default = True

    logging.info('Bot start')

    dp = mybot.dispatcher

    mybot.job_queue.run_repeating(send_updates, interval=5)

    #anketa = ConversationHandler(
        #entry_points=[RegexHandler('^(Анкета)$', anketa_start, pass_user_data=True)],
        #states={
            #"name": [MessageHandler(Filters.text, anketa_get_name, pass_user_data=True)],
            #"rating": [RegexHandler('^(1|2|3|4|5)$', anketa_rating, pass_user_data=True)],
            #"comment": [MessageHandler(Filters.text, anketa_comment, pass_user_data=True),
                       # CommandHandler('skip', anketa_skip_comment, pass_user_data=True)],
        #},
        #fallbacks=[MessageHandler(
            #Filters.text | Filters.video | Filters.photo | Filters.document,
           # dontknow, 
           # pass_user_data=True
      #  )]
 #   )

    dp.add_handler(CommandHandler("start", greet_user, pass_user_data=True))
    #dp.add_handler(anketa)
    dp.add_handler(CommandHandler('frog', send_frog_picture, pass_user_data=True))
    dp.add_handler(RegexHandler('^(Лягушку мне!)$', send_frog_picture, pass_user_data=True))
    dp.add_handler(RegexHandler('^(Сменить аватарку)$', change_avatar, pass_user_data=True))
    dp.add_handler(RegexHandler('^(Факты о лягушках)$', show_inline, pass_user_data=True))
    dp.add_handler(CallbackQueryHandler(inlene_button_pressed))
    #dp.add_handler(MessageHandler(Filters.contact, get_contact, pass_user_data=True))
    #dp.add_handler(MessageHandler(Filters.location, get_location, pass_user_data=True))
    dp.add_handler(CommandHandler('subscribe', subscribe))
    dp.add_handler(CommandHandler('unsubscribe', unsubscribe))
    dp.add_handler(CommandHandler('alarm', set_alarm, pass_args=True, pass_job_queue=True))

    dp.add_handler(MessageHandler(Filters.photo, check_user_photo, pass_user_data=True))
    dp.add_handler(MessageHandler(Filters.text, talk_to_me, pass_user_data=True))

    mybot.start_polling()
    mybot.idle()


main()
