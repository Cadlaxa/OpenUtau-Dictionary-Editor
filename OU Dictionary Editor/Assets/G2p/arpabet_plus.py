import onnxruntime as ort
import numpy as np
from collections import defaultdict
import traceback
import sys
sys.path.append('.')
from pathlib import Path as P

class ArpabetPlusG2p:
    graphemes = ["", "", "", "", "\'", "-", "a", "b", "c", "d", "e",
                 "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p",
                 "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
                 "A", "B", "C", "D", "E",
                 "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P",
                 "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]

    phonemes = ["", "", "", "", "aa", "ae", "ah", "ao", "aw", "ax", "ay", "b", "ch",
                "d", "dh", "dr", "dx", "eh", "er", "ey", "f", "g", "hh", "ih", "iy", "jh",
                "k", "l", "m", "n", "ng", "ow", "oy", "p", "q", "r", "s", "sh", "t",
                "th", "tr", "uh", "uw", "v", "w", "y", "z", "zh"]

    def __init__(self):
        self.lock = None  # Placeholder for thread safety if needed
        self.dict = {}
        self.grapheme_indexes = {}
        self.pred_cache = defaultdict(list)
        self.session = None
        self.phonemes = self.phonemes[4:]
        self.load_pack()

    def load_pack(self):
        dict_path = P('./Assets/G2p/g2p-en-arpa+/dict.txt')
        with open(dict_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('  ')
                if len(parts) >= 2:
                    grapheme = parts[0].lower()
                    phoneme_parts = parts[1:]
                    phonemes = ''.join(phoneme_parts).replace('0', '').replace('1', '').replace('2', '').replace('3', '').lower()
                    self.dict[grapheme] = phonemes.split()
                else:
                    print(f"Ignoring line: {line.strip()}")

        # Create grapheme indexes (skip the first four graphemes)
        self.grapheme_indexes = {g: i + 4 for i, g in enumerate(self.graphemes[4:])}

        onnx_path = P('./Assets/G2p/g2p-en-arpa+/g2p.onnx')
        self.session = ort.InferenceSession(onnx_path)

    def predict(self, input_text):
        words = input_text.strip().split()
        predicted_phonemes = []
        for word in words:
            word_lower = word.lower()
            if word_lower in self.dict:
                predicted_phonemes.append(' '.join(self.dict[word_lower]))
            else:
                cached_phoneme = self.pred_cache.get(word_lower)
                if cached_phoneme:
                    predicted_phonemes.append(' '.join(cached_phoneme))
                else:
                    predicted_phoneme = self.predict_with_model(word)
                    self.pred_cache[word_lower] = predicted_phoneme.split()
                    predicted_phonemes.append(predicted_phoneme)
        return ' '.join(predicted_phonemes)

    def predict_with_model(self, word):
        # Encode input word as indices of graphemes
        word_with_dash = "-" + word # funny workaround for that first skipped phoneme

        input_ids = np.array([self.grapheme_indexes.get(c, 0) for c in word_with_dash], dtype=np.int32) # equvilant to `Tensor<int> src = EncodeWord(grapheme);`
        input_length = len(input_ids)

        if len(input_ids.shape) == 1:
            input_ids = np.expand_dims(input_ids, axis=0)

        t = np.ones((1,), dtype=np.int32)
        
        src = input_ids
        tgt = np.array([2, ], dtype=np.int32)
        if len(tgt.shape) == 1:
            tgt = np.expand_dims(tgt, axis=0)
        print(tgt)

        try: 
            while t[0] < input_length and len(tgt) < 48:
                input_feed = {'src': src, 'tgt': tgt, 't': t}
                
                outputs = self.session.run(['pred'], input_feed)
                pred = outputs[0].flatten().astype(int)
                if pred != 2:
                    new_tgt_shape = (tgt.shape[0], tgt.shape[1] + 1)

                    new_tgt = np.zeros(new_tgt_shape, dtype=np.int32)

                    for i in range(tgt.shape[1]):
                        new_tgt[:, i] = tgt[:, i]

                    new_tgt[:, tgt.shape[1]] = pred
                    print(pred - 4)

                    tgt = new_tgt
                else:
                    t[0] += 1

            # these lines are equivalent to `var phonemes = DecodePhonemes(tgt.Skip(1).ToArray());`
            predicted_phonemes = []
            for id in tgt.flatten().astype(int):
                if id != 2: # skip the first phone (workaround) cuz of the np.array initial phoneme
                    predicted_phonemes.append(self.phonemes[id - 4])
            
            print(predicted_phonemes)

            predicted_phonemes_str = ' '.join(predicted_phonemes)
            return predicted_phonemes_str
        except Exception as e:

            print("Error in prediction", traceback.format_exc())