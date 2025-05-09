from aiogram.filters import CommandStart
from dotenv import load_dotenv
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F #html
from aiogram.filters.command import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, CallbackQuery, message_id
from handlers_for_user import userhandlers
from handlers_for_admin import adminshandlers
from db.db import PostgresBase
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

load_dotenv()

selected_subject = None
# Объект
operator = 0
bot = Bot(
    token= os.getenv('TG_API'),
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)
# Диспетчер
dp = Dispatcher()
dp.include_routers(userhandlers.router, adminshandlers.router)

async def answer_documents(file_path, message: types.Message):
        nice = await message.answer_document(
            document=types.FSInputFile(path=file_path))
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await asyncio.sleep(1200)
        try:
            await nice.delete()
        except Exception as e:
            pass



# Запуск процесса поллинга новых апдейто
async def main():
    try:
        await dp.start_polling(bot)
    finally:
        sqlbase_run = PostgresBase()
        await sqlbase_run.connect()
        await sqlbase_run.execute_query('''UPDATE administration_table SET login_for_admin = $1''', (False,))
        await sqlbase_run.connect_close()

if __name__ == "__main__":
    asyncio.run(main())
