import logging
import io
import re
import requests
from collections import defaultdict
from datetime import datetime
from telegram import Update, Document
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from openpyxl import load_workbook, Workbook

# ---------------------
# Configuração de logs
# ---------------------
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = "7705145588:AAH4M5dLssaqgB8Uwp4UXBL0eG4wEPrsUT0"

# ---------------------
# Funções auxiliares
# ---------------------
def consultar_cep(cep):
    cep = str(cep).replace("-", "").strip()
    if not cep.isdigit() or len(cep) != 8:
        return None
    url = f"https://opencep.com/v1/{cep}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("logradouro")
    except Exception as e:
        logging.warning(f"Erro consultando CEP {cep}: {e}")
    return None

def extrair_chave(endereco: str):
    endereco = endereco.strip()
    match = re.match(r"(.+?)(\d+)", endereco)
    if match:
        logradouro = match.group(1).strip().lower()
        numero = match.group(2)
        return f"{logradouro}|{numero}"
    return endereco.lower()

def corrigir_planilha(file_bytes):
    wb = load_workbook(io.BytesIO(file_bytes))
    ws = wb.active

    headers = [cell.value for cell in ws[1]]

    # Remove colunas indesejadas
    colunas_remover = ["AT ID", "Stop", "SPX TN"]
    for col in reversed(range(1, len(headers) + 1)):
        if headers[col - 1] in colunas_remover:
            ws.delete_cols(col)

    # Atualiza índices
    headers = [cell.value for cell in ws[1]]
    idx_seq = headers.index("Sequence") + 1
    idx_dest = headers.index("Destination Address") + 1
    idx_cep = headers.index("Zipcode/Postal code") + 1

    # Corrige endereços pelo CEP
    for row in range(2, ws.max_row + 1):
        cep = ws.cell(row=row, column=idx_cep).value
        endereco_original = str(ws.cell(row=row, column=idx_dest).value or "")
        logradouro_api = consultar_cep(cep)
        if logradouro_api:
            match = re.match(r"^[^\d]*", endereco_original.strip())
            if match:
                resto = endereco_original[len(match.group(0)):].strip(", ")
                novo_endereco = f"{logradouro_api}, {resto}" if resto else logradouro_api
                ws.cell(row=row, column=idx_dest, value=novo_endereco)

    # Agrupar por logradouro + número
    agrupado = defaultdict(list)
    dados_extra = {}
    for row in range(2, ws.max_row + 1):
        seq = str(ws.cell(row=row, column=idx_seq).value or "").strip()
        endereco = str(ws.cell(row=row, column=idx_dest).value or "").strip()
        if endereco:
            chave = extrair_chave(endereco)
            agrupado[chave].append(seq)
            if chave not in dados_extra:
                dados_extra[chave] = [
                    ws.cell(row=row, column=col).value for col in range(1, ws.max_column + 1)
                ]
                dados_extra[chave][headers.index("Destination Address")] = endereco

    # Criar nova planilha
    wb_novo = Workbook()
    ws_novo = wb_novo.active
    ws_novo.append(headers)

    for chave, seqs in agrupado.items():
        linha = dados_extra[chave][:]
        total = len(seqs)
        seq_final = ",".join(seqs)
        if total > 1:
            seq_final = f"{seq_final}; Total: {total} pacotes"
        linha[headers.index("Sequence")] = seq_final
        ws_novo.append(linha)

    output = io.BytesIO()
    wb_novo.save(output)
    output.seek(0)
    return output

# ---------------------
# Mensagem de saudação
# ---------------------
def saudacao():
    hora = datetime.now().hour
    if 5 <= hora < 12:
        return "Bom dia ☀️"
    elif 12 <= hora < 18:
        return "Boa tarde 🌤️"
    else:
        return "Boa noite 🌙"

# ---------------------
# Handler principal
# ---------------------
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document: Document = update.message.document
    user_name = update.message.from_user.first_name or "Usuário"
    logging.info(f"Recebida planilha de {user_name}")

    if document.mime_type != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        await update.message.reply_text("⚠️ Envie apenas arquivos Excel (.xlsx)")
        return

    # Saudação inicial
    await update.message.reply_text(
        f"{saudacao()}, {user_name}!\n\n📥 Estou aprimorando sua planilha, obrigado por aguardar. ⏳"
    )

    file = await context.bot.get_file(document.file_id)
    file_bytes = await file.download_as_bytearray()

    planilha_corrigida = corrigir_planilha(file_bytes)

    # Nome do arquivo de saída
    hoje = datetime.now().strftime("%d-%m-%Y")
    nome_completo = (update.message.from_user.full_name or user_name).upper()
    filename = f"Rota-Atualizada-{hoje} {nome_completo}.xlsx"

    # Envia planilha
    await update.message.reply_document(document=planilha_corrigida, filename=filename)

    # Mensagem final
    await update.message.reply_text(
        f"✅ Sua planilha foi atualizada com sucesso, {user_name}!\n\n"
        "🎉 Tenha uma ótima rota!\n\n"
        "Se precisar de mim novamente, é só enviar a planilha por aqui. Estou sempre pronto para ajudar! 🤖"
    )

    logging.info(f"Planilha enviada para {user_name} como {filename}")

# ---------------------
# Inicialização do Bot
# ---------------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    logging.info("🤖 Bot iniciado e aguardando planilhas...")
    app.run_polling()

if __name__ == "__main__":
    main()
