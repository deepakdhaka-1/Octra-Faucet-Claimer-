# 🚰 OCTRA Faucet Auto-Claimer 🛠️

![Octra Logo](https://emojicdn.elk.sh/🚀)

A powerful automated script that:
- 💧 Claims faucet drops for multiple OCTRA wallets
- 🧠 Solves reCAPTCHA using [SolveCaptcha]([https://solvecaptcha.com/](https://solvecaptcha.com?from=497338))
- 🗃️ Reads wallets from a single `wallets.txt` file
- 🕹️ Handles each claim sequentially, with delays & retries

---

## 📦 Features

✅ Reads wallet addresses from `wallets.txt`  
✅ Prompts for your 🔐 SolveCaptcha API key  
✅ Solves reCAPTCHA v2 in the background  
✅ Retries failed claims automatically  
✅ Clean console logs with `rich` output  
✅ Shows 📊 summary of successful & failed wallets  

---

## 📁 Project Structure
```📁 your-folder/
├── claim_faucet.py # Main Python script
├── wallets.txt # List of wallet addresses (1 per line)
└── README.md # This file
```

### 🛠️ Requirements

- Python 3.7+
- Install required library:
```bash
pip install rich
```
## Flow -
```
git clone https://github.com/deepakdhaka-1/Octra-Faucet-Claimer-
cd Octra-Faucet-Claimer-
```
### Paste wallets in `wallets.txt`
```
wallets.txt
```
## RUN - 
- Make sure to get api key from solvecaptcha.
```
python3 bot.py
```
