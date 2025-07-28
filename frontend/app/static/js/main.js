document.addEventListener('DOMContentLoaded', function() {
    const chatfabout = document.getElementById('chat-fab'); // Correcto: Este es el contenedor exterior
    const chatIcon = document.getElementById("svg-initial")
    const chatCloseIcon = document.getElementById("svg-alt")
    const chatFabInner = document.getElementById('chat-fab-inner'); // Renombrado para claridad
    const chatWindow = document.getElementById('chat-window');
    const closeChatBtn = document.getElementById('close-chat');
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const messagesContainer = document.getElementById('chat-messages');

    const chatWindowBorder = document.getElementById('chat-window-border'); 

    chatFabInner.addEventListener('click', () => { // El clic sigue en el inner para su área
        chatWindow.classList.toggle('hidden');
        
        if (chatWindowBorder) {
            chatWindowBorder.classList.toggle('hidden');
        }

        if (!chatWindow.classList.contains('hidden')) {
            // Si la ventana se ABRE, achicar el CONTENEDOR EXTERIOR
            chatfabout.style.width = '30px';
            chatfabout.style.height = '30px';
            chatIcon.style.opacity = '0';
            chatIcon.style.pointerEvents = 'none';
            chatCloseIcon.style.opacity = '1';
            chatCloseIcon.style.pointerEvents = 'auto';
            
            messageInput.focus(); 
        } else {
            // Si la ventana se CIERRA, agrandar el CONTENEDOR EXTERIOR
            chatfabout.style.width = '65px';
            chatfabout.style.height = '65px';
            chatIcon.style.opacity = '1';
            chatIcon.style.pointerEvents = 'auto';
            chatCloseIcon.style.opacity = '0';
            chatCloseIcon.style.pointerEvents = 'none';
        }
    });

    closeChatBtn.addEventListener('click', () => {
        chatWindow.classList.add('hidden');
        
        if (chatWindowBorder) {
            chatWindowBorder.classList.add('hidden');
        }

        // Al cerrar, agrandar el CONTENEDOR EXTERIOR
        chatfabout.style.width = '65px';
        chatfabout.style.height = '65px';
    });

    closeChatBtn.addEventListener('click', () => {
        chatWindow.classList.add('hidden');

        if (chatWindowBorder) {
            chatWindowBorder.classList.add('hidden');
        }

        chatfabout.style.width = '65px';
        chatfabout.style.height = '65px';

        // Restaurar íconos
        chatIcon.style.opacity = '1';
        chatIcon.style.pointerEvents = 'auto';
        chatCloseIcon.style.opacity = '0';
        chatCloseIcon.style.pointerEvents = 'none';
    });
});