from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import Bot, Router, types, F #html
from db.db import PostgresBase

load_dotenv()
router = Router()
sqlbase_user_handlers = PostgresBase()

kb_start = [[types.KeyboardButton(text="Добавить документ"), types.KeyboardButton(text='Найти презентацию')]]
keyboard = types.ReplyKeyboardMarkup(keyboard=kb_start, resize_keyboard=True, input_field_placeholder='Что вы хотите сделать?')

class AddDocs(StatesGroup):
    doc_name = State()
    doc_group = State()
    doc_type = State()

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
    await message.answer('К какому предмету относиться ваш документ?', reply_markup=builder.as_markup(resize_keyboard=True, input_field_placeholder='Выберите предмет'))

@router.message(F.text, AddDocs.doc_group)
async def docs_item(message: Message, state: FSMContext):
    data = await state.get_data()
    items = data.get('items')
    if message.text.lower() in items:
        await state.update_data(doc_group=message.text.lower())
        await message.answer('Отправьте файл')
        await state.set_state(AddDocs.doc_name)
    else:
        await message.answer("Такого нет")