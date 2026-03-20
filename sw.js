// sw.js - Service Worker для push-уведомлений
self.addEventListener('push', (event) => {
    console.log('[Service Worker] Push получено:', event);
    
    let data = {
        title: 'Новое сообщение',
        body: 'У вас новое сообщение',
        icon: '/static/default-avatar.png'
    };
    
    if (event.data) {
        try {
            const parsed = event.data.json();
            data.title = parsed.title || data.title;
            data.body = parsed.body || data.body;
        } catch(e) {
            data.body = event.data.text();
        }
    }
    
    event.waitUntil(
        self.registration.showNotification(data.title, {
            body: data.body,
            icon: data.icon,
            vibrate: [200, 100, 200],
            badge: '/static/badge.png'
        })
    );
});

// Обработка клика по уведомлению
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    event.waitUntil(
        clients.openWindow('/messager')  // открываем ваш сайт
    );
});