import time
import re
from enum import Enum
import random
import urllib.request
import secrets
from datetime import datetime
from android_controller import AndroidController
from android_controller import ElementNotFound
from android_controller import keycodes as keycodes
from guard_data import read_file
from tools import str_only_alphanumeric, str_only_numbers
from constants import BANCOLOMBIA_APP_PACKAGE_NAME, AccountType, IDType, BBVA_APP_PACKAGE_NAME, KIWI_BROSER, \
    NEQUI_PSE_URL, MAPPED_TABS_BBVA_ACCOUNT_TYPE, MAPPED_TABS_PSE_BANK_SELECTOR, AUT_USER, INTERNAL_ORDERS_LINK, \
    ORDERS_URL, DELETE_COMMAND
from Errors import *
from utils import get_absolute_points
import requests


class Bancolombia:
    def __init__(self, android_controller: AndroidController, ec_path: str, verbose=True, ):
        self.__controller = android_controller
        self.__verbose = verbose
        self.__last_login = None
        self.bank_data = read_file(ec_path)['bancolombia']

    def __print(self, text):
        if self.__verbose:
            print(text)

    def __close_app(self):
        self.__controller.close_app(BANCOLOMBIA_APP_PACKAGE_NAME)
        time.sleep(0.5)

    def __open_app(self):
        self.__controller.start_app(BANCOLOMBIA_APP_PACKAGE_NAME)
        time.sleep(0.5)

    def change_last_login(self):
        self.__last_login = None

    def check_transfer_error(self, check_text, retry=30, click_on_continue=False):
        while retry != 0:
            if self.__controller.find_text(check_text):
                self.__controller.click_on_text(check_text)
                break
            if self.__controller.find_text("intentalo mas tarde"):
                if click_on_continue:
                    self.__controller.click_on_text("intentalo mas tarde")
                else:
                    raise NequiAccountError
            if self.__controller.find_text("verifica la inscripcion"):
                raise BancolombiaError
            retry -= 1

    def login(self, fingerprint=False):
        check = True
        try:
            if (datetime.now() - self.__last_login).seconds < 150:
                check = False
        except TypeError:
            check = True
        if check:
            self.__close_app()
            self.__open_app()
            self.__print('Esperando que la aplicacion se inicie...')
            time.sleep(2)
            login_retry = 3
            while login_retry != 0:
                try:
                    self.__controller.click_on_text('iniciar sesion', max_y=0.4, use_canny=True, timeout=20.0)
                    if fingerprint:
                        self.__controller.click_on_text('CANCELAR', timeout=8)
                        login_retry = 0
                except TimeoutError:
                    login_retry -= 1
                    self.__controller.click_on_text('intentalo mas tarde', timeout=10)
            self.__print('Ingresando usuario...')
            self.__controller.click_on_text('Ingresa el usuario', timeout=5.0)
            self.__controller.input_text(self.bank_data['user_name'])
            self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
            time.sleep(3)
            self.__controller.click_on_text('CONTINUAR', timeout=5.0)
            self.__print('Ingresando contrasena')
            self.__controller.wait_for_text("ingresa la clave", timeout=40)
            self.__controller.input_text(self.bank_data['password'])
            time.sleep(1)
            self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
            self.__controller.click_on_text('CONTINUAR', timeout=15)

            self.__print('Esperando pantalla de bienvenida')
            try:
                self.__controller.wait_for_text('Hola {}'.format(self.bank_data['welcome_name']), timeout=40)
            except TimeoutError:
                raise TimeoutError('Nunca aparecio la pantalla de bienvenida')
            self.__print('Sesion iniciada')
        self.__last_login = datetime.now()

    def enroll_account(self,
                       num_account: str,
                       nickname: str,
                       acc_type: AccountType,
                       id_type: IDType,
                       id_number: str,
                       is_nequi=False
                       ):
        num_account = str_only_numbers(num_account)
        nickname = secrets.token_hex(nbytes=16)
        id_number = str_only_numbers(id_number)
        self.__print(f'Enrolling account {nickname}:')
        self.__print(f'  Account number: {num_account}')
        self.__print(f'  Account number: {acc_type}')
        self.__print(f'  Account number: {id_type}')
        self.__print(f'  Account number: {id_number}')
        self.__controller.click_on_text('Inicio')
        self.__controller.click_on_text('Transacciones', idx=1)
        self.__controller.click_on_text('Inscribir cuentas')
        for _ in range(4):
            self.__controller.wait_for_text('datos del producto', timeout=10)
        self.__controller.click_coordinate((242, 350))
        self.__controller.wait_for_text('Bancolombia', timeout=15, use_canny=True)
        account_text = "Ingresa el numero del producto"
        if is_nequi:
            account_text = 'Ingresa el numero'
            for _ in range(2):
                self.__controller.input_keyevent(keycodes.KEYCODE_DPAD_DOWN)
                time.sleep(0.3)
            time.sleep(1)
            self.__controller.input_text("nequi")
            time.sleep(2)
            self.__controller.click_coordinate((156, 590))
        else:
            time.sleep(1)
            self.__controller.click_on_text('Bancolombia')
        self.__controller.click_on_text(account_text)
        self.__controller.input_text(num_account)
        self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
        if not is_nequi:
            if acc_type == AccountType.AHORROS:
                self.__controller.click_on_text('Ahorros')
            else:
                self.__controller.click_on_text('Corriente')
        self.__controller.click_on_text('Ingresa nombre personalizado')
        time.sleep(0.1)
        self.__controller.input_text(nickname)
        self.__controller.click_on_text('Continuar')
        try:
            self.__controller.click_on_text('Selecciona el tipo de documento', timeout=15)
        except (ElementNotFound, TimeoutError):
            self.__controller.click_on_text('Cancelar')
            time.sleep(0.5)
            si = self.__controller.find_text('inscripci??n')[0]
            self.__controller.click_coordinate((si[0], si[1] + 69))
            raise AlreadyUsedNickname
        if id_type == IDType.CC:
            self.__controller.click_on_text('Cedula de ciudadania')
        elif id_type == IDType.NIT:
            self.__controller.click_on_text('Nit', timeout=10.0)
        elif id_type == IDType.CC_EXTRA:
            self.__controller.click_on_text('Cedula de extranjer??a', timeout=10.0)
        else:  # Passport
            self.__controller.click_on_text('Pasaporte', timeout=10.0)
        self.__controller.click_on_text('Ingresa el numero de documento', timeout=10.0)
        self.__controller.input_text(id_number)
        self.__controller.click_on_text('Continuar', timeout=15.0)
        self.__controller.click_on_text('Inscribir', timeout=15.0)
        option, _ = self.__controller.wait_for_any_of_this_texts(
            ['Inscripcion Exitosa', 'El producto ya se encuentra', 'verifica la inscripcion', 'intentalo mas tarde'],
            timeout=120
        )
        if option == 0:
            self.__controller.click_on_text('Inicio', timeout=15.0)
            self.__print('Inscription exitosa')
        elif option == 1:
            print("arreglo")
            self.__controller.click_on_text('Regresar', min_y=0.63, max_y=0.7, timeout=15)
            self.__controller.click_on_text('Inicio', timeout=10.0)
            raise AlreadyEnrolledAccount
        elif option == 2:
            self.__controller.click_on_text('cancelar', timeout=15)
            time.sleep(0.5)
            for _ in range(2):
                self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
                time.sleep(0.1)
            self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
            raise BancolombiaError
        elif option == 3:
            self.__controller.click_on_text('intentalo mas tarde', timeout=10)
            raise NequiAccountError
        self.__last_login = datetime.now()

    def transfer(self,
                 nickname: str,
                 amount: str,
                 binance_id: str,
                 account_type: str,
                 is_nequi=False,
                 ):
        nickname = str_only_alphanumeric(nickname)
        amount = re.sub(',', '', amount)
        amount = str(int(float(amount)))
        amount = str_only_numbers(amount)
        retry = 3
        while retry != 0:
            try:
                self.__controller.click_on_text('Inicio', delay=1.0, timeout=10)
                self.__controller.click_on_text('Transacciones', min_y=0.7)
                self.__controller.click_on_text('Transferir dinero', timeout=20)
                self.__controller.click_on_text('Enviar dinero', idx=1, timeout=20)
                self.__controller.click_on_text(self.bank_data['account_number'], timeout=10)
                self.__controller.input_text(amount)
                time.sleep(0.5)
                self.__controller.click_on_text('Continuar')
                time.sleep(0.5)
                if not is_nequi:
                    self.__controller.click_on_text('De Bancolombia', idx=1, timeout=10)
                else:
                    self.__controller.click_on_text('De Nequi', timeout=10)
                time.sleep(0.5)
                self.__controller.wait_for_text('Producto', 10)
                time.sleep(0.5)
                self.__controller.input_text(nickname)
                time.sleep(0.5)
                if is_nequi:
                    self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
                    time.sleep(0.3)
                    self.__controller.click_on_text('Continuar')
                else:
                    self.__controller.click_on_text(account_type)
                    time.sleep(0.5)
                    self.__controller.click_on_text('Continuar')
                    time.sleep(0.5)
                    self.__controller.click_on_text('Siguiente', timeout=5.0)
                time.sleep(0.5)
                self.__controller.click_on_text('Enviar dinero', timeout=15.0)
            except TimeoutError:
                try:
                    self.__controller.click_on_text('intentalo mas tarde', timeout=10)
                    retry -= 1
                except TimeoutError:
                    raise TransferNotFinished
            time.sleep(7)
            try:
                option, _ = self.__controller.wait_for_any_of_this_texts(
                    ['exitosa', 'intentalo mas tarde'],
                    timeout=200
                )
                if option == 0:
                    self.__controller.save_screen(binance_id)
                    break
                else:
                    if retry != 0:
                        retry -= 1
                        self.__controller.click_on_text('intentalo mas tarde', timeout=10)
                    else:
                        self.__controller.save_screen(binance_id)
                        raise TransferNotFinished
            except TimeoutError:
                self.__controller.save_screen(binance_id)
                raise TransferFailAtTheEnd
        try:
            time.sleep(7)
            self.__controller.click_on_text('Inicio', timeout=5.0)
            self.__print('Transaccion exitosa')
        except TimeoutError:
            self.__controller.save_screen(binance_id)
            raise TransferFailAtTheEnd
        self.__last_login = datetime.now()


