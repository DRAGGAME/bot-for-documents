# @dp.message(Command("privet"))
# async def cmd_start(message: types.Message):
#     await message.answer(
#     f"Hello, {html.bold(html.quote(message.from_user.first_name))}")
#
# @dp.message(Command("stop", prefix='['))
# async def cmd_start(message: types.Message):
#     await message.reply("Ответ на сообщение!") #reply - ответ
#
# @dp.message(Command("emoji"))
# async def cmd_start(message: types.Message):
#     await message.reply_dice(emodji = '🤣🤣') #reply - ответ
#
# @dp.message(Command("хворанг"))
# async def cmd_start(message: types.Message):
#     await message.reply('- Пидорас') #reply - ответ
#
# @dp.message(F.text, Command('end'))
# async def func_name(message: Message):
#     await message.reply('<b>Hello</b> boys!')
#     # parse_mode = ParseMode.HTML) #форматированние через html
#
#     # await message.answer('***Hello*** boys\!',
#     # parse_mode = ParseMode.MARKDOWN_V2) #форматированн
# Хэндлер на команду /start
# @dp.message(CommandStart(
#     deep_link=True, magic=F.args == 'one'))
# async def cmd_start(message: types.Message):
#     await message.answer('<b>А ты готов к полному провалу?</b>')
#
# @dp.message(CommandStart(
#     deep_link=True,
#     magic=F.args.regexp(re.compile(r'level_\d+'))))
#
# async def cmd_start_level(message: types.Message, command: CommandObject):
#     level = command.args.split('_')[1]
#     await message.answer(f'Ты зашёл на level:{level}')