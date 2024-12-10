document.querySelector('.submit').addEventListener('click', function() {
    const login = document.querySelector('input[type="login"]').value;
    const password = document.querySelector('input[type="password"]').value;

    if (login && password){
        const data = {
            username: login,
            password: password
        };

        fetch('./auth', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Данные успешно отправлены на сервер:', data);
            if (data.ok) {
                window.location.href = './chat';
            } else{
                document.getElementById("alert").setAttribute("style", "display: flex;");
                document.getElementById("alert_msg").textContent = data.msg;
            }
        })
        .catch(error => {
            console.error('Произошла ошибка при отправке данных:', error);
        });
    } else{
        alert('Fields are empty');
    }
});

$(document).keypress(function (e) {
    if (e.which == 13) {
            console.log(document.querySelector('input[type="password"]'));
            document.querySelector('.submit').click();
    }
});
