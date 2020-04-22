
import logging

from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, PicklePersistence,StringRegexHandler)

bot_token = "1238856081:AAH3fu9xEuKd0KSCh6GQhrj6_IksDkiAkTs"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

TABOO_WORD = "Eldar"

def start(update, context):
    update.message.reply_text(
        'Salam {}'.format(update.message.from_user.first_name))

BEGIN, IN_PROGRESS ,WIN, LOSE = range(4)

def begin(update,context):
    if update.message['text'] == TABOO_WORD :
        update.message.reply_text("You found the word!")
    else :
        update.message.reply_text("Try again..")



def cancel(update,context):
    user = update.message.from_user
    logger.info("User %s cancelled the game!",user.first_name)
    update.message.reply_text('Bye! I hope we can talk again some day.')
    return ConversationHandler.END

def done(update,context):
    return  ConversationHandler.END

def win(update,context):
    update.message.reply_text("You found the word!!!")


def main():
    
    updater = Updater(bot_token,use_context=True)


    dc = updater.dispatcher
    
    handler = MessageHandler(~ Filters.command,begin)

    dc.add_handler(handler)


    updater.start_polling()
    updater.idle()




if __name__ == '__main__':
    main()