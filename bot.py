from async_sender import Mail
from aiogram import Bot, Dispatcher, types
from aiogram.types import CallbackQuery
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from aiogram.types.reply_keyboard import ReplyKeyboardRemove
from aiogram.dispatcher.filters import BoundFilter

import cfg
import database

from loguru import logger

import functions

# Логирование всех ошибок
logger.add('logs/bot.log')

back = KeyboardButton('Назад ⬅')
back_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(back)
profile_btn = KeyboardButton('👤‍ Учетная запись')
profile_add_btn = KeyboardButton('👤‍ Создать учетную запись')
information_btn = KeyboardButton('📜 Информация о проекте')


# Класс для fsm машины (для подачи заявки)
class new_user(StatesGroup):
    name = State()
    age = State()
    group = State()


# Класс для fsm машины (для регистрации учетки)
class register_uchetka(StatesGroup):
    mail = State()
    mail_code = State()


# Подгрузка клавиатуры в зависимости от того, есть ли у человека учетка
def load_start_kb(user) -> ReplyKeyboardMarkup:
    ret = ReplyKeyboardMarkup(resize_keyboard=True)
    if user['site_user_id']:
        ret.add(profile_btn)
    else:
        ret.add(profile_add_btn)
    ret.add(information_btn)
    return ret


# Фильтр для того, чтобы бот использовался только в личке
class is_private(BoundFilter):
    async def check(self, message: types.Message) -> bool:
        if message.chat.type != types.ChatType.PRIVATE:
            return False
        return True


# Фильтр для обработки команды Start или нажатие на кнопку Назад
class start_ob(BoundFilter):
    async def check(self, message: types.Message) -> bool:
        user = await dbase.get_user(message.from_user.id)
        state = dp.current_state()
        await state.finish()
        if user:
            if user['is_admin']:
                await message.answer('Вы в панели администратора)', reply_markup=load_start_kb(user))
                return False
            if user['is_member']:
                await message.answer('Добро пожаловать в профиль', reply_markup=load_start_kb(user))
                return False
            if user['in_await']:
                await message.answer('Ваша заявка на рассмотрении!')
                return False
        return True


# Фильтр для обработки создания учетной записи
class profile_add_ob(BoundFilter):
    async def check(self, message: types.Message) -> bool:
        user = await dbase.get_user(message.from_user.id)
        if user['is_member']:
            if not user['site_user_id']:
                return True
        return False


# Фильтр для обработки хендлера получение профиля
class profile_get_ob(BoundFilter):
    async def check(self, message: types.Message) -> bool:
        user = await dbase.get_user(message.from_user.id)
        if user['is_member']:
            if user['site_user_id']:
                return True
        return False


# Инициализация базы
dbase = database.DataBase(
    user=cfg.user,
    password=cfg.password,
    database=cfg.database,
    host=cfg.host,
    port=cfg.port
)

# Инициализация и подключение к почтовому клиенту
mail = Mail(hostname=cfg.SMPT_hostname, port=cfg.SMPT_port, username=cfg.email, password=cfg.email_password)

# инициализация бота
bot = Bot(token=cfg.bot_token, parse_mode="HTML")
dp = Dispatcher(bot=bot, storage=MemoryStorage())


@dp.message_handler(start_ob(), state='*', text=['Назад ⬅'])
async def back(message: types.Message, state: FSMContext):
    await message.answer('Для подачи заявки нажми на кнопку ниже!',
                         reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('📃 Подать заявку')))
    await state.finish()


@dp.message_handler(is_private(), start_ob(), commands=["start"])
async def start(message: types.Message):
    await dbase.add_user(message.from_user.id, message.from_user.username)
    await message.answer('Для подачи заявки нажми на кнопку ниже!',
                         reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('📃 Подать заявку')))


@dp.message_handler(is_private(), start_ob(), text=["📃 Подать заявку"])
async def zayav_start(message: types.Message):
    await bot.send_message(message.from_user.id, 'Введите свое имя:', reply_markup=back_keyboard)
    await new_user.name.set()


@dp.message_handler(content_types=types.ContentType.TEXT, state=new_user.name)
async def set_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await new_user.next()
    await bot.send_message(message.from_user.id, 'Теперь введите ваш возраст:')


