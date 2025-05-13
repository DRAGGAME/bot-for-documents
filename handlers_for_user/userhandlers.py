import os

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
# from dotenv import load_dotenv
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import Bot, Router, F #html
from db.db import PostgresBase
from handlers_for_user import my_documents_handlers
from handlers_for_user.kb.keyboard import KeyboardFactory

# load_dotenv()
router_search = Router()
sqlbase_user_search = PostgresBase()
router_search.include_router(my_documents_handlers.router_my_docx)

scheduler_test = AsyncIOScheduler()

bot = Bot(token=os.getenv('TG_API'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

kb_Factor_search = KeyboardFactory()


class SearchDocs(StatesGroup):
    docx_group = State()
    docx_class = State()
    all_docx = State()
    callback_all_docx = State()


class Report(StatesGroup):
    report_class_num = State()
    report_item = State()

@router_search.message(Command('Userid'))
async def user_idd(message: Message):
    await message.answer(f'ID вашего профиля в телеграм: {message.chat.id}')

@router_search.message(CommandStart())
async def create_keyboard(message: Message, state: FSMContext):
    keyboard_for_start = await kb_Factor_search.builder_reply_start()
    await state.update_data(keyboard_for_start=keyboard_for_start)
    await message.answer('Что вы хотите сделать?', reply_markup=keyboard_for_start)

@router_search.message(F.text.lower().in_('помощь'))
async def help_for_user(message: Message):

    await message.answer('Сначала вы выбираете, что вы хотите - добавить документ или просмотреть документы, если выбирайте добавить, то выбираете, класс, предмет, а после отправляете название'

                         ', если же вы просмотреть документы, то так же - класс, предмет. Вы можете просмотреть документы и фото к любым классам и предметам.'

                         'Есть кнопка "Мои документы", в ней вы можете удалить добавленные вами документы. Если вашего предмета не имеется, что скорее всего, то отправьте через команду /report данные')

# @router.message(Command(commands=['report', 'Report']))
@router_search.message(F.text.lower().contains('найти документ'))
# @router.message(F.text.lower().contains('добавить документ'))
async def search_docs(message: Message, state: FSMContext):
    await sqlbase_user_search.connect()
    keyboard_reply = await kb_Factor_search.builder_reply_class()
        # if scheduler_test.get_job(job_id=f'auto_close_user{message.chat.id}'):
    #     pass
    # else:
    #     scheduler_test.add_job(auto_close_connect, 'date', run_date=datetime.now() + timedelta(hours=2),
    #                            args=(sqlbase_user_add_docx, ), id=f'auto_close_user{message.chat.id}')
    #     scheduler_test.start()
    await state.update_data(count=0)
    await state.update_data(kb_for_class=keyboard_reply)

    await state.set_state(SearchDocs.docx_class)
    await message.answer('Документы какого класса вы хотите просмотреть?', reply_markup=keyboard_reply)


@router_search.message(F.text, Report.report_class_num)
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

@router_search .message(F.text, Report.report_item)
async def report_item_name(message: Message, state: FSMContext):
    item_name = message.text.strip()
    data = await state.get_data()
    selected_classes = data.get("selected_classes", set())

    # Формируем поля классов
    class_flags = {f'class_{i}': i in selected_classes for i in range(5, 12)}

    # Вставка в базу данных с enabling = False
    await sqlbase_user_search.item_begin(item_name, class_flags)

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


@router_search.message(F.text.in_(('5', '6', '7', '8', '9', '10', '11')), SearchDocs.docx_class)
async def docx_class(message: Message, state: FSMContext):

    items_tuple = await sqlbase_user_search.execute_query(f'''SELECT item FROM item WHERE class_{message.text} = true AND enabling = true''')
    keyboard_reply, items_list = await kb_Factor_search.builder_reply_item(items_tuple)

    items_list = tuple(items_list)

    await state.update_data(items=items_list)
    await state.update_data(kb_class=keyboard_reply)
    await state.update_data(docx_class=message.text.lower())
    await state.set_state(SearchDocs.docx_group)
    await message.answer('По какому предмету вы хотите добавить файлы? Нажмите кнопку <b>Отмена</b>, если вы захотите сделать другое действие\n\nЕсли вашего предмета нет, '
                         'то пришлите по команде /report данные', reply_markup=keyboard_reply)

@router_search.message(~F.text.in_(('5', '6', '7', '8', '9', '10', '11')), SearchDocs.docx_class)
async def docx_class(message: Message, state: FSMContext):
    await message.reply('Для такого классов не предусмотренно документов')

@router_search.message(F, SearchDocs.docx_group)
async def search_docs(message: Message, state: FSMContext):
    if message.text.lower() in 'отмена':
        keyboard_for_start = await kb_Factor_search.builder_reply_start()
        await state.clear()
        await message.reply('Отмена всех предыдущих действий\n\nЧто вы хотите сделать?',
                            reply_markup=keyboard_for_start)
        return

    keyboard_inline = await kb_Factor_search.builder_inline_montage(
        True,
        True,
        True,
        True,
    )
    docx_group = message.text.lower()

    docx_data = await state.get_data()
    count = docx_data.get('count')
    docx_class = docx_data.get('docx_class')

    all_docs = await sqlbase_user_search.execute_query('''SELECT id, data_time, user_id, user_name,
                                                    documents_name, documents_group, documents_type, documents_id FROM
                                                     user_documents WHERE documents_group=$1 AND documents_class=$2''',
                                                       (docx_group, docx_class))
    if all_docs:
        user_id = message.chat.id

        login = await sqlbase_user_search.execute_query('''SELECT login_for_admin FROM administration_table''')
        if login[0][0] is True:
            keyboard_inline = await kb_Factor_search.builder_inline_montage(True,
                                                                            True,
                                                                            True,
                                                                            True,
                                                                            True
                                                                            )


        msg_obj = await message.answer(f'Выберете нужный вам файл:\n'
                             f'Всего файлов: {len(all_docs)}\n'
                             f'Время добавления: {all_docs[count][1]}\n'
                             f'Кто добавил: {all_docs[count][3]}\n'
                             f'Название файла: {all_docs[count][4]}\n'
                             f'Расширение: {all_docs[count][-2]}\n', reply_markup=keyboard_inline)

        forw = await bot.forward_message(chat_id=user_id, from_chat_id=os.getenv('id_chat'), message_id=int(all_docs[count][-1]))

        forw_chat = forw.chat.id
        forw_id = forw.message_id

        await state.update_data(docx_group=docx_group)
        await state.update_data(all_docx=all_docs)
        await state.update_data(msg_id=msg_obj.message_id)
        await state.update_data(forw=[forw_id, forw_chat])
        await state.update_data(user_id=user_id)

        await state.set_state(SearchDocs.callback_all_docx)
    else:
        await message.answer('Нет ни одного файла')

@router_search.callback_query(F.data == 'next_from_butt', SearchDocs.callback_all_docx)
async def next_from_butt(callback: CallbackQuery, state: FSMContext):
    all_docx = await state.get_data()

    docx_info = all_docx.get('all_docx')
    counts = all_docx.get('count')
    user_id = all_docx.get('user_id')
    forw = all_docx.get('forw')

    counts = int(counts)
    counts += 1

    if counts >= len(docx_info):
        await callback.answer(text='Дальше файлов нет', show_alert=True)
        await callback.answer()

    else:
        await callback.message.edit_text(
            text=f'Выберете нужный вам файл:\n'
                                 f'Всего файлов: {len(docx_info)}\n'
                                 f'Время добавления: {docx_info[counts][1]}\n'
                                 f'Кто добавил: {docx_info[counts][3]}\n'
                                 f'Название файла: {docx_info[counts][4]}\n'
                                 f'Расширение: {docx_info[counts][-2]}\n',
                                    reply_markup=callback.message.reply_markup)



        await bot.delete_message(chat_id=forw[1], message_id=forw[0])

        forw = await bot.forward_message(chat_id=user_id, from_chat_id=os.getenv('id_chat'), message_id=int(docx_info[counts][-1]))
        forw_chat = forw.chat.id
        forw_id = forw.message_id

        await state.update_data(forw=[forw_id, forw_chat])
        await state.update_data(user_id=user_id)
        await state.update_data(count=counts)

        await callback.answer()

@router_search.callback_query(F.data == 'back_from_butt', SearchDocs.callback_all_docx)
async def back_from_butt(callback: CallbackQuery, state: FSMContext):
    all_docx = await state.get_data()

    docx_info = all_docx.get('all_docx')
    counts = all_docx.get('count')
    user_id = all_docx.get('user_id')
    forw = all_docx.get('forw')

    counts = int(counts)
    if counts != 0:
        counts -= 1

    else:
        await callback.answer(text='Дальше файлов нет', show_alert=True)
        return

    await callback.message.edit_text(
        text=f'Выберете нужный вам файл:\n'
                             f'Всего файлов: {len(docx_info)}\n'
                             f'Время добавления: {docx_info[counts][1]}\n'
                             f'Кто добавил: {docx_info[counts][3]}\n'
                             f'Название файла: {docx_info[counts][4]}\n'
                             f'Расширение: {docx_info[counts][-2]}\n',
                                reply_markup=callback.message.reply_markup)


    await bot.delete_message(chat_id=forw[1], message_id=forw[0])

    forw = await bot.forward_message(chat_id=user_id, from_chat_id=os.getenv('id_chat'),
                                     message_id=int(docx_info[counts][-1]))
    forw_chat = forw.chat.id
    forw_id = forw.message_id

    await state.update_data(forw=[forw_id, forw_chat])
    await state.update_data(user_id=user_id)
    await state.update_data(count=counts)

    await callback.answer()

@router_search.callback_query(F.data == 'delete_file', SearchDocs.callback_all_docx)
async def deletes_files(callback: CallbackQuery, state: FSMContext):
    all_docx = await state.get_data()
    docx_info = all_docx.get('all_docx')
    counts = all_docx.get('count')
    docx_group = all_docx.get('docx_group')

    await sqlbase_user_search.execute_query('''DELETE FROM user_documents WHERE id=$1''', (docx_info[counts][0],))
    all_docs_db = await sqlbase_user_search.execute_query('''SELECT id, data_time, user_id, user_name,
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

    user_id = all_docx.get('user_id')
    forw = all_docx.get('forw')

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

@router_search.callback_query(F.data == 'cancel', SearchDocs.callback_all_docx)
async def cancel(callback: CallbackQuery, state: FSMContext):
    all_docx = await state.get_data()
    kb_for_class = all_docx.get('kb_for_class')

    forw = all_docx.get('forw')
    msg_id = all_docx.get('msg_id')

    counts = 0
    await bot.delete_messages(chat_id=forw[1], message_ids=[msg_id, forw[0]])

    await state.update_data(count=counts)

    await state.set_state(SearchDocs.docx_class)

    await callback.message.answer('К какому классу вам нужны документы?',
                         reply_markup=kb_for_class)

    await callback.answer()

@router_search.callback_query(F.data == 'action', SearchDocs.callback_all_docx)
async def create_keyboard_callback(callback: CallbackQuery, state: FSMContext):
    chat_info = await state.get_data()

    keyboard_for_start = chat_info.get('keyboard_for_start')
    forw = chat_info.get('forw')
    msg_id = chat_info.get('msg_id')

    await bot.delete_messages(chat_id=forw[1], message_ids=[msg_id, forw[0]])

    await state.clear()

    await sqlbase_user_search.connect_close()

    await callback.answer()
                # if scheduler_test.get_job(job_id=f'auto_close_user{forw[1]}'):
            #     scheduler_test.remove_job(job_id=f'auto_close_user{forw[1]}')
            #     scheduler_test.shutdown()
    await callback.message.answer('Что вы хотите сделать?', reply_markup=keyboard_for_start)

@router_search.callback_query(F.data.startswith('confirm_'))
async def confirm_report(callback: CallbackQuery):
    item = callback.data.replace('confirm_', '')
    await sqlbase_user_search.enable_report_subject(item)
    await callback.message.edit_text(f"Предмет <b>{item}</b> подтверждён и добавлен.", parse_mode='HTML')

@router_search.callback_query(F.data.startswith('deletes_'))
async def delete_report(callback: CallbackQuery):
    item = callback.data.replace('delete_', '')
    await sqlbase_user_search.delete_report_subject(item)
    await callback.message.edit_text(f"Предмет <b>{item}</b> удалён.", parse_mode='HTML')




