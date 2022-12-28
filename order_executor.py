import datetime
import json
import os
import time

from telegram_wrapped import TelegramBot
import yaml
from PIL import Image
from cryptography.fernet import Fernet
from django.core.wsgi import get_wsgi_application
from unidecode import unidecode
from yaml.loader import SafeLoader

from Errors import *
from android_controller import AndroidController
from bank_automation import Bancolombia, Bbva, NequiPseBbva, NequiDavivienda
from binance_listener import BinanceListener
from constants import CONFIG_PATH, ORDER_STATUS_TO_RUN, AUT_USER, MAPPED_ACCOUNTS, MAPPED_DOCUMENTS, \
    PARTNER_IDS
from orders_wrapped import OrderWrapped
from utils import Dict2Class, left_only_numbers

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
application = get_wsgi_application()
from orders.models import Order


class OrderExecutor:
    def __init__(self, ec_path, listener: BinanceListener, dark_mode=False):
        with open(CONFIG_PATH) as f:
            self.config = Dict2Class(yaml.load(f, Loader=SafeLoader))
        self.android_controller = AndroidController(dark_mode=dark_mode)
        self.__telegram_bot = TelegramBot()
        self.listener = listener
        self.order_wrapped = OrderWrapped()
        self.__bancolombia = Bancolombia(android_controller=self.android_controller, ec_path=ec_path)
        self.__bbva = Bbva(android_controller=self.android_controller, ec_path=ec_path)
        self.__nequi_pse_bbva = NequiPseBbva(android_controller=self.android_controller, ec_path=ec_path,
                                             bbva_bank=self.__bbva)
        self.__nequi_pse_davivienda = NequiDavivienda(android_controller=self.android_controller, ec_path=ec_path,
                                                      telebot=self.__telegram_bot)

    def __read_db_info(self):
        time_threshold = datetime.datetime.now() - datetime.timedelta(hours=self.config.past_hours)
        orders = Order.objects.filter(date__gt=time_threshold)
        return orders

    @staticmethod
    def __update_status(status, order: Order):
        order.status = status
        order.save()

    @staticmethod
    def __update_counter(order: Order):
        counter = order.fail_retry
        counter += 1
        order.fail_retry = counter

    def execute(self):
        while True:
            try:
                orders = self.order_wrapped.get_orders()
                for order in orders:

                    while order.fail_retry <= self.config.retry and order.status in ORDER_STATUS_TO_RUN:
                        try:

                            self.listener.send_message(binance_id=order.binance_id,
                                                       message="Se esta procesando tu orden en este momento")
                            order.status = 'running'
                            self.order_wrapped.update_order(order)
                            if order.bank.bank == 'pse_bbva':
                                self.__nequi_pse_bbva.pay(amount=order.amount, number=order.account,
                                                          binance_id=order.binance_id)
                            if order.bank.bank == "bancolombia":
                                status = self.order_wrapped.check_account(order.account)
                                print(status)
                                self.__bancolombia.login(fingerprint=self.config.bancolombia_fingerprint)
                                if status.status_code == 200:
                                    order.subscribe = True
                                    self.order_wrapped.update_order(order)
                                try:
                                    if not order.subscribe:
                                        self.listener.send_message(binance_id=order.binance_id,
                                                                   message=self.config.enrolling_account_message)
                                        self.__bancolombia.enroll_account(
                                            num_account=left_only_numbers(order.account),
                                            nickname=unidecode(order.name),
                                            acc_type=MAPPED_ACCOUNTS[
                                                order.account_type.account_type],
                                            id_type=MAPPED_DOCUMENTS[
                                                order.document_type.document],
                                            id_number=left_only_numbers(
                                                order.document_number),
                                            is_nequi=order.is_contact)
                                        self.listener.send_message(binance_id=order.binance_id,
                                                                   message=self.config.enrolling_account_done_message)
                                        order.subscribe = True
                                        self.order_wrapped.update_order(order)

                                except (AlreadyEnrolledAccount, AlreadyUsedNickname):
                                    order.subscribe = True
                                    self.order_wrapped.update_order(order)
                                self.listener.send_message(binance_id=order.binance_id,
                                                           message=self.config.process_payment_message)
                                self.__bancolombia.transfer(nickname=order.account, amount=order.amount,
                                                            binance_id=order.binance_id, is_nequi=order.is_contact,
                                                            account_type=order.account_type.account_type)
                            if order.bank.bank == 'BBVA':
                                self.__bbva.login(fingerprint=self.config.bbva_fingerprint)
                                self.__bbva.transfer(amount=order.amount, is_contact=order.is_contact,
                                                     account=left_only_numbers(order.account),
                                                     binance_id=order.binance_id,
                                                     document_number=left_only_numbers(order.document_number),
                                                     document_type=order.document_type.document,
                                                     name=unidecode(order.name),
                                                     account_type=order.account_type.account_type)
                            if order.bank.bank == 'pse_davivienda':
                                self.__nequi_pse_davivienda.pay(amount=order.amount,
                                                                number=left_only_numbers(order.account),
                                                                binance_id=order.binance_id)
                            print("Trasancion done !!")
                            order.status = 'done'
                            self.order_wrapped.update_order(order)
                            img = Image.open('imgs/{}.png'.format(order.binance_id))
                            img_link = self.listener.upload_img_to_drive('imgs/{}.png'.format(order.binance_id))
                            self.listener.send_message(binance_id=order.binance_id,
                                                       message=self.config.message_for_drive)
                            time.sleep(0.4)
                            self.listener.send_message(binance_id=order.binance_id, message=img_link)
                            time.sleep(0.4)
                            self.listener.send_message(binance_id=order.binance_id,
                                                       message=self.config.thanks_message)

                            if self.config.fix_price:
                                usdt_price = str(float(order.usdt_price) + float(config.amount_to_fix))
                            else:
                                usdt_price = order.usdt_price
                            message = "Se acaban de comprar {} pesos colombianos, a un precio de {}".format(
                                order.amount, usdt_price)
                            for partner in PARTNER_IDS:
                                self.__telegram_bot.send_message(chat_id=partner, text=message)

                            send_img_status = self.__telegram_bot.send_photo(chat_id=AUT_USER, img=img,
                                                                             caption='order: {}'.format(
                                                                                 order.binance_id))
                            if not send_img_status:
                                self.__telegram_bot.send_message(chat_id=AUT_USER,
                                                                 text="la imagen de la orden {} no pudo ser envia, buscar captura en la carpte de imagenes del pc".format(
                                                                     order.binance_id))
                            try:
                                self.listener.mark_order_as_paid(pay_id=order.pay_id, order_number=order.binance_id)
                            except:
                                self.__telegram_bot.send_message(chat_id=AUT_USER,
                                                                 text="la orden {} no se pudo marcar como paga !!!".format(
                                                                     order.binance_id))

                        except WrongDataOrAccountAlreadySubscribe:
                            order.fail_retry = 3
                            order.status = 'fail'
                            self.order_wrapped.update_order(order)
                            self.__telegram_bot.send_message(chat_id=AUT_USER,
                                                             text="datos incorrecto o cuenta ya inscrita en la orden {}".format(
                                                                 order.binance_id))

                        except TimeoutButAccountHasBeenSubscribe:
                            order.fail_retry = 3
                            order.status = 'fail'
                            self.order_wrapped.update_order(order)
                            self.__telegram_bot.send_message(chat_id=AUT_USER,
                                                             text="la orden {}, fallo pero se inscrbio la cuenta, borrar y volver a intentar".format(
                                                                 order.binance_id))

                        except TransferFailAtTheEnd:
                            order.fail_retry = 3
                            order.status = 'waiting_for_review'
                            self.order_wrapped.update_order(order)
                            if order.bank.bank == "BBVA":
                                text = "la orden {} fallo al final  y se inscribio!! revisar app del banco !!"
                            else:
                                text = " la orden {} fallo al final !! revisar app del banco !!"
                            self.__telegram_bot.send_message(chat_id=AUT_USER,
                                                             text=text.format(order.binance_id))
                            try:
                                img = Image.open('imgs/{}.png'.format(order.binance_id))
                                self.__telegram_bot.send_photo(chat_id=AUT_USER, img=img, caption='Error!!!'
                                                               )
                            except:
                                pass

                        except (BancolombiaError, NequiAccountError):
                            order.status = 'waiting_for_review'
                            self.order_wrapped.update_order(order)

                            self.__telegram_bot.send_message(chat_id=AUT_USER,
                                                             text="the order {} have wrong account data !!".format(
                                                                 order.binance_id))

                        except (
                                GettingTokenError, ContinueForTokenError, TimeoutError, TransferNotFinished,
                                IndexError):
                            self.__bancolombia.change_last_login()
                            print("Trasaction fails !!")
                            order.status = 'fail'
                            self.__update_counter(order=order)
                            self.order_wrapped.update_order(order)
                            try:
                                img = Image.open('imgs/{}.png'.format(order.binance_id))
                                self.__telegram_bot.send_photo(chat_id=AUT_USER, img=img, caption='Error!!!'
                                                               )
                            except:
                                pass
                            self.__telegram_bot.send_message(chat_id=AUT_USER,
                                                             text="order {} fails !!".format(order.binance_id))

                time.sleep(1)
            except ApiConnectionError:
                print("API is not working !!!")
                self.__telegram_bot.send_message(chat_id=AUT_USER, text="Can't connect to the server !!!!")
                time.sleep(10)


fernet = Fernet('L_V5YxcprMwMKyKtZt9ZGAe_iB2FfXPBYDcAHcpG190=')
with open('binance.data', 'rb') as enc_file:
    encrypted = enc_file.read()
    decrypted = fernet.decrypt(encrypted)
    data = json.loads(decrypted.decode("utf-8"))
    with open(CONFIG_PATH) as f:
        config = Dict2Class(yaml.load(f, Loader=SafeLoader))
    listener = BinanceListener(data=data, name=config.user_name, config=config, order_wrapped=OrderWrapped())
listener.join_wss_stream()
time.sleep(3)
executor = OrderExecutor(ec_path='banks_data.data', listener=listener)
executor.execute()
