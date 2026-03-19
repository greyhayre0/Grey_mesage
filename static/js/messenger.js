// static/js/messenger.js

// Глобальные переменные
let currentChatId = null;
let selectedUserId = null;
let ws = null;

// Загрузка при старте
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM загружен');
    loadChats();
});

// Загрузка списка чатов
async function loadChats() {
    try {
        const response = await fetch('/api/chats');
        const chats = await response.json();
        
        const contactList = document.getElementById('contactList');
        contactList.innerHTML = '';
        
        if (chats.length === 0) {
            contactList.innerHTML = '<div class="contact-name"><a>Нет чатов</a></div> ';
            return;
        }
        
        chats.forEach(chat => {
            const chatDiv = document.createElement('div');
            chatDiv.className = 'contact-name';
            chatDiv.style.cursor = 'pointer';
            
            // Добавляем класс active если это текущий выбранный чат
            if (currentChatId === chat.id) {
                chatDiv.classList.add('active');
            }
            
            chatDiv.onclick = () => selectChat(chat.id);
            
            let unreadBadge = '';
            if (chat.unread_count > 0) {
                unreadBadge = ` <span style="color: red; font-weight: bold;">(${chat.unread_count})</span>`;
            }
            
            chatDiv.innerHTML = `
            <div class="mycontact">
                <div><button class="contact-button-del" id="Delcontact">✖︎</button></div>
                <div class="contact-avatar"><img src="${chat.profileimage}" alt="A"></div>
                <div><a>${chat.name}${unreadBadge}</a></div>
            </div>
            `;
            // Добавляем обработчик на кнопку удаления
            const delBtn = chatDiv.querySelector('.contact-button-del');
            delBtn.addEventListener('click', (e) => {
                e.stopPropagation(); // Чтобы не открывался чат при клике на удаление
                deleteChat(chat.id);
            });
            
            contactList.appendChild(chatDiv);
        });
    } catch (error) {
        console.error('Ошибка загрузки чатов:', error);
    }
}

// Выбор чата
async function selectChat(chatId) {
    currentChatId = chatId;
    
    // Перезагружаем список чатов чтобы обновить подсветку
    await loadChats();
    
    document.getElementById('messageInputArea').style.display = 'flex';
    document.getElementById('messagesList').innerHTML = '<div class="incoming">Загрузка...</div>';
    
    await loadMessages(chatId);
    connectWebSocket(chatId);
}

// Загрузка сообщений чата
async function loadMessages(chatId) {
    try {
        const response = await fetch(`/api/chats/${chatId}/messages`);
        const messages = await response.json();
        
        const messagesList = document.getElementById('messagesList');
        messagesList.innerHTML = '';
        
        if (messages.length === 0) {
            messagesList.innerHTML = '<div class="incoming">Нет сообщений</div>';
            return;
        }
        
        messages.reverse().forEach(message => {
            addMessageToChat(message);
        });
        
        messagesList.scrollTop = messagesList.scrollHeight;
    } catch (error) {
        console.error('Ошибка загрузки сообщений:', error);
    }
}

// WebSocket соединение
function connectWebSocket(chatId) {
    if (ws) ws.close();
    
    const wsUrl = (location.protocol === 'https:' ? 'wss:' : 'ws:') + `//${window.location.host}/ws/${chatId}`;
    ws = new WebSocket(wsUrl);
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'new_message') {
            addMessageToChat(data.message);
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket ошибка:', error);
    };
}

// Добавление нового сообщения в чат
function addMessageToChat(message) {
    const messagesList = document.getElementById('messagesList');
    const messageContainer = document.createElement('div');
    
    const time = new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const date = new Date(message.timestamp).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' });
    
    // Получаем ссылку на аватар
    const avatarUrl = message.sender_id === currentUser.id 
        ? currentUser.profileimage   // для себя
        : message.sender_avatar;      // для других
    
    if (message.sender_id === currentUser.id) {
        // Исходящее сообщение (справа)
        messageContainer.className = 'outgoing';
        messageContainer.innerHTML = `
            <div class="message-info">
                <img class="contact-avatar" src="${avatarUrl}" style="width: 25px; height: 25px; border-radius: 50%; object-fit: cover;" alt="avatar">
                <span class="message-sender">Вы</span>
                <span class="message-time">| ${date} ${time} </span>
            </div>
            <div class="message-bubble">
                ${message.content}
            </div>
        `;
    } else {
        // Входящее сообщение (слева)
        messageContainer.className = 'incoming';
        messageContainer.innerHTML = `
            <div class="message-info">
                <img class="contact-avatar" src="${avatarUrl}" style="width: 25px; height: 25px; border-radius: 50%; object-fit: cover;" alt="avatar">
                <span class="message-sender">${message.sender_name}</span>
                <span class="message-time">| ${date} ${time}</span>
            </div>
            <div class="message-bubble">
                ${message.content}
            </div>
        `;
    }
    
    messagesList.appendChild(messageContainer);
    messagesList.scrollTop = messagesList.scrollHeight;
}