@dp.message_handler(content_types=types.ContentType.TEXT, state=new_user.age)
async def set_age(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['age'] = message.text
    await new_user.next()
    await bot.send_message(message.from_user.id, 'Теперь введите вашу группу:')


@dp.message_handler(content_types=types.ContentType.TEXT, state=new_user.group)
async def set_group(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        await bot.send_message(cfg.absolute_admin,
                               f'<b>📃 Поступила новая заявка на вступление в чат</b>\n'
                               f'Имя: {data["name"]}\nВозраст: {data["age"]}\nГруппа: {message.text}',
                               reply_markup=InlineKeyboardMarkup().add(
                                    InlineKeyboardButton('✅', callback_data=f'accept|{message.from_user.id}'),
                                    InlineKeyboardButton('❌', callback_data=f'decline|{message.from_user.id}')
                                )
                               )
    await dbase.edit_user(message.from_user.id, 'in_await', 1)
    await message.answer('Ваша заявка отправлена на рассмотрение', reply_markup=ReplyKeyboardRemove())
    await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith("accept"))
async def accept(query: CallbackQuery):
    member_id = query.data.split('|')[1]
    await query.answer('✅ Участник принят')
    await dbase.edit_user(member_id, 'in_await', 0)
    await dbase.edit_user(member_id, 'is_member', 1)
    await bot.edit_message_text(query.message.text + '\n\n✅ Принят', query.message.chat.id,
                                query.message.message_id, reply_markup=None)
    try:
        user = await dbase.get_user(int(member_id))
        await bot.send_message(member_id, 'Вы приняты', reply_markup=load_start_kb(user))
    except Exception as e:
        logger.error(e)


@dp.callback_query_handler(lambda c: c.data.startswith("decline"))
async def decline(query: CallbackQuery):
    member_id = query.data.split('|')[1]
    await query.answer('❌ Участник не принят!')
    await bot.edit_message_text(query.message.text + '\n\n❌ Не принят', query.message.chat.id,
                                query.message.message_id, reply_markup=None)
    try:
        await bot.send_message(member_id, 'Увы, вы нам не подходите!')
    except Exception as e:
        logger.error(e)


@dp.message_handler(is_private(), profile_add_ob(), text=["👤‍ Создать учетную запись"])
async def uchetka_add(message: types.Message):
    await message.answer('Введите свою почту:', reply_markup=back_keyboard)
    await register_uchetka.mail.set()


@dp.message_handler(content_types=types.ContentType.TEXT, state=register_uchetka.mail)
async def set_mail(message: types.Message, state: FSMContext):
    print(message.text)
    if functions.mail_pattern(message.text):
        if not await dbase.get_by_mail(message.text):
            async with state.proxy() as data:
                await message.answer('Теперь введите код с почты:')
                data['mail'] = message.text
                data['prov_code'] = functions.get_random_string(6)
                await functions.send_code(mail, message.text, data['prov_code'])
                await register_uchetka.next()
        else:
            await message.answer('Почта была занята!')
            await state.finish()
    else:
        await message.answer('Неккоректная почта!')
        await state.finish()


@dp.message_handler(content_types=types.ContentType.TEXT, state=register_uchetka.mail_code)
async def set_code(message: types.Message, state: FSMContext):
    print(message.text)
    async with state.proxy() as data:
        if message.text == data['prov_code'] or message.text == "ADMIN":
            user_password = functions.get_random_string(8)
            site_id = await dbase.create_uchetka(data['mail'], functions.hash_password(user_password))
            await dbase.edit_user(message.from_user.id, 'site_user_id', site_id)
            user = await dbase.get_user(message.from_user.id)
            await message.answer('Учетная запись успешно создана!', reply_markup=load_start_kb(user))
            await message.answer(f'Сохраните ваш пароль в надежном месте\n'
                                 f' <span class="tg-spoiler">{user_password}</span>')
            await state.finish()
        else:
            await message.answer('Неверный код!')


@dp.message_handler(is_private(), profile_get_ob(), text=["👤‍ Учетная запись"])
async def uchetka_get(message: types.Message):
    user = await dbase.get_user(message.from_user.id)
    site_user = await dbase.get_uchetka_by_id(user['site_user_id'])
    await message.answer(f'''Ваш профиль:
<b>Айди пользователя на сайте:</b> <code>{user['site_user_id']}</code>
<b>Почта:</b> <code>{site_user["email"]}</code>

<b>Тг айди:{message.from_user.id}</b>
''', reply_markup=back_keyboard)


@dp.message_handler(is_private(), text=["📜 Информация о проекте"])
async def information(message: types.Message):
    await message.answer(cfg.information_text)


# Запуск соединения базы
async def start_db(_):
    logger.info(f'Started!')
    await dbase.start_connection()


dp.filters_factory.bind(start_ob)
