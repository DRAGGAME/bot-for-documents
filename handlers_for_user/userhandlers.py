import os
import re
from datetime import datetime
from itertools import count

from pyexpat.errors import messages
from pytz import timezone
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, InputMediaDocument
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


class AddDocs(StatesGroup):
    docx_name = State()
    docx_group = State()
    docx_type = State()
    docx_class = State()
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
    builder.adjust(2)
    await state.update_data(items=items)
    await state.set_state(AddDocs.docx_group)
    if message.text.lower() == 'найти документ':
        counts = 0
        await state.update_data(count=counts)
        await state.set_state(SearchDocs.docx_group)
        await message.answer('К какому предмету относиться ваш документ?', reply_markup=builder.as_markup(resize_keyboard=True,                                                                                         input_field_placeholder='Выберите предмет'))
    else:
        await state.set_state(AddDocs.docx_group)
        await message.answer('По какому предмету, вы хотите найти документ', reply_markup=builder.as_markup(resize_keyboard=True,                                                                              input_field_placeholder='Выберите предмет'))



@router.message(F.text, AddDocs.docx_group)
async def docs_item(message: Message, state: FSMContext):
    builder_class = ReplyKeyboardBuilder()
    data = await state.get_data()
    items = data.get('items')
    if message.text.lower() in items:
        await state.update_data(docx_group=message.text.lower())
        for num_keyboard in range(5, 12):
            builder_class.add(types.KeyboardButton(text=str(num_keyboard)))
        await message.answer('Какой у вас класс?', reply_markup=builder_class.as_markup(resize_keyboard=True))
        await state.set_state(AddDocs.docx_class)
    else:
        await message.reply("Такого предмета нет")

@router.message(F, AddDocs.docx_class)
async def docx_class(message: Message, state: FSMContext):
    if message.text.lower() in ('5', '6', '7', '8', '9', '10', '11'):
        await state.update_data(docx_class=message.text.lower())
        await state.set_state(AddDocs.doc_id)
        await message.answer('Отправьте документ/фото')
    else:
        await message.reply('Для таких классов не предусмотрены презентации или такого класса не существует')

from pathlib import Path

@router.message(F, AddDocs.doc_id)
async def docx_name(message: Message, state: FSMContext):
    moscow_tz = timezone("Europe/Moscow")
    times = datetime.now(moscow_tz).strftime('%Y-%m-%d %H:%M:%S')

    if message.document:
        file_name = message.document.file_name
        docx_id = message.document.file_id

        docx_path = Path(file_name)
        docx_name = docx_path.stem          # имя без расширения
        docx_type = docx_path.suffix.lstrip('.')  # расширение без точки

        await state.update_data(docx_id=docx_id)
        await state.update_data(docx_type=docx_type)
        await state.update_data(docx_name=docx_name)

        docx_info = await state.get_data()
        user_id = message.from_user.id
        user_name = message.from_user.username

        bots_answer = await bot.send_document(chat_id=os.getenv('id_chat'), document=docx_id)
        await bot.forward_message(chat_id=user_id, from_chat_id=os.getenv('id_chat'), message_id=bots_answer.message_id)

        await sqlbase_user_handlers.execute_query(
            '''INSERT INTO user_documents (data_time, user_id, user_name, 
               documents_name, documents_class, documents_group, documents_type, documents_id)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)''',
            (
                times,
                int(user_id),
                user_name,
                docx_name,
                docx_info.get('docx_class'),
                docx_info.get('docx_group'),
                docx_type,
                str(bots_answer.message_id)
            )
        )

    elif message.photo:
        docx_id = message.photo[-1].file_id

        await state.update_data(docx_id=docx_id)
        docx_info = await state.get_data()

        bots_answer = await bot.send_photo(chat_id=os.getenv('id_chat'), photo=docx_id)

        await sqlbase_user_handlers.execute_query(
            '''INSERT INTO user_documents (data_time, user_id, user_name, 
               documents_name, documents_group, documents_class, documents_type, documents_id)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)''',
            (
                times,
                int(message.from_user.id),
                message.from_user.username,
                docx_info.get('docx_name'),
                docx_info.get('docx_group'),
                'Photo',
                str(bots_answer.message_id)
            )
        )

    await state.clear()
    await message.answer('Документ добавлен', reply_markup=types.ReplyKeyboardRemove())
    await sqlbase_user_handlers.connect_close()

@router.callback_query(F.data == 'next_from_butt', SearchDocs.docx_name)
async def next_from_butt(callback: CallbackQuery, state: FSMContext):
    all_docs = await state.get_data()
    all_docss = all_docs.get('all_docs')
    counts = all_docs.get('count')
    counts = int(counts)
    counts += 1

    if counts >= len(all_docss):
        await callback.answer(text='Дальше файлов нет', show_alert=True)
        await callback.answer()

    else:

        await callback.message.edit_text(
            text=f'Выберете нужный вам файл:\n'
                                 f'Всего файлов: {len(all_docss)}\n'
                                 f'Время добавления: {all_docss[counts][1]}\n'
                                 f'Кто добавил: {all_docss[counts][3]}\n'
                                 f'Название файла: {all_docss[counts][4]}\n'
                                 f'Расширение: {all_docss[counts][-2]}\n',
                                    reply_markup=callback.message.reply_markup)
        await state.update_data(count=counts)
        user_id = all_docs.get('user_id')
        forw = all_docs.get('forw')

        await bot.delete_message(chat_id=forw[1], message_id=forw[0])
        forw = await bot.forward_message(chat_id=user_id, from_chat_id=os.getenv('id_chat'), message_id=int(all_docss[counts][-1]))
        forw_chat = forw.chat.id
        forw_id = forw.message_id
        await state.update_data(forw=[forw_id, forw_chat])
        await state.update_data(user_id=user_id)
        await callback.answer()

