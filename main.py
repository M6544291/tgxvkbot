import config
import vk_api

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext

session = vk_api.VkApi(token=config.VK_TOKEN)
api = session.get_api()
upload = vk_api.VkUpload(api)

bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class States(StatesGroup):
    add_post = State()


@dp.message_handler(Text(equals="отмена", ignore_case=True),
                    state="*")
async def cancel_handler(msg: types.Message,
                         state: FSMContext):
    await state.finish()

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Опубликовать пост")

    await msg.answer("Вы вернулись назад", reply_markup=keyboard)


@dp.message_handler(commands=["start"])
async def start_handler(msg: types.Message):
    if msg.from_user.id != config.ADMIN_ID:
        await msg.answer("Ты не админ")

    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Опубликовать пост")

        await msg.answer("Привет :3", reply_markup=keyboard)


@dp.message_handler(state=States.add_post, content_types=["text", "photo"])
async def add_post_state_handler(msg: types.Message,
                                 state: FSMContext):
    photo = None

    if msg.photo:
        await msg.photo[0].download("photo.jpg")

        photo = upload.photo_wall(
            "photo.jpg",
            group_id=-config.GROUP_ID,
            caption=msg.text
        )[0]

        photo = "photo{}_{}".format(photo["owner_id"], photo["id"])

    text = msg.caption or msg.text

    api.wall.post(
        owner_id=config.GROUP_ID,
        attachments=photo,
        message=text
    )


@dp.message_handler(
    lambda msg: config.ADMIN_ID == msg.from_user.id,
    Text(equals="опубликовать пост", ignore_case=True)
)
async def add_post_handler(msg: types.Message):
    await States.add_post.set()

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Отмена")

    await msg.answer("Отправьте текст поста",
                     reply_markup=keyboard)


executor.start_polling(dp, skip_updates=True)
