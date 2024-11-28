from flask import Flask
import os
from threading import Thread

# Inisialisasi Flask
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!", 200

# Fungsi untuk menjalankan Flask server
def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# Fungsi untuk menjaga bot tetap hidup
def keep_alive():
    t = Thread(target=run)
    t.start()
