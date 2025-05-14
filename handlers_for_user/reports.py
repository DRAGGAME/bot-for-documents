

from aiogram import Router, F, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardRemove
from config import TG_API, tg_forw_report
from db.db import PostgresBase
from handlers_for_user.kb.keyboard import KeyboardFactory

sqlbase_user_report = PostgresBase()

bot = Bot(token=TG_API, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

kb_Factor_report = KeyboardFactory()

router_report = Router()


class ReportItem(StatesGroup):
    report_class_num = State()
    report_item = State()

class ReportBugs(StatesGroup):
    report_bugs = State()

@router_report.message(Command(commands=('report_item', 'Report_item', )))
async def report(message: Message, state: FSMContext):
    await sqlbase_user_report.connect()
    kb = await kb_Factor_report.builder_reply_class_reports()
    await state.set_state(ReportItem.report_class_num)
    await message.answer('Введите классы, к которым относиться предмет', reply_markup=kb)

@router_report.message(Command(commands=('report_bug', 'Report_bug', )))
async def report(message: Message, state: FSMContext):
    await sqlbase_user_report.connect()
    await state.set_state(ReportBugs.report_bugs)
    await message.answer('Опишите ошибку, в каких условиях она происходит, также можно приложить скрины')

@router_report.message(F, ReportBugs.report_bugs)
async def report_for_docx(message: Message, state: FSMContext):
    confirm_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Подтвердить', callback_data=f'confirm_bugs')],
        [InlineKeyboardButton(text='Отклонить', callback_data=f'deletes_bugs')]
    ])
    bots_answer = await bot.copy_message(chat_id=tg_forw_report, from_chat_id=message.chat.id,
                                         message_id=message.message_id, reply_markup=confirm_buttons)

    keyboard_reply = await kb_Factor_report.builder_reply_start()

    await message.answer('Баг отправлен', reply_markup=keyboard_reply)
    await state.clear()


@router_report.message(F.text.lower().in_(('5', '6', '7', '8', '9', '10', '11', 'стоп')), ReportItem.report_class_num)
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
        await state.set_state(ReportItem.report_item)
        await message.answer("Теперь отправьте название предмета, к которому относятся выбранные классы.", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer("Пожалуйста, выберите класс от 5 до 11 или нажмите 'Стоп'.")

@router_report.message(F.text, ReportItem.report_item)
async def report_item_name(message: Message, state: FSMContext):
    item_name = message.text.strip()
    data = await state.get_data()
    selected_classes = data.get("selected_classes", set())

    # Формируем поля классов
    class_flags = {f'class_{i}': i in selected_classes for i in range(5, 12)}

    # Вставка в базу данных с enabling = False
    await sqlbase_user_report.item_begin(item_name, class_flags)

    # Подтверждение
    confirm_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Подтвердить', callback_data=f'confirm_from_item_{item_name}')],
        [InlineKeyboardButton(text='Удалить', callback_data=f'deletes_from_item_{item_name}')]
    ])
    await bot.send_message(
        chat_id=tg_forw_report,
        text= f'Новый предмет: <b>{item_name}</b>\n'
                f'Для классов: {", ".join(map(str, sorted(selected_classes)))}',
        reply_markup=confirm_buttons,
        parse_mode='HTML'
    )
    keyboard_reply = await kb_Factor_report.builder_reply_start()

    await sqlbase_user_report.connect_close()
    await state.clear()
    await message.answer('Баг отправлен', reply_markup=keyboard_reply)

@router_report.callback_query(F.data.startswith('confirm_from_item_'))
async def confirm_report(callback: CallbackQuery):
    await sqlbase_user_report.connect()
    item = callback.data.replace('confirm_from_item_', '')
    await sqlbase_user_report.enable_report_subject(item)
    await sqlbase_user_report.connect_close()
    await callback.message.edit_text(f"Предмет <b>{item}</b> подтверждён и добавлен.", parse_mode='HTML')

@router_report.callback_query(F.data.startswith('deletes_from_item_'))
async def delete_report(callback: CallbackQuery):
    await sqlbase_user_report.connect()
    item = callback.data.replace('deletes_from_item_', '')
    await sqlbase_user_report.delete_report_subject(item)
    await sqlbase_user_report.connect_close()
    await callback.message.edit_text(f"Предмет <b>{item}</b> удалён.", parse_mode='HTML')

@router_report.callback_query(F.data.startswith('confirm_bugs'))
async def confirm_report(callback: CallbackQuery):
    await callback.message.edit_text(f"Баг подтверждён и исправен вами", parse_mode='HTML')

@router_report.callback_query(F.data.startswith('deletes_bugs'))
async def delete_report(callback: CallbackQuery):
    await callback.message.edit_text(f"Баг отклонён и не будет исправлен, либо это не баг", parse_mode='HTML')