import os
import re
from datetime import datetime, timedelta
from pathlib import Path

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from pytz import timezone
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, \
    ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
# from dotenv import load_dotenv
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import Bot, Router, types, F #html
from db.db import PostgresBase
from handlers_for_user import my_documents_handlers
from handlers_for_user.sheduler_user.auto_close_connect  import auto_close_connect

# load_dotenv()
router = Router()
sqlbase_user_handlers = PostgresBase()
router.include_router(my_documents_handlers.router)
kb_start = [
            [types.KeyboardButton(text="Добавить документ"), types.KeyboardButton(text='Найти документ')],
            [types.KeyboardButton(text="Мои документы")],
            [types.KeyboardButton(text="Помощь")]
            ]
keyboard = types.ReplyKeyboardMarkup(keyboard=kb_start, resize_keyboard=True, input_field_placeholder='Что вы хотите сделать?')
scheduler = AsyncIOScheduler()

bot = Bot(token=os.getenv('TG_API'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

build_inline_default = InlineKeyboardBuilder()

build_inline_remove = InlineKeyboardBuilder()

back_from_butt = InlineKeyboardButton(
    text='Назад',
    callback_data='back_from_butt'
)

delete_from_butt = InlineKeyboardButton(
    text='УДАЛИТЬ ФАЙЛ',
    callback_data='delete_file'
)

another_action_butt = InlineKeyboardButton(
    text='Выбрать другое действие',
    callback_data='action'
)

cancel_from_butt = InlineKeyboardButton(
    text='Выбрать другой предмет',
    callback_data='cancel'
)

next_from_butt = InlineKeyboardButton(
    text='Вперёд',
    callback_data='next_from_butt'
)
build_inline_default.add(back_from_butt)
build_inline_default.add(next_from_butt)
build_inline_default.add(cancel_from_butt)
build_inline_default.add(another_action_butt)
build_inline_default.adjust(2, 1)

build_inline_remove.add(back_from_butt)
build_inline_remove.add(next_from_butt)
build_inline_remove.add(cancel_from_butt)
build_inline_remove.add(another_action_butt)
build_inline_remove.add(delete_from_butt)
build_inline_remove.adjust(2, 1)


class AddDocs(StatesGroup):
    docx_name = State()
    docx_group = State()
    docx_type = State()
    docx_class = State()
    doc_id = State()


class SearchDocs(StatesGroup):
    docx_group = State()
    docx_class = State()
    all_docx = State()
    callback_all_docx = State()


class Report(StatesGroup):
    report_class_num = State()
    report_item = State()

@router.message(Command('Userid'))
async def user_idd(message: Message):
    await message.answer(f'ID вашего профиля в телеграм: {message.chat.id}')

@router.message(CommandStart())
async def create_keyboard(message: Message):
    await message.answer('Что вы хотите сделать?', reply_markup=keyboard)

@router.message(F.text.lower().in_('помощь'))
async def help_for_user(message: Message):

    await message.answer('Сначала вы выбираете, что вы хотите - добавить документ или просмотреть документы, если выбирайте добавить, то выбираете, класс, предмет, а после отправляете название'

                         ', если же вы просмотреть документы, то так же - класс, предмет. Вы можете просмотреть документы и фото к любым классам и предметам.'

                         'Есть кнопка "Мои документы", в ней вы можете удалить добавленные вами документы. Если вашего предмета не имеется, что скорее всего, то отправьте через команду /report данные')


@router.message(Command(commands=['report', 'Report']))
@router.message(F.text.lower().contains('найти документ'))
@router.message(F.text.lower().contains('добавить документ'))
async def add_docs(message: Message, state: FSMContext):
    await sqlbase_user_handlers.connect()
    builder_class = ReplyKeyboardBuilder()
    if scheduler.get_job(job_id=f'auto_close_user{message.chat.id}'):
        pass
    else:
        scheduler.add_job(auto_close_connect, 'date', run_date=datetime.now() + timedelta(hours=2),
                          args=(sqlbase_user_handlers, ), id=f'auto_close_user{message.chat.id}')
        scheduler.start()
    for num_keyboard in range(5, 12):
        builder_class.add(types.KeyboardButton(text=str(num_keyboard)))
    if message.text.lower() == 'найти документ':
        counts = 0
        await state.update_data(count=counts)
        await state.set_state(SearchDocs.docx_class)
        await message.answer('К какому классу вам нужны документы?', reply_markup=builder_class.as_markup(resize_keyboard=True))
    elif message.text.lower() == 'добавить документ':
        await state.set_state(AddDocs.docx_class)
        await message.answer('К какому классу вы хотите добавить документы?', reply_markup=builder_class.as_markup(resize_keyboard=True))
    else:
        await state.set_state(Report.report_class_num)
        builder_class.add(types.KeyboardButton(text='Стоп'))
        builder_class.adjust(7, 1)
        await message.answer('Отправьте по очереди классы, <b>к которым предмет относится</b>', reply_markup=builder_class.as_markup(resize_keyboard=True))

@router.message(F.text, Report.report_class_num)
async def report_class(message: Message, state: FSMContext):
    text = message.text.strip().lower()
    if text in ('5', '6', '7', '8', '9', '10', '11'):
        data = await state.get_data()
        selected_classes = data.get("selected_classes", set())
        selected_classes.add(int(text))
        await state.update_data(selected_classes=selected_classes)
        await message.answer(f'К предмету добавлен класс {text}')
    elif text == 'стоп':
        data = await state.get_data()
        selected_classes = data.get("selected_classes", set())
        if not selected_classes:
            await message.answer("Вы не выбрали ни одного класса.")
            return

        # Спрашиваем у пользователя название предмета
        await state.update_data(waiting_for_item_name=True)
        await state.set_state(Report.report_item)
        await message.answer("Теперь отправьте название предмета, к которому относятся выбранные классы.")
    else:
        await message.answer("Пожалуйста, выберите класс от 5 до 11 или нажмите 'Стоп'.")

@router.message(F.text, Report.report_item)
async def report_item_name(message: Message, state: FSMContext):
    item_name = message.text.strip()
    data = await state.get_data()
    selected_classes = data.get("selected_classes", set())

    # Формируем поля классов
    class_flags = {f'class_{i}': i in selected_classes for i in range(5, 12)}

    # Вставка в базу данных с enabling = False
    await sqlbase_user_handlers.item_begin(item_name, class_flags)

    # Подтверждение
    confirm_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Подтвердить', callback_data=f'confirm_{item_name}')],
        [InlineKeyboardButton(text='Удалить', callback_data=f'deletes_{item_name}')]
    ])
    await bot.send_message(
        chat_id=os.getenv('id_chat_reports'),
        text= f'Новый предмет: <b>{item_name}</b>\n'
                f'Для классов: {", ".join(map(str, sorted(selected_classes)))}',
        reply_markup=confirm_buttons,
        parse_mode='HTML'
    )
    await state.clear()


