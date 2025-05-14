from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup


class KeyboardFactory:
    def __init__(self):
        self.builder_reply = None

        self.builder_inline = None
        self.back_from_butt = InlineKeyboardButton(
            text='Назад',
            callback_data='back_from_butt'
        )

        self.delete_from_butt = InlineKeyboardButton(
            text='УДАЛИТЬ ФАЙЛ',
            callback_data='delete_file'
        )

        self.another_action_butt = InlineKeyboardButton(
            text='Выбрать другое действие',
            callback_data='action'
        )

        self.cancel_from_butt = InlineKeyboardButton(
            text='Выбрать другой предмет',
            callback_data='cancel'
        )

        self.next_from_butt = InlineKeyboardButton(
            text='Вперёд',
            callback_data='next_from_butt'
        )



    async def create_builder_reply(self):
        self.builder_reply = ReplyKeyboardBuilder()

    async def create_builder_inline(self):
        self.builder_inline = InlineKeyboardBuilder()

    async def builder_reply_start(self):
        await self.create_builder_reply()
        kb_start = [
            [KeyboardButton(text="Добавить документ"), KeyboardButton(text='Найти документ')],
            [KeyboardButton(text="Мои документы")],
            [KeyboardButton(text="Помощь")]
        ]
        keyboard = ReplyKeyboardMarkup(keyboard=kb_start, resize_keyboard=True,
                                             input_field_placeholder='Что вы хотите сделать?')
        return keyboard

    async def builder_reply_report(self):
        await self.create_builder_reply()
        kb_start = [
            [KeyboardButton(text="Добавить новый предмет"), KeyboardButton(text='Другая ошибка')],
        ]
        keyboard = ReplyKeyboardMarkup(keyboard=kb_start, resize_keyboard=True,
                                             input_field_placeholder='Какую вы встретили ошибку?')
        return keyboard

    async def builder_reply_class(self):
        await self.create_builder_reply()
        for num_keyboard in range(5, 12):
            self.builder_reply.add(KeyboardButton(text=str(num_keyboard)))
        self.builder_reply.row(KeyboardButton(text='Отмена'))

        keyboard = self.builder_reply.as_markup(resize_keyboard=True,
         input_field_placeholder='Выберите класс')
        return keyboard

    async def builder_reply_class_reports(self):
        await self.create_builder_reply()
        for num_keyboard in range(5, 12):
            self.builder_reply.add(KeyboardButton(text=str(num_keyboard)))
        self.builder_reply.row(KeyboardButton(text='Стоп'))

        keyboard = self.builder_reply.as_markup(resize_keyboard=True,
         input_field_placeholder='Выберите классы')
        return keyboard

    async def builder_reply_item(self, items_tuple: tuple):
        await self.create_builder_reply()
        item_list: list = []
        for item in items_tuple:
            item_list.append(item[0].lower())
            self.builder_reply.add(KeyboardButton(text=item[0]))
        self.builder_reply.adjust(2)
        self.builder_reply.row(KeyboardButton(text='Отмена'))

        keyboard = self.builder_reply.as_markup(resize_keyboard=True, input_field_placeholder='Выберите предмет')
        return keyboard, item_list

    async def builder_reply_cancel(self):
        await self.create_builder_reply()
        self.builder_reply.add(KeyboardButton(text='Отмена'))
        keyboard_cancel = self.builder_reply.as_markup(resize_keyboard=True,
                                                input_field_placeholder='Нажмите кнопку в случае необходимости')
        return keyboard_cancel

    async def builder_inline_montage(self,
                                     next_boot: bool = False,
                                     back_boot: bool = False,
                                     cancel_bott: bool = False,
                                     action_boot: bool = False,
                                     delete_boot: bool = False
                                     ) -> None:

        await self.create_builder_inline()

        if back_boot is True:
            self.builder_inline.add(self.back_from_butt)

        if next_boot is True:
            self.builder_inline.add(self.next_from_butt)

        if cancel_bott is True:
            self.builder_inline.add(self.cancel_from_butt)

        if action_boot is True:
            self.builder_inline.add(self.another_action_butt)

        if delete_boot is True:
            self.builder_inline.add(self.delete_from_butt)

        self.builder_inline.adjust(2, 1)

        return self.builder_inline.as_markup()








