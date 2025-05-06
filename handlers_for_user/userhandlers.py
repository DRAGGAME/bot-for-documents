import os
import re
from datetime import datetime
from pytz import timezone
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from dotenv import load_dotenv
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import Bot, Router, types, F #html
from db.db import PostgresBase
load_dotenv()
router = Router()
sqlbase_user_handlers = PostgresBase()
kb_start = [[types.KeyboardButton(text="Добавить документ"), types.KeyboardButton(text='Найти документ')]]
keyboard = types.ReplyKeyboardMarkup(keyboard=kb_start, resize_keyboard=True, input_field_placeholder='Что вы хотите сделать?')

bot = Bot(token=os.getenv('TG_API'), parce_mode='MARKDOWN')

build_inline = InlineKeyboardBuilder()

back_from_butt = InlineKeyboardButton(
    text='Назад',
    callback_data='back_from_butt'
)

download = InlineKeyboardButton(
    text='Показать',
    callback_data='download'
)

next_from_butt = InlineKeyboardButton(
    text='Вперёд',
    callback_data='next_from_butt'
)

build_inline.add(back_from_butt)
build_inline.add(download)
build_inline.add(next_from_butt)
build_inline.adjust(3)


class AddDocs(StatesGroup):
    docx_name = State()
    docx_group = State()
    docx_type = State()
    doc_id = State()


class SearchDocs(StatesGroup):
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

@router.message(F.text.lower().contains('найти документ'))
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
    if message.text.lower() == 'найти документ':
        count = 0
        await state.update_data(count=count)
        await state.set_state(SearchDocs.docx_group)
        await message.answer('К какому предмету относиться ваш документ?', reply_markup=builder.as_markup(resize_keyboard=True,                                                                                           input_field_placeholder='Выберите предмет'))
    else:
        await state.set_state(AddDocs.docx_group)
        await message.answer('По какому предмету, вы хотите найти документ', reply_markup=builder.as_markup(resize_keyboard=True,                                                                                           input_field_placeholder='Выберите предмет'))



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

@router.message(F, AddDocs.doc_id)
async def docs_name(message: Message, state: FSMContext):
    moscow_tz = timezone("Europe/Moscow")
    times = datetime.now(moscow_tz).strftime('%Y-%m-%d %H:%M:%S')
    if message.document:
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
    elif message.photo:
        docx_id = message.photo[-1].file_id

        await state.update_data(docx_id=docx_id)

        docx_info = await state.get_data()
        docx_name = docx_info.get('docx_name')
        docx_group = docx_info.get('docx_group')
        docx_type = docx_info.get('docx_type')
        docx_id = docx_info.get('docx_id')
        user_id = message.from_user.id
        user_name = message.from_user.username
        bots_answer = await bot.send_photo(chat_id=os.getenv('id_chat'), photo=docx_id)

        await sqlbase_user_handlers.execute_query('''INSERT into user_documents (data_time, user_id, user_name,
                                                    documents_name, documents_group, documents_type, documents_id)
                                                    VALUES ($1, $2, $3, $4, $5, $6, $7)''',
                                                  (times, int(user_id), user_name, docx_name, docx_group, 'Photo',
                                                   str(bots_answer.message_id)))

    await state.clear()
    await message.answer('Документ добавлен', reply_markup=types.ReplyKeyboardRemove())
    await sqlbase_user_handlers.connect_close()

@router.callback_query(F.data == 'next_from_butt', SearchDocs.docx_group)
async def back_from_butt(callback: CallbackQuery, state: FSMContext):
    all_docs = await state.get_data()
    all_docss = all_docs.get('all_docs')
    count = all_docs.get('count')
    count = int(count)
    count += 1
    if count >= len(all_docss):
        await callback.answer(text='Дальше файлов нет', show_alert=True)
        await callback.answer()

    else:
        await callback.message.edit_text(
            text=f'Выберете нужный вам файл:\n'
                                 f'Всего файлов: {len(all_docss)}\n'
                                 f'Время добавления: {all_docss[count][0]}\n'
                                 f'Кто добавил: {all_docss[count][2]}\n'
                                 f'Название файла: {all_docss[count][3]}\n'
                                 f'Расширение: {all_docss[count][-2]}\n',
                                    reply_markup=callback.message.reply_markup)
        await state.update_data(count=count)

        await callback.answer()

@router.callback_query(F.data == 'back_from_butt', SearchDocs.docx_group)
async def back_from_butt(callback: CallbackQuery, state: FSMContext):
    all_docs = await state.get_data()
    all_docss = all_docs.get('all_docs')
    count = all_docs.get('count')
    count = int(count)
    if count+1 > 1:
        count -= 1
    else:
        await callback.answer(text='Дальше файлов нет', show_alert=True)

    await callback.message.edit_text(
        text=f'Выберете нужный вам файл:\n'
                             f'Всего файлов: {len(all_docss)}\n'
                             f'Время добавления: {all_docss[count][0]}\n'
                             f'Кто добавил: {all_docss[count][2]}\n'
                             f'Название файла: {all_docss[count][3]}\n'
                             f'Расширение: {all_docss[count][-2]}\n',
                                reply_markup=callback.message.reply_markup)
    await state.update_data(count=count)

    await callback.answer()

@router.message(F, SearchDocs.docx_group)
async def search_docs(message: Message, state: FSMContext):
    docx_group = message.text.lower()
    all_docs = await sqlbase_user_handlers.execute_query('''SELECT data_time, user_id, user_name,
                                                    documents_name, documents_group, documents_type, documents_id FROM
                                                     user_documents WHERE documents_group = $1''', (docx_group, ))
    await state.update_data(all_docs=all_docs)

    if all_docs:
        count = await state.get_data()
        count = count.get('count')
        await message.answer(f'Выберете нужный вам файл:\n'
                             f'Всего файлов: {len(all_docs)}\n'
                             f'Время добавления: {all_docs[count][0]}\n'
                             f'Кто добавил: {all_docs[count][2]}\n'
                             f'Название файла: {all_docs[count][3]}\n'
                             f'Расширение: {all_docs[count][-2]}\n', reply_markup=build_inline.as_markup())
        user_id = message.chat.id
        await bot.forward_message(chat_id=user_id, from_chat_id=os.getenv('id_chat'), message_id=int(all_docs[0][-1]))
    else:
        await message.answer('Нет ни одного файла')