@router.message(F, SearchDocs.docx_class)
@router.message(F, AddDocs.docx_class)
async def docx_class(message: Message, state: FSMContext):
    if message.text.lower() in ('5', '6', '7', '8', '9', '10', '11'):
        items = []
        builder = ReplyKeyboardBuilder()

        items_tuple = await sqlbase_user_handlers.execute_query(f'''SELECT item FROM item WHERE class_{message.text} = TRUE''')
        for item in items_tuple:
            items.append(item[0].lower())
            builder.add(types.KeyboardButton(text=item[0]))

        items = tuple(items)
        builder.adjust(2)
        await state.update_data(items=items)

        await state.update_data(docx_class=message.text.lower())
        docx_state = await state.get_state()
        if docx_state in 'SearchDocs:docx_class':
            await message.answer('По какому предмету вам нужны файлы?', reply_markup=builder.as_markup(resize_keyboard=True,
                                                                                                    input_field_placeholder='Выберите предмет'))
            await state.set_state(SearchDocs.docx_group)
        else:
            await state.set_state(AddDocs.docx_group)
            await message.answer('По какому предмету вы хотите добавить файлы?\n\nЕсли вашего предмета нет, '
                                 'то пришлите по команде /report данные', reply_markup=builder.as_markup(resize_keyboard=True,
                                                                                                  input_field_placeholder='Выберите предмет'))
    else:
        await message.reply('Для таких классов не предусмотрено хранение документов или такого класса не существует')


@router.message(F.text, AddDocs.docx_group)
async def docs_item(message: Message, state: FSMContext):

    await state.update_data(docx_group=message.text.lower())
    await state.set_state(AddDocs.doc_id)
    await message.answer('Отправьте файл/фото\n\nВы можете прислать фото без сжатия, в таком случае вы пришлёте фото в '
                         'виде файла(Если его название не понятное, рекомендуется переименовать или отправить с сжатием',
                         reply_markup=ReplyKeyboardRemove())
    # else:
    #     await message.reply("Такого предмета нет")


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
        user_id = message.chat.id
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
        await sqlbase_user_handlers.connect_close()
        if scheduler.get_job(job_id=f'auto_close_user{message.chat.id}'):
            scheduler.remove_job(job_id=f'auto_close_user{message.chat.id}')
            scheduler.shutdown()
        await message.answer('Документ успешно добавлен', reply_markup=keyboard)

    elif message.photo:
        await message.answer('Введите название фото, чтобы было понятно, какая тема у него')
        docx_id = message.photo[-1].file_id

        await state.update_data(docx_id=docx_id)
        await state.set_state(AddDocs.docx_type)

