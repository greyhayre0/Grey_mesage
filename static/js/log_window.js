
async function sendRequest(action) {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const messageDiv = document.getElementById('result');
        
    if (!username || !password) {
        showMessage('Заполните все поля!', 'error');
        return;
    }
        
    try {
        const response = await fetch(`/api/v1/${action}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });
            
        const data = await response.json();
            
        if (response.ok) {
            if (data.redirect) {
                 window.location.href = data.redirect;
            }
        } else {
            // Обработка ошибок
            let errorMessage = '';
                
            if (Array.isArray(data.detail)) {
                const errors = [];
                for (const item of data.detail) {
                    if (item.loc && item.msg) {
                        const field = item.loc[item.loc.length - 1];
                        errors.push(`${field}: ${item.msg}`);
                    } else if (item.msg) {
                        errors.push(item.msg);
                    } else {
                        errors.push(JSON.stringify(item));
                    }
                }
                errorMessage = errors.join('\n');
            } else if (typeof data.detail === 'string') {
                errorMessage = data.detail;
            } else if (typeof data.detail === 'object' && data.detail !== null) {
                errorMessage = JSON.stringify(data.detail, null, 2);
            } else {
                errorMessage = 'Ошибка сервера';
            }
                
            showMessage(errorMessage, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('Ошибка соединения с сервером', 'error');
    }
}
    
function showMessage(text, type) {
    const messageDiv = document.getElementById('result');
    if (text && text.includes('\n')) {
        messageDiv.innerHTML = text.replace(/\n/g, '<br>');
    } else {
        messageDiv.innerHTML = text || 'Ошибка';
    }
    messageDiv.className = `result ${type}`;
}
    
function showLogin() {
    document.getElementById('loginForm').style.display = 'block';
    document.getElementById('registerForm').style.display = 'none';
    document.getElementById('result').innerHTML = '';
    document.getElementById('result').className = 'result';
}
    
function showRegister() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
    document.getElementById('result').innerHTML = '';
    document.getElementById('result').className = 'result';
}
    

document.addEventListener('DOMContentLoaded', function() {
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
        
    function clearMessage() {
        const messageDiv = document.getElementById('result');
        messageDiv.innerHTML = '';
        messageDiv.className = 'result';
    }
        
    if (usernameInput) {
        usernameInput.addEventListener('input', clearMessage);
    }
    if (passwordInput) {
        passwordInput.addEventListener('input', clearMessage);
    }
});
