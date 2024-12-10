import math
import time

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse
import sys
import functions
import cfg
from fastapi.staticfiles import StaticFiles
import uvicorn
from database import DataBase

from pydantic import BaseModel, Field


# Инициализация базы
dbase = DataBase(
        user=cfg.user,
        password=cfg.password,
        database=cfg.database,
        host=cfg.host,
        port=cfg.port
        )


# Инициализация FastApi
app = FastAPI(docs_url=None)
app.mount('/static', StaticFiles(directory='static', html=True), name='static')


# Класс для валидации поступающих данных для входа от клиента
class user_data(BaseModel):
    username: str
    password: str = Field(min_length=3, max_length=24)


# Менеджер для работы с вебсокетами
manager = functions.ConnectionManager(dbase)


# Проверка актуальности куков
async def check_actuality(request) -> bool:
    sess = request.cookies.get('session_id')
    if sess:
        profile = await dbase.get_profile_by_key(sess)
        if profile:
            if math.floor(time.time()) < profile['expires']:
                return True
    return False


@app.get("/", response_class=RedirectResponse)
async def check(request: Request):
    if await check_actuality(request):
        return '/chat'
    return '/login'


@app.get(path="/login")
async def login_page(request: Request):
    if not await check_actuality(request):
        return FileResponse('./static/login.html', media_type='text/html')
    else:
        return RedirectResponse("/chat")


@app.post("/auth")
async def auth(user: user_data, response: JSONResponse):
    usr = await dbase.get_by_mail(user.username)
    if usr:
        if functions.validate_password(user.password, usr['password']):
            session_id, expires = functions.get_random_string(), math.floor(time.time() + 86400)
            await dbase.set_session(usr['site_user_id'], session_id, expires)
            response.set_cookie(key='session_id', value=session_id, expires=expires)
            response.set_cookie(key='user_id', value=usr['site_user_id'], expires=expires)
            return {'ok': True}
    return {'ok': False, 'msg': 'Неверные данные'}


@app.get(path="/chat")
async def chat_page(request: Request):
    if await check_actuality(request):
        return FileResponse('./static/index.html', media_type='text/html')
    else:
        return RedirectResponse("/login")


@app.get(path="/logout")
async def logout(request: Request):
    user = await dbase.get_profile_by_key(request.cookies.get('session_id'))
    print(user)
    await dbase.log_out(user['site_user_id'])


@app.websocket("/ws")
async def get_ws(websocket: WebSocket):
    if await check_actuality(websocket):
        user = await dbase.get_profile_by_key(websocket.cookies.get('session_id'))
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                await manager.on_message(creator_id=user['site_user_id'], message=data)
        except WebSocketDisconnect:
            manager.disconnect(websocket)
    return RedirectResponse("/login")


@app.get(path="/last")
async def last_msgs(request: Request):
    if await check_actuality(request):
        messages = await dbase.get_messages()
        ret = {"messages": []}
        for message in messages:
            ret["messages"].append({'message': message['message_data'],
                                    'author': message['creator_id'],
                                    'time': message['time']})
        ret["messages"].reverse()
        return ret
    else:
        return RedirectResponse("/login")


@app.get(path='/online')
async def online_members(request: Request):
    if await check_actuality(request):
        return {'online': manager.get_online()}
    else:
        return RedirectResponse("/login")


@app.on_event("startup")
async def startup_event():
    await dbase.start_connection()
