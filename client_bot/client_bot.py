from aiogram import Bot, Dispatcher, types, executor

TOKEN = '6870326309:AAG8t7rAxaFRCA1pc3trG35wNPHlUINAx9E'
ADMIN_USERNAME = 'Metallname'
admin_chat_id = None  # Сюда будет сохранен chat_id админа

# Создание экземпляра бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Создание клавиатуры
def main_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Новостройки", url="https://t.me/NedvijimostArmy/2"))
    keyboard.add(types.InlineKeyboardButton(text="Вторичная недвижимость", url="https://t.me/NedvijimostArmy/3"))
    return keyboard

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    global admin_chat_id
    if message.from_user.username == ADMIN_USERNAME:
        admin_chat_id = message.chat.id
        await bot.send_message(message.chat.id, f"Привет, Миха! У тебя будет свой интерфейс. Твой chat.id – {admin_chat_id}")
    else:
        await bot.send_message(message.chat.id, 'Выберите что вас интересует', reply_markup=main_keyboard())
        await bot.send_message(message.chat.id, "Добрый день! Наш администратор Михаил уже получил уведомление и сейчас подключится к диалогу 🙂")
        await bot.send_message(admin_chat_id, f'Пользователь – @{message.from_user.username} зашёл в твой бот')

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)