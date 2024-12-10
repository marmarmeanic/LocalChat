import sys
import threading

from aiogram.utils import executor
import uvicorn

from bot import start_db
from bot import dp
import cfg

def run_backend():
    uvicorn.run("backend:app", host=cfg.back_host, port=cfg.back_port, reload=True)

def run_bot():
    executor.start_polling(dp, skip_updates=True, on_startup=start_db)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    threading.Thread(target=run_backend).start()
    input()
    sys.exit(0)
