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
            contactList.innerHTML = '<div class="contact-name"><a>Нет чатов</a></div>';
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
            
            chatDiv.innerHTML = `<a>${chat.name}${unreadBadge}</a>`;
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
    
    const time = new Date(message.timestamp).toLocaleTimeString();
    const date = new Date(message.timestamp).toLocaleDateString();
    
    if (message.sender_id === currentUser.id) {
        // Исходящее сообщение (справа)
        messageContainer.className = 'outgoing';
        messageContainer.innerHTML = `
            <div class="message-info">
                <span class="message-sender">Вы</span>
                <span class="message-time">| ${time}</span>
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
                <span class="message-sender">${message.sender_name}</span>
                <span class="message-time">| ${time}</span>
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