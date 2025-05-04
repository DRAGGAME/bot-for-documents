
import pytest
from db.db import PostgresBase

@pytest.mark.asyncio
async def test_connect():
    db = PostgresBase()
    result_for_connect = await db.connect()
    result_select = await db.execute_query('''SELECT documents FROM tests ORDER BY documents ASC''')
    result_create_document = await db.create_user_documents_table()
    result_create_item = await db.create_item_table()
    await db.execute_query('''DROP TABLE user_documents''')
    await db.execute_query('''DROP TABLE item''')
    result_close = await db.connect_close()
