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
def ina(path, i, a):
    @dp.callback_query(F.data == 'Geschiht')
    async def gechichte(callback: types.CallbackQuery):
        filename = os.path.splitext(os.path.basename(path))[0]
        await callback.message.answer(f'Вот список всех презентаций:\n{filename}')
        await callback.answer()


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
        "выберете предмет",
        reply_markup=builder.as_markup())
    await bot.pin_chat_message(chat_id=message.chat.id, message_id=sent_message.message_id)

@dp.callback_query(F.data == 'Geschiht')
async def gechichte(callback: types.CallbackQuery):
    await callback.message.answer(f'1. Просвещение\n2. Политическая карта Европы '
                                f'и мира в XVIII веке.pptx.Просвещение\n3. Новые идейно-политические течения и'
                                f' традиции в XVIII веке\n4. Материальный и духовный мир человека XVIII века.pptx\n'
                                f'5. Англия в XVIII веке.pptx.Просвещение\n6. Северная Америка в XVII веке\n'
                                f'7. Начало конфликта между Англией и её североамериканскими колониями\n'
                                f'8. Германские земли\n9. Презентация по 9 параграфу Демкин Алексей\n'
                                f'10. Австрийская монархия Габсбругов в XVIII веке\n'
                                f'11. Французская революция\n'
                                f'Выберете какую надо вам презентацию')

    builder = ReplyKeyboardBuilder()
    for i in range(1, 12):
        builder.add(types.KeyboardButton(text=str(i)))
    builder.adjust(3)
    await callback.message.answer(
        "Вот все презентации!",
        reply_markup=builder.as_markup(resize_keyboard=True))
    await callback.answer()


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











# @dp.callback_query(F.data == "random_value")
# async def send_random_value(callback: types.CallbackQuery):
#     await callback.message.answer(str(randint(1, 10)))
#     await callback.answer()
#



# star('1', 'Презентации/1.Просвещение.pptx')
#
# star('2', 'Презентации/2. Политическая карта Европы и мира в XVIII веке.pptx')
#
# star('3', 'Презентации/3. Новые идейно-политические течения и традиции в XVIII веке.pptx')
#
# star('4', 'Презентации/4. Материальный и духовный мир человека XVIII века.pptx')
#
# star('5', 'Презентации/5. Англия в XVIII веке.pptx')
#
# star('германские земли', 'Презентации/ГЕРМАНСКИЕ ЗЕМЛИ.pptx')
#
# star('франция(до революции)', 'Презентации/Презентация по 9 параграфу Демкин Алексей.pptx')
#
# star('австрия', 'Презентации/Австрийская монархия Габсбургов в XVIII веке.pptx')
#
# star('9', 'Презентации/6. Северная Америка в XVII веке.pptx')
#
# star('10', 'Презентации/7. Начало конфликта между Англией и её североамериканскими колониями.pptx')
#
# star('11', 'Презентации/французская революция2.pdf')


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())