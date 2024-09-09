import telebot
import config
 
from telebot import types
 
# Бот берет токен из файла config.py
bot = telebot.TeleBot(config.TOKEN)
 
 # Команда '/start'
@bot.message_handler(commands=['start'])
def welcome(message):
    sti = open('static/welcome.webp', 'rb')
    bot.send_sticker(message.chat.id, sti)
 
    # Клавиатура
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    start = types.KeyboardButton("Начать")

    markup.add(start)
 
    bot.send_message(message.chat.id, "Добро пожаловать, {0.first_name}!\nЯ - <b>{1.first_name}</b>, бот созданный чтобы ты смог быстро и удобно проверить расписание своих пар!".format(message.from_user, bot.get_me()),
        parse_mode='html', reply_markup=markup)

# Команда '/authors'
@bot.message_handler(commands=['authors'])
def authors(message):
    bot.send_message(message.chat.id, 'Authors:\nAlshov Vadim\nShirshov Alexander\nPugachev Nikita\nGanchev Dmitry\nThx for using this bot ❤️\nPowered by PYAN Inc. 2023.')
 
 # Чат с ботом
@bot.message_handler(content_types=['text'])
def lalala(message):
    if message.chat.type == 'private':
        if message.text == 'Начать':
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            group_1 = types.KeyboardButton("ИД 23.1/Б3-21")
            markup.add(group_1)
            bot.send_message(message.chat.id, 'Выбери свою группу', reply_markup=markup)

        elif message.text == 'ИД 23.1/Б3-21':
            bot.send_message(message.chat.id, 'Бот временно не работает 😥')

        else:
            bot.send_message(message.chat.id, 'Воспользуйтесь всплывающей клавиатурой бота, пожалуйста, или в случае, если вы только создаёте запрос, нажмите "/start"')

# Запуск
bot.polling(none_stop=True)