class Bbva:

    def __init__(self, android_controller: AndroidController, ec_path: str, verbose=True, ):
        self.__controller = android_controller
        self.__verbose = verbose
        self.bank_data = read_file(ec_path)
        self.__login_position = 0.5055, 0.64
        self.__transfer_position = 0.3902, 0.205
        self.__confirm_position = 0.4902, 0.945
        self.__transfer_position_low = 0.5236, 0.9175

    def __print(self, text):
        if self.__verbose:
            print(text)

    def __close_app(self):
        self.__controller.close_app(BBVA_APP_PACKAGE_NAME)
        time.sleep(0.5)

    def __open_app(self):
        self.__controller.start_app(BBVA_APP_PACKAGE_NAME)
        time.sleep(0.5)

    def __get_token(self, show=False):
        self.__controller.wait_for_text('validez', timeout=40.0)
        token = self.__controller.get_token_data(max_y=0.3, min_y=0.22)
        print(token)
        return token

    def get_token(self, fingerprint, show=True):
        self.__close_app()
        self.__open_app()
        if fingerprint:
            self.__controller.click_on_text('CANCELAR', timeout=60)
        for _ in range(2):
            self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
            time.sleep(0.2)
        for _ in range(3):
            self.__controller.input_keyevent(keycodes.KEYCODE_DPAD_DOWN)
            time.sleep(0.2)
        self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
        self.__controller.click_on_text("cancelar", timeout=5.0)
        self.__controller.click_on_text('Contrase??a', timeout=10.0, idx=1)
        self.__controller.input_text(self.bank_data["BBVA"]["password"])
        self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
        time.sleep(0.2)
        self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
        self.__controller.click_on_text("net", timeout=10.0)
        token = None
        while token is None:
            token = self.__get_token(show=show)
        print("el token es ", token)
        return token

    def login(self, fingerprint: bool):
        self.__close_app()
        self.__open_app()
        self.__print('Esperando que la aplicacion se inicie...')
        if fingerprint:
            self.__controller.click_on_text('CANCELAR', timeout=20.0)
        time.sleep(0.2)
        x, y = get_absolute_points(self.__login_position)
        self.__controller.click_coordinate((x, y))
        self.__controller.click_on_text('Contrase??a', timeout=5.0, idx=1)
        time.sleep(0.3)
        self.__controller.input_text(self.bank_data["BBVA"]["password"])
        self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
        time.sleep(0.2)
        self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
        try:
            self.__controller.wait_for_text('Hola {}'.format(self.bank_data['BBVA']['welcome_name']), timeout=30.0)
        except TimeoutError:
            raise TimeoutError('Nunca aparecio la pantalla de bienvenida')

    def transfer(self, amount: str, is_contact, account: str, binance_id, document_number: str = None,
                 document_type=None,
                 name: str = None, account_type: str = None):
        x, y = get_absolute_points(self.__transfer_position)
        for _ in range(5):
            self.__controller.click_coordinate((x, y), long_press=False)
        self.__controller.click_on_text("A personas", timeout=10.0)
        if is_contact:
            self.__controller.click_on_text("Ingresar", timeout=10.0)
            self.__controller.click_on_text("Nombre")
            self.__controller.input_text(name)
            self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
            self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
            self.__controller.input_text(account)
            self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
            self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
            time.sleep(0.5)
            self.__controller.input_text(amount)
            self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
            self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
            self.__controller.wait_for_text("PRODUCTO DE ORIGEN", timeout=60.0)
            x, y = get_absolute_points(self.__transfer_position_low)
            self.__controller.click_coordinate((x, y))
            self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
            self.__controller.wait_for_text("EXITOSA", timeout=240)
            self.__controller.save_screen(binance_id)
        else:
            time.sleep(1)
            self.__controller.click_on_text("Cuentas")
            self.__controller.click_on_text("A una cuenta nueva", timeout=60.0)
            self.__controller.click_on_text("Tipo de producto")
            account_type_number = MAPPED_TABS_BBVA_ACCOUNT_TYPE[account_type]
            for _ in range(account_type_number):
                self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
            self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
            self.__controller.click_on_text("Banco")
            self.__controller.input_keyevent(keycodes.KEYCODE_DPAD_DOWN)
            time.sleep(0.3)
            self.__controller.input_keyevent(keycodes.KEYCODE_DPAD_DOWN)
            time.sleep(0.3)
            self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
            time.sleep(0.3)
            self.__controller.click_on_text("N??mero de cuenta")
            time.sleep(0.5)
            self.__controller.input_text(account)
            time.sleep(0.3)
            self.__controller.click_on_text("Tipo de documento")
            if document_type == 'cc':
                for i in range(3):
                    self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
                    time.sleep(0.2)
                self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
            if document_type == 'passport':
                for i in range(3):
                    self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
                    time.sleep(0.2)
                for i in range(3):
                    self.__controller.input_keyevent(keycodes.KEYCODE_DPAD_DOWN)
                self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
            if document_type == 'cc_extranjera':
                for i in range(3):
                    self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
                    time.sleep(0.2)
                self.__controller.input_keyevent(keycodes.KEYCODE_DPAD_DOWN)
                self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
            self.__controller.click_on_text("N??mero de documento")
            self.__controller.input_text(document_number)
            self.__controller.input_keyevent(keycodes.KEYCODE_BACK)
            for i in range(4):
                self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
                time.sleep(0.2)
            self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
            self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
            x, y = get_absolute_points(self.__confirm_position)
            self.__controller.click_coordinate((x, y))
            try:
                self.__controller.wait_for_text("entendido", min_y=0.6, max_y=0.8, use_canny=True, timeout=60.0)
            except TimeoutError:
                raise WrongDataOrAccountAlreadySubscribe
            self.__controller.click_coordinate((500, 500))
            try:
                self.__controller.wait_for_text("transferir", timeout=120)
                self.__controller.input_text(amount)
                for _ in range(2):
                    self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
                    time.sleep(0.1)
                self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
                self.__controller.wait_for_text("confirmar", timeout=120)
                for _ in range(3):
                    self.__controller.input_keyevent(keycodes.KEYCODE_DPAD_DOWN)
                    time.sleep(0.2)
                self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
            except TimeoutError:
                raise TimeoutButAccountHasBeenSubscribe
            try:
                self.__controller.wait_for_text("transferencia exitosa", timeout=120)
                self.__controller.save_screen(binance_id)
            except TimeoutError:
                raise TransferFailAtTheEnd


