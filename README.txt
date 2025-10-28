P15 - Blockchain + Deep Learning Deepfake Detection (Flask)

Run instructions (local demo):
1. Create virtualenv and install requirements:
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt

2. (Optional) Train model with training.py and real/fake folders under data/.
   python training.py

3. Start Ganache (optional) and deploy contract:
   - Start Ganache on http://127.0.0.1:7545
   - python app/blockchain/deploy_contract.py
   This writes app/blockchain/contract_abi.json

4. Run Flask app:
   python app/app.py
   Open http://127.0.0.1:5000

Notes:
- A placeholder pretrained model is included for demo purposes (model/deepfake_model.h5).
- For accurate detection, train the model on FaceForensics++ or DFDC datasets and replace the model file.
