import os

from aiogram import Router, Bot, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import After
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from dotenv import load_dotenv
from aiogram.filters import Command, CommandStart
from db.db import PostgresBase

# session = AiohttpSession(
#     api=TelegramAPIServer.from_base('http://localhost:8081')
# )
load_dotenv()
router = Router()
login_for_admin = False
bot = Bot(token=os.getenv('TG_API'), parce_mode='MARKDOWN' """, session=session""")
sqlbase_admin_handlers = PostgresBase()


class LoginAdmin(StatesGroup):
    login = State()
    password = State()


@router.message(Command(commands=['login', 'Login']))
async def login_for_admin(message: Message, state: FSMContext):
    await sqlbase_admin_handlers.connect()
    login_and_password = await sqlbase_admin_handlers.execute_query('''SELECT login, password, login_for_admin FROM administration_table''')
    if login_and_password[0][2] is True:
        await message.reply('Аккаунт администратора занят')
        return
    await state.update_data(login_and_password=login_and_password)
    await message.answer('''Введите логин от аккаунта администратора''')
    await state.set_state(LoginAdmin.login)

@router.message(F, LoginAdmin.login)
async def loginadmin(message: Message, state: FSMContext):
    if message.text:
        await state.update_data(login=message.text)
        await state.set_state(LoginAdmin.password)
        await message.answer('''Введите пароль от аккаунта администратора''')

    else:
        await message.reply('Сообщение должно быть текстом!')

@router.message(F, LoginAdmin.password)
async def password_admin(message: Message, state: FSMContext):
    if message.text:
        await state.update_data(password=message.text)
        login_data = await state.get_data()
        login = login_data.get('login')
        password = login_data.get('password')
        login_and_password = login_data.get('login_and_password')
        if login in login_and_password[0][0] and password in login_and_password[0][1]:
            await sqlbase_admin_handlers.execute_query('''UPDATE administration_table SET login_for_admin = $1''', (True,))
            await message.answer('''Вы вошли в аккаунт администратора''')
        else:
            await message.reply('Введены неверные данные для входа')
    else:
        await message.reply('Сообщение должно быть текстом!')

    await state.clear()

@router.message(Command(commands=['exit', 'Exit']))
async def exit_admins(message: Message, state: FSMContext):
    await sqlbase_admin_handlers.execute_query('''UPDATE administration_table SET login_for_admin = $1''', (False,))
    await message.answer('Вы вышли из аккаунта администратора')