@router.callback_query(F.data == 'back_from_butt', SearchDocs.docx_name)
async def back_from_butt(callback: CallbackQuery, state: FSMContext):
    all_docs = await state.get_data()
    all_docss = all_docs.get('all_docs')
    counts = all_docs.get('count')
    counts = int(counts)

    if counts != 0:
        counts -= 1
    else:
        await callback.answer(text='Дальше файлов нет', show_alert=True)
        return
    print(all_docss)
    print(all_docss[counts])
    await callback.message.edit_text(
        text=f'Выберете нужный вам файл:\n'
                             f'Всего файлов: {len(all_docss)}\n'
                             f'Время добавления: {all_docss[counts][1]}\n'
                             f'Кто добавил: {all_docss[counts][3]}\n'
                             f'Название файла: {all_docss[counts][4]}\n'
                             f'Расширение: {all_docss[counts][-2]}\n',
                                reply_markup=callback.message.reply_markup)
    await state.update_data(count=counts)
    user_id = all_docs.get('user_id')
    forw = all_docs.get('forw')

    await bot.delete_message(chat_id=forw[1], message_id=forw[0])
    forw = await bot.forward_message(chat_id=user_id, from_chat_id=os.getenv('id_chat'),
                                     message_id=int(all_docss[counts][-1]))
    forw_chat = forw.chat.id
    forw_id = forw.message_id
    await state.update_data(forw=[forw_id, forw_chat])
    await state.update_data(user_id=user_id)

    await callback.answer()

@router.callback_query(F.data == 'delete_file', SearchDocs.docx_name)
async def deletes_files(callback: CallbackQuery, state: FSMContext):
    all_docs = await state.get_data()
    all_docs_get = all_docs.get('all_docs')
    counts = all_docs.get('count')
    docx_group = all_docs.get('docx_group')
    await sqlbase_user_handlers.execute_query('''DELETE FROM user_documents WHERE id=$1''', (all_docs_get[counts][0], ))
    all_docs_db = await sqlbase_user_handlers.execute_query('''SELECT id, data_time, user_id, user_name,
                                                    documents_name, documents_group, documents_type, documents_id FROM
                                                     user_documents WHERE documents_group = $1''', (docx_group, ))
    counts -= 1

    await callback.message.edit_text(
        text=f'Выберете нужный вам файл:\n'
             f'Всего файлов: {len(all_docs_db)}\n'
             f'Время добавления: {all_docs_db[counts][1]}\n'
             f'Кто добавил: {all_docs_db[counts][3]}\n'
             f'Название файла: {all_docs_db[counts][4]}\n'
             f'Расширение: {all_docs_db[counts][-2]}\n',
        reply_markup=callback.message.reply_markup)
    user_id = all_docs.get('user_id')
    forw = all_docs.get('forw')

    await bot.delete_message(chat_id=forw[1], message_id=forw[0])
    forw = await bot.forward_message(chat_id=user_id, from_chat_id=os.getenv('id_chat'),
                                     message_id=int(all_docs_db[counts][-1]))
    forw_chat = forw.chat.id
    forw_id = forw.message_id
    await state.update_data(forw=[forw_id, forw_chat])
    await state.update_data(user_id=user_id)
    await state.update_data(all_docs=all_docs_db)
    await state.update_data(count=counts)

    await callback.answer()



@router.message(F, SearchDocs.docx_group)
async def search_docs(message: Message, state: FSMContext):
    build_inline = InlineKeyboardBuilder()

    back_from_butt = InlineKeyboardButton(
        text='Назад',
        callback_data='back_from_butt'
    )

    delete_from_butt = InlineKeyboardButton(
        text='УДАЛИТЬ ФАЙЛ',
        callback_data='delete_file'
    )

    next_from_butt = InlineKeyboardButton(
        text='Вперёд',
        callback_data='next_from_butt'
    )
    build_inline.add(back_from_butt)
    build_inline.add(next_from_butt)
    build_inline.adjust(2)
    docx_group = message.text.lower()
    all_docs = await sqlbase_user_handlers.execute_query('''SELECT id, data_time, user_id, user_name,
                                                    documents_name, documents_group, documents_type, documents_id FROM
                                                     user_documents WHERE documents_group = $1''', (docx_group, ))
    if all_docs:
        login = await sqlbase_user_handlers.execute_query('''SELECT login_for_admin FROM administration_table''')
        if login[0][0] is True:
            build_inline.add(delete_from_butt)
            build_inline.adjust(2, 1)

        count = await state.get_data()
        count = count.get('count')
        print(count)
        print(all_docs[count])
        await message.answer(f'Выберете нужный вам файл:\n'
                             f'Всего файлов: {len(all_docs)}\n'
                             f'Время добавления: {all_docs[count][1]}\n'
                             f'Кто добавил: {all_docs[count][3]}\n'
                             f'Название файла: {all_docs[count][4]}\n'
                             f'Расширение: {all_docs[count][-2]}\n', reply_markup=build_inline.as_markup())
        user_id = message.chat.id

        forw = await bot.forward_message(chat_id=user_id, from_chat_id=os.getenv('id_chat'), message_id=int(all_docs[count][-1]))
        forw_chat = forw.chat.id
        forw_id = forw.message_id
        await state.update_data(docx_group=docx_group)
        await state.update_data(all_docs=all_docs)
        await state.update_data(forw=[forw_id, forw_chat])
        await state.update_data(user_id=user_id)
        await state.set_state(SearchDocs.docx_name)
    else:
        await message.answer('Нет ни одного файла')






