const modal = document.querySelector('#myModal');
const btnOpen = document.querySelector('#openModal');
const btnClose = document.querySelector('#closeModal');
const btnSave = document.querySelector('#saveModal');
const searchInput = document.querySelector('#searchNickname');
const searchResults = document.querySelector('#searchResults');
const chatTypeRadios = document.querySelectorAll('input[name="chatType"]');
const groupNameField = document.querySelector('#groupNameField');
const groupNameInput = document.querySelector('#groupName');
const selectedUsersDiv = document.querySelector('#selectedUsers');
const selectedUsersList = document.querySelector('#selectedUsersList');

let selectedUsers = []; // Массив для хранения выбранных пользователей

// Переключение между личным и групповым чатом
chatTypeRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
        if (e.target.value === 'group') {
            groupNameField.style.display = 'block';
        } else {
            groupNameField.style.display = 'none';
        }
    });
});

// Открыть окно
btnOpen.onclick = () => {
    searchInput.value = '';
    searchResults.innerHTML = '';
    selectedUsers = [];
    selectedUsersDiv.style.display = 'none';
    document.querySelector('input[value="personal"]').checked = true;
    groupNameField.style.display = 'none';
    groupNameInput.value = '';
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
        const response = await fetch(`/api/v1/users/search?query=${encodeURIComponent(query)}`);
        const users = await response.json();
        
        if (users.length === 0) {
            searchResults.innerHTML = '<div style="color: #999; padding: 5px;">Ничего не найдено</div>';
            return;
        }

        // Фильтруем уже выбранных пользователей
        const availableUsers = users.filter(user => 
            !selectedUsers.some(selected => selected.id === user.id)
        );

        searchResults.innerHTML = availableUsers.map(user => `
            <div style="padding: 8px; border-bottom: 1px solid #eee; cursor: pointer;" 
                 onmouseover="this.style.background='#f5f5f5'" 
                 onmouseout="this.style.background='white'"
                 onclick="addUserToSelection(${user.id}, '${user.nickname}')">
                ${user.nickname} (@${user.username})
            </div>
        `).join('');
    } catch (error) {
        console.error('Ошибка поиска:', error);
    }
};

// Добавление пользователя в список выбранных
window.addUserToSelection = (userId, nickname) => {
    if (!selectedUsers.some(u => u.id === userId)) {
        selectedUsers.push({ id: userId, nickname: nickname });
        updateSelectedUsersList();
    }
    searchInput.value = '';
    searchResults.innerHTML = '';
};

// Удаление пользователя из выбранных
window.removeUserFromSelection = (userId) => {
    selectedUsers = selectedUsers.filter(u => u.id !== userId);
    updateSelectedUsersList();
};

// Обновление отображения выбранных пользователей
function updateSelectedUsersList() {
    if (selectedUsers.length > 0) {
        selectedUsersDiv.style.display = 'block';
        selectedUsersList.innerHTML = selectedUsers.map(user => `
            <span class="selected-user-tag">
                ${user.nickname}
                <button onclick="removeUserFromSelection(${user.id})">✕</button>
            </span>
        `).join('');
    } else {
        selectedUsersDiv.style.display = 'none';
    }
}

// Сохранить/создать чат
btnSave.onclick = async () => {
    const chatType = document.querySelector('input[name="chatType"]:checked').value;
    
    if (chatType === 'personal') {
        // Личный чат - нужен ровно один участник
        if (selectedUsers.length !== 1) {
            alert('Для личного чата выберите одного пользователя');
            return;
        }
    } else {
        // Групповой чат - нужно минимум 2 участника + название
        if (selectedUsers.length < 2) {
            alert('Для группового чата выберите минимум 2 участников');
            return;
        }
        if (!groupNameInput.value.trim()) {
            alert('Введите название группы');
            return;
        }
    }

    try {
        const response = await fetch('/api/v1/chats', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: chatType === 'group' ? groupNameInput.value.trim() : null,
                participant_ids: selectedUsers.map(u => u.id),
                is_group: chatType === 'group'
            })
        });

        if (response.ok) {
            modal.close();
            loadChats(); // Перезагружаем список чатов
        } else {
            const error = await response.json();
            alert('Ошибка: ' + (error.detail || 'Не удалось создать чат'));
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка при создании чата');
    }
};