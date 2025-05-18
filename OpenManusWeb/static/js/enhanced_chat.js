/**
 * ISA-Agent Enhanced Chat UI JavaScript
 * Proporciona funcionalidades avanzadas para la interfaz de chat
 */

class EnhancedChat {
    /**
     * Inicializa la interfaz de chat mejorada
     * @param {Object} options - Opciones de configuración
     */
    constructor(options = {}) {
        // Opciones por defecto
        this.options = Object.assign({
            chatContainerId: 'chat-messages',
            messageFormId: 'message-form',
            messageInputId: 'message-input',
            sendButtonId: 'send-button',
            statusId: 'status',
            typingIndicatorId: 'typing-indicator',
            modelSelectId: 'model-select',
            temperatureRangeId: 'temperature-range',
            temperatureValueId: 'temperature-value',
            webSearchBtnId: 'web-search-btn',
            fileUploadBtnId: 'file-upload-btn',
            wsEndpoint: null, // Se determina automáticamente si es null
            sessionId: null // Se genera automáticamente si es null
        }, options);

        // Elementos DOM
        this.chatContainer = document.getElementById(this.options.chatContainerId);
        this.messageForm = document.getElementById(this.options.messageFormId);
        this.messageInput = document.getElementById(this.options.messageInputId);
        this.sendButton = document.getElementById(this.options.sendButtonId);
        this.statusElement = document.getElementById(this.options.statusId);
        this.typingIndicator = document.getElementById(this.options.typingIndicatorId);
        this.modelSelect = document.getElementById(this.options.modelSelectId);
        this.temperatureRange = document.getElementById(this.options.temperatureRangeId);
        this.temperatureValue = document.getElementById(this.options.temperatureValueId);
        this.webSearchBtn = document.getElementById(this.options.webSearchBtnId);
        this.fileUploadBtn = document.getElementById(this.options.fileUploadBtnId);

        // Estado
        this.isConnected = false;
        this.isProcessing = false;
        this.isSearching = false;
        this.searchModeActive = false;
        this.messages = [];
        this.ws = null;
        this.sessionId = this.options.sessionId || this._generateSessionId();

        // Inicializar
        this._initWebSocket();
        this._initEventListeners();
    }

    /**
     * Inicializa la conexión WebSocket
     * @private
     */
    _initWebSocket() {
        // Determinar endpoint WebSocket
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsEndpoint = this.options.wsEndpoint || `${wsProtocol}//${window.location.host}/ws/${this.sessionId}`;

        // Crear conexión WebSocket
        this.ws = new WebSocket(wsEndpoint);

        // Configurar eventos WebSocket
        this.ws.onopen = this._handleWsOpen.bind(this);
        this.ws.onclose = this._handleWsClose.bind(this);
        this.ws.onerror = this._handleWsError.bind(this);
        this.ws.onmessage = this._handleWsMessage.bind(this);
    }

    /**
     * Inicializa los event listeners
     * @private
     */
    _initEventListeners() {
        // Formulario de mensaje
        if (this.messageForm) {
            this.messageForm.addEventListener('submit', this._handleSubmit.bind(this));
        }

        // Input de mensaje (ajuste automático de altura)
        if (this.messageInput) {
            this.messageInput.addEventListener('input', this._adjustTextareaHeight.bind(this));

            // Enviar con Ctrl+Enter o Cmd+Enter
            this.messageInput.addEventListener('keydown', (e) => {
                if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                    this.messageForm.dispatchEvent(new Event('submit'));
                }
            });
        }

        // Botones de modo
        const reasoningModeBtn = document.getElementById('reasoning-mode-btn');
        const searchModeBtn = document.getElementById('search-mode-btn');

        if (reasoningModeBtn && searchModeBtn) {
            // Modo de razonamiento
            reasoningModeBtn.addEventListener('click', () => {
                reasoningModeBtn.classList.add('active');
                searchModeBtn.classList.remove('active');
                this.searchModeActive = false;
                this.messageInput.placeholder = "Escribe tu mensaje aquí...";
            });

            // Modo de búsqueda
            searchModeBtn.addEventListener('click', () => {
                searchModeBtn.classList.add('active');
                reasoningModeBtn.classList.remove('active');
                this.searchModeActive = true;
                this.messageInput.placeholder = "Escribe tu consulta de búsqueda aquí...";
            });
        }

        // Botón de carga de archivos
        const uploadButton = document.getElementById('upload-button');
        if (uploadButton) {
            uploadButton.addEventListener('click', this._handleFileUpload.bind(this));
        }

        // Selector de modelo
        if (this.modelSelect) {
            this.modelSelect.addEventListener('change', () => {
                // Guardar preferencia en localStorage
                localStorage.setItem('preferred_model', this.modelSelect.value);
            });

            // Cargar modelo preferido
            const preferredModel = localStorage.getItem('preferred_model');
            if (preferredModel && this.modelSelect.querySelector(`option[value="${preferredModel}"]`)) {
                this.modelSelect.value = preferredModel;
            }
        }

