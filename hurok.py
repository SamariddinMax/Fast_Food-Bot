from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio





bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Тугмаҳо
menu_button = KeyboardButton(text="📋 Меню")
cart_button = KeyboardButton(text="🛒 Корзина")
order_button = KeyboardButton(text="🚀 Оформить заказ")
confirm_button = KeyboardButton(text="✅ Тасдиқ")

main_kb = ReplyKeyboardMarkup(
    keyboard=[[menu_button, cart_button], [order_button, confirm_button]],
    resize_keyboard=True
)

# Маълумоти муваққатӣ
user_cart = {}
user_data = {}

# FSM
class OrderState(StatesGroup):
    waiting_for_name = State()
    waiting_for_address = State()

# Start
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Салом! Ман боти фармоиши хӯрок ҳастам! 🍔",
        reply_markup=main_kb
    )

# Меню
@dp.message(lambda msg: msg.text == "📋 Меню")
async def show_menu(message: Message):
    food_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍕 Пицца", callback_data="food_pizza")],
        [InlineKeyboardButton(text="🍔 Бургер", callback_data="food_burger")],
        [InlineKeyboardButton(text="🥤 Кола", callback_data="food_cola")]
    ])
    await message.answer("Менюи мо:", reply_markup=food_kb)

# Илова ба корзина
@dp.callback_query(lambda c: c.data.startswith("food_"))
async def add_to_cart(callback: CallbackQuery):
    user_id = callback.from_user.id
    item = callback.data.replace("food_", "")

    if user_id not in user_cart:
        user_cart[user_id] = []
    user_cart[user_id].append(item)

    await callback.answer(f"{item.capitalize()} ба корзина илова шуд ✅", show_alert=True)

# Нишон додани корзина
@dp.message(lambda msg: msg.text == "🛒 Корзина")
async def show_cart(message: Message):
    user_id = message.from_user.id
    cart = user_cart.get(user_id, [])

    if not cart:
        await message.answer("Корзинаи шумо холӣ аст ❌")
    else:
        items = "\n".join(f"– {item.capitalize()}" for item in cart)
        await message.answer(f"📦 Фармоишҳои шумо:\n{items}")

# Оформить заказ → ном
@dp.message(lambda msg: msg.text == "🚀 Оформить заказ")
async def ask_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not user_cart.get(user_id):
        await message.answer("Аввал хӯрок илова кунед! 🍕")
        return

    await message.answer("Лутфан, номи худро нависед:")
    await state.set_state(OrderState.waiting_for_name)

# Ном → адрес
@dp.message(OrderState.waiting_for_name)
async def save_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data[user_id] = {"name": message.text}
    await message.answer("Адреси худро нависед:")
    await state.set_state(OrderState.waiting_for_address)

# Адрес → охири FSM
@dp.message(OrderState.waiting_for_address)
async def save_address(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data[user_id]["address"] = message.text
    await state.clear()
    await message.answer("✅ Маълумоти шумо нигоҳ дошта шуд. Барои тасдиқ тугмаи ✅ Тасдиқ ро пахш кунед.")

# Паёми ҷамъбаст бо тугмаи тасдиқ
@dp.message(lambda msg: msg.text == "✅ Тасдиқ")
async def confirm_order(message: Message):
    user_id = message.from_user.id
    name = user_data.get(user_id, {}).get("name", "Номаълум")
    address = user_data.get(user_id, {}).get("address", "Номаълум")
    cart = user_cart.get(user_id, [])

    if not cart:
        await message.answer("Корзинаи шумо холӣ аст ❌")
        return

    items = "\n".join(f"– {item.capitalize()}" for item in cart)

    await message.answer(
        f"📦 Фармоиши шумо:\n"
        f"👤 Ном: {name}\n"
        f"📍 Адрес: {address}\n"
        f"🍽️ Хӯрокҳо:\n{items}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Тасдиқ", callback_data="confirm_order")]
        ])
    )

# Callback → фиристодан ба админ ва поккунӣ
@dp.callback_query(lambda c: c.data == "confirm_order")
async def handle_confirmation(callback: CallbackQuery):
    user_id = callback.from_user.id
    name = user_data.get(user_id, {}).get("name", "Номаълум")
    address = user_data.get(user_id, {}).get("address", "Номаълум")
    cart = user_cart.get(user_id, [])

    items = "\n".join(f"– {item.capitalize()}" for item in cart)

    # Фиристодан ба админ
    await bot.send_message(
        ADMIN_ID,
        f"📥 Фармоиши нав:\n"
        f"👤 Ном: {name}\n"
        f"📍 Адрес: {address}\n"
        f"🆔 Telegram ID: {user_id}\n"
        f"🍽️ Хӯрокҳо:\n{items}"
    )

    # Пок кардани маълумот
    user_cart.pop(user_id, None)
    user_data.pop(user_id, None)

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("✅ Фармоиши шумо ба админ фиристода шуд. Ташаккур барои истифода! 🙏")
    await callback.answer()

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("bot started")
    asyncio.run(main())
