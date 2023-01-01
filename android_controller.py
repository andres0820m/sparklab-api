import os
import time
import cv2
import pytesseract

import numpy as np

from ppadb.client import Client
from ppadb.device import Device
import ppadb.keycode as keycodes

from pathlib import Path
from enum import Enum

from tools import simplify_texts_list, simplify_text

TEMPLATES_PATH = Path('./templates')
DEFAULT_CLICK_DELAY = 0.5
MATCH_TEMPLATE_TH = 0.3
WAITS_DELAY = 0.5


class NotDevicesConnected(Exception): pass


class AppNotInstalled(Exception): pass


class ElementNotFound(Exception): pass


class Position(Enum):
    TOPLEFT = 0
    CENTER = 1


class ImgTemplate:

    def __init__(self, img_path):
        bgr = cv2.imread(str(img_path))
        self.__img = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        self.__click_point = (self.__img.shape[1] / 2, self.__img.shape[0] / 2)

    def get_img(self):
        return self.__img

    def get_click_point(self):
        return self.__click_point


class AndroidController:

    @staticmethod
    def get_device(devices: list[Device], serial=''):
        if len(devices) == 1:
            return devices[0]
        else:
            for device in devices:
                if device.get_serial_no() == serial:
                    return device

    def __init__(self, serial=None, dark_mode=False):
        self.__templates: dict[ImgTemplate] = {}

        self.__dark_mode = dark_mode

        self.__adb = Client()

        devices = self.__adb.devices()
        print(devices[0].get_serial_no())
        # ZT322CVCLS ZY32FSWLMG
        if len(devices) == 0:
            raise NotDevicesConnected
        self.__device: Device = self.get_device(devices=devices, serial='')

        self.__get_templates()
        self.__take_screenshot()
        self.__process_ocr()

    def _get_device(self):
        return self.__device

    def save_screen(self, name):
        time.sleep(1)
        self.__device.shell("screencap -p /sdcard/{}.png".format(name))
        self.__device.pull("/sdcard/{}.png".format(name), "imgs/{}.png".format(name))

    def __get_templates(self):
        files_list = os.listdir(TEMPLATES_PATH)
        pngs_list = filter(lambda file: file.endswith('.png'), files_list)
        for png_filename in pngs_list:
            name = png_filename[:-4]
            self.__templates[name] = ImgTemplate(TEMPLATES_PATH / png_filename)

    def __take_screenshot(self, show=False):
        png = np.asarray(self.__device.screencap())
        bgr = cv2.imdecode(png, cv2.IMREAD_COLOR)
        self.__screenshot = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        self.__screenshot_inverted = cv2.bitwise_not(self.__screenshot)

    def __process_ocr(self,
                      new_screenshot=True,
                      min_x=0.0, max_x=1.0, min_y=0.0, max_y=1.0,
                      show=False, use_canny=False
                      ):
        if new_screenshot:
            self.__take_screenshot(show=show)
        if self.__dark_mode:
            ss = self.__screenshot_inverted
        else:
            ss = self.__screenshot
        if min_x > 0.0 or max_x < 1.0 or min_y > 0.0 or max_y < 1.0:
            ss = np.copy(ss)
            min_x_idx = int((ss.shape[1] - 1) * min_x)
            max_x_idx = int((ss.shape[1] - 1) * max_x)
            min_y_idx = int((ss.shape[0] - 1) * min_y)
            max_y_idx = int((ss.shape[0] - 1) * max_y)
            ss[:min_y_idx, :, :] = 0
            ss[max_y_idx:, :, :] = 0
            ss[:, :min_x_idx, :] = 0
            ss[:, max_x_idx:, :] = 0
            if use_canny:
                ss = cv2.Canny(ss, 100, 200)
        self.__ocr_info = pytesseract.image_to_data(
            ss, output_type=pytesseract.Output.DICT, lang="spa"
        )
        self.__ocr_info['text'] = simplify_texts_list(self.__ocr_info['text'])

    def __get_word_pos_idx(self,
                           idx,
                           position: Position = Position.CENTER
                           ):
        if position == Position.TOPLEFT:
            return (self.__ocr_info['left'][idx], self.__ocr_info['top'][idx])
        else:
            return (
                self.__ocr_info['left'][idx] + self.__ocr_info['width'][idx] // 2,
                self.__ocr_info['top'][idx] + self.__ocr_info['height'][idx] // 2
            )

    def list_apps(self):
        return self.__device.list_packages()

    def start_app(self, app: str, data=''):
        if app not in self.list_apps():
            raise AppNotInstalled()
        self.__device.shell(
            f'monkey -p {app} -c android.intent.category.LAUNCHER 1 -d {data}'
        )

    def start_nequi_pse(self, url):
        self.__device.shell(f'am start --user 0 -a android.intent.action.VIEW -d {url}')

    def close_app(self, app: str):
        self.__device.shell(f'am force-stop {app}')

    def input_text(self, text):
        self.__device.input_text(text)

    def input_keyevent(self, keyevent):
        self.__device.input_keyevent(keyevent)

    def click_coordinate(self,
                         coord: tuple[int, int],
                         delay: float = DEFAULT_CLICK_DELAY,
                         long_press=False
                         ):
        if not long_press:
            self.__device.input_tap(coord[0], coord[1])
        else:
            self.__device.input_swipe(coord[0], coord[1], coord[0] + 3, coord[1] + 5, duration=300)
        time.sleep(delay)

    def get_screenshot(self, new_screenshot=True):
        if new_screenshot:
            self.__take_screenshot()
        return self.__screenshot

    def find_template(self, template: str, min_x=0.0, max_x=1.0, min_y=0.0, max_y=1, new_screenshot=True):
        if new_screenshot:
            png = np.asarray(self.__device.screencap())
            img = cv2.imdecode(png, cv2.IMREAD_COLOR)
        if min_x > 0.0 or max_x < 1.0 or min_y > 0.0 or max_y < 1.0:
            ss = np.copy(img)
            min_x_idx = int((ss.shape[1] - 1) * min_x)
            max_x_idx = int((ss.shape[1] - 1) * max_x)
            min_y_idx = int((ss.shape[0] - 1) * min_y)
            max_y_idx = int((ss.shape[0] - 1) * max_y)
            ss[:min_y_idx, :, :] = 0
            ss[max_y_idx:, :, :] = 0
            ss[:, :min_x_idx, :] = 0
            ss[:, max_x_idx:, :] = 0
        template_img = self.__templates[template].get_img()
        template_img = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
        ss = cv2.cvtColor(ss, cv2.COLOR_BGR2GRAY)
        match = cv2.matchTemplate(
            ss, template_img, cv2.TM_CCOEFF_NORMED
        )
        _, mx, minLoc, mxLoc = cv2.minMaxLoc(match)
        if mx >= MATCH_TEMPLATE_TH:
            return mxLoc
        else:
            return None

    def click_template(self, template: str, min_x=0.0, max_x=1.0, min_y=0.0, max_y=1):
        template_loc = self.find_template(template, min_x=min_x, min_y=min_y, max_y=max_y, max_x=max_x)
        if template_loc is None:
            return False
        click_point = self.__templates[template].get_click_point()
        self.click_coordinate((
            template_loc[0] + click_point[0],
            template_loc[1] + click_point[1]
        ))
        return True

    def __find_word(self,
                    word: str,
                    position: Position = Position.CENTER,
                    new_ocr: bool = True,
                    return_idxs: bool = False,
                    show=False,
                    min_x=0.0, max_x=1.0, min_y=0.0, max_y=1.0, use_canny=False
                    ):
        poss = []
        word = simplify_text(word)
        if new_ocr:
            self.__process_ocr(
                min_x=min_x, max_x=max_x, min_y=min_y, max_y=max_y, show=show, use_canny=use_canny
            )
        idxs = [i for i, x in enumerate(self.__ocr_info['text'])
                if x == word]

        for idx in idxs:
            poss.append(self.__get_word_pos_idx(idx, position))

        if return_idxs:
            return (poss, idxs)
        else:
            return poss

    def __find_words(self,
                     words: list[str],
                     position: Position = Position.CENTER,
                     new_ocr: bool = True,
                     return_idxs: bool = False,
                     min_x=0.0, max_x=1.0, min_y=0.0, max_y=1.0
                     ):
        if new_ocr:
            self.__process_ocr(
                min_x=min_x, max_x=max_x, min_y=min_y, max_y=max_y
            )
        words = simplify_texts_list(words)
        posss = []
        idxss = []
        for word in words:
            poss, idxs = self.__find_word(
                word, position, new_ocr=False, return_idxs=True
            )
            posss.append(poss)
            idxss.append(idxs)

        if return_idxs:
            return (posss, idxss)
        else:
            return posss

    def __find_phrase(self,
                      words: list[str],
                      position: Position = Position.CENTER,
                      new_ocr: bool = True,
                      show=False,
                      min_x=0.0, max_x=1.0, min_y=0.0, max_y=1.0, use_canny=False
                      ):
        if new_ocr:
            self.__process_ocr(
                min_x=min_x, max_x=max_x, min_y=min_y, max_y=max_y, use_canny=use_canny
            )

        words = simplify_texts_list(words)
        if len(words) > len(self.__ocr_info['text']):
            return []

        poss_avgs = []
        for i in range(len(self.__ocr_info['text']) - len(words) + 1):
            if self.__ocr_info['text'][i:i + len(words)] == words:
                pos_avg = [0, 0]
                for idx in range(len(words)):
                    pos = self.__get_word_pos_idx(idx + i, position)
                    pos_avg[0] += pos[0]
                    pos_avg[1] += pos[1]
                pos_avg[0] //= len(words)
                pos_avg[1] //= len(words)
                poss_avgs.append(tuple(pos_avg))

        return poss_avgs

    def get_all_text(self):
        return self.__ocr_info['text']

    def find_text(self,
                  text: str,
                  position: Position = Position.CENTER,
                  new_ocr: bool = True,
                  show=False,
                  min_x=0.0, max_x=1.0, min_y=0.0, max_y=1.0, use_canny=False
                  ):
        words = list(filter(lambda s: s != '', text.split(' ')))
        if len(words) > 1:
            return self.__find_phrase(
                words=words,
                position=position,
                new_ocr=new_ocr,
                min_x=min_x, max_x=max_x, min_y=min_y, max_y=max_y,
                show=show, use_canny=use_canny
            )
        elif len(words) == 1:
            return self.__find_word(
                word=words[0],
                position=position,
                new_ocr=new_ocr,
                min_x=min_x, max_x=max_x, min_y=min_y, max_y=max_y,
                show=show, use_canny=use_canny
            )
        else:
            return []

    def wait_for_text(self,
                      text: str,
                      timeout=0.0,
                      position: Position = Position.CENTER,
                      new_ocr: bool = True,
                      min_x=0.0, max_x=1.0, min_y=0.0, max_y=1.0, use_canny=False
                      ):
        start_time = time.time()
        while True:
            poss = self.find_text(
                text=text,
                position=position,
                new_ocr=new_ocr,
                min_x=min_x, max_x=max_x, min_y=min_y, max_y=max_y, use_canny=use_canny
            )
            if poss:
                return poss
            if timeout > 0.0 and (time.time() > (start_time + timeout)):
                raise TimeoutError
            time.sleep(WAITS_DELAY)

    def wait_for_any_of_this_texts(self,
                                   texts: list[str],
                                   timeout=0.0,
                                   position: Position = Position.CENTER,
                                   new_ocr: bool = True,
                                   min_x=0.0, max_x=1.0, min_y=0.0, max_y=1.0
                                   ):
        start_time = time.time()
        while True:
            for i, text in enumerate(texts):
                poss = self.find_text(
                    text=text,
                    position=position,
                    new_ocr=new_ocr,
                    min_x=min_x, max_x=max_x, min_y=min_y, max_y=max_y
                )
                if poss:
                    return i, poss
            if timeout > 0.0 and (time.time() > (start_time + timeout)):
                raise TimeoutError
            time.sleep(WAITS_DELAY)

    def get_token_data(self, min_x=0.0, max_x=1.0, min_y=0.0, max_y=1.0):
        png = np.asarray(self.__device.screencap())
        bgr = cv2.imdecode(png, cv2.IMREAD_COLOR)
        ss = np.copy(bgr)
        if min_x > 0.0 or max_x < 1.0 or min_y > 0.0 or max_y < 1.0:
            min_x_idx = int((ss.shape[1] - 1) * min_x)
            max_x_idx = int((ss.shape[1] - 1) * max_x)
            min_y_idx = int((ss.shape[0] - 1) * min_y)
            max_y_idx = int((ss.shape[0] - 1) * max_y)
            ss = ss[min_y_idx:max_y_idx, min_x_idx:max_x_idx]
        gry = cv2.cvtColor(ss, cv2.COLOR_BGR2GRAY)
        gry = cv2.Canny(gry, 100, 200)
        txt = pytesseract.image_to_string(gry, config='outputbase digits')
        #print("".join([t for t in txt if t != '!']).strip())
        return txt #"".join([t for t in txt if t != '!']).strip()

    def click_on_text(self,
                      text: str,
                      idx=0,
                      timeout=2.0,
                      delay=DEFAULT_CLICK_DELAY,
                      position: Position = Position.CENTER,
                      new_ocr: bool = True,
                      min_x=0.0, max_x=1.0, min_y=0.0, max_y=1.0,
                      use_canny=False
                      ):
        print("clicking on text: {}".format(text))
        if timeout > 0.0:
            poss = self.wait_for_text(
                text=text,
                timeout=timeout,
                position=position,
                new_ocr=new_ocr,
                min_x=min_x, max_x=max_x, min_y=min_y, max_y=max_y,
                use_canny=use_canny
            )
        else:
            poss = self.find_text(
                text=text,
                position=position,
                new_ocr=new_ocr,
                min_x=min_x, max_x=max_x, min_y=min_y, max_y=max_y,
                use_canny=use_canny
            )
        if not poss:
            print("fallo el click en texto {}".format(text))
            raise ElementNotFound
        self.click_coordinate(poss[idx], delay=delay)
