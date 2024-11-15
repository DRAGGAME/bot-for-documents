from random import *
from dotenv import load_dotenv
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F #html
from aiogram.filters.command import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import message_id
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

load_dotenv()


# Объект бота
bot = Bot(
    token= os.getenv('API_KEY'),
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)
# Диспетчер
dp = Dispatcher()

def inputs(file_path, x):
    @dp.message(F.text.lower() == x)
    async def presintation(message: types.Message):
        nice = await message.answer_document(
            document=types.FSInputFile(path=file_path))
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await asyncio.sleep(1200)
        try:
            await nice.delete()
        except Exception as e:
            pass


@dp.message(Command("start"))
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

@dp.message(Command('help'))
async def helpcmd(message: types.Message):
    await message.reply('Команды:\n'
                        '/help - помощь\n'
                        '/start - начало работы. После выбора предмета, у вас будет выведен список с презентацием, а '
                        'также будут введены кнопки ниже ввода, которые соответсвуют списку, нажмите кнопку и будет '
                        'выведена презентация и удалена через 20 минут.\n\n'
                        'Если вы хотите вывести другие презентации нажмите на закреплённое сообщение.')

@dp.callback_query(F.data == 'Geschiht')
async def gechichte(callback: types.CallbackQuery):
    builder = ReplyKeyboardBuilder()
    status = F.data
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
    inputs('Презентации/1.Просвещение.pptx', '1')
    inputs('Презентации/2. Политическая карта Европы и мира в XVIII веке.pptx', '2')
    inputs('Презентации/3. Новые идейно-политические течения и традиции в XVIII веке.pptx', '3')
    inputs('Презентации/4. Материальный и духовный мир человека XVIII века.pptx', '4')
    inputs('Презентации/5. Англия в XVIII веке.pptx', '5')
    inputs('Презентации/6. Северная Америка в XVII веке.pptx', '6')
    inputs('Презентации/7. Начало конфликта между Англией и её североамериканскими колониями.pptx', '7')
    inputs('Презентации/ГЕРМАНСКИЕ ЗЕМЛИ.pptx', '8')
    inputs('Презентации/Презентация по 9 параграфу Демкин Алексей.pptx', '9')
    inputs('Презентации/Австрийская монархия Габсбургов в XVIII веке.pptx', '10')
    inputs('Презентации/французская революция2.pdf', '11')
    inputs('Презентации/10. Индия.pptx', '12')

    await callback.answer()



@dp.callback_query(F.data == 'Obchaga')
async def gechichte(callback: types.CallbackQuery):
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
        f'4. В процессе',
        reply_markup=builder.as_markup(resize_keyboard=True))
    inputs('Презентации/1. Что делает человека человеком.pptx', '1')
    inputs('Презентации/3. Общество как форма жизнедеятельности людей.pptx', '3')
    await callback.answer()

# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())