import re
from typing import List

from .char_convert import tranditional_to_simplified
from .chronology import RE_DATE
from .chronology import RE_DATE2
from .chronology import RE_TIME
from .chronology import RE_TIME_RANGE
from .chronology import replace_date
from .chronology import replace_date2
from .chronology import replace_time
from .constants import F2H_ASCII_LETTERS
from .constants import F2H_DIGITS
from .constants import F2H_SPACE
from .num import RE_DECIMAL_NUM
from .num import RE_DEFAULT_NUM
from .num import RE_FRAC
from .num import RE_INTEGER
from .num import RE_NUMBER
from .num import RE_PERCENTAGE
from .num import RE_POSITIVE_QUANTIFIERS
from .num import RE_RANGE
from .num import RE_TO_RANGE
from .num import replace_default_num
from .num import replace_frac
from .num import replace_negative_num
from .num import replace_number
from .num import replace_percentage
from .num import replace_positive_quantifier
from .num import replace_range
from .num import replace_to_range
from .phonecode import RE_MOBILE_PHONE
from .phonecode import RE_NATIONAL_UNIFORM_NUMBER
from .phonecode import RE_TELEPHONE
from .phonecode import replace_mobile
from .phonecode import replace_phone
from .quantifier import RE_TEMPERATURE
from .quantifier import replace_measure
from .quantifier import replace_temperature


class TextNormalizer():
    def __init__(self):
        self.SENTENCE_SPLITOR = re.compile(r'([：、，；。？！,;?!][”’]?)')

    def _split(self, text: str, lang="zh") -> List[str]:
        # Only for pure Chinese here
        if lang == "zh":
            # 去除空格
            text = text.replace(" ", "")

            # 过滤掉特殊字符，直接删除
            text = re.sub(r'[——《》【】<=>{}()（）#&@“”^_|\\]', '', text)

        # 识别每一个句子，识别到就加一个换行
        text = self.SENTENCE_SPLITOR.sub(r'\1\n', text)
        text = text.strip()
        #根据换行对句子进行分割
        sentences = [sentence.strip() for sentence in re.split(r'\n+', text)]

        return sentences

    def _post_replace(self, sentence: str) -> str:
        sentence = sentence.replace('/', '每')
        # sentence = sentence.replace('~', '至')
        # sentence = sentence.replace('～', '至')
        sentence = sentence.replace('①', '一')
        sentence = sentence.replace('②', '二')
        sentence = sentence.replace('③', '三')
        sentence = sentence.replace('④', '四')
        sentence = sentence.replace('⑤', '五')
        sentence = sentence.replace('⑥', '六')
        sentence = sentence.replace('⑦', '七')
        sentence = sentence.replace('⑧', '八')
        sentence = sentence.replace('⑨', '九')
        sentence = sentence.replace('⑩', '十')
        sentence = sentence.replace('α', '阿尔法')
        sentence = sentence.replace('β', '贝塔')
        sentence = sentence.replace('γ', '伽玛').replace('Γ', '伽玛')
        sentence = sentence.replace('δ', '德尔塔').replace('Δ', '德尔塔')
        sentence = sentence.replace('ε', '艾普西龙')
        sentence = sentence.replace('ζ', '捷塔')
        sentence = sentence.replace('η', '依塔')
        sentence = sentence.replace('θ', '西塔').replace('Θ', '西塔')
        sentence = sentence.replace('ι', '艾欧塔')
        sentence = sentence.replace('κ', '喀帕')
        sentence = sentence.replace('λ', '拉姆达').replace('Λ', '拉姆达')
        sentence = sentence.replace('μ', '缪')
        sentence = sentence.replace('ν', '拗')
        sentence = sentence.replace('ξ', '克西').replace('Ξ', '克西')
        sentence = sentence.replace('ο', '欧米克伦')
        sentence = sentence.replace('π', '派').replace('Π', '派')
        sentence = sentence.replace('ρ', '肉')
        sentence = sentence.replace('ς', '西格玛').replace('Σ', '西格玛').replace(
            'σ', '西格玛')
        sentence = sentence.replace('τ', '套')
        sentence = sentence.replace('υ', '宇普西龙')
        sentence = sentence.replace('φ', '服艾').replace('Φ', '服艾')
        sentence = sentence.replace('χ', '器')
        sentence = sentence.replace('ψ', '普赛').replace('Ψ', '普赛')
        sentence = sentence.replace('ω', '欧米伽').replace('Ω', '欧米伽')
        # re filter special characters, have one more character "-" than line 68
        sentence = re.sub(r'[-——《》【】<=>{}()（）#&@“”^_|\\]', '', sentence)
        return sentence

    def normalize_sentence(self, sentence: str) -> str:

        # 将繁体字转换成简体字
        sentence = tranditional_to_simplified(sentence)

        # 将句子的全角字符转换成半角字符
        sentence = sentence.translate(F2H_ASCII_LETTERS).translate(
            F2H_DIGITS).translate(F2H_SPACE)

        # 将句子里面的日期进行转换，如 2023年变为 二零二三年
        sentence = RE_DATE.sub(replace_date, sentence)
        sentence = RE_DATE2.sub(replace_date2, sentence)

        # 对句子里的时间进行转换
        sentence = RE_TIME_RANGE.sub(replace_time, sentence)
        sentence = RE_TIME.sub(replace_time, sentence)

        # 处理~波浪号作为至的替换
        sentence = RE_TO_RANGE.sub(replace_to_range, sentence)
        sentence = RE_TEMPERATURE.sub(replace_temperature, sentence)
        sentence = replace_measure(sentence)
        sentence = RE_FRAC.sub(replace_frac, sentence)
        sentence = RE_PERCENTAGE.sub(replace_percentage, sentence)
        sentence = RE_MOBILE_PHONE.sub(replace_mobile, sentence)

        sentence = RE_TELEPHONE.sub(replace_phone, sentence)
        sentence = RE_NATIONAL_UNIFORM_NUMBER.sub(replace_phone, sentence)

        sentence = RE_RANGE.sub(replace_range, sentence)
        sentence = RE_INTEGER.sub(replace_negative_num, sentence)
        sentence = RE_DECIMAL_NUM.sub(replace_number, sentence)
        sentence = RE_POSITIVE_QUANTIFIERS.sub(replace_positive_quantifier,
                                               sentence)
        sentence = RE_DEFAULT_NUM.sub(replace_default_num, sentence)
        sentence = RE_NUMBER.sub(replace_number, sentence)
        sentence = self._post_replace(sentence)

        return sentence

    def normalize(self, text: str) -> List[str]: # 定义function，返回为list
        # 将长段落根据标点进行分割，得到一些短句
        sentences = self._split(text)
        
        # 处理句子中的数字，日期。。。 标准化处理
        sentences = [self.normalize_sentence(sent) for sent in sentences]

        return sentences
