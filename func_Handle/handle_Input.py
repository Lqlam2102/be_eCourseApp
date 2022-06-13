import re
from unidecode import unidecode


def no_accent_vietnamese(utf8_str):
    return unidecode(utf8_str)

def is_vietnamese(utf8_str):
    regex = re.compile(r'[àảãáạăằẳẵắặâầẩẫấậđèẻẽéẹêềểễếệìỉĩíịòỏõóọôồổỗốộơờởỡớợùủũúụưừửữứựỳỷỹýỵ]')
    matches = re.findall(regex, utf8_str)
    if matches:
        return True
    else:
        return False