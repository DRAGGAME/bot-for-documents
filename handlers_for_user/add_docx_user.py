import os
from datetime import datetime
from pathlib import Path

from aiogram import F, Router, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove

from config import TG_API
from db.db_add_docx import DbForDocx
from handlers_for_user.kb.keyboard import KeyboardFactory
from pytz import timezone

bot = Bot(token=TG_API, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

router_add_docx = Router()
sqlbase_user_add_docx = DbForDocx()
kb_Factor_add = KeyboardFactory()


class AddDocs(StatesGroup):
    docx_name = State()
    docx_group = State()
    docx_type = State()
    docx_class = State()
    doc_id = State()


@router_add_docx.message(F.text.lower().contains('добавить документ'))
async def add_docs(message: Message, state: FSMContext):
    await state.clear()
    await sqlbase_user_add_docx.connect()
    keyboard_reply = await kb_Factor_add.builder_reply_class()
    # if scheduler_test.get_job(job_id=f'auto_close_user{message.chat.id}'):
    #     pass
    # else:
    #     scheduler_test.add_job(auto_close_connect, 'date', run_date=datetime.now() + timedelta(hours=2),
    #                            args=(sqlbase_user_add_docx, ), id=f'auto_close_user{message.chat.id}')
    #     scheduler_test.start()

    await state.update_data(kb=keyboard_reply)
    await state.set_state(AddDocs.docx_class)
    await message.answer('К какому классу вы хотите добавить документы?\n\nНажмите отмена, чтобы отменить все действия"',
                         reply_markup=keyboard_reply)

@router_add_docx.message(F.text.lower().in_(('5', '6', '7', '8', '9', '10', '11', 'отмена')), AddDocs.docx_class)
async def docx_class(message: Message, state: FSMContext):
    if message.text.lower() in 'отмена':
        keyboard_for_start = await kb_Factor_add.builder_reply_start()
        await state.clear()
        await message.reply('Отмена всех предыдущих действий\n\nЧто вы хотите сделать?',
                            reply_markup=keyboard_for_start)
        return
    else:
        items_tuple = await sqlbase_user_add_docx.execute_query(f'''SELECT item FROM item WHERE class_{message.text} = TRUE''')
        keyboard_reply, items_list = await kb_Factor_add.builder_reply_item(items_tuple)

        items_list = tuple(items_list)

        await state.update_data(items=items_list)

        await state.update_data(docx_class=message.text.lower())
        await state.set_state(AddDocs.docx_group)
        await message.answer('По какому предмету вы хотите добавить файлы?\n\nЕсли вашего предмета нет, '
                             'то пришлите по команде /report данные', reply_markup=keyboard_reply)



@router_add_docx.message(F.text, AddDocs.docx_group)
async def docs_item(message: Message, state: FSMContext):
    if message.text.lower() in 'отмена':
        keyboard_for_start = await kb_Factor_add.builder_reply_start()
        await state.clear()
        await message.reply('Отмена всех предыдущих действий\n\nЧто вы хотите сделать?',
                            reply_markup=keyboard_for_start)
        return
    else:
        await state.update_data(docx_group=message.text.lower())
        kb_cancel = await kb_Factor_add.builder_reply_cancel()
        await state.set_state(AddDocs.doc_id)
        await message.answer('Отправьте файл/фото\n\nВы можете прислать фото без сжатия, в таком случае вы пришлёте фото в '
                             'виде файла(Если его название не понятное, рекомендуется переименовать или отправить с сжатием\n\n'
                             'Если вы хотите отменить <b>ВСЕ</b> свои действия до, нажмите кнопку "Отмена"',
                             reply_markup=kb_cancel)


@router_add_docx.message(F, AddDocs.doc_id)
async def docx_name(message: Message, state: FSMContext):
    data_kb = await state.get_data()
    keyboard_reply = data_kb.get('kb')
    if message.document:
        moscow_tz = timezone("Europe/Moscow")
        times = datetime.now(moscow_tz).strftime('%Y-%m-%d %H:%M:%S')
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
        print(docx_info.get('docx_class'))
        await sqlbase_user_add_docx.insert_data(
                times,
                int(user_id),
                user_name,
                docx_name,
                docx_info.get('docx_class'),
                docx_info.get('docx_group'),
                docx_type,
                str(bots_answer.message_id)
            )
        await sqlbase_user_add_docx.connect_close()
        # if scheduler_test.get_job(job_id=f'auto_close_user{message.chat.id}'):
        #     scheduler_test.remove_job(job_id=f'auto_close_user{message.chat.id}')
        #     scheduler_test.shutdown()
        await message.answer('Документ успешно добавлен', reply_markup=keyboard_reply)

    elif message.photo:
        await state.set_state(AddDocs.docx_type)
        await message.answer('Введите имя фото, чтобы все понимали, к чему он относится', reply_markup=ReplyKeyboardRemove())

    elif message.text.lower() in 'отмена':
        keyboard_for_start = await kb_Factor_add.builder_reply_start()
        await state.clear()
        await message.reply('Отмена всех предыдущих действий\n\nЧто вы хотите сделать?',
                            reply_markup=keyboard_for_start)
        return

@router_add_docx.message(F, AddDocs.docx_type)
async def edit_name_photo(message: Message, state: FSMContext):
    data_kb = await state.get_data()
    keyboard_reply = await kb_Factor_add.builder_reply_start()
    if message.text:

        moscow_tz = timezone("Europe/Moscow")
        times = datetime.now(moscow_tz).strftime('%Y-%m-%d %H:%M:%S')

        docx_id = data_kb.get('docx_id')
        bots_answer = await bot.send_photo(chat_id=os.getenv('id_chat'), photo=docx_id)

        await sqlbase_user_add_docx.insert_data(
                times,
                int(message.chat.id),
                message.from_user.username,
                message.text,
                data_kb.get('docx_group'),
                data_kb.get('docx_class'),
                'Photo',
                str(bots_answer.message_id)
            )
    # if scheduler_test.get_job(job_id=f'auto_close_user{message.chat.id}'):
    #     scheduler_test.remove_job(job_id=f'auto_close_user{message.chat.id}')
    #     scheduler_test.shutdown()
    await state.clear()
    await sqlbase_user_add_docx.connect_close()
    await message.answer('Фото успешно добавлено', reply_markup=keyboard_reply)