        // Control de temperatura
        if (this.temperatureRange) {
            this.temperatureRange.addEventListener('input', () => {
                const value = this.temperatureRange.value;

                // Actualizar valor mostrado
                if (this.temperatureValue) {
                    this.temperatureValue.textContent = value;
                }

                // Guardar preferencia en localStorage
                localStorage.setItem('temperature', value);
            });

            // Cargar temperatura preferida
            const preferredTemp = localStorage.getItem('temperature');
            if (preferredTemp) {
                this.temperatureRange.value = preferredTemp;
                if (this.temperatureValue) {
                    this.temperatureValue.textContent = preferredTemp;
                }
            }
        }
    }

    /**
     * Maneja la apertura de la conexión WebSocket
     * @private
     */
    _handleWsOpen() {
        console.log('Conexión WebSocket establecida');
        this.isConnected = true;
        this._updateStatus('Conectado', 'success');
        this.sendButton.disabled = false;

        // No añadimos el mensaje de bienvenida aquí para evitar duplicación
        // El mensaje de bienvenida se mostrará desde el servidor
    }

    /**
     * Añade un mensaje de bienvenida personalizado
     * @private
     */
    _addWelcomeMessage() {
        // Verificar si el contenedor de chat está vacío
        if (this.chatContainer && this.chatContainer.children.length === 0) {
            const welcomeDiv = document.createElement('div');
            welcomeDiv.className = 'welcome-message';

            welcomeDiv.innerHTML = `
                <div class="welcome-logo">
                    <i class="ri-information-line"></i>
                </div>
                <h1>ISA-Agent</h1>
                <p>¡Hola! Soy el asistente ISA. ¿En qué puedo ayudarte hoy?</p>
            `;

            this.chatContainer.appendChild(welcomeDiv);
        }
    }

    /**
     * Maneja el cierre de la conexión WebSocket
     * @private
     */
    _handleWsClose() {
        console.log('Conexión WebSocket cerrada');
        this.isConnected = false;
        this._updateStatus('Desconectado', 'error');
        this.sendButton.disabled = true;

        // Intentar reconectar después de 5 segundos
        setTimeout(() => {
            if (!this.isConnected) {
                this._initWebSocket();
            }
        }, 5000);
    }

    /**
     * Maneja errores en la conexión WebSocket
     * @param {Event} error - Evento de error
     * @private
     */
    _handleWsError(error) {
        console.error('Error en la conexión WebSocket:', error);
        this._updateStatus('Error de conexión', 'error');
        this.sendButton.disabled = true;
    }

    /**
     * Maneja mensajes recibidos por WebSocket
     * @param {MessageEvent} event - Evento de mensaje
     * @private
     */
    _handleWsMessage(event) {
        const data = JSON.parse(event.data);

        // Manejar mensaje de bienvenida especial
        if (data.type === 'welcome') {
            // Verificar si ya existe un contenedor de bienvenida
            let welcomeContainer = document.querySelector('.welcome-container');

            // Si no existe, crearlo
            if (!welcomeContainer) {
                // Crear contenedor de bienvenida
                welcomeContainer = document.createElement('div');
                welcomeContainer.className = 'welcome-container';

                // Crear mensaje de bienvenida personalizado
                const welcomeDiv = document.createElement('div');
                welcomeDiv.className = 'welcome-message';

                welcomeDiv.innerHTML = `
                    <div class="welcome-logo">
                        <i class="ri-cloud-line"></i>
                    </div>
                    <h1>ISA-Agent</h1>
                    <p>${data.content}</p>
                `;

                // Añadir mensaje al contenedor
                welcomeContainer.appendChild(welcomeDiv);

                // Añadir contenedor al chat
                this.chatContainer.appendChild(welcomeContainer);
            }

            // Verificar si hay mensajes en el chat
            const hasMessages = this.chatContainer.querySelectorAll('.message').length > 0;

            // Si hay mensajes, ocultar el mensaje de bienvenida; de lo contrario, mostrarlo
            if (hasMessages) {
                this._hideWelcomeMessage();
            } else {
                this._showWelcomeMessage();
            }

            return;
        }

        if (data.type === 'message') {
            // Ocultar indicador de escritura
            this._hideTypingIndicator();

            // Ocultar mensaje de bienvenida si existe
            this._hideWelcomeMessage();

            // Añadir mensaje normalmente
            this._addMessage(data.content, 'bot');

            // Guardar mensaje en el historial
            this.messages.push({
                role: 'assistant',
                content: data.content
            });

            // Auto-scroll al final
            this._scrollToBottom();

            // Actualizar estado
            this.isProcessing = false;
            this.sendButton.disabled = false;

        } else if (data.type === 'status') {
            // Actualizar estado
            if (data.status === 'typing') {
                // Mostrar indicador de escritura
                this._showTypingIndicator();
                this.statusElement.style.display = 'none';
            } else {
                // Mostrar estado
                this._hideTypingIndicator();
                this.statusElement.style.display = 'block';
                this._updateStatus(data.content, data.status);

                // Si es un error, habilitar el botón de envío
                if (data.status === 'error') {
                    this.isProcessing = false;
                    this.sendButton.disabled = false;
                }
            }
        } else if (data.type === 'models') {
            // Actualizar selector de modelos
            this._updateModelSelector(data.models);
        }
    }

    /**
     * Maneja el envío del formulario
     * @param {Event} e - Evento de submit
     * @private
     */
    _handleSubmit(e) {
        e.preventDefault();

        // Verificar si está conectado y no está procesando
        if (!this.isConnected || this.isProcessing) {
            return;
        }

        const message = this.messageInput.value.trim();
        if (!message) {
            return;
        }

        // Si está en modo búsqueda, realizar búsqueda en lugar de enviar mensaje
        if (this.searchModeActive) {
            this._handleWebSearch();
            return;
        }

        // Obtener configuración
        const model = this.modelSelect ? this.modelSelect.value : null;
        const temperature = this.temperatureRange ? parseFloat(this.temperatureRange.value) : 0.7;

        // Enviar mensaje
        this._sendMessage(message, model, temperature);

        // Limpiar input
        this.messageInput.value = '';
        this._adjustTextareaHeight();
        this.messageInput.focus();
    }

    /**
     * Envía un mensaje al servidor
     * @param {string} content - Contenido del mensaje
     * @param {string|null} model - Modelo a utilizar (opcional)
     * @param {number} temperature - Temperatura de muestreo (opcional)
     * @private
     */
    _sendMessage(content, model = null, temperature = 0.7) {
        // Verificar conexión
        if (!this.isConnected) {
            this._updateStatus('No conectado', 'error');
            return;
        }

        // Crear objeto de mensaje
        const messageData = {
            content,
            config: {}
        };

        // Añadir configuración si está disponible
        if (model) {
            messageData.config.model = model;
        }

        if (temperature) {
            messageData.config.temperature = temperature;
        }

        // Enviar mensaje al servidor
        this.ws.send(JSON.stringify(messageData));

        // Ocultar mensaje de bienvenida si existe
        this._hideWelcomeMessage();

        // Añadir mensaje del usuario a la interfaz
        this._addMessage(content, 'user');

        // Guardar mensaje en el historial
        this.messages.push({
            role: 'user',
            content
        });

        // Mostrar indicador de escritura
        this._showTypingIndicator();
        this.statusElement.style.display = 'none';

        // Actualizar estado
        this.isProcessing = true;
        this.sendButton.disabled = true;

        // Auto-scroll al final
        this._scrollToBottom();
    }

    /**
     * Añade un mensaje al chat
     * @param {string} content - Contenido del mensaje
     * @param {string} sender - Remitente ('user' o 'bot')
     * @private
     */
    _addMessage(content, sender) {
        // Ocultar mensaje de bienvenida si existe
        this._hideWelcomeMessage();

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
            this._processCodeBlocks(contentElement);
        } else {
            // Para mensajes del usuario, solo texto plano
            contentElement.textContent = content;
        }

        messageElement.appendChild(contentElement);
        this.chatContainer.appendChild(messageElement);
    }

    /**
     * Maneja la búsqueda web
     * @private
     */
    async _handleWebSearch() {
        if (this.isSearching) return;

        // Obtener consulta del usuario del campo de mensaje
        const query = this.messageInput.value.trim();
        if (!query || query === '') {
            this._updateStatus('Por favor, escribe una consulta de búsqueda', 'warning');
            return;
        }

        // Mostrar estado
        this.isSearching = true;
        this._updateStatus('Buscando en internet...', 'info');

        try {
            // Realizar solicitud al servidor
            const response = await fetch('/api/web-search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    max_results: 5,
                    search_depth: 'basic'
                })
            });

            // Procesar respuesta
            const data = await response.json();

            if (data.success) {
                // Formatear resultados
                let resultsMarkdown = `## Resultados de búsqueda para: "${query}"\n\n`;

                if (data.results.length === 0) {
                    resultsMarkdown += 'No se encontraron resultados.';
                } else {
                    data.results.forEach((result, index) => {
                        if (result.metadata && result.metadata.type === 'answer') {
                            resultsMarkdown += `### Respuesta generada\n${result.snippet}\n\n`;
                        } else {
                            resultsMarkdown += `### ${index + 1}. ${result.title}\n`;
                            resultsMarkdown += `[${result.url}](${result.url})\n\n`;
                            resultsMarkdown += `${result.snippet}\n\n`;
                        }
                    });
                }

                // Añadir resultados al chat
                this._addMessage(resultsMarkdown, 'bot');

                // Limpiar el campo de mensaje
                this.messageInput.value = '';
                this._adjustTextareaHeight();

                // Actualizar estado
                this._updateStatus('Búsqueda completada', 'success');
            } else {
                // Mostrar error
                this._updateStatus(`Error en la búsqueda: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Error al realizar búsqueda:', error);
            this._updateStatus('Error al realizar búsqueda', 'error');
        } finally {
            this.isSearching = false;
        }
    }

    /**
     * Maneja la carga de archivos
     * @private
     */
    async _handleFileUpload() {
        // Crear un input de archivo oculto
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.txt,.pdf,.docx,.jpg,.jpeg,.png';
        fileInput.style.display = 'none';

        // Añadir al DOM
        document.body.appendChild(fileInput);

        // Configurar evento de cambio
        fileInput.addEventListener('change', async (event) => {
            const file = event.target.files[0];
            if (!file) return;

            // Mostrar mensaje de carga
            this._updateStatus(`Cargando archivo: ${file.name}...`, 'info');

            try {
                // Crear FormData para enviar el archivo
                const formData = new FormData();
                formData.append('file', file);

                // Añadir ID de sesión si está disponible
                if (this.sessionId) {
                    formData.append('session_id', this.sessionId);
                }

                // Enviar archivo al servidor
                const response = await fetch('/api/upload-file', {
                    method: 'POST',
                    body: formData
                });

                // Procesar respuesta
                const data = await response.json();

                if (data.success) {
                    // Ocultar mensaje de bienvenida si existe
                    this._hideWelcomeMessage();

                    // Mostrar información del archivo y análisis
                    let fileInfo = `## Archivo cargado: ${data.filename}\n\n`;
                    fileInfo += `**Tipo:** ${data.content_type}\n`;
                    fileInfo += `**Tamaño:** ${this._formatFileSize(data.size)}\n\n`;
                    fileInfo += `### Análisis:\n${data.analysis}\n\n`;

                    // Añadir mensaje con la información
                    this._addMessage(fileInfo, 'bot');

                    // Actualizar estado
                    this._updateStatus('Archivo cargado correctamente', 'success');
                } else {
                    // Mostrar error
                    this._updateStatus(`Error al cargar archivo: ${data.error}`, 'error');
                    this._addMessage(`Error al cargar archivo: ${data.error}`, 'bot');
                }
            } catch (error) {
                console.error('Error al cargar archivo:', error);
                this._updateStatus('Error al cargar archivo', 'error');
                this._addMessage(`Error al cargar archivo: ${error.message}`, 'bot');
            } finally {
                // Eliminar el input
                document.body.removeChild(fileInput);
            }
        });

        // Simular clic en el input
        fileInput.click();
    }

    /**
     * Formatea el tamaño de un archivo en unidades legibles
     * @param {number} bytes - Tamaño en bytes
     * @returns {string} Tamaño formateado
     * @private
     */
    _formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Oculta el mensaje de bienvenida
     * @private
     */
    _hideWelcomeMessage() {
        // Buscar el contenedor de bienvenida
        const welcomeContainer = document.querySelector('.welcome-container');
        if (welcomeContainer) {
            // Ocultar el contenedor de bienvenida con la clase CSS
            welcomeContainer.classList.add('hidden');
        }
    }

    /**
     * Muestra el mensaje de bienvenida
     * @private
     */
    _showWelcomeMessage() {
        // Buscar el contenedor de bienvenida
        const welcomeContainer = document.querySelector('.welcome-container');
        if (welcomeContainer) {
            // Mostrar el contenedor de bienvenida quitando la clase CSS
            welcomeContainer.classList.remove('hidden');
        }
    }

    /**
     * Limpia el chat y muestra el mensaje de bienvenida
     */
    clearChat() {
        // Limpiar mensajes
        this.messages = [];

        // Limpiar contenedor de mensajes
        const messages = this.chatContainer.querySelectorAll('.message');
        messages.forEach(message => {
            message.remove();
        });

        // Mostrar mensaje de bienvenida
        this._showWelcomeMessage();
    }

    // Otros métodos auxiliares
    _processCodeBlocks(container) { /* ... */ }
    _scrollToBottom() { /* ... */ }
    _adjustTextareaHeight() { /* ... */ }
    _updateStatus(message, status) { /* ... */ }
    _showTypingIndicator() { /* ... */ }
    _hideTypingIndicator() { /* ... */ }
    _generateSessionId() { /* ... */ }
    _updateModelSelector(models) { /* ... */ }
}

// Exportar clase
window.EnhancedChat = EnhancedChat;
