import time

from android_controller import AndroidController, Position
from constants import AccountType, IDType
from android_controller import keycodes as keycodes


def get_token(list_of_text):
    for n in list_of_text:
        if len(n) == 7:
            return n


controller = AndroidController(dark_mode=False)


"intentalo mas tarde  para nequi"
"verifica la inscripcion bancolombia mal"
"intentalo mas tarde problema de conexion"