class NequiPse:
    def __init__(self, bank, controller: AndroidController):
        self.__bank = bank
        self.__controller = controller
        self.__pse_email_position = 0.4347, 0.76875

    def skip_im_not_a_robot(self):
        try_counter = 0
        time.sleep(2)
        try:
            self.__controller.click_on_text("Continuar", timeout=8.0, min_y=0.7, use_canny=True)
        except TimeoutError:
            print("buscando template")
            self.__controller.click_template(template='fix', min_y=0.80, max_y=1)
            for _ in range(5):
                try:
                    self.__controller.wait_for_text("Continuar", timeout=5.0)
                    break
                except TimeoutError:
                    self.__controller.click_template(template='fix_andres', min_y=0.75, max_y=1)
                    try_counter += 1
                if try_counter == 5:
                    raise TimeoutError
        self.__controller.wait_for_text("Continuar", timeout=10.0)
        self.__controller.click_on_text("Continuar", timeout=10.0)

    def fill_data_in_pse(self, number, amount):
        self.__controller.wait_for_text("cuenta", timeout=30.0)
        print("iniciando proceso ....")
        self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
        self.__controller.input_text(number)
        time.sleep(0.1)
        self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
        self.__controller.input_text(number)
        time.sleep(0.1)
        self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
        self.__controller.input_text(amount)
        time.sleep(0.1)
        for i in range(2):
            self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
            time.sleep(0.1)
        self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
        time.sleep(0.3)
        for i in range(MAPPED_TABS_PSE_BANK_SELECTOR[self.__bank]):
            self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
            time.sleep(0.1)
        self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
        self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
        self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)

    def __fill_email_and_click_continue(self, email, time_out):
        x, y = get_absolute_points(self.__pse_email_position)
        self.__controller.click_coordinate((x, y))
        self.__controller.input_text(email)
        self.__controller.click_on_text("Ir al Banco", timeout=time_out)

    def fill_pse_welcome_data(self, email, time_out):
        print(email)
        self.__controller.wait_for_text('E-mail', timeout=time_out, min_y=0.7)
        self.__fill_email_and_click_continue(email=email, time_out=time_out)
        try:
            self.__controller.wait_for_text("es 'requerido", timeout=5.0)
            self.__fill_email_and_click_continue(email=email, time_out=time_out)
        except TimeoutError:
            pass


