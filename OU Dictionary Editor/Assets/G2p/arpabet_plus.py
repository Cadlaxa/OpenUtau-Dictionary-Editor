import onnxruntime as ort
import numpy as np
from collections import defaultdict

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
        self.load_pack()

    def load_pack(self):
        dict_path = 'Assets/G2p/arpabet-plus/dict.txt'
        with open(dict_path, 'r') as f:
            for line in f:
                parts = line.strip().split('  ')
                if len(parts) >= 2:
                    grapheme = parts[0].lower()
                    phoneme_parts = parts[1:]
                    phonemes = ''.join(phoneme_parts).replace('0', '').replace('1', '').replace('2', '').lower()
                    self.dict[grapheme] = phonemes.split()
                else:
                    print(f"Ignoring line: {line.strip()}")

        # Create grapheme indexes (skip the first four graphemes)
        self.grapheme_indexes = {g: i + 4 for i, g in enumerate(self.graphemes[4:])}

        onnx_path = 'Assets/G2p/arpabet-plus/g2p.onnx'
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
        input_ids = np.array([self.grapheme_indexes.get(c, 0) for c in word], dtype=np.int32)
        input_length = len(input_ids)

        max_sequence_length = 32
        src = np.zeros((1, max_sequence_length), dtype=np.int32)
        tgt = np.zeros((1, max_sequence_length), dtype=np.int32)
        t = np.ones((1,), dtype=np.int32)
        
        src[0, :input_length] = input_ids
        tgt[0, :input_length] = np.arange(input_length)

        input_feed = {'src': src, 'tgt': tgt, 't': t}

        try:
            # Run inference with the ONNX model
            outputs = self.session.run(None, input_feed)
            predicted_phoneme_ids = outputs[0].flatten().astype(int)

            # Map predicted phoneme IDs to actual phonemes
            predicted_phonemes = [self.phonemes[id] for id in predicted_phoneme_ids]

            # Post-process phonemes if necessary (e.g., remove trailing digits)
            predicted_phonemes = [phoneme.rstrip('012') for phoneme in predicted_phonemes if phoneme != ""]

            # Join phonemes into a single string
            predicted_phonemes_str = ' '.join(predicted_phonemes)

            return predicted_phonemes_str

        except Exception as e:
            print(f"Error predicting phonemes for '{word}' with ONNX model: {e}")
            return ''


arpabet_g2p = ArpabetPlusG2p()
result = arpabet_g2p.predict("cu")
print(result)
