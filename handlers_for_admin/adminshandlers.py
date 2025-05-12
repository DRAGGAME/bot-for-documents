import os

from aiogram import Router, Bot, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import After
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
# from dotenv import load_dotenv
from aiogram.filters import Command, CommandStart
from db.db import PostgresBase

# session = AiohttpSession(
#     api=TelegramAPIServer.from_base('http://localhost:8081')
# )
# load_dotenv()
router = Router()
login_for_admin = False
bot = Bot(token=os.getenv('TG_API'), parce_mode='MARKDOWN' """, session=session""")
sqlbase_admin_handlers = PostgresBase()


class UpdLogin(StatesGroup):
    newlog = State()


class UpdPassword(StatesGroup):
    newpass = State()


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
    await sqlbase_admin_handlers.connect_close()

    await state.clear()


@router.message(Command('UpdLogin'))
async def upd(message: Message, state: FSMContext):
    """Обновление логина"""
    await sqlbase_admin_handlers.connect()
    login = await sqlbase_admin_handlers.execute_query('''SELECT login_for_admin FROM administration_table''')
    if login[0][0] is True:
      # Проверяем права
        await message.answer('Введите новый логин')
        await state.set_state(UpdLogin.newlog)
    else:
        await message.answer('Ошибка: вы не администратор. Напишите /Login - чтобы начать процесс входа в аккаунт '
                             'администратора')

@router.message(UpdLogin.newlog, F.text)
async def newlogs(message: Message, state: FSMContext):
    # Получаем данные из состояния
    data = await state.get_data()
    altnewlog = data.get("altnewlog")  # Первый ввод логина

    if altnewlog is None:  # Первый ввод нового логинае п
        if message.text.lower() == 'stop':
            await message.answer("Обновление логина прервано.")
            await sqlbase_admin_handlers.connect_close()

            await state.clear()
        else:
            await state.update_data(altnewlog=message.text)
            await message.answer('Введите ещё раз новый логин для подтверждения.')
    else:  # Второй ввод логина
        if message.text.lower() == 'stop':
            await message.answer("Обновление логина прервано.")
            await state.clear()
        elif altnewlog == message.text:  # Если логины совпадают
            query = 'UPDATE administration_table SET login = $1 WHERE id = 1;'
            await sqlbase_admin_handlers.execute_query(query, (altnewlog,))
            await sqlbase_admin_handlers.execute_query('''UPDATE administration_table SET login_for_admin = $1 WHERE id=1''', (False,))
            await message.answer('Логин успешно обновлён!')
            await sqlbase_admin_handlers.connect_close()

            await state.clear()
        else:  # Если логины не совпадают
            await message.answer('Логины не совпадают. Повторите ввод нового логина.')
            await state.update_data(altnewlog=None)  # Сбрасываем первый ввод

#Изменение пароля
@router.message(Command('UpdPassword'))
async def upd(message: Message, state: FSMContext):
    """Изменение пароля"""
    await sqlbase_admin_handlers.connect()
    login = await sqlbase_admin_handlers.execute_query('''SELECT login_for_admin FROM administration_table''')
    if login[0][0] is True:
        await message.answer('Введите новый пароль')
        await state.set_state(UpdPassword.newpass)
    else:
        await message.answer('Ошибка: вы не администратор. Напишите /Login - чтобы начать процесс входа в аккаунт '
                             'администратора')


@router.message(UpdPassword.newpass, F.text)
async def new_password(message: Message, state: FSMContext):
    """Изменение пароля"""
    global base

    data = await state.get_data()
    altnewpass = data.get("altnewpass")  # Проверяем, был ли сохранён первый ввод пароля

    if altnewpass is None:  # Первый ввод пароля
        if message.text.lower() == 'stop':
            await message.answer("Обновление пароля прервано.")
            await sqlbase_admin_handlers.connect_close()

            await state.clear()
        else:
            await state.update_data(altnewpass=message.text)  # Сохраняем первый ввод
            await message.answer('Введите ещё раз новый пароль, чтобы подтвердить.')
    else:  # Второй ввод пароля
        if message.text.lower() == 'stop':
            await message.answer("Обновление пароля прервано.")
            await state.clear()
        elif altnewpass == message.text: #При совпадении пароля
            query = 'UPDATE administration_table SET password = $1 WHERE id = 1;'
            await sqlbase_admin_handlers.execute_query(query, (altnewpass,))
            await sqlbase_admin_handlers.execute_query('''UPDATE administration_table SET login_for_admin = $1 WHERE id=1''', (False,))
            await message.answer('Пароль успешно обновлён!')
            await sqlbase_admin_handlers.connect_close()

            await state.clear()
        else:  # Если пароли не совпадают
            await message.answer('Пароли не совпадают. Повторите ввод нового пароля.')
            await state.set_state(UpdPassword.newpass)  # Возвращаем в текущее состояние


@router.message(Command(commands=['exit', 'Exit']))
async def exit_admins(message: Message):
    await sqlbase_admin_handlers.connect()
    await sqlbase_admin_handlers.execute_query('''UPDATE administration_table SET login_for_admin = $1 WHERE id=1''', (False,))
    await sqlbase_admin_handlers.connect_close()

    await message.answer('Вы вышли из аккаунта администратора')

@router.message(Command(commands=['Help_admin', 'help_admin']))
async def help_admin(message: Message):
    await message.answer('/Login\n'
                         '/UpdLogin\n'
                         '/UpdPassword\n'
                         '/Exit')
