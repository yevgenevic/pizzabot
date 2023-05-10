import os

import psycopg2
from aiogram import Bot, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from database import conn, cur, create_table

BOT_TOKEN = os.getenv('TOKEN')

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class AddPizzaState(StatesGroup):
    add_name = State()
    add_price = State()


class AddAdminState(StatesGroup):
    waiting_for_user_id = State()


admin_customer_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 Customer", callback_data="customer"),
            InlineKeyboardButton(text="👑 Admin", callback_data="admin"),
            InlineKeyboardButton(text='🆘 Help', callback_data='help')
        ],
    ]
)

admin_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🍕 Pizzalar ro'yxati", callback_data="admin_pizza_list")
        ],
        [
            InlineKeyboardButton(text="🌟 Pizza qo'shish", callback_data="admin_add_pizza"),
            InlineKeyboardButton(text="🗑️ Pizza o'chirish", callback_data="admin_remove_pizza"),
        ],
        [
            InlineKeyboardButton(text="🧾 Buyurtma tarixi", callback_data="admin_order_history")
        ], [
            InlineKeyboardButton(text="back", callback_data="back_to_menu_main")
        ], [
            InlineKeyboardButton(text="Add admin", callback_data="add_admin")
        ],
    ]
)

buy_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🍕 Menu", callback_data="user_menu")
        ],
        [
            InlineKeyboardButton(text="🛒 Savatcha", callback_data="user_basket")
        ],
        [
            InlineKeyboardButton(text="📝 Buyurtmalar tarixi", callback_data="user_order_history")
        ],
        [
            InlineKeyboardButton(text="❌ Buyurtmani bekor qilish", callback_data="user_cancel_order")
        ],
        [
            InlineKeyboardButton(text="🔙 Menyuga qaytish", callback_data="back_to_")
        ]
    ]
)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Assalomu alaykum! Pizzariabotga xush kelibsiz!", reply_markup=admin_customer_markup)


@dp.message_handler()
async def send_welcome(message: types.Message):
    await message.delete()


@dp.callback_query_handler(lambda query: query.data == 'help')
async def process_admin_callback(callback_query: types.CallbackQuery):
    cur.execute("SELECT name, price FROM pizzas;")
    pizzas = cur.fetchall()
    cur.close()

    pizza_list = ''
    for pizza in pizzas:
        pizza_list += f'{pizza[0]} - {pizza[1]} so\'m\n'

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=True)
    bt = KeyboardButton('menu')
    bt1 = KeyboardButton('order')
    bt2 = KeyboardButton('status')
    bt3 = KeyboardButton('cancel')
    bt4 = KeyboardButton('back')
    keyboard.row(bt, bt1)
    keyboard.row(bt2, bt3)
    keyboard.add(bt4)

    help_text = (
        "Salom! Mening nomim Pizzariabot. Men sizga pizzalarni buyurtma berishga yordam beraman. Quyidagi buyruqlardan foydalaning:\n"
    )
    await bot.send_message(callback_query.from_user.id, text=help_text,
                           reply_markup=keyboard)


@dp.message_handler(lambda msg: msg.text == 'back')
async def send_order(message: types.Message):
    await message.answer('Bosh menyuga qaytiz', reply_markup=admin_customer_markup)


@dp.message_handler(lambda msg: msg.text == 'menu')
async def send_menu(message: types.Message):
    cur = conn.cursor()
    cur.execute("SELECT name, price FROM pizzas;")
    pizzas = cur.fetchall()
    cur.close()
    pizza_list = ''
    for pizza in pizzas:
        pizza_list += f'{pizza[0]} - {pizza[1]} so\'m\n'
    await message.reply("Pizzalar ro'yxati:\n" + pizza_list)


@dp.message_handler(lambda msg: msg.text == 'order')
async def send_order(message: types.Message):
    await message.reply(
        "Pizzangizni tanlang va iltimos, miqdorini yuboring. Misol uchun: Margrita 2 - bu buyurtmada 2 ta Margrita pizzasi buyurtma berilgani anglatadi.\n\n")


