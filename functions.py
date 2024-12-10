import hashlib
import json
import random
import string
import cfg
from fnmatch import fnmatch
from typing import List
from fastapi import WebSocket


# Класс для более удобной работы с подключениями по вебсокетами
class ConnectionManager:
    # Инициализация подключений и передача объекта с базой
    def __init__(self, dbase) -> None:
        self.active_connections: List[WebSocket] = []
        self.dbase = dbase

    # При подключении пользователя добавляет объект websocket в активных подключения
    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    # При отключении пользователя удаляет объект websocket из активных подключений
    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)

    # При получении сообщения от пользователя записывает его в базу данных и отпрвляет другим пользователям
    async def on_message(self, message: str, creator_id: int) -> None:
        await self.dbase.add_message(creator_id=creator_id, message_data=message)
        for connection in self.active_connections:
            await connection.send_text(json.dumps({"message": message, "author": creator_id}))

    # Выводит из класса количество активных подключений по websocket
    def get_online(self) -> int:
        return len(self.active_connections)


# Получение рандомной строки
def get_random_string(length=48) -> str:
    return "".join(random.choice(string.ascii_letters) for _ in range(length))


# Получение sha256 хеша пароля
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


# Проверка на валидность пароля
def validate_password(password: str, hashed_password_db: str) -> bool:
    return hash_password(password) == hashed_password_db


# Проверка на валидность почты
def mail_pattern(mail) -> bool:
    if mail.split('@')[-1:][0] in cfg.domains:
        return fnmatch(mail, "*@*.*")
    return False


# Отправка кода подтверждения по почте
async def send_code(mail_st, mail, code) -> None:
    await mail_st.send_message("Код для проверки аккаунта!", from_address=cfg.email,
                               to=mail, body=f"Здравствуйте, ваш код для подтверждения почты:\n{code}")
