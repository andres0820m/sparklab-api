import re


def simplify_text(text):
    text = text.lower()
    text = text.replace('á', 'a')
    text = text.replace('é', 'e')
    text = text.replace('í', 'i')
    text = text.replace('ó', 'o')
    text = text.replace('ú', 'u')
    text = re.sub('[.,?!¡¿]', '', text)
    return text


def simplify_texts_list(texts):
    for i in range(len(texts)):
        texts[i] = simplify_text(texts[i])
    return texts


def str_only_numbers(str):
    return re.sub('\D', '', str)


def str_only_alphanumeric(str):
    return re.sub('[\W_]', '', str)
