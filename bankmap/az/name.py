
def is_latin(letter):
    if letter.isalpha():
        return 65 <= ord(letter) <= 90 or 97 <= ord(letter) <= 122
    else:
        return False


def replace_char(x):
    if is_latin(x):
        return x
    if x in '-0123456789':
        return x
    return "_"


def fix_exp_name(name: str, max_len: int = 50) -> str:
    return ''.join(replace_char(x) for x in name)[:max_len]
