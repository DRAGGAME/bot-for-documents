import os

# from dotenv import load_dotenv
# load_dotenv()

TG_API = os.getenv('TG_API')
PG_HOST = os.getenv('ip')
PG_USER = os.getenv('user')
PG_PASSWORD = os.getenv('password')
PG_DATABASE = os.getenv('DATABASE')

tg_forw_docx = os.getenv('id_chat')
tg_forw_report = os.getenv('id_chat_reports')