@router.message(F, AddDocs.docx_type)
async def edit_name_photo(message: Message, state: FSMContext):
    if message.text:
        moscow_tz = timezone("Europe/Moscow")
        times = datetime.now(moscow_tz).strftime('%Y-%m-%d %H:%M:%S')

        docx_info = await state.get_data()
        docx_id = docx_info.get('docx_id')
        bots_answer = await bot.send_photo(chat_id=os.getenv('id_chat'), photo=docx_id)

        await sqlbase_user_handlers.execute_query(
            '''INSERT INTO user_documents (data_time, user_id, user_name, 
               documents_name, documents_group, documents_class, documents_type, documents_id)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)''',
            (
                times,
                int(message.chat.id),
                message.from_user.username,
                message.text,
                docx_info.get('docx_group'),
                docx_info.get('docx_class'),
                'Photo',
                str(bots_answer.message_id)
            )
        )
    if scheduler.get_job(job_id=f'auto_close_user{message.chat.id}'):
        scheduler.remove_job(job_id=f'auto_close_user{message.chat.id}')
        scheduler.shutdown()
    await state.clear()
    await sqlbase_user_handlers.connect_close()
    await message.answer('Фото успешно добавлено', reply_markup=keyboard)

@router.callback_query(F.data == 'next_from_butt', SearchDocs.callback_all_docx)
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

@router.callback_query(F.data == 'back_from_butt', SearchDocs.callback_all_docx)
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

@router.callback_query(F.data == 'delete_file', SearchDocs.callback_all_docx)
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

@router.callback_query(F.data == 'cancel', SearchDocs.callback_all_docx)
async def cancel(callback: CallbackQuery, state: FSMContext):
    builder_class = ReplyKeyboardBuilder()
    all_docs = await state.get_data()

    forw = all_docs.get('forw')
    msg_id = all_docs.get('msg_id')
    await bot.delete_messages(chat_id=forw[1], message_ids=[msg_id, forw[0]])
    for num_keyboard in range(5, 12):
        builder_class.add(types.KeyboardButton(text=str(num_keyboard)))
    counts = 0
    await state.update_data(count=counts)
    await state.set_state(SearchDocs.docx_class)
    await callback.message.answer('К какому классу вам нужны документы?',
                         reply_markup=builder_class.as_markup(resize_keyboard=True))
    await callback.answer()

@router.callback_query(F.data == 'action', SearchDocs.callback_all_docx)
async def create_keyboard_callback(callback: CallbackQuery, state: FSMContext):
    all_docs = await state.get_data()
    forw = all_docs.get('forw')
    msg_id = all_docs.get('msg_id')
    await bot.delete_messages(chat_id=forw[1], message_ids=[msg_id, forw[0]])
    await sqlbase_user_handlers.connect_close()
    await state.clear()
    await callback.answer()
    if scheduler.get_job(job_id=f'auto_close_user{forw[1]}'):
        scheduler.remove_job(job_id=f'auto_close_user{forw[1]}')
        scheduler.shutdown()
    await callback.message.answer('Что вы хотите сделать?', reply_markup=keyboard)

@router.message(F, SearchDocs.docx_group)
async def search_docs(message: Message, state: FSMContext):
    build_inline = build_inline_default
    count = await state.get_data()
    count = count.get('count')
    docx_group = message.text.lower()
    docx_data = await state.get_data()
    docx_class = docx_data.get('docx_class')
    all_docs = await sqlbase_user_handlers.execute_query('''SELECT id, data_time, user_id, user_name,
                                                    documents_name, documents_group, documents_type, documents_id FROM
                                                     user_documents WHERE documents_group=$1 AND documents_class=$2''', (docx_group, docx_class))
    if all_docs:
        login = await sqlbase_user_handlers.execute_query('''SELECT login_for_admin FROM administration_table''')
        if login[0][0] is True:
            build_inline = build_inline_remove


        msg_id =await message.answer(f'Выберете нужный вам файл:\n'
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
        await state.update_data(msg_id=msg_id.message_id)

        await state.update_data(forw=[forw_id, forw_chat])
        await state.update_data(user_id=user_id)
        await state.set_state(SearchDocs.callback_all_docx)

    else:
        await message.answer('Нет ни одного файла')

@router.callback_query(F.data.startswith('confirm_'))
async def confirm_report(callback: CallbackQuery):
    item = callback.data.replace('confirm_', '')
    await sqlbase_user_handlers.enable_report_subject(item)
    await callback.message.edit_text(f"Предмет <b>{item}</b> подтверждён и добавлен.", parse_mode='HTML')

@router.callback_query(F.data.startswith('deletes_'))
async def delete_report(callback: CallbackQuery):
    item = callback.data.replace('delete_', '')
    await sqlbase_user_handlers.delete_report_subject(item)
    await callback.message.edit_text(f"Предмет <b>{item}</b> удалён.", parse_mode='HTML')