@dp.message_handler(lambda msg: msg.text == 'status')
async def send_menu(message: types.Message):
    cur = conn.cursor()
    cur.execute(f"SELECT status FROM orders WHERE user_id = '{message.from_user.id}' AND status != 'completed';")
    status = cur.fetchone()
    if status is None:
        await message.reply("Sizda hech qanday aktiv buyurtma yo'q.")
    else:
        await message.reply(f"Sizning buyurtmangiz holati: {status[0]}")
    cur.close()


@dp.message_handler(lambda msg: msg.text == 'cancel')
async def send_menu(message: types.Message):
    cur = conn.cursor()
    cur.execute("DELETE FROM orders WHERE user_id = %s::varchar AND status != 'completed'", (message.from_user.id,))
    conn.commit()
    cur.close()
    await message.reply("Sizning aktiv buyurtmangiz bekor qilindi.")


@dp.callback_query_handler(lambda query: query.data == 'admin')
async def process_admin_callback(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Admin panelga xush kelibsiz', reply_markup=admin_markup)


@dp.callback_query_handler(lambda query: query.data == 'add_admin')
async def add_admin(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, 'Enter the user ID you want to add as an admin:')
    await AddAdminState.waiting_for_user_id.set()


@dp.callback_query_handler(lambda query: query.data == 'back_to_menu_main')
async def process_customer_callback(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Siz orqaga qaytingiz', reply_markup=admin_customer_markup)


@dp.message_handler(state=AddAdminState.waiting_for_user_id)
async def wait(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = message.text.strip()
        if not user_id.isdigit() or int(user_id) <= 0:
            await message.reply("Please enter a valid positive integer as the user ID.")
            return

        data['user_id'] = int(user_id)

        cur = conn.cursor()
        cur.execute("SELECT is_admin FROM users WHERE user_id = %s", (str(data['user_id']),))
        row = cur.fetchone()

    if row and row[0]:
        await message.answer(f"{data['user_id']} is already an admin.", reply_markup=admin_markup)
    else:
        cur = conn.cursor()
        cur.execute("INSERT INTO users (user_id, is_admin) VALUES (%s, %s)", (data['user_id'], True))
        conn.commit()

    await message.answer(f"{data['user_id']} added to the list of admins.", reply_markup=admin_markup)
    await state.finish()
    await message.delete()


@dp.callback_query_handler(text='admin_pizza_list')
async def show_pizza_list(callback_query: types.CallbackQuery):
    cur = conn.cursor()
    cur.execute("SELECT name, price FROM pizzas")
    pizzas = cur.fetchall()
    cur.close()
    message_text = ''
    if pizzas:
        for pizza in pizzas:
            message_text += f'{pizza[0]} - {pizza[1]} so\'m\n'
    else:
        message_text = 'Pizzalar ro\'yxati bo\'sh'
    await bot.send_message(chat_id=callback_query.from_user.id, text=message_text, reply_markup=admin_markup)
    await callback_query.message.delete()


@dp.callback_query_handler(text='admin_add_pizza')
async def add_new_pizza(callback_query: types.CallbackQuery):
    await bot.send_message(chat_id=callback_query.from_user.id, text='Yangi pizzaning nomini kiriting:')
    await AddPizzaState.add_name.set()


@dp.message_handler(state=AddPizzaState.add_name)
async def add_pizza_price(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await message.answer('Yangi pizzaning narxini kiriting:')
    await AddPizzaState.add_price.set()


@dp.message_handler(state=AddPizzaState.add_price)
async def add_pizza_price(message: types.Message, state: FSMContext):
    try:
        price = int(message.text)
        if price < 0:
            await message.answer('Noto\'g\'ri qiymat kiritildi, iltimos musbat qiymat kiriting.')
            return
        async with state.proxy() as data:
            data['price'] = price
        cur = conn.cursor()
        cur.execute(f"INSERT INTO pizzas (name, price) VALUES ('{data['name']}', {data['price']})")
        conn.commit()
        cur.close()
        try:
            await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id,
                                        text=f"{data['name']} {data['price']} so'm narxi bilan ro'yxatga qo'shildi.",
                                        reply_markup=admin_markup)
        except Exception:
            await bot.send_message(chat_id=message.chat.id,
                                   text=f"{data['name']} {data['price']} so'm narxi bilan ro'yxatga qo'shildi.",
                                   reply_markup=admin_markup)
        await state.finish()
    except ValueError:
        await message.answer('Narxni raqam ko\'rinishida kiriting, masalan: 15000')
        await message.delete()


class DeletePizzaState(StatesGroup):
    waiting_for_pizza_name = State()


@dp.callback_query_handler(text='admin_remove_pizza')
async def delete_pizza(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Qaysi pizzani o\'chirmoqchisiz?')
    cur = conn.cursor()
    cur.execute("SELECT name, price FROM pizzas;")
    pizzas = cur.fetchall()
    cur.close()
    pizza_list = ''
    for pizza in pizzas:
        pizza_list += f'{pizza[0]} - {pizza[1]} so\'m\n'
    await bot.send_message(callback_query.from_user.id, "Pizzalar ro'yxati:\n" + pizza_list)
    await callback_query.message.delete()
    await state.update_data(pizza_list=pizza_list)
    await DeletePizzaState.waiting_for_pizza_name.set()


@dp.message_handler(state=DeletePizzaState.waiting_for_pizza_name)
async def process_delete_pizza(message: types.Message, state: FSMContext):
    pizza_name = message.text.strip()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT name FROM pizzas WHERE name = '{pizza_name}'")
    except psycopg2.errors.SyntaxError as e:
        print(f"tugri kiriting: {e}")
    row = cur.fetchone()
    if row is None:
        await message.answer('Ushbu nomli pitsa topilmadi, iltimos nomini tekshiring.')
        await message.delete()
        return
    cur.execute(f"DELETE FROM pizzas WHERE name = '{pizza_name}'")
    conn.commit()
    cur.close()
    await message.answer(f'{pizza_name} o\'chirildi', reply_markup=admin_markup)
    await state.finish()
    await message.delete()


@dp.callback_query_handler(text='admin_order_history')
async def show_order_history(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    cur = conn.cursor()
    query = 'SELECT id, user_id,pizza_name, quantity, status, created_at FROM orders'
    cur.execute(query)
    orders = cur.fetchall()
    cur.close()
    message_text = ''
    for order in orders:
        message_text += f"ID: {order[0]}\n"
        message_text += f"User: {callback_query.from_user.first_name}\n"
        message_text += f"Pizza: {order[2]} \n"
        message_text += f"Quantity: {order[3]}\n"
        message_text += f"status: {order[4]}\n"
        message_text += f"created_at: {order[5]}\n"
        message_text += "---------------+--------\n"
    if message_text == '':
        message_text = "Hozircha hech qanday buyurtma yo'q."
    await bot.send_message(chat_id=callback_query.from_user.id,
                           text=message_text,
                           reply_markup=admin_markup)


@dp.callback_query_handler(lambda query: query.data == 'customer')
async def process_customer_callback(callback_query: types.CallbackQuery):
    btn = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🍕 Menu", callback_data="user_menu")
            ],
            [
                InlineKeyboardButton(text="🛒 Savatcha", callback_data="user_basket")
            ],
            [
                InlineKeyboardButton(text="📝 Buyurtmalar tarixi", callback_data="user_order_history")
            ],
            [
                InlineKeyboardButton(text="❌ Buyurtmani bekor qilish", callback_data="user_cancel_order")
            ], [
                InlineKeyboardButton(text="❌ orqaga", callback_data="back_to_menu_main")
            ]
        ])
    await bot.send_message(callback_query.from_user.id, 'Siz buyurtma beruvchi mijozsiz.',
                           reply_markup=btn)
    await callback_query.message.delete()


@dp.callback_query_handler(lambda query: query.data == 'user_cancel_order')
async def process_user_cancel_order(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    cur = conn.cursor()
    cur.execute("DELETE FROM orders WHERE user_id = %s::text AND status != 'completed'",
                (str(callback_query.from_user.id),))
    conn.commit()
    cur.close()
    await bot.send_message(callback_query.from_user.id, "Sizning aktiv buyurtmangiz bekor qilindi.",
                           reply_markup=buy_markup)


@dp.callback_query_handler(lambda query: query.data == 'user_order_history')
async def process_user_order_history(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    cur = conn.cursor()
    query = 'SELECT pizza_name, quantity, status FROM orders WHERE user_id = %s::varchar(255)'
    cur.execute(query, (str(callback_query.from_user.id),))
    orders = cur.fetchall()
    cur.close()
    message_text = ''
    for order in orders:
        message_text += f"Pizza: {order[0]}\n"
        message_text += f"Quantity: {order[1]}\n"
        message_text += f"Status: {order[2]}\n"
        message_text += "-----------------------\n"
    if message_text == '':
        message_text = "Hozircha hech qanday buyurtma yo'q."
    await bot.send_message(chat_id=callback_query.from_user.id,
                           text=message_text,
                           reply_markup=buy_markup)


@dp.callback_query_handler(lambda query: query.data == 'user_basket')
async def process_user_basket(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    user_idd = str(callback_query.from_user.id)
    cur = conn.cursor()
    cur.execute('SELECT user_id,pizza_name, quantity FROM orders  ', (user_idd, 'In basket'))
    orders = cur.fetchall()
    cur.close()
    message_text = ''
    for order in orders:
        if order[0] == user_idd:
            message_text += f"Pizza: {order[1]}\nQuantity: {order[2]}\n-----------------------\n"
    if not message_text:
        message_text = "Sizning savatchangiz bo'sh"
    await bot.send_message(chat_id=user_idd, text=message_text, reply_markup=buy_markup)


@dp.callback_query_handler(lambda c: c.data == 'user_menu')
async def process_buy_pizza(callback_query: types.CallbackQuery):
    cur = conn.cursor()
    cur.execute("SELECT name, price FROM pizzas;")
    pizzas = cur.fetchall()
    cur.close()
    pizza_list = ''
    for pizza in pizzas:
        pizza_list += f'{pizza[0]} - {pizza[1]} so\'m\n'
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[
                            [InlineKeyboardButton(text=pizza[0], callback_data=f"pizza_{pizza[0]}")] for pizza in pizzas
                        ] + [
                            [InlineKeyboardButton(text="🔙 Menyuga qaytish", callback_data="back_to")]
                        ]
    )
    await bot.edit_message_reply_markup(chat_id=callback_query.from_user.id,
                                        message_id=callback_query.message.message_id, reply_markup=reply_markup)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('pizza_'))
async def process_pizza(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    pizza_name = callback_query.data.split('_')[1]
    cur = conn.cursor()
    cur.execute(f"SELECT id, price ,name FROM pizzas WHERE name = '{pizza_name}';")
    pizza_data = cur.fetchone()
    pizza_id, pizza_price, pizza_nam = pizza_data[0], pizza_data[1], pizza_data[2]
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO orders (user_id, pizza_id, pizza_name, quantity, status) "
        "VALUES (%s, %s, %s, %s, %s)",
        (callback_query.from_user.id, pizza_id, pizza_nam, 1, "New"),
    )
    conn.commit()
    cur.close()
    await bot.send_message(chat_id=callback_query.from_user.id,
                           text=f"{pizza_name} {pizza_price} so'm narxi bilan savatga qo'shildi.\n\n",
                           reply_markup=buy_markup)


@dp.callback_query_handler(lambda query: query.data == 'back_to')
async def process_customer_callback(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Siz orqadasz',
                           reply_markup=buy_markup)


@dp.callback_query_handler(lambda query: query.data == 'back_to_')
async def process_customer_callback(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Siz orqadasz',
                           reply_markup=admin_customer_markup)


@dp.callback_query_handler(lambda query: query.data == 'back')
async def process_customer_callback(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Siz orqadasz',
                           reply_markup=admin_markup)


async def on_startup(dp):
    create_table()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
