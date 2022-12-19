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

number_to_delete = 1250

for i in range(number_to_delete):
    controller.click_coordinate((78, 255))
    time.sleep(0.3)
    controller.click_coordinate((399, 414))
    time.sleep(3)
    controller.input_keyevent(keycodes.KEYCODE_MOVE_END)
    time.sleep(0.1)
    controller.click_coordinate((6, 1405))
    time.sleep(0.1)
    controller.click_coordinate((220, 1475))
    time.sleep(0.1)
    controller.click_coordinate((308, 505))
    time.sleep(0.1)
    print("se han borrado {} cuentas".format(i + 1))



