from aiogram.filters import CommandStart
from dotenv import load_dotenv
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F #html
from aiogram.filters.command import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, CallbackQuery, message_id

from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

load_dotenv()

selected_subject = None
# Объект
operator = 0
bot = Bot(
    token= os.getenv('API_KEY'),
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)
# Диспетчер
dp = Dispatcher()


async def nices(file_path, message: types.Message):
        nice = await message.answer_document(
            document=types.FSInputFile(path=file_path))
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await asyncio.sleep(1200)
        try:
            await nice.delete()
        except Exception as e:
            pass


@dp.message(Command('help'))
async def helpcmd(message: types.Message):
    await message.answer('/start - начало работы.\n Сначала выбор предмета, потом выбор с помощью клавиатуры презентации'
                         'где на предварительно, выведенном сообщении цифра соответствует презентации\n\n'
                         '/help - помощь в работе')



@dp.message(CommandStart())
async def vibor(message: types.Message):

    builder = InlineKeyboardBuilder()

    builder.add(types.InlineKeyboardButton(
        text="История",
        callback_data="Geschiht"))
    builder.add(types.InlineKeyboardButton(
        text="Обществознание",
        callback_data="Obchaga")
    )
    sent_message = await message.answer(
        "<b>Введите /help для получения доп. информации.</b>\n\n"
        "<b>Выберете предмет:</b>",
        reply_markup=builder.as_markup())
    await bot.pin_chat_message(chat_id=message.chat.id, message_id=sent_message.message_id)

@dp.callback_query(F.data == 'Geschiht')
async def gechichte(callback: types.CallbackQuery):
    global selected_subject
    selected_subject = 'IS'
    builder = ReplyKeyboardBuilder()
    for i in range(1, 13):
        builder.add(types.KeyboardButton(text=str(i)))
    builder.adjust(3)
    await callback.message.answer(
        f'Выберите презентацию:\n'
             f'1. Просвещение\n2. Политическая карта Европы '
             f'и мира в XVIII веке.pptx.Просвещение\n3. Новые идейно-политические течения и'
             f' традиции в XVIII веке\n4. Материальный и духовный мир человека XVIII века.pptx\n'
             f'5. Англия в XVIII веке.pptx.Просвещение\n6. Северная Америка в XVII веке\n'
             f'7. Начало конфликта между Англией и её североамериканскими колониями\n'
             f'8. Германские земли\n9. Презентация по 9 параграфу Демкин Алексей\n'
             f'10. Австрийская монархия Габсбругов в XVIII веке\n'
             f'11. Французская революция\n'
             f'12. Индия\n'
             f'Выберете какую надо вам презентацию',
             reply_markup=builder.as_markup(resize_keyboard=True))
    await callback.answer()

@dp.callback_query(F.data == 'Obchaga')
async def Obc(callback: types.CallbackQuery):
    global selected_subject
    builder = ReplyKeyboardBuilder()
    for i in range(1, 4):
        if i == 2:
            builder.add(types.KeyboardButton(text='НЕТ'))
        else:
            builder.add(types.KeyboardButton(text=str(i)))
    builder.adjust(2)
    await callback.message.answer(
        f'Выберите презентацию:\n'
        f'1. Что делает человека человеком\n '
        f'2. В процессе\n'
        f'3. Общество как форма жизнедеятельности людей\n'
        f'4. В процессе\n',
        reply_markup=builder.as_markup(resize_keyboard=True))

    selected_subject = 'OB'
    await callback.message.answer('1. Что делает человека человеком\n'
                                    '2. Нет\n'
                                    '3. Общество как форма жизнедеятельности людей\n')
    await callback.answer()

@dp.message(F.text)
async def handle_presentation_request(message: Message):
    global selected_subject
    user_input = message.text.strip()
    #Презентации по общаге
    if selected_subject == 'OB':
        if user_input == '1':
            await nices('Презентации/1. Что делает человека человеком.pptx', message)
        elif user_input == '3':
            await nices('Презентации/3. Общество как форма жизнедеятельности людей.pptx', message)

    #Презентации по истории
    elif selected_subject == 'IS':
        if user_input == '1':
            await nices('Презентации/1.Просвещение.pptx', message)

        elif user_input == '2':
            await nices('Презентации/2. Политическая карта Европы и мира в XVIII веке.pptx', message)

        elif user_input == '3':
            await nices('Презентации/3. Общество как форма жизнедеятельности людей.pptx', message)

        elif user_input == '4':
            await nices('Презентации/4. Материальный и духовный мир человека XVIII века.pptx', message)

        elif user_input == '5':
            await nices('Презентации/5. Англия в XVIII веке.pptx', message)

        elif user_input == '6':
            await nices('Презентации/6. Северная Америка в XVII веке.pptx', message)

        elif user_input == '7':
            await nices('Презентации/7. Начало конфликта между Англией и её североамериканскими колониями.pptx', message)

        elif user_input == '8':
            await nices('Презентации/ГЕРМАНСКИЕ ЗЕМЛИ.pptx', message)
        elif user_input == '9':
            await nices('Презентации/Презентация по 9 параграфу Демкин Алексей.pptx', message)

        elif user_input == '10':
            await nices('Презентации/Австрийская монархия Габсбургов в XVIII веке.pptx', message)

        elif user_input == '11':
            await nices('Презентации/французская революция2.pdf', message)

        elif user_input == '12':
            await nices('Презентации/10. Индия.pptx', message)

# Запуск процесса поллинга новых апдейто
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())