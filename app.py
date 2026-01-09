from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")

@app.route("/", methods=["GET"])
def home():
    return "Webhook Mercado Pago ONLINE", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Webhook recebido:", data)

    if data and data.get("type") == "payment":
        payment_id = data["data"]["id"]
        confirmar_pagamento(payment_id)

    return jsonify({"status": "ok"}), 200


def confirmar_pagamento(payment_id):
    url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    r = requests.get(url, headers=headers)
    pagamento = r.json()

    status = pagamento.get("status")
    print("Status:", status)

    if status == "approved":
        print("✅ PAGAMENTO APROVADO")
        # 👉 AQUI você libera créditos, plano, Telegram etc


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
