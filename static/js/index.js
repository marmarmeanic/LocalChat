const inputField = document.getElementById("message_text");
let counter = 0;
var elName = "";
const socket = new WebSocket('ws://127.0.0.1:80/ws');
var userId = document.cookie.split("user_id=")[1];
let i = 0;


var last = function(){
    fetch('./last', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
    })
    .then(response => response.json())
    .then(data => {
        console.log('Данные успешно отправлены на сервер:', data);
        for (var key in data.messages){
            var msg_ = 'msg_' + counter;
            var msg_ms_ = 'msg_ms_' + counter;
            console.log(data.messages[key].message);
            console.log(data.messages[key].author);
            console.log(getTime(data.messages[key].time));
            if(data.messages[key].author == userId) {
                CreateDiv('msg my', 'msg_', 'messages');
                CreateDiv('ms', 'msg_ms_', msg_);
                CreateP("Вы:", 'msg_text_name', 'margin-top: 10px; margin-left: 10px;', msg_ms_); // Имя отправившего сообщение
                CreateP(data.messages[key].message, 'msg_text_p', 'margin-bottom: 10px;', msg_ms_); // Само сообщение
                CreateP(getTime(data.messages[key].time), 'time', 'margin: 10px; align-self: flex-end;', msg_); // Время отправки
            }
            else {
                CreateDiv('bobic', '', 'messages')
                CreateDiv('msg', 'msg_', `${counter}`);
                CreateDiv('ms', 'msg_ms_', msg_);
                CreateP(`Пользователь ${data.messages[key].author}:`, 'msg_text_name', 'margin-top: 10px; margin-left: 10px;', msg_ms_); // Имя отправившего сообщение
                CreateP(data.messages[key].message, 'msg_text_p', 'margin-bottom: 10px;', msg_ms_); // Само сообщение
                CreateP(getTime(data.messages[key].time), 'time', 'margin: 10px; align-self: flex-end;', msg_); // Время отправки
            }
            location.href = "#msg_" + counter;
            counter += 1;
            delNoMsg(); // Скрыть надпись "Нет сообщений"
        };
    })
    .catch(error => {
        console.error('Произошла ошибка при отправке данных:', error);
    });
};


last();
Online();


// Чек онлайна
async function Online() {
    while (i == 0) {
        await new Promise(resolve => setTimeout(resolve, 2000)); // Ждем 2 секунды
        try {
            const response = await fetch('./online', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
            });
            if (!response.ok) {
                throw new Error('Ошибка HTTP: ' + response.status);
            }

            const data = await response.json();
            console.log('Онлайн:', data.online);
            document.getElementById("online").textContent = data.online;
        } catch (error) {
            console.error('Произошла ошибка при отправке данных:', error);
        }
    }
}


socket.onopen = function(event) {
    console.log('WebSocket connection opened');
    document.getElementById("name").textContent = `Пользователь ${userId}`;
    console.log(`Пользователь ${userId}`);
};


function Logout(){
    i = 1;
    fetch('./logout', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
    })
    window.location.href = './login';
}


socket.addEventListener("message", (event) => {
    var msg_ = 'msg_' + counter;
    var msg_ms_ = 'msg_ms_' + counter;
    var da = JSON.parse(event.data);
    if(da.author == userId) {
        CreateDiv('msg my', 'msg_', 'messages');
        CreateDiv('ms', 'msg_ms_', msg_);
        CreateP("Вы:", 'msg_text_name', 'margin-top: 10px; margin-left: 10px;', msg_ms_); // Имя отправившего сообщение
        CreateP(JSON.parse(event.data).message, 'msg_text_p', 'margin-bottom: 10px;', msg_ms_); // Само сообщение
        CreateP(getTime(), 'time', 'margin: 10px; align-self: flex-end;', msg_); // Время отправки
    }
    else {
        CreateDiv('bobic', '', 'messages')
        CreateDiv('msg', 'msg_', `${counter}`);
        CreateDiv('ms', 'msg_ms_', msg_);
        CreateP(`Пользователь ${da.author}:`, 'msg_text_name', 'margin-top: 10px; margin-left: 10px;', msg_ms_); // Имя отправившего сообщение
        CreateP(JSON.parse(event.data).message, 'msg_text_p', 'margin-bottom: 10px;', msg_ms_); // Само сообщение
        CreateP(getTime(), 'time', 'margin: 10px; align-self: flex-end;', msg_); // Время отправки
    }
    location.href = "#msg_" + counter;
    counter += 1;
    delNoMsg(); // Скрыть надпись "Нет сообщений"
    inputField.value = "";
    inputField.focus();
});


function InputValue(msg){
    if(inputField.value.length > 0){
        socket.send(inputField.value)
    }
}


function CreateP(inputF, clas, style, parentEl) {
    const place = document.getElementById(parentEl)
    const p = document.createElement('p');
    if (clas != 'none') {
        p.setAttribute('class', clas);
    }
    if (style != 'none') {
        p.setAttribute('style', style);
    }
    if (inputF != 'none') {
        p.textContent = inputF
    }
    place.appendChild(p);
}


function CreateDiv(clas, idPref, parentEl) {
    const place = document.getElementById(parentEl)
    const Div = document.createElement('div');
    Div.setAttribute('class', clas);
    Div.setAttribute('id', idPref + counter);
    place.appendChild(Div);
}


function delNoMsg() {
    const noMsg = document.getElementById("no_msg");
    if (counter != 0){
        noMsg.setAttribute('style', 'display: none;')
    }
}


function getTime(time) {
    var date = new Date(null);
    date.setSeconds(time)
    console.log(date)
    var hours = date.getHours();
    var minutes = date.getMinutes();
    var seconds = date.getSeconds();
    return hours + ":" + minutes + ":" + seconds;
}

$(document).keypress(function (e) {
    if (e.which == 13) {

            document.querySelector('#submit').click();
    }
});