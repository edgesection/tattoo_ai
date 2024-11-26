import json
import time
import base64

import requests

from random import randint as r
from random import choice as ch

import os

import time

import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from threading import Thread

import sqlite3

users = dict()

api = 'edgesection'

connection = sqlite3.connect('edgesection.db')
cursor = connection.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
id INTEGER PRIMARY KEY,
telegram_id_user INTEGER NOT NULL,
last_active TEXT NOT NULL,
amount_generation INTEGER
)
''')

connection.commit()

def check_user(id_user):
    cursor.execute(f'SELECT * FROM Users WHERE `telegram_id_user` = {id_user}')
    users = cursor.fetchall()

    if len(users) <= 0:
        cursor.execute(f'INSERT INTO Users (`telegram_id_user`, `last_active`, `amount_generation`) VALUES ({id_user}, {int(time.time())}, 0)')
    else:
        cursor.execute(f'UPDATE Users SET `last_active` = {int(time.time())} WHERE `telegram_id_user` = {id_user}')
    
    connection.commit()


''''''
''''''
''''''
class Text2ImageAPI:

    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }

    def generation(self, prompt, uid, attempts=18, delay=10):
    
        #Получаем модель
        response_get_model = requests.get(self.URL + 'key/api/v1/models', headers=self.AUTH_HEADERS).json()
        print('[', uid,'] Получение модели: ', response_get_model)
        response_get_model = response_get_model[0]['id']
        
        #Генерируем
        params_gen = {
            "type": "GENERATE",
            "numImages": 1, #Кол-во изображений
            "width": 1024, #Ширина изображения
            "height": 1024, #Высота изображения
            "generateParams": {
                "query": f"{prompt}"
            }
        }

        data_gen = {
            'model_id': (None, response_get_model),
            'params': (None, json.dumps(params_gen), 'application/json')
        }
        response_gen = requests.post(self.URL + 'key/api/v1/text2image/run', headers=self.AUTH_HEADERS, files=data_gen).json()
        approximate_time = response_gen['status_time']
        requests.get(f"https://api.telegram.org/bot7171127112:AAEs8ZomragSltS9BJHFYUwJI8NyxgzN49A/sendMessage?chat_id={uid}&text=Время ожидания: {approximate_time}сек.").json()
        print('[', uid,'] Получение ответа при генерации: ', response_gen)
        response_gen = response_gen['uuid']
        
        #Получаем
        while attempts > 0:
            response = requests.get(self.URL + 'key/api/v1/text2image/status/' + response_gen, headers=self.AUTH_HEADERS)
            data = response.json()
            if data['status'] == 'DONE':
                print('Картинка для пользователя ', uid, ' сгенерирована (время ожидания - ', str(approximate_time),'сек., прошло времени: ', str(180-(attempts*10)) ,'сек.)')
                image_base64 = data['images'][0]
                # Декодируем строку base64 в бинарные данные
                image_data = base64.b64decode(image_base64)

                nameimage = f"{uid}_{int(time.time())}_{r(0, 100000)}.jpg"

                # Открываем файл для записи бинарных данных изображения
                try:
                    with open(nameimage, "wb") as file:
                        file.write(image_data)
                except:
                    with open(nameimage, "w+") as file:
                        file.write(image_data)
                        
                document = open(nameimage, 'rb')
                
                url = f"https://api.telegram.org/bot7171127112:AAEs8ZomragSltS9BJHFYUwJI8NyxgzN49A/sendDocument"
                response = requests.post(url, data={'chat_id': uid}, files={'document': document})
                
                print("Удаляем сгенерированную картинку пользователя ", uid," с директории")
 
                document.close()
                if os.path.exists(nameimage):
                    os.remove(nameimage)
                
                keyboard = json.dumps({
                "inline_keyboard": [
                        [
                            {
                                "text": "Записаться",
                                "callback_data": "1"
                            },
                            {
                                "text": "Генерация тату",
                                "callback_data": "2"
                            }
                        ]
                    ]
                })

                reply_markup = keyboard

                requests.get(f"https://api.telegram.org/bot7171127112:AAEs8ZomragSltS9BJHFYUwJI8NyxgzN49A/sendMessage?chat_id={uid}&text=Твоё тату готово&reply_markup={reply_markup}").json()
                try:
                    del users[uid]
                except:
                    print("Ошибка при удалении пользователя, после генерации картинки (возможно он уже удалён - происходит при более одной одновременной генерации с одного аккаунта)")
                return data['images']
                
            elif data['status'] == 'INITIAL':
                print('Картинка пользователя ', uid, ' ещё генерируется (время ожидания - ', str(approximate_time),'сек., прошло времени: ', str(180-(attempts*10)) ,'сек.)')

            attempts -= 1
            time.sleep(delay)
''''''
''''''
''''''
api = Text2ImageAPI('https://api-key.fusionbrain.ai/', '528FF82D360D2904B0EDE44217897E12', '126D509D9FD7B21EAB751B31621CCA83')

def kar_generate(promt_text, user_id):
    dirr = "res"
    prom = "чёрно-белое тату "+promt_text
    cursor.execute(f'UPDATE Users SET `amount_generation` = `amount_generation` + 1 WHERE `telegram_id_user` = {user_id}')
    connection.commit()
    th = Thread(target=api.generation, args=(prom, user_id,))
    th.start()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    check_user(update.message.from_user.id)
    
    """Sends a message with three inline buttons attached."""
    keyboard = [
        [
            InlineKeyboardButton("Записаться", callback_data="1"),
        ],
        [
            InlineKeyboardButton("Генерация тату", callback_data="2")
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    user = update.effective_user
    
    await update.message.reply_html(rf"Привет {user.mention_html()}!. Мы тату-салон Skin's Secret. Выбери что ты хочешь, нажав нужную кнопку:", reply_markup=reply_markup)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with three inline buttons attached."""
    keyboard = [
        [
            InlineKeyboardButton("Назад", callback_data="3"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    cursor.execute(f'SELECT COUNT(*) AS count, SUM(amount_generation) AS sum FROM Users')
    amount_all_users = cursor.fetchall()

    await update.message.reply_html(f"Всего пользователей: {amount_all_users[0][0]}\nВсего генераций: {amount_all_users[0][1]}\nАктивных пользователей: {len(users)}", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    check_user(update.callback_query.from_user.id)

    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    if query.data == "1":
        keyboard = [
            [
                InlineKeyboardButton("Отмена", callback_data="3"),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=f"Через несколько минут с вами свяжется менеджер", reply_markup=reply_markup)
    elif query.data == "2":
        users[update.callback_query.from_user.id] = 'generate'
        await query.edit_message_text(text=f"Введите ваш образ")
    elif query.data == "3":
        keyboard = [
            [
                InlineKeyboardButton("Записаться", callback_data="1"),
            ],
            [
                InlineKeyboardButton("Генерация тату", callback_data="2")
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=f"Заявка отменена", reply_markup=reply_markup)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    check_user(update.message.from_user.id)

    """Echo the user message."""
    if len(users) > 0:
        print("Все пользователи [1]:")
        print(users)
        if users[update.message.from_user.id] == 'generate':
            users[update.message.from_user.id] = "generating"
            print("Пользователи, которым генерируется картинка [2]:")
            print(users)
            await update.message.reply_text("Идёт генерация тату...")
            kar_generate(update.message.text, update.message.from_user.id)
            

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("7171127112:AAEs8ZomragSltS9BJHFYUwJI8NyxgzN49A").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CallbackQueryHandler(button))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
