from collections import defaultdict
import sys
import re
sys.path.append('.')
from pathlib import Path as P

class JapaneseMonophoneG2p:
    graphemes = ["", "", "", "", "a", "b", "c", "d", "e", "f", "g",
            "h", "i", "j", "k", "m", "n", "o", "p", "r", "s",
            "t", "u", "v", "w", "y", "z", "あ", "い", "う", "え",
            "お", "ぁ", "ぃ", "ぅ", "ぇ", "ぉ", "か", "き", "く",
            "け", "こ", "さ", "し", "す", "せ", "そ", "ざ", "じ", "ず",
            "ぜ", "ぞ", "た", "ち", "つ", "て", "と", "だ", "ぢ", "づ", "で",
            "ど", "な", "に", "ぬ", "ね", "の", "は", "ひ", "ふ", "へ", "ほ",
            "ば", "び", "ぶ", "べ", "ぼ", "ぱ", "ぴ", "ぷ", "ぺ", "ぽ", "ま",
            "み", "む", "め", "も", "や", "ゆ", "よ", "ゃ", "ゅ", "ょ", "ら",
            "り", "る", "れ", "ろ", "わ", "を", "ん", "っ", "ヴ", "ゔ","゜",
            "ゐ", "ゑ", "ア", "イ", "ウ", "エ", "オ", "ァ", "ィ", "ゥ", "ェ",
            "ォ", "カ", "キ", "ク", "ケ", "コ", "サ", "シ", "ス", "セ", "ソ",
            "ザ", "ジ", "ズ", "ゼ", "ゾ", "タ", "チ", "ツ", "テ", "ト", "ダ",
            "ヂ", "ヅ", "デ", "ド", "ナ", "ニ", "ヌ", "ネ", "ノ", "ハ", "ヒ",
            "フ", "ヘ", "ホ", "バ", "ビ", "ブ", "ベ", "ボ", "パ", "ピ", "プ",
            "ペ", "ポ", "マ", "ミ", "ム", "メ", "モ", "ヤ", "ユ", "ヨ", "ャ",
            "ュ", "ョ", "ラ", "リ", "ル", "レ", "ロ", "ワ", "ヲ", "ン", "ッ",
            "ヰ", "ヱ", "息", "吸", "-", "R"]

    phonemes = ["", "", "", "", "A", "AP", "E", "I", "N", "O", "U",
            "SP", "a", "b", "ch", "cl", "d", "dy", "e", "f", "g", "gw",
            "gy", "h", "hy", "i", "j", "k", "kw", "ky", "m", "my", "n",
            "ng", "ny", "o", "p", "py", "r", "ry", "s", "sh", "t", "ts",
            "ty", "u", "v", "w", "y", "z"]

    def __init__(self):
        self.lock = None  # Placeholder for thread safety if neededy
        self.dict = {}
        self.pred_cache = defaultdict(list)
        self.session = None
        self.load_pack()

    def load_pack(self):
        hira_path = P('./Assets/G2p/jp-mono/hiragana.txt')
        katakana_path = P('./Assets/G2p/jp-mono/katakana.txt')
        romaji_path = P('./Assets/G2p/jp-mono/romaji.txt')
        special_path = P('./Assets/G2p/jp-mono/special.txt')
        with open(hira_path, 'r', encoding='utf-8') as hira_f, \
            open(katakana_path, 'r', encoding='utf-8') as katakana_f, \
            open(romaji_path, 'r', encoding='utf-8') as romaji_f, \
            open(special_path, 'r', encoding='utf-8') as special_f:
            all_data = hira_f.read() + katakana_f.read() + romaji_f.read() + special_f.read()
            for line in all_data.splitlines():
                parts = line.strip().split('  ')
                if len(parts) >= 2:
                    grapheme = parts[0]
                    phoneme_parts = parts[1:]
                    phonemes = ''.join(phoneme_parts).replace('0', '').replace('1', '').replace('2', '').replace('3', '')
                    self.dict[grapheme] = phonemes.split()

    def split_input(self, text):
        # Regular expression to check if character is Roman
        is_roman = re.compile(r'[aeioun]')

        result = []
        i = 0
        while i < len(text):
            if is_roman.match(text[i]):
                # If the character is Roman and the next character is also Roman
                if i + 1 < len(text) and is_roman.match(text[i + 1]):
                    result.append(text[i:i+2])
                    i += 2
                else:
                    result.append(text[i])
                    i += 1
            else:
                result.append(text[i])
                i += 1

        return ' '.join(result)

    def predict(self, input_text):
        # Split the input text
        split_text = self.split_input(input_text)
        
        words = split_text.strip().split()
        predicted_phonemes = []
        for word in words:
            word_lower = word
            if word_lower in self.dict:
                predicted_phonemes.append(' '.join(self.dict[word_lower]))
            else:
                cached_phoneme = self.pred_cache.get(word_lower)
                if cached_phoneme:
                    predicted_phonemes.append(' '.join(cached_phoneme))
                else:
                    return ''  # Return empty string if an error occurs
        return ' '.join(predicted_phonemes)

