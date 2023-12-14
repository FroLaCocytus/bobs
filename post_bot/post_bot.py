from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import Text
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import asyncpg
import asyncio

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_CHAT_ID = os.getenv('CHANNEL_CHAT_ID')
NAME_GROUP = os.getenv('NAME_GROUP')
ADMINS = set(os.getenv('ADMINS').split(','))
LINK_CLIENT_BOT = os.getenv('LINK_CLIENT_BOT')
DB_NAME = os.getenv('DB_NAME') 
DB_USER = os.getenv('DB_USER') 
DB_PASSWORD = os.getenv('DB_PASSWORD') 
DB_HOST = os.getenv('DB_HOST') 


bot = Bot(token=TOKEN)

# Создаем экземпляр MemoryStorage
storage = MemoryStorage()
# Используем MemoryStorage в диспетчере
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

class PostForm(StatesGroup):
    photo = State()  # Будет хранить фото
    text = State()  # Будет хранить текст

# Глобальная переменная для подключения к базе данных
db_pool = None

# Инициализация БД
async def init_db():
    global db_pool
    # Здесь должны быть данные для подключения к вашей базе данных
    db_pool = await asyncpg.create_pool(database=DB_NAME, 
                                        user=DB_USER, 
                                        password=DB_PASSWORD, 
                                        host=DB_HOST)

# Функция для добавления ссылки в базу данных
async def save_post_link(post_link):
    async with db_pool.acquire() as connection:
        await connection.execute(
            'INSERT INTO posts (url) VALUES ($1);',
            post_link
        )

# Проверка пользователя в списке разрешенных
def is_user_allowed(username):
    return username in ADMINS

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    if not is_user_allowed(message.from_user.username):
        await message.answer("У вас нет доступа к этому боту!")
        return
    start_message = ("Привет, ты админ. Ты можешь добавлять посты в группу, используя комманду /post")
    await message.answer(start_message)

# Обработчик команды /post
@dp.message_handler(commands=['post'], state='*')
async def post_command(message: types.Message):
    if not is_user_allowed(message.from_user.username):
        await message.answer("У вас нет доступа к этому боту.")
        return
    await PostForm.photo.set()
    await message.reply("Пожалуйста, отправьте фотографию для поста.")

# Обработчик для неожиданного содержимого вместо фото
@dp.message_handler(lambda message: not message.photo, state=PostForm.photo)
async def handle_wrong_photo_input(message: types.Message):
    await message.reply("Это не похоже на фото. Пожалуйста, отправьте фотографию.")

# Обработчик получения фото
@dp.message_handler(content_types=['photo'], state=PostForm.photo)
async def handle_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['photo'] = message.photo[-1].file_id  # Сохраняем file_id самой большой версии фото
    await PostForm.next()
    await message.reply("Теперь отправьте текст для поста.")

# Обработчик для неожиданного содержимого вместо текста
@dp.message_handler(lambda message: message.content_type != 'text', state=PostForm.text)
async def handle_wrong_text_input(message: types.Message):
    await message.reply("Это не похоже на текст. Пожалуйста, отправьте текст поста.")

# Обработчик получения текста
@dp.message_handler(state=PostForm.text)
async def handle_text(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['text'] = message.text

    # Получаем данные о фото
    user_data = await state.get_data()
    photo_id = user_data['photo']
    text = user_data['text']

    # Создаем кнопку с ссылкой
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('➕', url=LINK_CLIENT_BOT))

    # Отправляем запись в канал
    sent_message = await bot.send_photo(CHANNEL_CHAT_ID, photo=photo_id, caption=text, reply_markup=keyboard)
    await message.reply("Запись была опубликована в канале.")

    # Формируем ссылку на сообщение
    post_link = f"https://t.me/{NAME_GROUP}/{sent_message.message_id}"

    # Сохраняем ссылку в базу данных
    await save_post_link(post_link)

    # Завершаем состояние
    await state.finish()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())
    executor.start_polling(dp, loop=loop)
