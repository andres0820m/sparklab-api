import yaml
from yaml.loader import SafeLoader
from constants import VALID_BANKS, VALID_ACCOUNTS_TYPE, VALID_DOCUMENT_TYPE, CONFIG_PATH, NUMBERS, KEYS_FOR_CHECK

with open(CONFIG_PATH) as f:
    config = yaml.load(f, Loader=SafeLoader)


def check_order_data(data):
    errors = []
    if data['document_type'] not in VALID_DOCUMENT_TYPE:
        errors.append("upps los documentos validos son : {}".format(str(VALID_DOCUMENT_TYPE)))
    if data['account_type'] not in VALID_ACCOUNTS_TYPE:
        errors.append("upps los tipos de cuenta validos son : {}".format(str(VALID_ACCOUNTS_TYPE)))
    if data['bank'] not in VALID_BANKS:
        errors.append("upps los bancos validos son : {}".format(str(VALID_BANKS)))
    return errors


class Dict2Class(object):

    def __init__(self, my_dict):
        for key in my_dict:
            setattr(self, key, my_dict[key])


def get_absolute_points(d):
    return int(d[0] * config['x_max']), int(d[1] * config['y_max'])


def left_only_numbers(text: str):
    number = ""
    for key in text:
        if key in NUMBERS:
            number += key
    return number


def mapped_dict_from_data(acc_dict, data, bank):
    account_data = dict()
    if bank == 'Nequi':
        acc_dict['is_contact'] = True
    for acc_data in data:
        if acc_data['fieldName'] == 'Full name of receiver':
            account_data['name'] = acc_data['fieldValue']
        else:
            account_data[acc_data['fieldName']] = acc_data['fieldValue']
    account_data = {k.lower().replace(" ", "_"): v for k, v in account_data.items()}
    acc_keys = account_data.keys()
    for key in acc_keys:
        if key not in KEYS_FOR_CHECK:
            acc_dict[key] = None
        else:
            acc_dict[key] = account_data[key]
    try:
        acc_dict.pop('bank_name')
    except KeyError:
        pass
