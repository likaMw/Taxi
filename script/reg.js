document.addEventListener('DOMContentLoaded', function() {
    const registerBtn = document.querySelector('.formm button');
    
    if (registerBtn) {
        registerBtn.addEventListener('click', async function() {
            const email = document.querySelector('input[name="email"]').value;
            const password = document.querySelector('input[name="password"]').value;
            
            let msgDiv = document.getElementById('message');
            if (!msgDiv) {
                msgDiv = document.createElement('div');
                msgDiv.id = 'message';
                msgDiv.style.textAlign = 'center';
                msgDiv.style.marginTop = '10px';
                document.querySelector('.from-full').appendChild(msgDiv);
            }
            
            if (!email || !password) {
                msgDiv.style.color = 'red';
                msgDiv.innerHTML = 'Заполните все поля';
                return;
            }
            
            msgDiv.innerHTML = '⏳ Отправка...';
            
            try {
                const response = await fetch('/api/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: email, password: password })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    msgDiv.style.color = 'green';
                    msgDiv.innerHTML = 'Успешная регистрация';
                    setTimeout(() => {
                        window.location.href = 'login.html';
                    }, 1500);
                } else {
                    msgDiv.style.color = 'red';
                    msgDiv.innerHTML = + data.message;
                }
            } catch (error) {
                msgDiv.style.color = 'red';
                msgDiv.innerHTML = 'Ошибка соединения с сервером';
            }
        });
    }
});