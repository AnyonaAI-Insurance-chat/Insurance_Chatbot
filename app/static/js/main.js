document.addEventListener('DOMContentLoaded', function() {
    
    // --- LÓGICA DEL FORMULARIO (Esta parte ya funciona bien) ---
    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
        chatForm.addEventListener('submit', function(event) {
            const messageInput = document.getElementById('message-input');
            const messagesContainer = document.getElementById('chat-messages');

            if (messageInput && messagesContainer) {
                const userMessage = messageInput.value.trim();
                if (userMessage) {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message user-message';
                    messageDiv.textContent = userMessage;
                    messagesContainer.appendChild(messageDiv);
                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                }
            }
        });
    }

    // --- LÓGICA DEL CHAT Y BOTÓN FLOTANTE (¡LA VERSIÓN CORREGIDA!) ---
    const chatFab = document.getElementById('chat-fab');
    const chatWindow = document.getElementById('chat-window');

    if (chatFab && chatWindow) {
        chatFab.addEventListener('click', () => {
            // Simplemente añadimos o quitamos la clase 'is-open' del BODY.
            // El CSS se encargará de toda la lógica de mostrar/ocultar y animar.
            document.body.classList.toggle('chat-is-open');

            // Enfocar el input cuando se abre el chat
            if (document.body.classList.contains('chat-is-open')) {
                const messageInput = document.getElementById('message-input');
                if (messageInput) {
                    messageInput.focus();
                }
            }
        });
    }
});
