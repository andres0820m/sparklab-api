import telebot
from constants import P2P_SCREENSHOT_BOT


class TelegramBot:
    def __init__(self):
        self.__telegram_bot = telebot.TeleBot(P2P_SCREENSHOT_BOT)

    def send_message(self, chat_id, text, retry=3):
        while retry != 0:
            try:
                self.__telegram_bot.send_message(chat_id=chat_id, text=text, timeout=3)
                return True
            except:
                print("Message fails !!")
                retry -= 1
        return False

    def send_photo(self, chat_id, img, caption, retry=3):
        while retry != 0:
            try:
                self.__telegram_bot.send_photo(chat_id=chat_id, photo=img,
                                               caption=caption)
                return True
            except:
                print("Message fails !!")
                retry -= 1
        return False
