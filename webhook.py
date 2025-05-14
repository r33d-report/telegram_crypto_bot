from flask import Flask, request
import subprocess
import logging

app = Flask(__name__)
logging.basicConfig(filename='webhook.log', level=logging.INFO)

@app.route('/', methods=['POST'])
def webhook():
    logging.info("✅ GitHub webhook received!")
    # Pull latest changes
    subprocess.run(['git', 'pull'], cwd='/root/telegram_crypto_bot')
    # Restart the bot
    subprocess.run(['pm2', 'restart', 'crypto-bot'])
    return 'Success', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
