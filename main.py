import logging
import json
import openai
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
GEN_TEXT = 0
GEN_IMG = 1
messagesByUserId = {}
usersStatus = {}
usersPending = {}
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    intro = "/gen_text - Dân hỏi bộ trưởng trả lời\n/gen_img - Tưởng tượng ra ảnh"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=intro)
    
async def select_gen_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mess = "Hỏi gì hỏi nhanh đi!"
    usersStatus[update.effective_chat.id] = GEN_TEXT
    await context.bot.send_message(chat_id=update.effective_chat.id, text=mess)
    
async def select_gen_img(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mess = "Mô tả ảnh đi!"
    usersStatus[update.effective_chat.id] = GEN_IMG
    await context.bot.send_message(chat_id=update.effective_chat.id, text=mess)
    
async def handleMess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global usersPending, usersStatus, messagesByUserId
    userId = update.effective_chat.id
    print(usersPending)
    if (userId in usersPending and usersPending[userId] == 1):
        await context.bot.send_message(chat_id=userId, text= "Chờ tí đi, câu trước còn đang nghĩ chưa trả lời xong mà :((")
        return
    usersPending[userId] = 1
    status = GEN_TEXT
    if (userId in usersStatus):
        status = usersStatus[userId]
    if (status == GEN_IMG):
        await gen_img(userId, update.message.text, context)
    else:
        await gen_text(userId, update.message.text, context)
    usersPending[userId] = 0
    del usersPending[userId]
    
async def gen_text(userId, user_message, context: ContextTypes.DEFAULT_TYPE):
    messages = []
    if (not userId in messagesByUserId):
        messages = []
        messagesByUserId[userId] = messages
    else:
        messages = messagesByUserId[userId]
    messages.append({
        "role": "user",
        "content": user_message
    })
    responseText = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    newMessage = responseText.choices[0].message
    messages.append({
        "role": newMessage.role,
        "content": newMessage.content
    })
    await context.bot.send_message(chat_id=userId, text = newMessage.content)
    if (len(messages) > 20):
        messages.pop(0)
        messages.pop(0)
    
async def gen_img(userId, user_message, context: ContextTypes.DEFAULT_TYPE):
    response = openai.Image.create(
        prompt=user_message,
        n=1,
        size="1024x1024"
    )
    await context.bot.send_photo(chat_id=userId, photo = response['data'][0]['url'])

if __name__ == '__main__':
    openai.api_key = "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"
    application = ApplicationBuilder().token('6068277181:AAGVmQYR4rRB0zRk-jsDNryusVMiCRKSlCQ').build()
    
    mess_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handleMess)
    start_handler = CommandHandler('start', start)
    select_text_handler = CommandHandler('gen_text', select_gen_text)
    select_img_handler = CommandHandler('gen_img', select_gen_img)
    application.add_handler(start_handler)
    application.add_handler(mess_handler)
    application.add_handler(select_text_handler)
    application.add_handler(select_img_handler)
    
    application.run_polling()