import os
import subprocess
from flask import Flask, request
from git import Repo

app = Flask(__name__)
REPO_DIR = os.path.abspath(os.path.dirname(__file__))

@app.route("/trigger", methods=["POST"])
def webhook():
    print("✅ Webhook received!")

    try:
        # Pull latest changes from GitHub
        print("[INFO] Pulling latest changes...")
        repo = Repo(REPO_DIR)
        origin = repo.remotes.origin
        origin.pull()

        # Restart the bot with PM2
        print("[INFO] Restarting crypto-bot using PM2...")
        subprocess.run(["pm2", "restart", "crypto-bot"], check=True)

        return "✔ Updated and restarted.\n", 200
    except Exception as e:
        print(f"[ERROR] {e}")
        return f"❌ Error: {e}\n", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
