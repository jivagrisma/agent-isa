/**
 * ISA-Agent Chat UI JavaScript
 * Gestiona la interfaz de usuario del chat, tema claro/oscuro y renderizado de Markdown
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const chatMessages = document.getElementById('chat-messages');
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const statusElement = document.getElementById('status');
    const typingIndicator = document.getElementById('typing-indicator');
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const htmlElement = document.documentElement;
    
    // =============== Tema Claro/Oscuro ===============
    
    // Cargar preferencia de tema del localStorage
    function loadThemePreference() {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            htmlElement.dataset.theme = savedTheme;
            updateCodeTheme(savedTheme);
        } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            // Usar preferencia del sistema si no hay preferencia guardada
            htmlElement.dataset.theme = 'dark';
            updateCodeTheme('dark');
        }
    }
    
    // Alternar entre tema claro y oscuro
    function toggleTheme() {
        const currentTheme = htmlElement.dataset.theme || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        htmlElement.dataset.theme = newTheme;
        localStorage.setItem('theme', newTheme);
        updateCodeTheme(newTheme);
    }
    
    // Actualizar tema para los bloques de código
    function updateCodeTheme(theme) {
        const lightTheme = document.getElementById('code-theme-light');
        const darkTheme = document.getElementById('code-theme-dark');
        
        if (theme === 'dark') {
            lightTheme.disabled = true;
            darkTheme.disabled = false;
        } else {
            lightTheme.disabled = false;
            darkTheme.disabled = true;
        }
    }
    
    // =============== WebSocket y Comunicación ===============
    
    // Generar ID de sesión único
    const sessionId = Math.random().toString(36).substring(2, 15) + 
                     Math.random().toString(36).substring(2, 15);
    
    // Conectar al WebSocket
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws/${sessionId}`);
    
    // Manejar eventos del WebSocket
    ws.onopen = () => {
        console.log('Conexión WebSocket establecida');
        updateStatus('Conectado', 'success');
        sendButton.disabled = false;
    };
    
    ws.onclose = () => {
        console.log('Conexión WebSocket cerrada');
        updateStatus('Desconectado', 'error');
        sendButton.disabled = true;
    };
    
    ws.onerror = (error) => {
        console.error('Error en la conexión WebSocket:', error);
        updateStatus('Error de conexión', 'error');
        sendButton.disabled = true;
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'message') {
            // Ocultar indicador de escritura
            typingIndicator.classList.remove('visible');
            
            // Añadir mensaje del bot
            addMessage(data.content, 'bot');
            
            // Auto-scroll al final
            scrollToBottom();
        } else if (data.type === 'status') {
            // Actualizar estado
            if (data.status === 'typing') {
                // Mostrar indicador de escritura
                typingIndicator.classList.add('visible');
                statusElement.style.display = 'none';
            } else {
                // Mostrar estado
                typingIndicator.classList.remove('visible');
                statusElement.style.display = 'block';
                updateStatus(data.content, data.status);
            }
        }
    };
    
    // Actualizar el elemento de estado
    function updateStatus(message, status) {
        statusElement.textContent = message;
        statusElement.className = `status ${status || ''}`;
    }
    
    // =============== Manejo de Mensajes ===============
    
    // Enviar mensaje al servidor
    function sendMessage(content) {
        if (!content.trim()) return;
        
        // Enviar mensaje al servidor
        ws.send(JSON.stringify({ content }));
        
        // Añadir mensaje del usuario
        addMessage(content, 'user');
        
        // Mostrar indicador de escritura
        typingIndicator.classList.add('visible');
        statusElement.style.display = 'none';
        
        // Auto-scroll al final
        scrollToBottom();
    }
    
    // Función para añadir mensajes al chat
    function addMessage(content, sender) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}-message`;
        
        // Crear encabezado del mensaje
        const headerElement = document.createElement('div');
        headerElement.className = 'message-header';
        
        // Añadir icono según el remitente
        const iconElement = document.createElement('i');
        iconElement.className = sender === 'user' ? 'ri-user-line' : 'ri-robot-line';
        headerElement.appendChild(iconElement);
        
        // Añadir nombre del remitente
        const nameElement = document.createElement('span');
        nameElement.textContent = sender === 'user' ? 'Usuario' : 'ISA-Agent';
        headerElement.appendChild(nameElement);
        
        messageElement.appendChild(headerElement);
        
        // Crear contenedor para el contenido
        const contentElement = document.createElement('div');
        contentElement.className = 'message-content markdown-content';
        
        // Para mensajes del bot, procesar markdown
        if (sender === 'bot') {
            // Renderizar markdown
            contentElement.innerHTML = marked.parse(content);
            
            // Procesar bloques de código después de renderizar
            processCodeBlocks(contentElement);
        } else {
            // Para mensajes del usuario, solo texto plano
            contentElement.textContent = content;
        }
        
        messageElement.appendChild(contentElement);
        chatMessages.appendChild(messageElement);
    }
    
    // Procesar bloques de código para añadir encabezado y botón de copiar
    function processCodeBlocks(container) {
        // Buscar todos los bloques pre>code
        const codeBlocks = container.querySelectorAll('pre > code');
        
        codeBlocks.forEach(codeBlock => {
            const pre = codeBlock.parentNode;
            
            // Obtener el lenguaje del código
            let language = '';
            codeBlock.classList.forEach(cls => {
                if (cls.startsWith('language-')) {
                    language = cls.substring(9);
                }
            });
            
            // Crear el encabezado del código
            const header = document.createElement('div');
            header.className = 'code-header';
            
            // Añadir el nombre del lenguaje
            const langSpan = document.createElement('span');
            langSpan.textContent = language || 'código';
            header.appendChild(langSpan);
            
            // Añadir botón de copiar
            const copyButton = document.createElement('button');
            copyButton.className = 'copy-button';
            copyButton.innerHTML = '<i class="ri-file-copy-line"></i> Copiar';
            copyButton.addEventListener('click', () => {
                // Copiar el contenido al portapapeles
                navigator.clipboard.writeText(codeBlock.textContent)
                    .then(() => {
                        copyButton.innerHTML = '<i class="ri-check-line"></i> Copiado';
                        copyButton.classList.add('copied');
                        
                        // Restaurar el botón después de 2 segundos
                        setTimeout(() => {
                            copyButton.innerHTML = '<i class="ri-file-copy-line"></i> Copiar';
                            copyButton.classList.remove('copied');
                        }, 2000);
                    })
                    .catch(err => {
                        console.error('Error al copiar texto: ', err);
                    });
            });
            header.appendChild(copyButton);
            
            // Insertar el encabezado antes del código
            pre.insertBefore(header, codeBlock);
            
            // Aplicar highlight.js si no se ha hecho ya
            if (!codeBlock.classList.contains('hljs')) {
                hljs.highlightElement(codeBlock);
            }
        });
    }
    
    // Auto-scroll al final del chat
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Ajustar altura del textarea
    function adjustTextareaHeight() {
        // Resetear altura
        messageInput.style.height = 'auto';
        
        // Establecer nueva altura basada en el contenido
        const newHeight = Math.min(messageInput.scrollHeight, 120); // Máximo 120px
        messageInput.style.height = `${newHeight}px`;
    }
    
    // =============== Event Listeners ===============
    
    // Manejar envío de mensajes
    messageForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const message = messageInput.value.trim();
        if (message) {
            sendMessage(message);
            messageInput.value = '';
            adjustTextareaHeight();
            messageInput.focus();
        }
    });
    
    // Ajustar altura del textarea al escribir
    messageInput.addEventListener('input', adjustTextareaHeight);
    
    // Manejar cambio de tema
    themeToggleBtn.addEventListener('click', toggleTheme);
    
    // Habilitar envío con Ctrl+Enter o Cmd+Enter
    messageInput.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            messageForm.dispatchEvent(new Event('submit'));
        }
    });
    
    // Botón de nueva conversación (recargar página)
    const newChatBtn = document.querySelector('.new-chat-btn button');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', () => {
            if (confirm('¿Deseas iniciar una nueva conversación? La conversación actual se perderá.')) {
                window.location.reload();
            }
        });
    }
    
    // =============== Inicialización ===============
    
    // Cargar preferencia de tema
    loadThemePreference();
    
    // Ajustar altura inicial del textarea
    adjustTextareaHeight();
    
    // Establecer foco en el input
    messageInput.focus();
});
