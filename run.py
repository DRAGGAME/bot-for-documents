from aiogram.filters import CommandStart
# from dotenv import load_dotenv
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F #html
from aiogram.filters.command import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, CallbackQuery, message_id
from handlers_for_user import userhandlers, add_docx_user
from handlers_for_admin import adminshandlers
from db.db import PostgresBase

from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# load_dotenv()
# Объект
bot = Bot(
    token= os.getenv('TG_API'),
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)
# Диспетчер
dp = Dispatcher()
dp.include_routers(userhandlers.router_search, adminshandlers.router, add_docx_user.router_add_docx)

# Запуск процесса поллинга новых апдейто
async def main():
    try:
        sqlbase_run = PostgresBase()
        await sqlbase_run.connect()
        await sqlbase_run.create_item_table()
        await sqlbase_run.create_user_documents_table()
        await sqlbase_run.administration_table()
        await sqlbase_run.connect_close()
        await dp.start_polling(bot)
    finally:
        sqlbase_run = PostgresBase()
        await sqlbase_run.connect()
        await sqlbase_run.execute_query('''UPDATE administration_table SET login_for_admin = $1''', (False,))
        await sqlbase_run.connect_close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
