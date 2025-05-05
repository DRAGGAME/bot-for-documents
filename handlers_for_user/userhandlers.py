import io
import os
import re
from datetime import datetime
from pytz import timezone

import aiofiles
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import Bot, Router, types, F #html
from db.db import PostgresBase
import asyncio
load_dotenv()
router = Router()
sqlbase_user_handlers = PostgresBase()
kb_start = [[types.KeyboardButton(text="Добавить документ"), types.KeyboardButton(text='Найти презентацию')]]
keyboard = types.ReplyKeyboardMarkup(keyboard=kb_start, resize_keyboard=True, input_field_placeholder='Что вы хотите сделать?')

bot = Bot(token=os.getenv('TG_API'), parce_mode='MARKDOWN')

class AddDocs(StatesGroup):
    doc_name = State()
    doc_group = State()
    doc_type = State()
    doc_byt = State()

@router.message(CommandStart())
async def create_keyboard(message: Message):
    await message.answer('Что вы хотите сделать?', reply_markup=keyboard)

@router.message(F.text.lower().contains('добавить документ'))
async def add_docs(message: Message, state: FSMContext):
    items = []
    builder = ReplyKeyboardBuilder()
    await sqlbase_user_handlers.connect()
    items_tuple = await sqlbase_user_handlers.execute_query('''SELECT item FROM item ORDER BY id ASC''')
    for item in items_tuple:
        items.append(item[0].lower())
        builder.add(types.KeyboardButton(text=item[0]))
    items = tuple(items)
    print(items)
    builder.adjust(3)
    await state.update_data(items=items)
    await state.set_state(AddDocs.doc_group)
    await message.answer('К какому предмету относиться ваш документ?', reply_markup=builder.as_markup(resize_keyboard=True,
                                                                                                      input_field_placeholder='Выберите предмет'))

@router.message(F.text, AddDocs.doc_group)
async def docs_item(message: Message, state: FSMContext):
    data = await state.get_data()
    items = data.get('items')
    if message.text.lower() in items:
        await state.update_data(doc_group=message.text.lower())
        await message.answer('Отправьте файл')
        await state.set_state(AddDocs.doc_byt)
    else:
        await message.answer("Такого нет")

@router.message(F.document, AddDocs.doc_byt)
async def docs_name(message: Message, state: FSMContext):
    docs = message.document
    docs_info = await bot.get_file(docs.file_id)
    docs_path = docs_info.file_path
    docs_split_path = re.split(r'[./]', docs_path)
    file_name = f"{docs_split_path[-2]}.{docs_split_path[-1]}"
    await bot.download_file(docs_path, destination=file_name)
    print(f'{docs_path}\n{file_name}')
    create_bytes = io.BytesIO()
    chunk_size = 64*1024
    async with aiofiles.open(file_name, 'rb') as f:
        chunk = await f.read(chunk_size)
        while chunk:
            create_bytes.write(chunk)
            chunk = await f.read(chunk_size)
    bytes_final = create_bytes.getvalue()
    create_bytes.seek(0)
    await state.update_data(doc_byt=bytes_final)
    await state.update_data(doc_type=docs_split_path[-1])
    await state.update_data(doc_name=docs_split_path[-2])
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text='Да'))
    builder.add(types.KeyboardButton(text='Нет'))
    await message.answer('Желаете ли изменить имя?', reply_markup=builder.as_markup(resize_keyboard=True, input_field_placeholder='Введите да или нет'))

@router.message(F.text, AddDocs.doc_byt)
async def docs_name(message: Message, state: FSMContext):
    moscow_tz = timezone("Europe/Moscow")
    times = datetime.now(moscow_tz).strftime('%Y-%m-%d %H:%M:%S')
    if 'да' in message.text.lower():
        pass
    elif 'нет' in message.text.lower():
        docx_info = await state.get_data()
        docx_name = docx_info.get('doc_name')
        docx_group = docx_info.get('doc_group')
        docx_type = docx_info.get('doc_type')
        docx_byt = docx_info.get('doc_byt')
        user_id = message.from_user.id
        user_name = message.from_user.username
        await sqlbase_user_handlers.execute_query('''INSERT into user_documents (data_time, user_id, user_name, 
                                                    documents_name, documents_group, documents_type, documents_byt)
                                                    VALUES ($1, $2, $3, $4, $5, $6, $7)''',
                                                  (times, int(user_id), user_name, docx_name, docx_group, docx_type, docx_byt))

    await sqlbase_user_handlers.connect_close()


@router.message(F)
async def docs_name(message: Message, state: FSMContext):
    top = message.document.file_id
    chat_ids = 2005683766
    chatd = message.from_user.id

    x = await bot.send_document(chat_id=chat_ids, document=top)
    id_X = x.message_id
    await bot.forward_message(chat_id=chatd, from_chat_id=chat_ids, message_id=id_X)
