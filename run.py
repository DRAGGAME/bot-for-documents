import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F #html
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import TG_API
from handlers_for_user import userhandlers, add_docx_user, reports
from handlers_for_admin import adminshandlers
from db.db import PostgresBase

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TG_API, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

#
# Диспетчер
dp = Dispatcher()
dp.include_routers(userhandlers.router_search, adminshandlers.router, add_docx_user.router_add_docx, reports.router_report)

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
