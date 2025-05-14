from flask import Flask, request
import os
import git
import subprocess

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    repo = git.Repo('/root/telegram_crypto_bot')
    origin = repo.remotes.origin
    origin.pull()
    
    # Optional: restart the bot with PM2
    subprocess.run(["pm2", "restart", "crypto-bot"])

    return 'Webhook received and bot updated!', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
