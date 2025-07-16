from flask import Flask
from threading import Thread
import time

app = Flask('')

@app.route('/')
def home():
    return "Леви Аккерман активен! Бот работает."

@app.route('/health')
def health():
    return {"status": "ok", "bot": "active", "timestamp": time.time()}

@app.route('/ping')
def ping():
    return "pong"

@app.route('/status')
def status():
    return "Леви Аккерман на страже! Бот активен и готов к бою!"

def run():
    import logging
    import sys
    import os
    
    # Полностью отключить все логи Flask
    log = logging.getLogger('werkzeug')
    log.disabled = True
    
    # Перенаправить стандартный вывод во время запуска Flask
    with open(os.devnull, 'w') as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
        finally:
            sys.stdout = old_stdout

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
