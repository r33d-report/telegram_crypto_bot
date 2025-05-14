from flask import Flask, request
import os
import subprocess

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        repo_path = "/root/telegram_crypto_bot"
        try:
            subprocess.run(['git', '-C', repo_path, 'pull'], check=True)
            subprocess.run(['pm2', 'restart', 'crypto-bot'], check=True)
            return 'Updated and restarted', 200
        except subprocess.CalledProcessError as e:
            return f'Error: {e}', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