// Отправка сообщения
async function sendMessage() {
    const input = document.getElementById('messageText');
    const content = input.value.trim();
    
    if (!content || !currentChatId) return;
    
    try {
        await fetch('/api/messages', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content: content,
                chat_id: currentChatId
            })
        });
        
        input.value = '';
    } catch (error) {
        console.error('Ошибка отправки:', error);
    }
}

// Обработка клавиш в поле ввода
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        if (event.shiftKey) {
            // Shift+Enter - новая строка
            // Ничего не делаем, текст сам перенесется
            return;
        } else {
            // Просто Enter - отправка сообщения
            event.preventDefault();  // Отменяем переход на новую строку
            sendMessage();
        }
    }
}

// Выход
async function logout() {
    await fetch('/logout', { method: 'POST' });
    window.location.href = '/';
}

// Прикрепить файл
function attachFile() {
    alert('Функция прикрепления файлов будет добавлена позже');
}

// Настройки
function setting() {
    alert('Функция настроек удет добавлена позже');
}

// Добавление аватарки
const dialog = document.getElementById('avatarDialog');
const myavatar = document.getElementById('myavatar');
const closeBtn = document.getElementById('closeDialog');
const saveBtn = document.getElementById('saveAvatar');
const avatarInput = document.getElementById('avatarUrl');

// Открыть диалог при клике на аватар
myavatar.addEventListener('click', () => {
    avatarInput.value = currentUser.profileimage || ''; // текущий URL
    dialog.showModal();
});

// Закрыть по кнопке Отмена
closeBtn.addEventListener('click', () => {
    dialog.close();
});

// Сохранить
saveBtn.addEventListener('click', async (e) => {
    e.preventDefault(); // предотвращаем закрытие формы
    
    const newAvatarUrl = avatarInput.value.trim();
    
    if (!newAvatarUrl) {
        alert('Введите URL');
        return;
    }
    
    try {
        const response = await fetch('/update-avatar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                profileimage: newAvatarUrl
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Обновляем на странице
            document.querySelector('#myavatar img').src = newAvatarUrl;
            // Обновляем в объекте
            currentUser.profileimage = newAvatarUrl;
            // Закрываем диалог
            dialog.close();
        } else {
            alert('Ошибка: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка при сохранении');
    }
});

// Закрыть по клику на backdrop
dialog.addEventListener('click', (e) => {
    if (e.target === dialog) {
        dialog.close();
    }
});

// Смена никнейма
const nicknameDialog = document.getElementById('nicknameDialog');
const myname = document.getElementById('myname');
const closeNicknameBtn = document.getElementById('closeNicknameDialog');
const saveNicknameBtn = document.getElementById('saveNickname');
const nicknameInput = document.getElementById('nicknameInput');

// Открыть диалог при клике на никнейм
myname.addEventListener('click', () => {
    nicknameInput.value = currentUser.nickname || '';
    nicknameDialog.showModal();
});

// Закрыть по кнопке Отмена
closeNicknameBtn.addEventListener('click', () => {
    nicknameDialog.close();
});

// Сохранить
saveNicknameBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    
    const newNickname = nicknameInput.value.trim();
    
    if (!newNickname) {
        alert('Никнейм не может быть пустым');
        return;
    }
    
    try {
        const response = await fetch('/api/update-nickname', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                nickname: newNickname
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Обновляем на странице
            myname.textContent = newNickname;
            // Обновляем в объекте
            currentUser.nickname = newNickname;
            // Закрываем диалог
            nicknameDialog.close();
        } else {
            alert('Ошибка: ' + (data.error || 'Неизвестная ошибка'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка при сохранении');
    }
});

// Закрыть по клику на backdrop
nicknameDialog.addEventListener('click', (e) => {
    if (e.target === nicknameDialog) {
        nicknameDialog.close();
    }
});


// Удаление чата
async function deleteChat(chatId) {
    if (!confirm('Удалить чат? Все сообщения будут безвозвратно удалены.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/chats/${chatId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Если удалили текущий открытый чат - очищаем
            if (currentChatId === chatId) {
                currentChatId = null;
                document.getElementById('messageInputArea').style.display = 'none';
                document.getElementById('messagesList').innerHTML = '<div class="incoming">Выберите чат</div>';
            }
            // Перезагружаем список чатов
            await loadChats();
        } else {
            alert('Ошибка: ' + (data.error || 'Не удалось удалить чат'));
        }
    } catch (error) {
        console.error('Ошибка удаления чата:', error);
        alert('Ошибка при удалении');
    }
}