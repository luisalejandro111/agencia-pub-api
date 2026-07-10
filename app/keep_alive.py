# keep_alive.py
import requests
import time
import os

URL = os.getenv("RENDER_URL", "https://agencia-api.onrender.com/ping")

def ping_server():
    try:
        response = requests.get(URL, timeout=10)
        print(f"✅ Ping exitoso: {response.status_code} - {response.json().get('timestamp')}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print(f"🚀 Iniciando keep-alive para {URL}")
    while True:
        ping_server()
        time.sleep(600)  # 10 minutos