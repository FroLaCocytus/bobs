import asyncio
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncpg
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Конфигурация бота и базы данных из переменных окружения
TOKEN = os.getenv('TELEGRAM_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Подключение к базе данных
async def create_db_pool():
    return await asyncpg.create_pool(DATABASE_URL)

# Функция для добавления записи в базу данных
async def add_record_to_db(pool, photo_url, text, link):
    async with pool.acquire() as connection:
        await connection.execute('INSERT INTO records (photo_url, text, link) VALUES ($1, $2, $3)', photo_url, text, link)

# Функция для отправки записи в группу
async def send_record_to_group(photo_url, text, link):
    keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton('Подробнее', url=link))
    await bot.send_photo(GROUP_CHAT_ID, photo=photo_url, caption=text, reply_markup=keyboard)

# Обработчик для команды /post
@dp.message_handler(commands=['post'])
async def post_record(message: types.Message):
    # Здесь должна быть логика получения данных для записи (фото, текст, ссылка)
    photo_url = 'URL_ФОТОГРАФИИ'
    text = 'ТЕКСТ СООБЩЕНИЯ'
    link = 'ССЫЛКА'

    # Добавляем запись в базу данных
    pool = await create_db_pool()
    await add_record_to_db(pool, photo_url, text, link)

    # Отправляем запись в группу
    await send_record_to_group(photo_url, text, link)
    await message.answer("Запись была опубликована в группе.")

# Главная функция
async def main():
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(main())
