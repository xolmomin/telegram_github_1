import asyncio
import csv
import logging
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import settings
from models import Region, District

dp = Dispatcher()


class RegionUpdateForm(StatesGroup):
    name = State()


def make_region_inline_btns():
    regions = Region.get_all()
    ikm = InlineKeyboardBuilder()
    for region in regions:
        ikm.row(
            InlineKeyboardButton(text=region.name, callback_data=f'region:{region.id}'),
        )
    return ikm


def make_districts_inline_btns(region_id):
    districts = District.filter(region_id=region_id)
    ikm = InlineKeyboardBuilder()
    for district in districts:
        ikm.row(
            InlineKeyboardButton(text=district.name, callback_data=f'district:{district.id}'),
            InlineKeyboardButton(text='✏️', callback_data=f'change_district:{district.id}'),
            InlineKeyboardButton(text='❌', callback_data=f'remove_district:{district.id}')
        )
    ikm.row(
        InlineKeyboardButton(text='⬅️ Back', callback_data='back:region'),
    )
    return ikm


@dp.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer('Xush kelibsiz!')
    ikm = make_region_inline_btns()
    await message.answer('Viloyatlar', reply_markup=ikm.as_markup())


@dp.callback_query(F.data.startswith('region:'))
async def callback_handler(callback: CallbackQuery) -> None:
    region_id = callback.data.removeprefix('region:')
    ikm = make_districts_inline_btns(region_id)
    await callback.message.edit_text('Tumanlar')
    await callback.message.edit_reply_markup(callback.inline_message_id, reply_markup=ikm.as_markup())


@dp.callback_query(F.data.startswith('change_district:'))
async def callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    district_id = callback.data.removeprefix('change_district:')
    await state.update_data(district_id=district_id)
    await state.set_state(RegionUpdateForm.name)
    await callback.message.answer('Yangi nomini kiriting')


@dp.message(RegionUpdateForm.name)
async def callback_handler(message: Message, state: FSMContext) -> None:
    new_district_name = message.text
    data = await state.get_data()
    district_id = data['district_id']
    District.update(district_id, name=new_district_name)
    await state.clear()
    await message.answer('Nomi ozgartirildi!')


@dp.callback_query(F.data.startswith('remove_district:'))
async def callback_handler(callback: CallbackQuery) -> None:
    district_id = callback.data.removeprefix('remove_district:')
    district = District.delete(district_id)
    await callback.answer(f"{district.name} o'chirildi", show_alert=True)
    ikm = make_districts_inline_btns(district.region_id)
    await callback.message.edit_reply_markup(callback.inline_message_id, reply_markup=ikm.as_markup())


@dp.callback_query(F.data.startswith('back:'))
async def callback_handler(callback: CallbackQuery) -> None:
    key = callback.data.removeprefix('back:')
    if key == 'region':
        ikm = make_region_inline_btns()
        await callback.message.edit_text('Viloyatlar')
        await callback.message.edit_reply_markup(callback.inline_message_id, reply_markup=ikm.as_markup())


@dp.message(Command('migrate'))
async def migrate_handler(message: Message) -> None:
    with open('regions.csv', encoding='utf-8-sig') as f1, open('districts.csv', encoding='utf-8-sig') as f2:
        regions = csv.DictReader(f1)
        districts = csv.DictReader(f2)
        Region.bulk_create(list(regions))
        District.bulk_create(list(districts))

    await message.answer('Bazaga yozildi')


async def main() -> None:
    bot = Bot(settings.TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
