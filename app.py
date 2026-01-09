from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# ==========================
# CONFIGURAÇÃO
# ==========================
ACCESS_TOKEN = os.getenv("APP_USR-264234346131232-071723-2b11d40f943d9721d869863410833122-777482543")

# ==========================
# ROTA PRINCIPAL (TESTE)
# ==========================
@app.route("/")
def home():
    return "Webhook Mercado Pago ONLINE", 200


# ==========================
# WEBHOOK MERCADO PAGO
# ==========================
@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    # 👉 Mercado Pago faz GET no teste
    if request.method == "GET":
        return "Webhook Mercado Pago OK", 200

    # 👉 Notificação real (POST)
    data = request.json
    print("📩 Webhook recebido:", data)

    if not data:
        return jsonify({"error": "sem dados"}), 400

    # Evento de pagamento
    if data.get("type") == "payment":
        payment_id = data["data"]["id"]
        confirmar_pagamento(payment_id)

    return jsonify({"status": "ok"}), 200


# ==========================
# CONFIRMAR PAGAMENTO
# ==========================
def confirmar_pagamento(payment_id):
    url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    response = requests.get(url, headers=headers)
    payment = response.json()

    print("💰 Pagamento:", payment)

    status = payment.get("status")

    if status == "approved":
        print("✅ PAGAMENTO APROVADO")
        # aqui você pode:
        # - liberar créditos
        # - avisar Telegram
        # - salvar no banco
    else:
        print("⏳ Status:", status)


# ==========================
# START
# ==========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)