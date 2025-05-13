from db.db import PostgresBase


class DbForDocx(PostgresBase):

    async def insert_data(self, data_time: str, user_id: int, user_name: str, documents_name: str,
                          documents_group: str, documents_class: str, documents_type: str, documents_id: str) -> None:
        await self.execute_query(
            '''INSERT INTO user_documents (data_time, user_id, user_name, 
               documents_name, documents_group, documents_class, documents_type, documents_id)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)''',
            (
                data_time,
                user_id,
                user_name,
                documents_name,
                documents_class,
                documents_group,
                documents_type,
                documents_id
                )
            )