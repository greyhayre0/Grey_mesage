// static/js/messenger.js

// Глобальные переменные
let currentChatId = null;
let selectedUserId = null;
let ws = null;
let lastTotalUnread = 0; // Для отслеживания новых непрочитанных

// Загрузка при старте
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM загружен');
    loadChats();
    
    // Запрашиваем разрешение на уведомления
    if (Notification.permission === 'default') {
        Notification.requestPermission();
    }
});

// Функция воспроизведения звука уведомления
function playNotificationSound() {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        gainNode.gain.value = 0.2;
        
        oscillator.start();
        gainNode.gain.exponentialRampToValueAtTime(0.00001, audioContext.currentTime + 0.2);
        oscillator.stop(audioContext.currentTime + 0.2);
        
        if (audioContext.state === 'suspended') {
            audioContext.resume();
        }
    } catch (error) {
        console.log('Звук не поддерживается:', error);
    }
}

// Загрузка списка чатов
async function loadChats() {
    try {
        const response = await fetch('/api/v1/chats');
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
            chatDiv.setAttribute('data-chat-id', chat.id);
            
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
            
            const delBtn = chatDiv.querySelector('.contact-button-del');
            delBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                deleteChat(chat.id);
            });
            
            contactList.appendChild(chatDiv);
        });
        
        startPolling();
        
    } catch (error) {
        console.error('Ошибка загрузки чатов:', error);
    }
}

// ========== ОБНОВЛЕНИЕ НЕПРОЧИТАННЫХ ==========

let pollingInterval = null;

// Функция обновления бейджей
async function updateUnreadBadges() {
    try {
        const response = await fetch('/api/v1/messages/unread-counts', {
            credentials: 'include'
        });
        
        if (!response.ok) return;
        
        const counts = await response.json();
        
        const contactList = document.getElementById('contactList');
        const chatDivs = contactList.querySelectorAll('.contact-name');
        
        counts.forEach(count => {
            let chatDiv = null;
            for (let div of chatDivs) {
                if (div.getAttribute('data-chat-id') == count.chat_id) {
                    chatDiv = div;
                    break;
                }
            }
            
            if (chatDiv) {
                const linkElement = chatDiv.querySelector('a');
                if (linkElement) {
                    const chatName = linkElement.innerHTML.replace(/<span[^>]*>.*<\/span>/, '').trim();
                    
                    if (count.unread_count > 0) {
                        linkElement.innerHTML = `${chatName} <span style="color: red; font-weight: bold;">(${count.unread_count})</span>`;
                    } else {
                        linkElement.innerHTML = chatName;
                    }
                }
            }
        });
        
        const totalUnread = counts.reduce((sum, item) => sum + item.unread_count, 0);
        
        // ВОТ ЗДЕСЬ ДОБАВЛЕН ЗВУК ПРИ НОВЫХ СООБЩЕНИЯХ
        if (totalUnread > lastTotalUnread && totalUnread > 0) {
            playNotificationSound(); // БРЯК!
        }
        
        lastTotalUnread = totalUnread;
        
        if (totalUnread > 0) {
            document.title = `(${totalUnread}) Чат`;
        } else {
            document.title = 'Чат';
        }
        
        if (totalUnread > 0 && !document.hasFocus()) {
            if (window.lastTotalUnread === undefined) {
                window.lastTotalUnread = totalUnread;
            }
            
            if (window.lastTotalUnread < totalUnread) {
                new Notification('Новые сообщения!', {
                    body: `У вас ${totalUnread} непрочитанных сообщений`,
                    icon: '/static/default-avatar.png'
                });
            }
            window.lastTotalUnread = totalUnread;
        } else if (totalUnread === 0) {
            window.lastTotalUnread = 0;
        }
        
    } catch (error) {
        console.error('Ошибка обновления бейджей:', error);
    }
}

// Запуск проверки
function startPolling() {
    if (pollingInterval) return;
    updateUnreadBadges();
    pollingInterval = setInterval(updateUnreadBadges, 10000);
}

// Функция отметки чата как прочитанного
async function markChatAsRead(chatId) {
    try {
        const response = await fetch(`/api/v1/messages/mark-chat-read/${chatId}`, {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok) {
            await updateUnreadBadges();
        }
    } catch (error) {
        console.error('Ошибка отметки прочитанных:', error);
    }
}

// Останавливаем проверку когда страница неактивна
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        stopPolling();
    } else {
        startPolling();
        updateUnreadBadges();
    }
});

// Выбор чата
async function selectChat(chatId) {
    if (currentChatId === chatId) return;
    
    currentChatId = chatId;
    
    await loadChats();
    
    document.getElementById('messageInputArea').style.display = 'flex';
    document.getElementById('messagesList').innerHTML = '<div class="incoming">Загрузка...</div>';
    
    await loadMessages(chatId);
    await markChatAsRead(chatId);
    connectWebSocket(chatId);
}

