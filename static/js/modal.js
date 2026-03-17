// static/js/modal.js

const modal = document.querySelector('#myModal');
const btnOpen = document.querySelector('#openModal');
const btnClose = document.querySelector('#closeModal');
const btnSave = document.querySelector('#saveModal');
const searchInput = document.querySelector('#searchNickname');
const searchResults = document.querySelector('#searchResults');

// Открыть окно
btnOpen.onclick = () => {
    searchInput.value = '';
    searchResults.innerHTML = '';
    selectedUserId = null;
    modal.showModal();
};

// Закрыть окно
btnClose.onclick = () => modal.close();

// Поиск при вводе
searchInput.oninput = async function() {
    const query = this.value.trim();
    if (query.length < 2) {
        searchResults.innerHTML = '';
        return;
    }

    try {
        const response = await fetch(`/api/users/search?query=${encodeURIComponent(query)}`);
        const users = await response.json();
        
        if (users.length === 0) {
            searchResults.innerHTML = '<div style="color: #999; padding: 5px;">Ничего не найдено</div>';
            return;
        }

        searchResults.innerHTML = users.map(user => `
            <div style="padding: 8px; border-bottom: 1px solid #eee; cursor: pointer;" 
                 onmouseover="this.style.background='#f5f5f5'" 
                 onmouseout="this.style.background='white'"
                 onclick="selectUser(${user.id}, '${user.nickname}')">
                ${user.nickname} (@${user.username})
            </div>
        `).join('');
    } catch (error) {
        console.error('Ошибка поиска:', error);
    }
};

// Выбор пользователя
window.selectUser = (userId, nickname) => {
    searchInput.value = nickname;
    searchResults.innerHTML = '';
    selectedUserId = userId;
};

// Сохранить контакт
btnSave.onclick = async () => {
    if (!selectedUserId) {
        alert('Выберите пользователя из списка');
        return;
    }

    try {
        const response = await fetch('/api/chats', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: null,
                participant_ids: [selectedUserId]
            })
        });

        if (response.ok) {
            modal.close();
            loadChats(); // Перезагружаем список чатов
        } else {
            alert('Ошибка при создании чата');
        }
    } catch (error) {
        console.error('Ошибка:', error);
    }
};