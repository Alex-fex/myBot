from glob import glob
import logging
from random import choice

from emoji import emojize
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import settings


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename='Bot.log'
                    )


def greet_user(bot, update, user_data):
    emo = emojize(choice(settings.USER_EMOJI), use_aliases=True)
    user_data['emo'] = emo
    text = 'Привет  {}'.format(emo)
    update.message.reply_text(text)


def talk_to_me(bot, update, user_data):
    user_text = "Привет {} {}! Ты написал: {}".format(update.message.chat.first_name, user_data['emo'],
                update.message.text)
    logging.info("User: %s, Chat ud: %s, Message: %s", update.message.chat.username,
                update.message.chat.id, update.message.text)
    update.message.reply_text(user_text)

def send_frog_picture(bot, update, user_data):
    frog_list = glob('images/frog*.jpg')
    frog_pic = choice(frog_list)
    bot.send_photo(chat_id=update.message.chat.id, photo=open(frog_pic, 'rb'))

def get_user_emo(user_data):
    if 'emo' in user_data:
        return user_data['emo']
    else:
        user_data['emo'] = emojize(choice(settings.USER_EMOJI), use_aliases=True)
        return user_data['emo']

def main():
    mybot = Updater(settings.API_KEY)

    logging.info('Bot start')

    dp = mybot.dispatcher
    dp.add_handler(CommandHandler("start", greet_user, pass_user_data=True))
    dp.add_handler(CommandHandler('frog', send_frog_picture, pass_user_data=True))

    dp.add_handler(MessageHandler(Filters.text, talk_to_me, pass_user_data=True))

    mybot.start_polling()
    mybot.idle()

main()
