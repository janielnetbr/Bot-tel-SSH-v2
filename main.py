from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters
from telegram import ChatAction
from telegram import Bot, ParseMode
import requests
import paramiko
import logging
import random
import string
import time
import sqlite3
import os
import threading
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = '' #TOKEN DO SEU BOT DO TELEGRAM


conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

# Criando a tabela de usuários se ela não existir
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        last_test_timestamp REAL
    )
''')
conn.commit()

def start(update: Update, context: CallbackContext) -> None:
    user_name = update.message.from_user.first_name
    link_referencias = "<a href='https://t.me/ntsreferencias'>REFERÊNCIAS📌</a>"# link clicável de referência
    link_site = "<a href='https://ntsoff1.000webhostapp.com'>COMPRAR ACESSO VIP👤</a>"# link clicável do site
    start_message = f"Olá {user_name}, Seja bem-vindo!\n\n" \
                   f"APP PARA USAR O TESTE SSH📡 -> /apk\n\n" \
                   f"{link_referencias}\n\n{link_site}"
    
    keyboard = [
        [InlineKeyboardButton("GERAR TESTE SSH 🤖", callback_data="generate_ssh_test")], # botão de gera teste ssh
        [InlineKeyboardButton("BOT DO WHATS", url="http://wa.me/+5575991044171")],# botão de bot do whatsapp ou seu whats
        [InlineKeyboardButton("SUPORTE ⚙️", url="https://t.me/ntsoff1kytbr")],# botão do seu perfil do telegram
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_photo(photo="https://ntsoff1.000webhostapp.com/Capture%202022-05-20%2001.14.26_105203.jpg", # imagem do começo
                               caption=start_message, parse_mode="HTML", reply_markup=reply_markup)


def menu(update: Update, context: CallbackContext) -> None:
    keyboard = [
        #[InlineKeyboardButton("GERAR TESTE SSH 🤖", callback_data="generate_ssh_test")],
        #[InlineKeyboardButton("REFERÊNCIAS📌", url="https://t.me/ntsreferencias")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Escolha uma opção:", reply_markup=reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    if query.data == "menu":
        menu(update, context)
    elif query.data == "generate_ssh_test":
        generate_ssh_test(update, context)
    query.answer()

def generate_ssh_test(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Check last test timestamp in user_data dictionary
    user_data = context.user_data
    if user_id in user_data and time.time() - user_data[user_id]['timestamp'] < 7 * 24 * 60 * 60:
        error_message = update.callback_query.message.reply_text("⚠️ OPA VOCÊ JÁ SOLICITOU UM TESTE\nAGUARDE 7 DIAS E PEÇA UM NOVO TESTE\n\nCOMPRAR ACESSO VIP @ntsoff1kytbr")
        def remove_error_message():
            error_message.delete()
        timer = threading.Timer(10, remove_error_message)
        timer.start()
    else:
        try:
            # Generate random username and password
            random_username = f"teste{''.join(random.choices(string.ascii_lowercase, k=5))}"
            random_password = ''.join(random.choices(string.digits, k=6))

            # Store the generated credentials and timestamp
            user_data[user_id] = {'username': random_username, 'password': random_password, 'timestamp': time.time()}

            # Connect to the SSH server
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect('51.222.150.100', username='root', password='3LEv6tCmcyoOc', port=22, timeout=10)

            # Execute commands to create new SSH user
            create_user_command = f"sudo useradd -m -e $(date -d '+1 day' '+%Y-%m-%d') {random_username} -p $(openssl passwd -1 {random_password})"
            stdin, stdout, stderr = ssh.exec_command(create_user_command)

            ssh_test_info = (
                f"⚠️ TESTE GERADO COM SUCESSO! ⚠️\n\n"
                f"👤 USUÁRIO: <code>{random_username}</code>\n"
                f"🔒 SENHA: <code><pre>{random_password}</pre></code>\n"
                f"⏳ EXPIRA EM: 1 DIA\n"
                f"️📂 BAIXAR APP  /apk"
            )
            update.callback_query.message.reply_text(ssh_test_info, parse_mode='HTML')

            ssh.close()

            # Agendando a exclusão do teste após 2 minutos
            context.job_queue.run_once(delete_ssh_test, 120, context=user_id)

        except paramiko.AuthenticationException:
            update.callback_query.message.reply_text("Erro de autenticação ao se conectar ao servidor SSH.")
        except paramiko.SSHException as e:
            update.callback_query.message.reply_text(f"Erro SSH: {e}")
        except Exception as e:
            update.callback_query.message.reply_text(f"Erro ao gerar informações de teste SSH: {e}")

def delete_ssh_test(context: CallbackContext) -> None:
    user_id = context.job.context
    user_data = context.user_data
    if user_id in user_data:
        # Realize a ação necessária para excluir o teste (por exemplo, conectar ao servidor e remover o usuário)
        del user_data[user_id]

def doa(update: Update, context: CallbackContext) -> None:
    text = " ".join(context.args)
    update.message.reply_text(f"CHAVE PIX 🔑 EMAIL ABAIXO\nPARA DOAÇÕES 😀\n\n ntsoff1k@gmail.com: {text}") #sua chave pix aqui

ultimo_pedido1 = {}

def enviar_apk(update, context):
    user_id = update.message.from_user.id

    # Verificar se o usuário já fez uma solicitação nas últimas 30 minutos
    if user_id in ultimo_pedido1 and time.time() - ultimo_pedido1[user_id] < 1800:
        mensagem_espera = update.message.reply_text("Você já solicitou o APK recentemente. Por favor, aguarde um pouco antes de solicitar novamente.")
        # Agendar a remoção da mensagem após 25 segundos
        def remover_mensagem_espera():
            mensagem_espera.delete()
        timer_mensagem_espera = threading.Timer(25, remover_mensagem_espera)
        timer_mensagem_espera.start()
        return

    # Registrar o tempo da solicitação atual
    ultimo_pedido1[user_id] = time.time()

    # Enviar a mensagem inicial para o usuário
    mensagem_enviando = update.message.reply_text("Enviando arquivo 📁. Por favor, aguarde... 📌", parse_mode='HTML')

    # Agendar a remoção da mensagem após 5 segundos
    def remover_mensagem():
        mensagem_enviando.delete()

    timer = threading.Timer(6, remover_mensagem)
    timer.start()

    apk_url = 'https://nts4g.000webhostapp.com/CAIXA_VIP.apk'  # URL correto do seu app aqui

    try:
        # Baixar o arquivo APK do URL
        response = requests.get(apk_url)
        if response.status_code == 200:
            local_file_path = '/tmp/CAIXA_VIP.apk'  # Caminho temporário local para armazenar o arquivo

            with open(local_file_path, 'wb') as apk_file:
                apk_file.write(response.content)

            with open(local_file_path, 'rb') as apk_file:
                update.message.reply_document(document=apk_file, filename='CAIXA_VIP.apk')

            # Limpar o arquivo local temporário
            os.remove(local_file_path)
        else:
            update.message.reply_text("Ocorreu um erro ao baixar o arquivo.")

    except Exception as e:
        print("Erro:", str(e))
        update.message.reply_text("Ocorreu um erro ao enviar o arquivo.")

ultimo_pedido = {}

def enviar_apk2(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    # Verificar se o usuário já fez uma solicitação nas últimas 30 minutos
    if user_id in ultimo_pedido and time.time() - ultimo_pedido[user_id] < 1800:
        mensagem_espera = update.message.reply_text("Você já solicitou o APK recentemente. Por favor, aguarde um pouco antes de solicitar novamente.")
        # Agendar a remoção da mensagem após 25 segundos
        def remover_mensagem_espera():
            mensagem_espera.delete()
        timer_mensagem_espera = threading.Timer(25, remover_mensagem_espera)
        timer_mensagem_espera.start()
        return

    # Registrar o tempo da solicitação atual
    ultimo_pedido[user_id] = time.time()

    # Enviar a mensagem inicial para o usuário
    mensagem_enviando = update.message.reply_text("Enviando arquivo 📁. Por favor, aguarde... 📌", parse_mode='HTML')

    # Agendar a remoção da mensagem após 5 segundos
    def remover_mensagem():
        mensagem_enviando.delete()

    timer = threading.Timer(6, remover_mensagem)
    timer.start()

    apk_url = 'https://nts4g.000webhostapp.com/FOGO_VPN.apk'  # URL correto do APK

    try:
        # Baixar o arquivo APK do URL
        response = requests.get(apk_url)
        if response.status_code == 200:
            local_file_path = '/tmp/FOGO_VPN.apk'  # Caminho temporário local para armazenar o arquivo

            with open(local_file_path, 'wb') as apk_file:
                apk_file.write(response.content)

            # Mensagem a ser enviada antes do APK
            mensagem_personalizada = "⚙️ 𝑂 𝐴𝑃𝑃 𝑁𝐴̃𝑂 𝑃𝑅𝐸𝐶𝐼𝑆𝐴 𝐶𝑂𝐿𝑂𝐶𝐴𝑅 𝑁𝐸𝑀 🔐𝑆𝐸𝑁𝐻𝐴 𝐸 𝑁𝐸𝑀 👤𝑈𝑆𝑈𝐴́𝑅𝐼𝑂\n🗃️ 𝐸𝑁𝑉𝐼𝐴𝑁𝐷𝑂 𝐴𝐺𝑈𝐴𝑅𝐷𝐸 𝑂 𝐴𝑃𝑃"
            mensagem_enviada = update.message.reply_text(mensagem_personalizada)

            # Agendar a remoção da mensagem personalizada após 10 segundos
            def remover_mensagem_personalizada():
                mensagem_enviada.delete()
            timer_mensagem_personalizada = threading.Timer(20, remover_mensagem_personalizada)
            timer_mensagem_personalizada.start()

            with open(local_file_path, 'rb') as apk_file:
                update.message.reply_document(document=apk_file, filename='FOGO_VPN.apk')

            # Limpar o arquivo local temporário
            os.remove(local_file_path)
        else:
            update.message.reply_text("Ocorreu um erro ao baixar o arquivo.")

    except Exception as e:
        print("Erro:", str(e))
        update.message.reply_text("Ocorreu um erro ao enviar o arquivo.")

def main() -> None:
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("menu", start))
    dp.add_handler(CommandHandler("doa", doa))
    dp.add_handler(CommandHandler("apk", enviar_apk))
    dp.add_handler(CommandHandler("fogo_vpn", enviar_apk2))
    dp.add_handler(CallbackQueryHandler(button))
    
    updater.start_polling()
    updater.idle()

    conn.close()

if __name__ == "__main__":
    main()
