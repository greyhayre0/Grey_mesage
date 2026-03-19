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
//function attachFile() {
//    alert('Функция прикрепления файлов будет добавлена позже');
//}


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















// Функция для сжатия изображения и конвертации в JPEG
async function compressImage(file, maxSizeMB = 2) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        
        reader.onload = (event) => {
            const img = new Image();
            img.src = event.target.result;
            
            img.onload = () => {
                const canvas = document.createElement('canvas');
                let width = img.width;
                let height = img.height;
                
                // Вычисляем новые размеры если изображение слишком большое
                const maxDimension = 1920; // максимальный размер по большей стороне
                if (width > height && width > maxDimension) {
                    height = Math.round((height * maxDimension) / width);
                    width = maxDimension;
                } else if (height > maxDimension) {
                    width = Math.round((width * maxDimension) / height);
                    height = maxDimension;
                }
                
                canvas.width = width;
                canvas.height = height;
                
                const ctx = canvas.getContext('2d');
                
                // Заливаем белым фоном (для PNG с прозрачностью)
                ctx.fillStyle = '#FFFFFF';
                ctx.fillRect(0, 0, width, height);
                
                // Рисуем изображение поверх белого фона
                ctx.drawImage(img, 0, 0, width, height);
                
                // Качество сжатия (начинаем с 0.9 и уменьшаем если нужно)
                let quality = 0.9;
                let compressedDataUrl;
                
                const compressWithQuality = () => {
                    // Всегда конвертируем в JPEG
                    compressedDataUrl = canvas.toDataURL('image/jpeg', quality);
                    
                    // Приблизительный расчет размера из base64
                    // Формула: размер в байтах = (длина строки * 3) / 4 - (количество символов = в конце)
                    const compressedSize = Math.round((compressedDataUrl.length * 3) / 4);
                    
                    console.log(`Попытка с качеством ${quality}: ${Math.round(compressedSize/1024)}KB`);
                    
                    if (compressedSize > maxSizeMB * 1024 * 1024 && quality > 0.1) {
                        quality -= 0.1;
                        compressWithQuality();
                    } else {
                        // Конвертируем DataURL в Blob
                        const byteString = atob(compressedDataUrl.split(',')[1]);
                        const ab = new ArrayBuffer(byteString.length);
                        const ia = new Uint8Array(ab);
                        
                        for (let i = 0; i < byteString.length; i++) {
                            ia[i] = byteString.charCodeAt(i);
                        }
                        
                        const blob = new Blob([ab], { type: 'image/jpeg' });
                        
                        // Создаем новое имя файла с расширением .jpg
                        const originalName = file.name.replace(/\.[^/.]+$/, "");
                        const compressedFile = new File([blob], `${originalName}.jpg`, { 
                            type: 'image/jpeg',
                            lastModified: Date.now()
                        });
                        
                        console.log(`✅ Исходный: ${Math.round(file.size/1024)}KB, Сжатый: ${Math.round(compressedSize/1024)}KB, Качество: ${quality}`);
                        resolve(compressedFile);
                    }
                };
                
                compressWithQuality();
            };
            
            img.onerror = (error) => {
                console.error('Ошибка загрузки изображения:', error);
                reject(new Error('Не удалось загрузить изображение'));
            };
        };
        
        reader.onerror = (error) => {
            console.error('Ошибка чтения файла:', error);
            reject(new Error('Не удалось прочитать файл'));
        };
    });
}
// Функция для загрузки файла на сервер
async function uploadImage(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/upload/image', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка загрузки файла');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Ошибка загрузки:', error);
        throw error;
    }
}

// Функция для отправки сообщения с изображением
async function sendImageMessage(content, chatId) {
    try {
        const response = await fetch('/api/messages', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json' 
            },
            body: JSON.stringify({
                content: content,  // Здесь будет HTML код с изображением
                chat_id: chatId
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка отправки сообщения');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Ошибка отправки:', error);
        throw error;
    }
}

// Функция создания HTML блока для изображения
function createImageMessageBlock(imageUrl, filename) {
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const date = new Date().toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' });
    
    // Создаем HTML код для сообщения
    const messageHTML = `
                <img class="message-img" src="${imageUrl}" alt="${filename}">
    `;
    
    return messageHTML;
}

// Обновленная функция attachFile
async function attachFile() {
    try {
        // Создаем input для выбора файла
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.multiple = false;
        
        input.onchange = async (event) => {
            const file = event.target.files[0];
            if (!file) return;
            
            // Проверяем, что это изображение
            if (!file.type.startsWith('image/')) {
                alert('Пожалуйста, выберите изображение');
                return;
            }
            
            // Показываем индикатор загрузки
            showLoadingIndicator('Обработка изображения...');
            
            try {
                // Сжимаем изображение (до 2MB)
                const compressedFile = await compressImage(file, 2);
                
                updateLoadingStatus('Загрузка на сервер...');
                
                // Загружаем на сервер
                const uploadResult = await uploadImage(compressedFile);
                
                updateLoadingStatus('Отправка сообщения...');
                
                // Создаем HTML для сообщения
                const messageHTML = createImageMessageBlock(
                    uploadResult.fileUrl, 
                    compressedFile.name
                );
                
                // Отправляем сообщение через существующий API
                await sendImageMessage(messageHTML, currentChatId);
                
                // Сообщение добавится через WebSocket, поэтому не нужно добавлять вручную
                
            } catch (error) {
                console.error('Ошибка:', error);
                alert('Не удалось загрузить изображение: ' + error.message);
            } finally {
                hideLoadingIndicator();
            }
        };
        
        input.click();
    } catch (error) {
        console.error('Ошибка выбора файла:', error);
        alert('Не удалось выбрать файл');
    }
}

// Вспомогательные функции для индикации загрузки
function showLoadingIndicator(message = 'Загрузка...') {
    // Удаляем старый индикатор если есть
    hideLoadingIndicator();
    
    const indicator = document.createElement('div');
    indicator.id = 'image-upload-indicator';
    indicator.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 20px;
        border-radius: 10px;
        z-index: 1000;
        text-align: center;
    `;
    
    const spinner = document.createElement('div');
    spinner.style.cssText = `
        border: 3px solid #f3f3f3;
        border-top: 3px solid #3498db;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 0 auto 10px auto;
    `;
    
    const messageEl = document.createElement('div');
    messageEl.id = 'upload-status-message';
    messageEl.textContent = message;
    
    indicator.appendChild(spinner);
    indicator.appendChild(messageEl);
    document.body.appendChild(indicator);
    
    // Добавляем стили для анимации
    if (!document.getElementById('spin-animation')) {
        const style = document.createElement('style');
        style.id = 'spin-animation';
        style.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }
}

function updateLoadingStatus(message) {
    const statusEl = document.getElementById('upload-status-message');
    if (statusEl) {
        statusEl.textContent = message;
    }
}

function hideLoadingIndicator() {
    const indicator = document.getElementById('image-upload-indicator');
    if (indicator) {
        indicator.remove();
    }
}