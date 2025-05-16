import asyncio
import logging
import weakref
import asyncpg
from config import PG_HOST, PG_USER, PG_PASSWORD, PG_DATABASE

logging.basicConfig(level=logging.INFO)

pg_host = PG_HOST
pg_user = PG_USER
pg_password = PG_PASSWORD
pg_database = PG_DATABASE

class PostgresBase:

    _instances = weakref.WeakSet()

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
        User_id BIGINT,
        User_name TEXT,
        Documents_name TEXT,
        Documents_class TEXT,
        Documents_group TEXT,
        Documents_type TEXT,
        Documents_id TEXT
        );''')

    async def create_item_table(self):
        await self.execute_query('''
            CREATE TABLE IF NOT EXISTS item (
                Id SERIAL PRIMARY KEY,
                item TEXT UNIQUE,
                class_5 BOOLEAN DEFAULT FALSE,
                class_6 BOOLEAN DEFAULT FALSE,
                class_7 BOOLEAN DEFAULT FALSE,
                class_8 BOOLEAN DEFAULT FALSE,
                class_9 BOOLEAN DEFAULT FALSE,
                class_10 BOOLEAN DEFAULT FALSE,
                class_11 BOOLEAN DEFAULT FALSE,
                Enabling BOOLEAN DEFAULT FALSE
            );
        ''')

        await self.execute_query(
        '''
            INSERT INTO item (item, class_5, class_6, class_7, class_8, class_9, class_10, class_11, Enabling)
            VALUES
                ('Алгебра', FALSE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
                ('Геометрия', FALSE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
                ('Русский язык', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
                ('Немецкий язык', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
                ('Английский язык', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
                ('География', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
                ('Биология', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
                ('История', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
                ('Обществознание', FALSE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
                ('Литература', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
                ('Физика', FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
                ('Информатика', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
                ('Химия', FALSE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
                ('Математика', TRUE, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, TRUE)
            ON CONFLICT (item) DO NOTHING;
        '''
        )

    async def administration_table(self):
        await self.execute_query('''CREATE TABLE IF NOT EXISTS administration_table
        (
        Id SERIAL PRIMARY KEY,
        Login TEXT,
        Password TEXT,
        Login_for_admin BOOLEAN
        );''')
        login = await self.execute_query('''SELECT login_for_admin FROM administration_table''')
        if login:
            pass
        else:
            await self.execute_query('''INSERT into administration_table (login, password, login_for_admin) 
                                      VALUES ($1, $2, $3)''',
                                     ('12345', '12345', False)
                                    )

    async def item_begin(self, item: str, classes: dict) -> None:
        query = '''
            INSERT INTO item (item, class_5, class_6, class_7, class_8, class_9, class_10, class_11, enabling)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, FALSE)
            ON CONFLICT (item) DO NOTHING
        '''
        await self.execute_query(query, [
            item,
            classes.get('class_5', False),
            classes.get('class_6', False),
            classes.get('class_7', False),
            classes.get('class_8', False),
            classes.get('class_9', False),
            classes.get('class_10', False),
            classes.get('class_11', False),
        ])

    async def enable_report_subject(self, item: str) -> None:
        await self.execute_query('UPDATE item SET enabling = TRUE WHERE item = $1', [item])

    async def delete_report_subject(self, item: str) -> None:
        await self.execute_query('DELETE FROM item WHERE item = $1', [item])

    @classmethod
    async def close_all(cls):
        for instance in list(cls._instances):  # делаем list, чтобы избежать ошибок изменения во время итерации
            await instance.close()

if __name__ == '__main__':
    async def post():
        postes = PostgresBase()

        res = await postes.connect()
        result_create_document = await postes.create_item_table()
        await postes.administration_table()
        await PostgresBase.close_all()
        print(result_create_document)
        if not result_create_document:
            assert result_create_document is None
    asyncio.run(post())