// Загрузка сообщений чата
async function loadMessages(chatId) {
    try {
        const response = await fetch(`/api/v1/chats/${chatId}/messages`);
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
            // Звук при получении сообщения через WebSocket (если чат не активен)
            if (currentChatId !== data.message.chat_id) {
                playNotificationSound();
            }
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
    
    const avatarUrl = message.sender_id === currentUser.id 
        ? currentUser.profileimage
        : message.sender_avatar;
    
    if (message.sender_id === currentUser.id) {
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
        await fetch('/api/v1/messages', {
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
            return;
        } else {
            event.preventDefault();
            sendMessage();
        }
    }
}

// Выход
async function logout() {
    await fetch('/api/v1/logout', { method: 'POST' });
    window.location.href = '/';
}

// Добавление аватарки
const dialog = document.getElementById('avatarDialog');
const myavatar = document.getElementById('myavatar');
const closeBtn = document.getElementById('closeDialog');
const saveBtn = document.getElementById('saveAvatar');
const avatarInput = document.getElementById('avatarUrl');

myavatar.addEventListener('click', () => {
    avatarInput.value = currentUser.profileimage || '';
    dialog.showModal();
});

closeBtn.addEventListener('click', () => {
    dialog.close();
});

saveBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    
    const newAvatarUrl = avatarInput.value.trim();
    
    if (!newAvatarUrl) {
        alert('Введите URL');
        return;
    }
    
    try {
        const response = await fetch('/api/v1/update-avatar', {
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
            document.querySelector('#myavatar img').src = newAvatarUrl;
            currentUser.profileimage = newAvatarUrl;
            dialog.close();
        } else {
            alert('Ошибка: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка при сохранении');
    }
});

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

myname.addEventListener('click', () => {
    nicknameInput.value = currentUser.nickname || '';
    nicknameDialog.showModal();
});

closeNicknameBtn.addEventListener('click', () => {
    nicknameDialog.close();
});

saveNicknameBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    
    const newNickname = nicknameInput.value.trim();
    
    if (!newNickname) {
        alert('Никнейм не может быть пустым');
        return;
    }
    
    try {
        const response = await fetch('/api/v1/update-nickname', {
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
            myname.textContent = newNickname;
            currentUser.nickname = newNickname;
            nicknameDialog.close();
        } else {
            alert('Ошибка: ' + (data.error || 'Неизвестная ошибка'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка при сохранении');
    }
});

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
        const response = await fetch(`/api/v1/chats/${chatId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (currentChatId === chatId) {
                currentChatId = null;
                document.getElementById('messageInputArea').style.display = 'none';
                document.getElementById('messagesList').innerHTML = '<div class="incoming">Выберите чат</div>';
            }
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
                
                const maxDimension = 1920;
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
                ctx.fillStyle = '#FFFFFF';
                ctx.fillRect(0, 0, width, height);
                ctx.drawImage(img, 0, 0, width, height);
                
                let quality = 0.9;
                let compressedDataUrl;
                
                const compressWithQuality = () => {
                    compressedDataUrl = canvas.toDataURL('image/jpeg', quality);
                    const compressedSize = Math.round((compressedDataUrl.length * 3) / 4);
                    
                    console.log(`Попытка с качеством ${quality}: ${Math.round(compressedSize/1024)}KB`);
                    
                    if (compressedSize > maxSizeMB * 1024 * 1024 && quality > 0.1) {
                        quality -= 0.1;
                        compressWithQuality();
                    } else {
                        const byteString = atob(compressedDataUrl.split(',')[1]);
                        const ab = new ArrayBuffer(byteString.length);
                        const ia = new Uint8Array(ab);
                        
                        for (let i = 0; i < byteString.length; i++) {
                            ia[i] = byteString.charCodeAt(i);
                        }
                        
                        const blob = new Blob([ab], { type: 'image/jpeg' });
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
        const response = await fetch('/api/v1/upload/image', {
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
        const response = await fetch('/api/v1/messages', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json' 
            },
            body: JSON.stringify({
                content: content,
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
    return `<img class="message-img" src="${imageUrl}" alt="${filename}">`;
}

// Обновленная функция attachFile
async function attachFile() {
    if (!currentChatId) {
        alert('Сначала выберите чат');
        return;
    }
    
    try {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.multiple = false;
        
        input.onchange = async (event) => {
            const file = event.target.files[0];
            if (!file) return;
            
            if (!file.type.startsWith('image/')) {
                alert('Пожалуйста, выберите изображение');
                return;
            }
            
            showLoadingIndicator('Обработка изображения...');
            
            try {
                const compressedFile = await compressImage(file, 2);
                updateLoadingStatus('Загрузка на сервер...');
                const uploadResult = await uploadImage(compressedFile);
                updateLoadingStatus('Отправка сообщения...');
                const messageHTML = createImageMessageBlock(uploadResult.fileUrl, compressedFile.name);
                await sendImageMessage(messageHTML, currentChatId);
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