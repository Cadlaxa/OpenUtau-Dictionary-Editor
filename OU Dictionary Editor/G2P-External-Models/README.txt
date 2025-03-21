🔤 G2P-External-Models Instructions
-------------------------------------
1. Place each G2P model inside its own folder here.
2. Each model folder **must** contain a `config.yaml` file.
3. `config.yaml` should specify:
   - `onnx`: Path to the ONNX model file (or 'auto' to auto-detect)
   - `dict`: Path to the dictionary file (or 'auto' to auto-detect)
   - `graphemes`: List of graphemes
   - `phonemes`: List of phonemes
4. Example folder structure:
   📂 G2P-External-Models/
   ├── 📂 Model1/
   │   ├── config.yaml
   │   ├── model1.onnx
   │   ├── dictionary.txt
   ├── 📂 Model2/
   │   ├── config.yaml
   │   ├── model2.onnx
   │   ├── dictionary.txt

5. The system will automatically load all models inside this folder.
6. To use a model, select it from the UI or call `get_model('ModelName')`.
