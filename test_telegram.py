import telebot


bot = telebot.TeleBot('5530513392:AAG89CLkxSe_ytQvCMTJQZOfRF-NqbOov4A')

# Функция, обрабатывающая команду /start
@bot.message_handler(commands=["start"])
def start(m, res=False):
    bot.send_message(m.chat.id, 'Я на связи. Пришлю информацию по просроченным поставкам )')
    file = open("chats_ud.txt", "a")
    file.write(str(m.chat.id)+'\n')
    file.close()

    
# Запускаем бота
bot.polling(none_stop=True, interval=10)