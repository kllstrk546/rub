from aiogram import Router

from src.bot.handlers_user import router as user_router


router = Router(name="main")
router.include_router(user_router)