class NequiPseBbva:
    def __init__(self, android_controller: AndroidController, ec_path: str, bbva_bank: Bbva, verbose=True, ):
        self.__controller = android_controller
        self.__nequi_pse = NequiPse(bank="bbva", controller=self.__controller)
        self.__verbose = verbose
        self.bank_data = read_file(ec_path)
        self.bank = bbva_bank

    def __print(self, text):
        if self.__verbose:
            print(text)

    def __close_app(self):
        self.__controller.close_app(KIWI_BROSER)
        time.sleep(0.5)

    def __open_app(self):
        self.__controller.start_nequi_pse(NEQUI_PSE_URL)
        time.sleep(0.5)

    def resume_app(self):
        self.__controller.start_app(KIWI_BROSER)

    def __get_token(self):
        retry = 5
        while retry != 0:
            token = self.bank.get_token(fingerprint=True)
            self.resume_app()
            self.__controller.click_on_text("ingrese el token", timeout=30.0)
            for _ in range(10):
                self.__controller.input_keyevent(DELETE_COMMAND)
            self.__controller.input_text(token)
            self.__controller.input_keyevent(keycodes.KEYCODE_BACK)
            time.sleep(0.2)
            self.__controller.click_on_text("pagar", timeout=10.0)
            try:
                self.__controller.wait_for_text("error en los datos", timeout=5.0)
                retry = - 1
            except TimeoutError:
                break
        if retry == 0:
            raise GettingTokenError

    def __continue_for_token(self):
        re_try = 5
        while re_try != 0:
            try:
                for _ in range(2):
                    self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
                    time.sleep(0.2)
                self.__controller.wait_for_text("referencia", timeout=5.0)
                self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
                break
            except TimeoutError:
                re_try -= 1
        if re_try == 0:
            raise ContinueForTokenError

    def pay(self, amount, number, binance_id):
        self.__close_app()
        self.__open_app()
        print(self.bank_data)
        self.__print('Esperando que la aplicacion se inicie...')
        self.__nequi_pse.fill_data_in_pse(amount=amount, number=number)
        self.__nequi_pse.skip_im_not_a_robot()
        self.__nequi_pse.fill_pse_welcome_data(email=self.bank_data['pse_bbva']['user_name'], time_out=60.0)
        self.__controller.wait_for_text("Cuentas", timeout=30.0)
        self.__controller.click_on_text("(personas)", timeout=5.0, idx=1)
        self.__controller.click_on_text("N??mero de documento", timeout=30.0)
        self.__controller.input_text(self.bank_data["pse_bbva"]["account_number"])
        self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
        self.__controller.input_text(self.bank_data["BBVA"]["password"])
        time.sleep(0.5)
        self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
        self.__controller.wait_for_text("recarga nequi pse", timeout=60.0)
        time.sleep(1)
        self.__continue_for_token()
        self.__controller.wait_for_text("ingrese el token", timeout=60.0)
        self.__get_token()
        try:
            self.__controller.wait_for_text("finalizaste tu pago", timeout=120)
            self.__controller.save_screen(binance_id)
        except TimeoutError:
            raise TransferFailAtTheEnd


