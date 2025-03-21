import ruamel.yaml
import onnxruntime as ort
import numpy as np
from collections import defaultdict
import traceback
import sys
sys.path.append('.')
from pathlib import Path as P

class G2pModelManager:
    def __init__(self):
        self.models = {}  # Stores loaded models {name: model_instance}
        self.model_names = {}  # Maps names to folder paths {name: folder}
        self.g2p_root = P("./G2P-External-Models")
        self.yaml = ruamel.yaml.YAML(typ="safe")
        self.ensure_main_folder()  # Ensure folder & README exist
        self.load_all_g2p_models()

    def ensure_main_folder(self):
        """Creates 'G2P-External-Models/' and adds 'README.txt' if missing."""
        self.g2p_root.mkdir(exist_ok=True)
        readme_path = self.g2p_root / "README.txt"
        if not readme_path.exists():
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(
                    "🔤 G2P-External-Models Instructions\n"
                    "-------------------------------------\n"
                    "1. Place each G2P model inside its own folder here.\n"
                    "2. Each model folder **must** contain a `config.yaml` file.\n"
                    "3. The `config.yaml` should specify:\n"
                    "   - `name`: Model name for the dropdown\n"
                    "   - `onnx`: Path to the ONNX model file (or 'auto')\n"
                    "   - `dict`: Path to the dictionary file (or 'auto')\n"
                    "   - `graphemes`: List of graphemes\n"
                    "   - `phonemes`: List of phonemes\n"
                    "4. Example folder structure:\n"
                    "   📂 G2P-External-Models/\n"
                    "   ├── 📂 Model1/\n"
                    "   │   ├── config.yaml\n"
                    "   │   ├── model1.onnx\n"
                    "   │   ├── dictionary.txt\n"
                    "   ├── 📂 Model2/\n"
                    "   │   ├── config.yaml\n"
                    "   │   ├── model2.onnx\n"
                    "   │   ├── dictionary.txt\n"
                    "\n"
                    "5. The system will automatically load all models inside this folder.\n"
                    "6. To use a model, select it from the UI or call `get_model('Model Name')`.\n"
                )
            print("📄 Created README.txt in G2P-External-Models/")

    def load_all_g2p_models(self):
        """Scans 'G2P-External-Models/' for model folders containing 'config.yaml' and loads them."""
        for model_folder in self.g2p_root.iterdir():
            config_path = model_folder / "config.yaml"
            if model_folder.is_dir() and config_path.exists():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = self.yaml.load(f)

                    model_name = config.get("name", model_folder.name)  # Use folder name if 'name' missing
                    model = G2p(model_folder)
                    self.models[model_name] = model
                    self.model_names[model_name] = model_folder.name  # Store folder name for lookups

                    print(f"✅ Loaded G2P Model: {model_name}")

                except Exception as e:
                    print(f"❌ Error loading model from {model_folder.name}:\n{traceback.format_exc()}")
            else:
                print(f"⚠️ Skipping {model_folder.name} (No config.yaml found)")

    def get_model(self, model_name):
        """Returns a loaded model by name."""
        return self.models.get(model_name, None)

class G2p:
    def __init__(self, model_path):
        self.model_path = P(model_path)
        self.dict = {}
        self.grapheme_indexes = {}
        self.pred_cache = defaultdict(list)
        self.yaml = ruamel.yaml.YAML(typ="safe")
        self.session = None
        self.graphemes = []
        self.phonemes = []
        self.phonemes = self.phonemes[4:]
        self.load_g2p_model()

    def load_g2p_model(self):
        """Loads a single G2P model from its folder."""
        config_path = self.model_path / "config.yaml"

        if not config_path.exists():
            print(f"❌ Missing config.yaml in {self.model_path}, skipping model.")
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = self.yaml.load(f)

            # ✅ Correctly auto-detect ONNX and dict.txt files
            onnx_path = self.auto_detect_file(config.get("onnx", "auto"), "*.onnx")
            dict_path = self.auto_detect_file(config.get("dict", "auto"), "*.txt")

            # ✅ Load graphemes and phonemes
            self.graphemes = config.get("graphemes", [])
            self.phonemes = config.get("phonemes", [])
            if not self.graphemes or not self.phonemes:
                raise ValueError(f"⚠️ Missing 'graphemes' or 'phonemes' list in {config_path}.")
            
            self.load_dictionary(dict_path)
            # ✅ Create grapheme indexes (skip the first four graphemes)
            self.grapheme_indexes = {g: i + 4 for i, g in enumerate(self.graphemes[4:])}
            self.session = ort.InferenceSession(str(onnx_path))

            print(f"✅ Successfully loaded G2P Model from {self.model_path.name}")

        except Exception as e:
            print(f"❌ Error loading model from {self.model_path}:\n{traceback.format_exc()}")

    def auto_detect_file(self, file_path, pattern):
        # Auto-detects a file in the model directory if 'auto' is specified
        if file_path == "auto":
            files = list(self.model_path.glob(pattern))  # Find all matching files
            if not files:
                raise FileNotFoundError(f"❌ No matching {pattern} found in {self.model_path}.")
            return files[0]
        return self.model_path / file_path  # Use the specified path

    def load_dictionary(self, dict_path):
        # Loads the dictionary from a file while handling formatting inconsistencies
        try:
            with open(dict_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):  # Ignore empty lines and comments
                        continue
                    
                    # ✅ Use `split(None, 1)` to split by any whitespace instead of `"  "`
                    parts = line.split(None, 1)
                    if len(parts) < 2:
                        print(f"Ignoring malformed line: {line}")
                        continue
                    
                    grapheme = parts[0].lower()
                    phonemes = parts[1].split()  # Split phonemes correctly
                    # ✅ Remove stress markers (0, 1, 2, 3)
                    phonemes = [p.lower().strip("0123") for p in phonemes]
                    self.dict[grapheme] = phonemes

            print(f"✅ Loaded dictionary: {dict_path} ({len(self.dict)} words)")

        except Exception as e:
            print(f"❌ Error loading dictionary {dict_path}:\n{traceback.format_exc()}")

    def predict(self, input_text):
        words = input_text.strip().split()
        predicted_phonemes = []
        for word in words:
            word_lower = word.lower()
            # ✅ Check if word exists in `dict.txt`
            if word_lower in self.dict:
                phoneme_list = self.dict[word_lower]
                predicted_phonemes.append(" ".join(phoneme_list))
                continue  # Skip model prediction since we found it in the dictionary
            # ✅ Check cache before calling ONNX model
            if word_lower in self.pred_cache:
                predicted_phonemes.append(" ".join(self.pred_cache[word_lower]))
                continue
            # ✅ If not in dictionary, use the model
            predicted_phoneme = self.predict_with_model(word)
            self.pred_cache[word_lower] = predicted_phoneme.split()
            predicted_phonemes.append(predicted_phoneme)

        return " ".join(predicted_phonemes)

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
                    predicted_phonemes.append(self.phonemes[id - 0])
            
            print(predicted_phonemes)

            predicted_phonemes_str = ' '.join(predicted_phonemes)
            return predicted_phonemes_str
        except Exception as e:

            print("Error in prediction", traceback.format_exc())