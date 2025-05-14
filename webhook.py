from flask import Flask, request
import subprocess
import logging

app = Flask(__name__)

# Set up logging to file
logging.basicConfig(filename='webhook.log', level=logging.INFO)

@app.route('/', methods=['POST'])
def webhook():
    logging.info('✅ Received GitHub webhook')
    subprocess.call(['git', 'pull'])
    subprocess.call(['pm2', 'restart', 'crypto-bot'])
    return 'Webhook received and deployment started!', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