class NequiDavivienda:
    def __init__(self, android_controller: AndroidController, telebot, ec_path: str, verbose=True):
        self.__controller = android_controller
        self.__verbose = verbose
        self.bank_data = read_file(ec_path)
        self.__telebot = telebot
        self.__nequi_pse = NequiPse(bank="davivienda", controller=self.__controller)
        self.__pse_email_position = 0.4347, 0.76875
        self.__persona_natural_location = 0.3708, 0.4606
        self.__documento_position = 0.5263, 0.54
        self.__continuar_1_davivienda = 0.3513, 0.5968
        self.__clave_virtual_position = 0.5263, 0.60437
        self.__continuar_2_davivienda = 0.3513, 0.67125
        self.__efectuar_pago_position = 0.3722, 0.52875
        self.__token_position = 0.5055, 0.5043

    def __print(self, text):
        if self.__verbose:
            print(text)

    def __close_app(self):
        self.__controller.close_app(KIWI_BROSER)
        time.sleep(0.5)

    def __open_app(self):
        self.__controller.start_nequi_pse(NEQUI_PSE_URL)
        time.sleep(0.5)

    def resume_app(self):
        self.__controller.start_app(KIWI_BROSER)

    def pay(self, amount, number, binance_id):
        self.__close_app()
        self.__open_app()
        self.__nequi_pse.fill_data_in_pse(number=number, amount=amount)
        self.__nequi_pse.skip_im_not_a_robot()
        self.__nequi_pse.fill_pse_welcome_data(email=self.bank_data['pse_davivienda']['user_name'], time_out=60.0)
        time.sleep(1)
        x, y = get_absolute_points(self.__persona_natural_location)
        self.__controller.click_coordinate((x, y))
        self.__controller.wait_for_text("ingreso persona natural", min_y=0.25, max_y=0.30, timeout=120, use_canny=True)
        time.sleep(1)
        x, y = get_absolute_points(self.__documento_position)
        self.__controller.click_coordinate((x, y))
        time.sleep(1)
        self.__controller.input_text(self.bank_data["pse_bbva"]["account_number"])
        ##########
        self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
        self.__controller.wait_for_text("clave Virtual", timeout=40)
        x, y = get_absolute_points(self.__clave_virtual_position)
        self.__controller.click_coordinate((x, y))
        self.__controller.input_text('2008')
        self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
        self.__controller.wait_for_text('efectuar pago', timeout=40)
        x, y = get_absolute_points(self.__efectuar_pago_position)
        self.__controller.click_coordinate((x, y))
        #####################################################
        need_token = False
        try:
            self.__controller.wait_for_text("codigo de confirmacion", timeout=12)
            need_token = True
        except TimeoutError:
            pass
        if need_token:
            token_getting_time = 60
            sender = 15
            old_order = ""
            while token_getting_time != 0:
                if sender >= 15:
                    text = INTERNAL_ORDERS_LINK.format(binance_id)
                    self.__telebot.send_message(chat_id=AUT_USER,
                                                text="ingrese el token de davivienda")
                    self.__telebot.send_message(chat_id=AUT_USER,
                                                text=text)
                    sender = 0
                order = requests.get(ORDERS_URL.format(binance_id)).json()
                if order['document_number'] and (old_order != order['document_number']):
                    old_order = order['document_number']
                    self.__controller.click_coordinate((531, 1318))
                    for _ in range(8):
                        self.__controller.input_keyevent(DELETE_COMMAND)
                    self.__controller.input_text(order['document_number'])
                    self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
                    try:
                        self.__controller.wait_for_text("numero de aprobacion", timeout=20)
                        break
                    except TimeoutError:
                        token_getting_time -= 20
                        sender += 20
                else:
                    token_getting_time -= 1
                    sender += 1
                    time.sleep(1)
            if token_getting_time <= 0:
                raise TransferNotFinished

        try:
            self.__controller.wait_for_text("numero de aprobacion", timeout=120)
            self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
            self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
            self.__controller.wait_for_text("Aprobada", timeout=60.0)
            self.__controller.input_keyevent(keycodes.KEYCODE_TAB)
            self.__controller.input_keyevent(keycodes.KEYCODE_ENTER)
            self.__controller.wait_for_text("Aprobada", timeout=60.0)
            self.__controller.save_screen(binance_id)
        except TimeoutError:
            raise TransferFailAtTheEnd


