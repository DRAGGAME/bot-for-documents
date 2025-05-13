import os
from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from handlers_for_user.sheduler_user.auto_close_connect import auto_close_connect
from db.db import PostgresBase
from handlers_for_user.kb.keyboard import KeyboardFactory

load_dotenv()
scheduler = AsyncIOScheduler()

kb_Factor_my_docx = KeyboardFactory()

bot = Bot(token=os.getenv('TG_API'), parce_mode='MARKDOWN')
sqlbase_my_docx = PostgresBase()

router_my_docx = Router()

@router_my_docx.message(F.text.lower().contains('мои документы'))
async def my_documents(message: Message, state: FSMContext):
    await sqlbase_my_docx.connect()

    kb_inline_for_my_docx = await kb_Factor_my_docx.builder_inline_montage(
        next_boot=True,
        back_boot=True,
        action_boot=True,
        delete_boot=True
    )
    count = 0
    user_id = message.chat.id

    all_docs = await sqlbase_my_docx.execute_query('''SELECT id, data_time, user_id, user_name,
                                                     documents_name, documents_group, documents_type, documents_id FROM
                                                      user_documents WHERE user_id = $1''',
                                                         (user_id,))
    if all_docs:
        msg_id = await message.answer(f'Выберете нужный вам файл:\n'
                                      f'Всего файлов: {len(all_docs)}\n'
                                      f'Время добавления: {all_docs[count][1]}\n'
                                      f'Кто добавил: {all_docs[count][3]}\n'
                                      f'Название файла: {all_docs[count][4]}\n'
                                      f'Расширение: {all_docs[count][-2]}\n', reply_markup=kb_inline_for_my_docx)

        forw = await bot.forward_message(chat_id=user_id, from_chat_id=os.getenv('id_chat'),
                                         message_id=int(all_docs[count][-1]))
        forw_chat = forw.chat.id
        forw_id = forw.message_id

        await state.update_data(count=count)
        await state.update_data(all_docs=all_docs)
        await state.update_data(msg_id=msg_id.message_id)
        await state.update_data(kb_inline_for_my_docx=kb_inline_for_my_docx)
        await state.update_data(forw=[forw_id, forw_chat])
        await state.update_data(user_id=user_id)
        # if scheduler.get_job(job_id=f'auto_close_{forw_id}'):
        #     pass
        # else:
        #     scheduler.add_job(auto_close_connect, 'date', run_date=datetime.now() + timedelta(hours=2),
        #                       args=(sqlbase_my_docx,), id=f'auto_close_{forw_id}')
        #     scheduler.start()
    else:
        await sqlbase_my_docx.connect_close()
        await message.answer('Вы не добавили ни единого файла')

@router_my_docx.callback_query(F.data == 'next_from_butt')
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

@router_my_docx.callback_query(F.data == 'back_from_butt')
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

@router_my_docx.callback_query(F.data == 'delete_file')
async def deletes_files(callback: CallbackQuery, state: FSMContext):
    all_docs = await state.get_data()
    all_docs_get = all_docs.get('all_docs')
    counts = all_docs.get('count')
    user_id = all_docs.get('user_id')


    await sqlbase_my_docx.execute_query('''DELETE FROM user_documents WHERE id=$1''', (all_docs_get[counts][0], ))
    all_docs_db = await sqlbase_my_docx.execute_query('''SELECT id, data_time, user_id, user_name,
                                                    documents_name, documents_group, documents_type, documents_id FROM
                                                     user_documents WHERE user_id = $1''', (user_id, ))
    if counts-1 < 0:
        forw = all_docs.get('forw')
        msg_id = all_docs.get('msg_id')
        await bot.delete_messages(chat_id=forw[1], message_ids=[msg_id, forw[0]])
        keyboard = await kb_Factor_my_docx.builder_reply_start()
        await sqlbase_my_docx.connect_close()
        await state.clear()
        await callback.answer()
        # if scheduler.get_job(job_id=f'auto_close_{forw[0]}'):
        #     scheduler.remove_job(job_id=f'auto_close_{forw[0]}')
        #     scheduler.shutdown()
        await callback.message.answer('Все файлы удалены. Выберите действие', reply_markup=keyboard)
        return

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

@router_my_docx.callback_query(F.data == 'action')
async def create_keyboard_callback(callback: CallbackQuery, state: FSMContext):
    all_docs = await state.get_data()
    forw = all_docs.get('forw')
    keyboard = await kb_Factor_my_docx.builder_reply_start()

    msg_id = all_docs.get('msg_id')
    await bot.delete_messages(chat_id=forw[1], message_ids=[msg_id, forw[0]])
    await sqlbase_my_docx.connect_close()
    await state.clear()
    await callback.answer()
    # if scheduler.get_job(job_id=f'auto_close_{forw[0]}'):
    #     scheduler.remove_job(job_id=f'auto_close_{forw[0]}')
    #     scheduler.shutdown()

    await callback.message.answer('Что вы хотите сделать?', reply_markup=keyboard)