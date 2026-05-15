document.addEventListener('DOMContentLoaded', function() {
    const loginBtn = document.querySelector('.formm button');
    
    if (loginBtn) {
        loginBtn.addEventListener('click', async function() {
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
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: email, password: password })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    localStorage.setItem('userId', data.user.id);
                    localStorage.setItem('userEmail', data.user.email);
                    
                    msgDiv.style.color = 'green';
                    msgDiv.innerHTML = 'Успешный вход';
                    setTimeout(() => {
                        window.location.href = 'index.html';
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