class BancolombiaPymeWrapped:
    @staticmethod
    def gen_random_hex_string(size):
        return ''.join(random.choices('0123456789abcdef', k=size))

    @staticmethod
    def get_time_for_login():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")[0:-3]

    @staticmethod
    def get_time_for_transfer():
        return datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    @staticmethod
    def get_transfer_id():
        return str(int(datetime.timestamp(datetime.now()) * 1000))[1:]

    def __init__(self, client_document, business_document, android_controller: AndroidController):
        self.client_document = client_document
        self.business_document = business_document
        self.message_id = self.gen_random_hex_string(16)
        self.external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
        self.session_tracker = self.gen_random_hex_string(16)
        self.devide_id = self.gen_random_hex_string(16)
        self.__controller = android_controller

    LOGIN_HEADER = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
        'Connection': 'keep-alive',
        'Content-Type': 'Application/json',
        'Origin': 'https://sucursalvirtualpyme.bancolombia.com',
        'Referer': 'https://sucursalvirtualpyme.bancolombia.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        'app-version': '1',
        'application-id': 'AW1180',
        'authorization': '',
        'channel': 'NDB',
        'device-id': '',
        'ip': "",
        'message-id': '',
        'platform-type': 'web',
        'request-timestamp': '',
        'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'session-tracker': '',
        'validate-captcha': 'false'}

    CHECK_ACCOUNT_HEADERS = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
        'Authorization': '',
        'Connection': 'keep-alive',
        'Content-Type': 'Application/json',
        'Origin': 'https://sucursalvirtualpyme.bancolombia.com',
        'Referer': 'https://sucursalvirtualpyme.bancolombia.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"'}
    TRANSFER_HEADERS = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
        'Authorization': '',
        'Connection': 'keep-alive',
        'Content-Type': 'Application/json',
        'Origin': 'https://sucursalvirtualpyme.bancolombia.com',
        'Referer': 'https://sucursalvirtualpyme.bancolombia.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"'}

    def login(self, login_key):
        self.push_id = self.gen_random_hex_string(16)
        self.detect_id = self.gen_random_hex_string(16)
        data = {"clientInfo": {"clientDocument": self.client_document, "clientDocumentType": "CC",
                               "businessDocument": self.business_document,
                               "businessDocumentType": "NT"},
                "transactionInfo": {"type": "authentication", "consumer": "SVN"},
                "additionalInfo": {"pushId": self.push_id,
                                   "detectId": self.detect_id, "credentials": [{"key": "pinblock",
                                                                                "value": login_key}],
                                   "authenticationType": "firstkey"}}
        self.LOGIN_HEADER['ip'] = self.external_ip
        self.LOGIN_HEADER['message-id'] = '38023512-7cc9-4b98-bb73-ef35dc05e40b'
        self.LOGIN_HEADER['session-tracker'] = '38023512-7cc9-4b98-bb73-ef35dc05e40b'
        self.LOGIN_HEADER['request-timestamp'] = self.get_time_for_login()
        self.LOGIN_HEADER['device-id'] = '38023512-7cc9-4b98-bb73-ef35dc05e40b'
        response = requests.post(
            'https://sucursalvirtualpyme.bancolombia.com/pyme-bancolombia/api/v1/security-filters/authentication-ndb/authenticate',
            headers=self.LOGIN_HEADER,
            json=data)
        if response.status_code == 200:
            self.token = response.json()['sessionInfo']['accessToken']
            return True
        else:
            return response

    def check_account(self, name, document, account):

        data = {"data": [
            {"header": {"type": "verifyAccount", "id": "0103244618958611"}, "consumerId": "SVN", "channelId": "NDB",
             "clientIp": "10.5.31.115", "device": "Web",
             "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
             "transactionDate": "2022/12/30 16:16:51", "accountType": "Cuenta ahorros", "accountNumber": account,
             "verifyIdType": "CC", "verifyIdNumber": document, "businessDocumentType": "NT",
             "businessDocument": self.business_document, "clientDocument": self.client_document,
             "clientDocumentType": "CC"}]}

        self.CHECK_ACCOUNT_HEADERS['Authorization'] = 'Bearer {}'.format(self.token)

        response = requests.post(
            'https://sucursalvirtualpyme.bancolombia.com/pyme-bancolombia/edge-service/verify-account',
            headers=self.CHECK_ACCOUNT_HEADERS,
            json=data)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 424:
            return False

    def __get_dynamic_key(self):
        self.__controller.find_text('.')
        all_text = self.__controller.get_all_text()
        for text in all_text:
            if len(str_only_numbers(text)) == 6:
                return text

    def transfer(self):
        key = self.__get_dynamic_key()
        print(key)
        data = {"data": [
            {"header": {"type": "saving-account-transfer", "id": "0103244618958661"}, "consumerId": "SVN",
             "channelId": "NDB",
             "clientIp": "10.5.31.115", "device": "Web",
             "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
             "transactionDate": "2022/12/30 16:17:41", "clientDocumentType": "CC", "clientDocument": "1032446189",
             "businessDocumentType": "NT", "businessDocument": "901658576",
             "targetClientInfo": {"targetClientDocumentType": "", "targetClientDocument": ""},
             "sourceAccountInfo": {"sourceProductType": "Cuenta ahorros", "sourceProductNumber": "04000005253"},
             "targetProductInfo": {"targetProductType": "Cuenta ahorros", "targetProductNumber": "91200786853"},
             "transferInfo": {"trackingNumber": self.get_transfer_id(), "transferValue": "100", "reference1": "",
                              "reference2": "",
                              "reference3": "", "transactionCodeDebit": "8561", "transactionCodeCredit": "8567",
                              "currencyCode": "COP", "movementDescriptionDebit": "Traslado Cta Suc Virtual Pyme",
                              "movementDescriptionCredit": "Traslado Cta Suc Virtual Pyme", "deviceCode": "SVN"},
             "officeInfo": {"entryOfficeCreditTransaction": "", "entryOfficeDebitTransaction": ""},
             "sessionId": self.detect_id, "authenticateTransaction": {"authenticationtType": "softoken",
                                                                      "authenticationValue": [
                                                                          {"key": "softoken",
                                                                           "value": key}]},
             "deviceId2": ""}]}
        self.TRANSFER_HEADERS['Authorization'] = 'Bearer {}'.format(self.token)
        response = requests.post(
            'https://sucursalvirtualpyme.bancolombia.com/pyme-bancolombia/edge-service/transfer',
            headers=self.TRANSFER_HEADERS,
            json=data)
        return response

'''
login_key = "126285836F7F84103B3D31A13EBFF3E31CD99F60989F95E4ED17F9F8D4FA341B613FB9BE8F085B4271CD0BAFED7345BE68DEC5F9A79C6FB7F57C6BDF24AF32B88F9233E9F4BFF94D9A3CA552F4B5DA96C437A1AE9B71A202802E86FDDEF8CEB530B9C32473B3F44585CE9600FACE39F69372BDF09D134B4E9778A9FF29DEA7B8DA92F81730864C84C6C35F37435FC9175013B69D1237D586072EB6191C3C37512E87A888888474C7E548B8DBB9A76E0A9EC8C030A7D763CE05C54DEA63ECFFF9EFC54C93E32DBF61B40543BCEF009F44E17B2854F09D0673280F86354A843AB94E37FB534295F45ACFB65CFFC65BA9FE1A26509238202756FE66688175193A80"

bancolombia_pyme = BancolombiaPymeWrapped(client_document='1032446189', business_document='901658576',
                                          android_controller=AndroidController(dark_mode=False))
bancolombia_pyme.login(login_key=login_key)
print(bancolombia_pyme.transfer().json())
'''