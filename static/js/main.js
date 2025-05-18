// Configuración de Marked para el renderizado de Markdown
marked.setOptions({
    highlight: function(code, lang) {
        if (lang && hljs.getLanguage(lang)) {
            return hljs.highlight(code, { language: lang }).value;
        }
        return hljs.highlightAuto(code).value;
    },
    breaks: true,
    gfm: true
});

// Variables globales
let socket = null;
let sessionId = null;
let isConnected = false;
let isTyping = false;

// Elementos del DOM
const messageForm = document.getElementById('message-form');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const messagesContainer = document.getElementById('chat-messages');
const statusElement = document.getElementById('status');
const typingIndicator = document.getElementById('typing-indicator');
const themeToggleBtn = document.getElementById('theme-toggle-btn');
const newChatBtn = document.querySelector('.new-chat-btn button');

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    // Generar ID de sesión único
    sessionId = generateSessionId();
    
    // Inicializar WebSocket
    connectWebSocket();
    
    // Configurar eventos
    setupEventListeners();
    
    // Cargar tema
    loadTheme();
    
    // Ajustar altura del textarea
    adjustTextareaHeight();
});

// Función para generar un ID de sesión único
function generateSessionId() {
    return 'session_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

// Función para conectar WebSocket
function connectWebSocket() {
    // Cerrar socket existente si hay uno
    if (socket) {
        socket.close();
    }
    
    // Crear nuevo socket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;
    socket = new WebSocket(wsUrl);
    
    // Configurar eventos del socket
    socket.onopen = handleSocketOpen;
    socket.onmessage = handleSocketMessage;
    socket.onclose = handleSocketClose;
    socket.onerror = handleSocketError;
}

// Manejadores de eventos del socket
function handleSocketOpen() {
    isConnected = true;
    updateStatus('Conectado', 'success');
}

function handleSocketMessage(event) {
    const data = JSON.parse(event.data);
    
    switch (data.type) {
        case 'message':
            addMessage(data.content, 'bot');
            break;
        case 'status':
            updateStatus(data.content, data.status);
            break;
        default:
            console.log('Mensaje desconocido:', data);
    }
}

function handleSocketClose() {
    isConnected = false;
    updateStatus('Desconectado', 'error');
    
    // Intentar reconectar después de 3 segundos
    setTimeout(() => {
        if (!isConnected) {
            connectWebSocket();
        }
    }, 3000);
}

function handleSocketError(error) {
    console.error('Error de WebSocket:', error);
    updateStatus('Error de conexión', 'error');
}

// Configurar eventos
function setupEventListeners() {
    // Enviar mensaje
    messageForm.addEventListener('submit', handleMessageSubmit);
    
    // Ajustar altura del textarea al escribir
    messageInput.addEventListener('input', adjustTextareaHeight);
    
    // Enviar mensaje con Enter (pero nueva línea con Shift+Enter)
    messageInput.addEventListener('keydown', handleInputKeydown);
    
    // Cambiar tema
    themeToggleBtn.addEventListener('click', toggleTheme);
    
    // Nueva conversación
    newChatBtn.addEventListener('click', startNewConversation);
}

// Manejar envío de mensaje
function handleMessageSubmit(event) {
    event.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message || !isConnected) return;
    
    // Enviar mensaje al servidor
    sendMessage(message);
    
    // Limpiar input
    messageInput.value = '';
    adjustTextareaHeight();
    
    // Enfocar el input
    messageInput.focus();
}

// Manejar teclas en el input
function handleInputKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        messageForm.dispatchEvent(new Event('submit'));
    }
}

// Enviar mensaje al servidor
function sendMessage(content) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        updateStatus('No conectado', 'error');
        return;
    }
    
    // Añadir mensaje a la interfaz
    addMessage(content, 'user');
    
    // Mostrar indicador de escritura
    setTypingIndicator(true);
    
    // Enviar mensaje al servidor
    const message = {
        content: content,
        config: {
            model: 'default',
            temperature: 0.7
        }
    };
    
    socket.send(JSON.stringify(message));
}

// Añadir mensaje a la interfaz
function addMessage(content, role) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${role}`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    // Renderizar Markdown si es un mensaje del bot
    if (role === 'bot') {
        messageContent.innerHTML = marked.parse(content);
        
        // Aplicar highlight.js a los bloques de código
        messageElement.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    } else {
        // Para mensajes del usuario, escapar HTML y preservar saltos de línea
        messageContent.textContent = content;
    }
    
    messageElement.appendChild(messageContent);
    messagesContainer.appendChild(messageElement);
    
    // Scroll al final
    scrollToBottom();
}

// Actualizar estado
function updateStatus(message, status) {
    statusElement.textContent = message;
    statusElement.className = 'status';
    
    if (status) {
        statusElement.classList.add(status);
    }
    
    // Si no está escribiendo, ocultar el indicador
    if (status !== 'typing') {
        setTypingIndicator(false);
    }
}

// Mostrar/ocultar indicador de escritura
function setTypingIndicator(show) {
    isTyping = show;
    typingIndicator.classList.toggle('active', show);
}

// Scroll al final de los mensajes
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Ajustar altura del textarea
function adjustTextareaHeight() {
    messageInput.style.height = 'auto';
    messageInput.style.height = (messageInput.scrollHeight) + 'px';
}

// Cargar tema
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Activar/desactivar hojas de estilo para el resaltado de código
    document.getElementById('code-theme-light').disabled = (savedTheme === 'dark');
    document.getElementById('code-theme-dark').disabled = (savedTheme === 'light');
}

// Cambiar tema
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Activar/desactivar hojas de estilo para el resaltado de código
    document.getElementById('code-theme-light').disabled = (newTheme === 'dark');
    document.getElementById('code-theme-dark').disabled = (newTheme === 'light');
}

// Iniciar nueva conversación
function startNewConversation() {
    // Limpiar mensajes
    messagesContainer.innerHTML = '';
    
    // Reconectar WebSocket
    sessionId = generateSessionId();
    connectWebSocket();
}
