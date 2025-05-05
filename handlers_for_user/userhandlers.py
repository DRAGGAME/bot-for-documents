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
    docx_name = State()
    docx_group = State()
    docx_type = State()
    doc_id = State()


@router.message(Command('Userid'))
async def user_idd(message: Message):
    await message.answer(f'ID вашего профиля в телеграм: {message.chat.id}')

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
    builder.adjust(3)
    await state.update_data(items=items)
    await state.set_state(AddDocs.docx_group)
    await message.answer('К какому предмету относиться ваш документ?', reply_markup=builder.as_markup(resize_keyboard=True,
                                                                                                      input_field_placeholder='Выберите предмет'))

@router.message(F.text, AddDocs.docx_group)
async def docs_item(message: Message, state: FSMContext):
    data = await state.get_data()
    items = data.get('items')
    if message.text.lower() in items:
        await state.update_data(docx_group=message.text.lower())
        await message.answer('Отправьте файл')
        await state.set_state(AddDocs.doc_id)
    else:
        await message.answer("Такого нет")

@router.message(F.document, AddDocs.doc_id)
async def docs_name(message: Message, state: FSMContext):
    moscow_tz = timezone("Europe/Moscow")
    times = datetime.now(moscow_tz).strftime('%Y-%m-%d %H:%M:%S')

    docs_path = message.document.file_name
    docs_split_path = re.split(r'[.]', docs_path)
    docx_id = message.document.file_id

    await state.update_data(docx_id=docx_id)
    await state.update_data(docx_type=docs_split_path[-1])
    await state.update_data(docx_name=docs_split_path[-2])

    docx_info = await state.get_data()
    docx_name = docx_info.get('docx_name')
    docx_group = docx_info.get('docx_group')
    docx_type = docx_info.get('docx_type')
    docx_id = docx_info.get('docx_id')
    user_id = message.from_user.id
    user_name = message.from_user.username
    bots_answer = await bot.send_document(chat_id=os.getenv('id_chat'), document=docx_id)
    await bot.forward_message(chat_id=user_id, from_chat_id=os.getenv('id_chat'), message_id=bots_answer.message_id)

    await sqlbase_user_handlers.execute_query('''INSERT into user_documents (data_time, user_id, user_name, 
                                                documents_name, documents_group, documents_type, documents_id)
                                                VALUES ($1, $2, $3, $4, $5, $6, $7)''',
                                              (times, int(user_id), user_name, docx_name, docx_group, docx_type,
                                               str(bots_answer.message_id)))

    await state.clear()
    await message.answer('Документ добавлен', reply_markup=types.ReplyKeyboardRemove())
    await sqlbase_user_handlers.connect_close()

