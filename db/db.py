import asyncio
import logging

import asyncpg
import os

from aiogram.fsm.scene import After
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
pg_host = os.getenv('ip')
pg_user = os.getenv('user')
pg_password = os.getenv('password')
pg_database = os.getenv('DATABASE')
api_tg = os.getenv('TG_API')

class PostgresBase:

    def __init__(self):
        """Инициализация начальных переменных"""
        self.pool = None

    async def connect(self) -> None:
        try:
            self.pool = await asyncpg.create_pool(
                host=pg_host,
                user=pg_user,
                password=pg_password,
                database=pg_database,
                min_size=1,
                max_size=10000
            )
        except asyncpg.PostgresError as e:
            raise f"Ошибка подключения к базе данных: {e}"

    async def connect_close(self) -> None:
        try:
            if self.pool:
                await self.pool.close()
        except asyncpg.PostgresError as e:
            raise f"Ошибка закрытия подключения к базе данных: {e}"

    async def execute_query(self, query: str, params=None) -> tuple:
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                if params:
                    return await connection.fetch(query, *params)
                return await connection.fetch(query)

    async def create_user_documents_table(self):
        await self.execute_query('''CREATE TABLE IF NOT EXISTS user_documents 
        (
        Id SERIAL PRIMARY KEY,
        Data_time TEXT,
        User_id INT,
        User_name TEXT,
        Documents_name TEXT,
        Documents_class TEXT,
        Documents_group TEXT,
        Documents_type TEXT,
        Documents_id TEXT
        );''')

    async def create_item_table(self):
        await self.execute_query('''CREATE TABLE IF NOT EXISTS item 
        (
        Id SERIAL PRIMARY KEY,
        Item TEXT
        );''')

    async def administration_table(self):
        await self.execute_query('''CREATE TABLE IF NOT EXISTS administration_table
        (
        Id SERIAL PRIMARY KEY,
        Login TEXT,
        Password TEXT,
        Login_for_admin BOOLEAN
        );''')
        await self.execute_query('''INSERT into administration_table (login, password, login_for_admin) 
                                    VALUES ($1, $2, $3)''',
                                 ('12345', '12345', False)
                                 )

if __name__ == '__main__':
    async def post():
        postes = PostgresBase()
        res = await postes.connect()
        result_create_document = await postes.create_user_documents_table()
        await postes.administration_table()
        print(result_create_document)
        if not result_create_document:
            assert result_create_document is None
    asyncio.run(post())
