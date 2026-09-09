from flask import Flask
from threading import Thread
import os

app_flask = Flask('')
@app_flask.route('/')
def home():
    return "Bot Global Activo!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)

Thread(target=run_flask).start()
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# TOKEN Y ADMIN - NO TOCAR
TOKEN = "8151031700:AAEmYKYcBmBjSahqdW43AsRDwqWwuquV4vM"
TU_ID_ADMIN = 8720063185

# ESTADOS DE LA CONVERSACION
ORIGEN, DESTINO, HORA = range(3)

# LOGS PARA VER ERRORES
logging.basicConfig(level=logging.INFO)

# TECLADOS DEL BOT
teclado_principal = ReplyKeyboardMarkup([["COTIZAR VIAJE", "TARIFAS"], ["CONTACTO", "AYUDA"]], resize_keyboard=True)
teclado_ubicacion = ReplyKeyboardMarkup([[KeyboardButton("Enviar mi ubicacion actual", request_location=True)], ["Escribir direccion manual"]], resize_keyboard=True, one_time_keyboard=True)
teclado_cancelar = ReplyKeyboardMarkup([["Cancelar"]], resize_keyboard=True)

# COMANDO START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("BIENVENIDO A COTIZADOR DIDI GLOBAL - 24/7\n\nServicio rapido, seguro y economico a nivel mundial.\n\nDisponible 24 horas\nLlegamos en minutos\nConductores verificados\n\nSelecciona una opcion:", reply_markup=teclado_principal)
    return ConversationHandler.END

# VER TARIFAS
async def tarifas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("TARIFAS GLOBALES\n\nTarifas justas segun distancia y ciudad. Dale a COTIZAR VIAJE y te cotizo en 1 minuto.", reply_markup=teclado_principal)

# CONTACTO
async def contacto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Contacto directo 24/7: @KISHIRIKAKISHIRIZURE", reply_markup=teclado_principal)

# AYUDA
async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("AYUDA: Dale a COTIZAR VIAJE y sigue los 3 pasos.", reply_markup=teclado_principal)

# INICIO COTIZACION
async def cotizar_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Vamos a cotizar tu viaje\n\nPaso 1 de 3: Donde te recogemos?\nManda tu ubicacion o escribe tu direccion completa con ciudad:", reply_markup=teclado_ubicacion)
    return ORIGEN

# RECIBIR ORIGEN
async def recibir_origen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text if update.message.text else ""
    if "Escribir direccion" in texto:
        await update.message.reply_text("Ok, escribe tu direccion completa, colonia y ciudad:", reply_markup=teclado_cancelar)
        return ORIGEN
    if update.message.location:
        lat = update.message.location.latitude
        lon = update.message.location.longitude
        context.user_data['origen'] = f"https://maps.google.com/?q={lat},{lon}"
        context.user_data['origen_texto'] = "Ubicacion GPS enviada"
    else:
        if len(texto) < 5:
            await update.message.reply_text("Escribe una direccion mas completa por favor:")
            return ORIGEN
        context.user_data['origen'] = texto
        context.user_data['origen_texto'] = texto
    await update.message.reply_text("Paso 2 de 3: A donde vas? Escribe destino completo y ciudad:", reply_markup=teclado_cancelar)
    return DESTINO

# RECIBIR DESTINO
async def recibir_destino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    if len(texto) < 5:
        await update.message.reply_text("Escribe un destino mas completo por favor:")
        return DESTINO
    context.user_data['destino'] = texto
    await update.message.reply_text("Paso 3 de 3: A que hora? Ej: Ahora mismo, 10:30pm, Manana 8am", reply_markup=teclado_cancelar)
    return HORA

# RECIBIR HORA Y ENVIAR A ADMIN
async def recibir_hora(update: Update, context: ContextTypes.DEFAULT_TYPE):
    origen = context.user_data.get('origen', 'No especificado')
    origen_texto = context.user_data.get('origen_texto', origen)
    destino = context.user_data.get('destino', 'No especificado')
    hora = update.message.text
    usuario = update.effective_user
    nombre = usuario.first_name or "Cliente"
    username = f"@{usuario.username}" if usuario.username else f"{nombre} (ID: {usuario.id})"
    mensaje_cliente = f"Solicitud Recibida {nombre}!\n\nOrigen: {origen_texto}\nDestino: {destino}\nHora: {hora}\n\nVerificando conductor cerca de ti. En 1 min te confirmo precio."
    await update.message.reply_text(mensaje_cliente, reply_markup=teclado_principal)
    texto_admin = f"NUEVA COTIZACION GLOBAL\n\nCliente: {nombre}\nUsuario: {username}\nID: {usuario.id}\n\nOrigen: {origen}\nDestino: {destino}\nHora: {hora}"
    try:
        await context.bot.send_message(chat_id=TU_ID_ADMIN, text=texto_admin)
    except Exception as e:
        print(f"Error admin: {e}")
    context.user_data.clear()
    return ConversationHandler.END

# CANCELAR
async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Cotizacion cancelada.", reply_markup=teclado_principal)
    return ConversationHandler.END

# INICIAR BOT
app = Application.builder().token(TOKEN).build()
conv = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^(COTIZAR VIAJE|/cotizar)$"), cotizar_inicio)],
    states={
        ORIGEN: [MessageHandler(filters.TEXT | filters.LOCATION, recibir_origen)],
        DESTINO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_destino)],
        HORA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_hora)],
    },
    fallbacks=[MessageHandler(filters.Regex("^Cancelar$"), cancelar), CommandHandler("cancelar", cancelar), CommandHandler("start", start)],
    allow_reentry=True
)
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Regex("^TARIFAS$"), tarifas))
app.add_handler(MessageHandler(filters.Regex("^CONTACTO$"), contacto))
app.add_handler(MessageHandler(filters.Regex("^AYUDA$"), ayuda))
app.add_handler(conv)
print("Bot GLOBAL iniciado")
app.run_polling(drop_pending_updates=True)
