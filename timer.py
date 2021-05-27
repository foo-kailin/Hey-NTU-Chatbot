import logging

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def timer(update: Update, _: CallbackContext) -> None:
    update.message.reply_text('Use /set <timing> to set a timer.')


def alarm(context: CallbackContext) -> None:
    """Send the alarm message."""
    job = context.job
    context.bot.send_message(job.context, text='Beep beep! Timer\'s up. \U0000231B')


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def set_timer(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        print(context.args[0])  #show time
        print(context.args[1])  #show seconds, minutes, or hours
        due = int(context.args[0])
        length = str(context.args[1])
        if due < 0:
            update.message.reply_text('Sorry we cannot go back to the past!')
            return
        elif due == 0:
            update.message.reply_text('That is now.')
            return
        else:
            if length in ('seconds','second','secs','sec'):
                job_removed = remove_job_if_exists(str(chat_id), context)
                context.job_queue.run_once(alarm, due, context=chat_id, name=str(chat_id))

                text = 'Timer successfully set for '+str(due)+' second(s)!'
                if job_removed:
                    text += ' Old one was removed.'
                update.message.reply_text(text)
            elif length in ('minutes','minute','mins','min'):
                job_removed = remove_job_if_exists(str(chat_id), context)
                minute = due*60
                context.job_queue.run_once(alarm, minute, context=chat_id, name=str(chat_id))

                text = 'Timer successfully set for '+str(due)+' minute(s)!'
                if job_removed:
                    text += ' Old one was removed.'
                update.message.reply_text(text)
            elif length in ('hours','hour','hrs','hr'):
                job_removed = remove_job_if_exists(str(chat_id), context)
                hour = due*3600
                context.job_queue.run_once(alarm, hour, context=chat_id, name=str(chat_id))

                text = 'Timer successfully set for '+str(due)+' hour(s)!'
                if job_removed:
                    text += ' Old one was removed.'
                update.message.reply_text(text)
            elif length == '':
                text = 'Please specify time (seconds / minutes / hours).'
                update.message.reply_text(text)

    except (IndexError, ValueError):
        update.message.reply_text('Use /set <timing> to set a timer. Remember to specify time (seconds/minutes/hours).')


def unset(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Timer has been cancelled.' if job_removed else 'You have no active timer.'
    update.message.reply_text(text)


def main() -> None:
    """Run bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater("1446373870:AAEZTQdFkmUIMa6qNDVo1AngkKZyYcoV4Yw")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("timer", timer))
    dispatcher.add_handler(CommandHandler("set", set_timer))
    dispatcher.add_handler(CommandHandler("unset", unset))

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()