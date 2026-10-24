import telebot
import sqlite3
from telebot import types

conn = sqlite3.connect("history.db", check_same_thread = False) #без понятия для чего check_same_thread
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS history ( 
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    mode TEXT,
    value REAL,
    result REAL
    )""")# создание таблицы - хранение истории в ней

with open("token.txt", "r", encoding = "utf8")as f:
    token = f.read().strip()
bot = telebot.TeleBot(token) #оставил токен в безопасном месте - в коде не спалится

direction = {} # словарь для запоминания мода конвертации. текст берется из кнопок, которые прописаны в factors 
factors = {"Км в мили": 1 / 1.609344, "Мили в км": 1.609344, "Кг в фунты": 2.20462, "Литры в галлоны": 0.264172} # <-
descrip = {
    "Км в мили": "миль",
    "Мили в км": "км",
    "Кг в фунты": "фунты",
    "Литры в галлоны": "галлоны"
}


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Привет! Нажми на кнопки, а после напиши число.")
    kb = types.ReplyKeyboardMarkup(resize_keyboard = True, row_width = 2) #создание кнопок. просто синтаксис
    kb.add(*factors)
    
    bot.send_message(message.chat.id, "Выбери, что переведем:", reply_markup=kb)


@bot.message_handler(commands=["history"])
def check_story(message):
    cur.execute("SELECT mode, value, result FROM history WHERE chat_id = ? ORDER BY id DESC LIMIT 5",
                (message.chat.id,))
    rows = cur.fetchall()

    if not rows:
        bot.send_message(message.chat.id, "История пока пустая")
        return

    total = ""
    for cid, (mode, num, result) in enumerate(rows,1): # cid - своя добавленная переменная, которая нужна просто для нумерации красивой
        total += f"{cid}) {mode}: {num} -> {result} {descrip[mode]}\n"
    bot.send_message(message.chat.id, total)


@bot.message_handler(commands=["clear"])
def clear_text(message):
    cur.execute("DELETE FROM history WHERE chat_id = ?",
                (message.chat.id,))
    bot.send_message(message.chat.id, "История запросов удалена.")
    conn.commit()



@bot.message_handler(content_types=["text"])
def converter(message):
    
    if message.text in factors:
        direction[message.chat.id] = message.text  #текст отправляется сюда и сохраняется - по нему будут выполняться операции
        bot.send_message(message.chat.id, "Отправь число")
        
    else:
        try: #блок try\except нужен только для точного ввода данных
            num = float(message.text)
            mode = direction.get(message.chat.id)
            if mode is None:
                bot.send_message(message.chat.id, "Выбери кнопку сначала.")
                return 0
            
            result = num * factors[mode]
                
            result = round(result,2)
            if result.is_integer():
                result = int(result)
                        
            bot.send_message(message.chat.id, f"{result} {descrip[mode]}")

            cur.execute("INSERT INTO history(chat_id, mode, value, result) VALUES (?,?,?,?)",
                        (message.chat.id, mode, num, result))
            conn.commit() 
        except ValueError:
            bot.send_message(message.chat.id, "Отправь число..")

bot.polling()
