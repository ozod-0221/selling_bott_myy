import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import *
import asyncio
import helper_func as hf

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# States
class OrderStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_contact = State()
    

# Keyboards
def start_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Buyurtma berish"))
    return builder.as_markup(resize_keyboard=True)

def contact_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Kontaktni ulashish", request_contact=True))
    builder.add(KeyboardButton(text="Bekor qilish"))
    return builder.as_markup(resize_keyboard=True)

# Handlers
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        await bot.forward_message(
            chat_id=message.from_user.id,
            from_chat_id=CHANNEL_ID,
            message_id=2,
            protect_content=True
        )
    except Exception as e:
        logging.error(f"Channel forwarding error: {e}")
        await message.answer(
            "Kanaldan ma`lumotlarni olishda xatolik yuz berdi, yana bir bor urinib ko`ring",
            reply_markup=start_keyboard()
        )
    
    await message.answer(
        "Assalomu alekum! Buyurtma berish uchun pastgi qismdagi \n"
        "'Buyurtma berish' tugmasini bosing\n"
        "Yoki pastdagi rangi yozuv ustiga bosing👇🏻👇🏻👇🏻👇🏻👇🏻\n"
        "                          /order",
        reply_markup=start_keyboard()
    )

@dp.message(F.text == "Buyurtma berish")
@dp.message(Command("order"))
async def ask_name(message: types.Message, state: FSMContext):
    await message.answer(
        "Ismingizni yozib jo`nating",
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer("Yoki /cancel komandasi orqali bekor qilishingiz mumkin")
    await state.set_state(OrderStates.waiting_for_name)

@dp.message(OrderStates.waiting_for_name)
async def ask_contact(message: types.Message, state: FSMContext):
    if len(message.text) > 100 or hf.has_digit(message.text):  # Basic name validation
        await message.answer("Iltimos, to'g'ri ism kiriting")
        return
        
    await state.update_data(name=message.text, user_id=message.from_user.id)
    await message.answer(
        f"Rahmat, {message.text}! Endi telefon raqamingizni jo`ntaing!\n"
        "Jo`natish uchun pastdagi tugmalardan foydalaning",
        reply_markup=contact_keyboard()
    )
    await state.set_state(OrderStates.waiting_for_contact)

@dp.message(OrderStates.waiting_for_contact, F.contact)
async def process_contact(message: types.Message, state: FSMContext):
    contact = message.contact
    user_data = await state.get_data()
    
    order_text = (
        f"Yangi buyurtma!\n"
        f"Ism: {user_data.get('name', 'Aniqlanmadi')}\n"
        f"Foydalanuvchi ID: {user_data.get('user_id', 'Aniqlanmadi')}\n"
        f"Telefon: {contact.phone_number}\n"
        f"Username: @{message.from_user.username if message.from_user.username else 'Aniqlanmadi'}"
    )
    
    try:
        await bot.send_message(ADMIN_ID, order_text)
        await message.answer(
            f"Hurmatli {user_data.get('name')}, ma`lumotlaringiz jo`natildi. "
            "Tez orada siz bilan aloqaga chiqishadi",
            reply_markup=start_keyboard()
        )
    except Exception as e:
        logging.error(f"Adminga yuborishda xatolik: {e}")
        await message.answer(
            "Xatolik yuz berdi, yana bir bor urinib ko`ring:\n/start",
            reply_markup=start_keyboard()
        )
    
    await state.clear()

@dp.message(F.text.lower() == "bekor qilish")
@dp.message(Command("cancel"))
async def cancel_order(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi", reply_markup=start_keyboard())

# Fallback handler
@dp.message()
async def handle_unknown(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == OrderStates.waiting_for_name:
        await message.answer("Iltimos, faqat ismingizni yuboring")
    elif current_state == OrderStates.waiting_for_contact:
        await message.answer("Iltimos, kontaktni yuboring yoki 'Bekor qilish' tugmasini bosing")
    else:
        await message.answer("Noma'lum buyruq. /start ni bosing")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import asyncio
    asyncio.run(main())