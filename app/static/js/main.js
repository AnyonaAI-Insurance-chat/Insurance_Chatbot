document.addEventListener('DOMContentLoaded', function() {
    
    // --- LÓGICA DEL FORMULARIO DE CHAT ---
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const messagesContainer = document.getElementById('chat-messages');
    
    if (chatForm && messageInput && messagesContainer) {
        
        // Escuchamos el evento 'submit' del formulario
        chatForm.addEventListener('submit', function(event) {
            const userMessage = messageInput.value.trim();

            if (userMessage) {
                // 1. Muestra el mensaje del usuario inmediatamente
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message user-message';
                messageDiv.textContent = userMessage;
                messagesContainer.appendChild(messageDiv);
                
                // 2. Limpia el campo de texto INMEDIATAMENTE
                messageInput.value = '';

                // 3. Hace scroll para ver el nuevo mensaje
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        });
    }

    // --- LÓGICA DEL BOTÓN FLOTANTE (FAB) ---
    const chatFab = document.getElementById('chat-fab');
    const chatWindow = document.getElementById('chat-window');

    if (chatFab && chatWindow) {
        chatFab.addEventListener('click', () => {
            // Alterna la clase 'chat-is-open' en el body
            document.body.classList.toggle('chat-is-open');

            // Enfoca el input si se abre la ventana
            if (document.body.classList.contains('chat-is-open')) {
                messageInput.focus();
            }
        });
    }
});
