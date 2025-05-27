<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LIDIA - Inteligência Artificial do LID-IPT</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background: white;
            color: #2c3e50;
            overflow-x: hidden;
        }

        /* Página de Login */
        .login-page {
            min-height: 100vh;
            background: white;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 2rem;
        }

        .login-logo {
            width: 160px;
            height: 160px;
            background: linear-gradient(45deg, #e91e63, #f57c00, #8bc34a, #673ab7);
            border-radius: 50%;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 2rem;
            box-shadow: 0 12px 40px rgba(0,0,0,0.15);
        }

        .login-logo::before {
            content: '';
            position: absolute;
            width: 128px;
            height: 128px;
            background: white;
            border-radius: 50%;
        }

        .login-logo::after {
            content: '• • •';
            position: absolute;
            color: #3b82f6;
            font-size: 36px;
            letter-spacing: 12px;
            z-index: 1;
        }

        .login-title {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .login-subtitle {
            font-size: 1.5rem;
            color: #1f2937;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }

        .login-institution {
            font-size: 1.125rem;
            color: #6b7280;
            margin-bottom: 2rem;
            font-weight: 400;
        }

        .login-access-text {
            font-size: 1rem;
            color: #6b7280;
            margin-bottom: 2rem;
            max-width: 400px;
        }

        .login-form {
            max-width: 400px;
            width: 100%;
        }

        .login-input {
            width: 100%;
            padding: 1rem 1.5rem;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            font-size: 1rem;
            margin-bottom: 1rem;
            transition: all 0.2s;
        }

        .login-input:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .login-button {
            width: 100%;
            background: #3b82f6;
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 12px;
            font-size: 1.125rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        }

        .login-button:hover {
            background: #2563eb;
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
        }

        .login-button:disabled {
            background: #d1d5db;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        /* Interface Principal */
        .main-app {
            display: none;
        }

        .main-app.active {
            display: block;
        }

        .header {
            background: white;
            border-bottom: 1px solid #e5e7eb;
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .logo-container {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .lidia-logo {
            width: 48px;
            height: 48px;
            background: linear-gradient(45deg, #e91e63, #f57c00, #8bc34a, #673ab7);
            border-radius: 50%;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }

        .lidia-logo::before {
            content: '';
            position: absolute;
            width: 36px;
            height: 36px;
            background: white;
            border-radius: 50%;
        }

        .lidia-logo::after {
            content: '• • •';
            position: absolute;
            color: #3b82f6;
            font-size: 14px;
            letter-spacing: 2px;
            z-index: 1;
        }

        .brand-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: #1f2937;
        }

        .brand-subtitle {
            font-size: 0.875rem;
            color: #6b7280;
            margin-top: -2px;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .admin-panel {
            display: none;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-size: 0.875rem;
            color: #475569;
        }

        .admin-panel.show {
            display: block;
        }

        .new-chat-btn, .logout-btn {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .logout-btn {
            background: #6b7280;
        }

        .new-chat-btn:hover {
            background: #2563eb;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        }

        .logout-btn:hover {
            background: #4b5563;
        }

        .main-container {
            display: flex;
            height: calc(100vh - 80px);
        }

        .sidebar {
            width: 280px;
            background: #f8fafc;
            border-right: 1px solid #e5e7eb;
            padding: 1rem;
            overflow-y: auto;
        }

        .chat-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
        }

        .welcome-screen {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            text-align: center;
        }

        .welcome-logo {
            width: 120px;
            height: 120px;
            background: linear-gradient(45deg, #e91e63, #f57c00, #8bc34a, #673ab7);
            border-radius: 50%;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.12);
        }

        .welcome-logo::before {
            content: '';
            position: absolute;
            width: 96px;
            height: 96px;
            background: white;
            border-radius: 50%;
        }

        .welcome-logo::after {
            content: '• • •';
            position: absolute;
            color: #3b82f6;
            font-size: 28px;
            letter-spacing: 8px;
            z-index: 1;
        }

        .greeting-text {
            font-size: 2rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #1f2937;
        }

        .help-text {
            font-size: 1.125rem;
            color: #9ca3af;
            margin-bottom: 2rem;
            max-width: 600px;
        }

        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            max-width: 800px;
            width: 100%;
        }

        .feature-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            transition: all 0.3s;
            cursor: pointer;
        }

        .feature-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
            border-color: #3b82f6;
        }

        .feature-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            margin-bottom: 1rem;
        }

        .feature-title {
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }

        .feature-description {
            color: #6b7280;
            font-size: 0.875rem;
            line-height: 1.5;
        }

        .chat-area {
            display: none;
            flex-direction: column;
            height: 100%;
        }

        .chat-area.active {
            display: flex;
        }

        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 2rem;
        }

        .message {
            margin-bottom: 1.5rem;
            display: flex;
            gap: 1rem;
        }

        .message.user {
            flex-direction: row-reverse;
        }

        .message-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            flex-shrink: 0;
        }

        .message.user .message-avatar {
            background: #3b82f6;
            color: white;
        }

        .message.assistant .message-avatar {
            background: linear-gradient(45deg, #e91e63, #f57c00, #8bc34a, #673ab7);
            color: white;
            position: relative;
        }

        .message.assistant .message-avatar::before {
            content: '';
            position: absolute;
            width: 32px;
            height: 32px;
            background: white;
            border-radius: 50%;
        }

        .message.assistant .message-avatar::after {
            content: '•••';
            position: absolute;
            color: #3b82f6;
            font-size: 8px;
            letter-spacing: 1px;
            z-index: 1;
        }

        .message-content {
            background: white;
            padding: 1rem 1.5rem;
            border-radius: 16px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            max-width: 70%;
            line-height: 1.6;
        }

        .message.user .message-content {
            background: #3b82f6;
            color: white;
            border-color: #3b82f6;
        }

        .input-container {
            padding: 1.5rem 2rem;
            border-top: 1px solid #e5e7eb;
            background: white;
        }

        .input-wrapper {
            display: flex;
            align-items: flex-end;
            gap: 1rem;
            max-width: 800px;
            margin: 0 auto;
            position: relative;
        }

        .message-input {
            flex: 1;
            border: 2px solid #e5e7eb;
            border-radius: 24px;
            padding: 1rem 1.5rem;
            font-size: 1rem;
            outline: none;
            resize: none;
            min-height: 48px;
            max-height: 120px;
            transition: all 0.2s;
            background: #f8fafc;
        }

        .message-input:focus {
            border-color: #3b82f6;
            background: white;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .message-input::placeholder {
            color: #9ca3af;
        }

        .send-button {
            background: #3b82f6;
            color: white;
            border: none;
            width: 48px;
            height: 48px;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
            font-size: 18px;
        }

        .send-button:hover:not(:disabled) {
            background: #2563eb;
            transform: scale(1.05);
        }

        .send-button:disabled {
            background: #d1d5db;
            cursor: not-allowed;
        }

        .loading-indicator {
            display: none;
            align-items: center;
            gap: 1rem;
            color: #6b7280;
            font-size: 0.875rem;
            margin: 1rem 0;
            padding: 1rem;
        }

        .loading-indicator.show {
            display: flex;
        }

        .loading-avatar {
            width: 40px;
            height: 40px;
            background: linear-gradient(45deg, #e91e63, #f57c00, #8bc34a, #673ab7);
            border-radius: 50%;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .loading-avatar::before {
            content: '';
            position: absolute;
            width: 32px;
            height: 32px;
            background: white;
            border-radius: 50%;
        }

        .loading-avatar::after {
            content: '•••';
            position: absolute;
            color: #3b82f6;
            font-size: 8px;
            letter-spacing: 1px;
            z-index: 1;
            animation: sparkle 1.5s ease-in-out infinite;
        }

        @keyframes sparkle {
            0%, 100% { opacity: 0.5; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.1); }
        }

        .typing-animation {
            display: flex;
            gap: 4px;
            align-items: center;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #3b82f6;
            animation: typing 1.4s infinite ease-in-out;
        }

        .typing-dot:nth-child(2) {
            animation-delay: 0.2s;
        }

        .typing-dot:nth-child(3) {
            animation-delay: 0.4s;
        }

        @keyframes typing {
            0%, 80%, 100% {
                transform: scale(0.8);
                opacity: 0.5;
            }
            40% {
                transform: scale(1);
                opacity: 1;
            }
        }

        .alert {
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }

        .alert-error {
            background: #fef2f2;
            border: 1px solid #fecaca;
            color: #dc2626;
        }

        .alert-success {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            color: #166534;
        }

        @media (max-width: 768px) {
            .sidebar {
                display: none;
            }
            
            .chat-content {
                width: 100%;
            }
            
            .header {
                padding: 1rem;
            }
            
            .features-grid {
                grid-template-columns: 1fr;
            }
            
            .message-content {
                max-width: 85%;
            }

            .login-title {
                font-size: 2rem;
            }

            .login-subtitle {
                font-size: 1.25rem;
            }
        }
    </style>
</head>
<body>
    <!-- Página de Login -->
    <div class="login-page" id="loginPage">
        <div class="login-logo"></div>
        <h1 class="login-title">LIDIA</h1>
        <h2 class="login-subtitle">Inteligência Artificial do LID-IPT</h2>
        <p class="login-institution">Instituto de Pesquisas Tecnológicas de São Paulo</p>
        <p class="login-access-text">Acesso exclusivo para colaboradores do IPT</p>
        
        <div class="login-form">
            <div id="loginAlert" style="display: none;"></div>
            <input 
                type="email" 
                id="emailInput" 
                class="login-input" 
                placeholder="seu.nome@ipt.br"
                onkeydown="handleLoginKeyDown(event)"
            >
            <button class="login-button" id="loginButton" onclick="login()">
                Acessar LIDIA
            </button>
        </div>
    </div>

    <!-- Interface Principal -->
    <div class="main-app" id="mainApp">
        <header class="header">
            <div class="logo-container">
                <div class="lidia-logo"></div>
                <div>
                    <h1 class="brand-title">LIDIA</h1>
                    <p class="brand-subtitle">IA do LID-IPT</p>
                </div>
            </div>
            <div class="header-actions">
                <div class="admin-panel" id="adminPanel">
                    <span id="adminCostText">Carregando custos...</span>
                </div>
                <button class="new-chat-btn" onclick="startNewChat()">
                    <span>+</span>
                    Nova Conversa
                </button>
                <button class="logout-btn" onclick="logout()">
                    Sair
                </button>
            </div>
        </header>

        <div class="main-container">
            <aside class="sidebar">
                <h3 style="margin-bottom: 1rem; color: #374151; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em;">Conversas Anteriores</h3>
                <ul id="chatHistory">
                    <!-- Histórico será carregado aqui -->
                </ul>
            </aside>

            <main class="chat-content">
                <div class="welcome-screen" id="welcomeScreen">
                    <div class="welcome-logo"></div>
                    <div class="greeting-text" id="greetingText">Bom dia</div>
                    <div class="help-text">Como posso ajudar você hoje?</div>
                    
                    <div class="features-grid">
                        <div class="feature-card" onclick="startChatWithPrompt('Preciso de ajuda para estruturar uma metodologia de pesquisa')">
                            <div class="feature-icon" style="background: #eff6ff; color: #3b82f6;">📝</div>
                            <h3 class="feature-title">Suporte à Pesquisa</h3>
                            <p class="feature-description">Auxílio na estruturação de metodologias, revisão de literatura e organização de ideias</p>
                        </div>
                        <div class="feature-card" onclick="startChatWithPrompt('Preciso escrever um relatório técnico')">
                            <div class="feature-icon" style="background: #f0fdf4; color: #22c55e;">📄</div>
                            <h3 class="feature-title">Redação Técnica</h3>
                            <p class="feature-description">Auxílio na elaboração de relatórios, artigos e documentação técnica</p>
                        </div>
                        <div class="feature-card" onclick="startChatWithPrompt('Preciso interpretar alguns dados e resultados')">
                            <div class="feature-icon" style="background: #fef3f2; color: #ef4444;">📊</div>
                            <h3 class="feature-title">Interpretação de Dados</h3>
                            <p class="feature-description">Auxílio na interpretação de resultados e sugestões de análises estatísticas</p>
                        </div>
                        <div class="feature-card" onclick="startChatWithPrompt('Tenho dúvidas sobre tecnologias para meu projeto')">
                            <div class="feature-icon" style="background: #fefbeb; color: #f59e0b;">💡</div>
                            <h3 class="feature-title">Consultoria Tecnológica</h3>
                            <p class="feature-description">Orientação sobre tecnologias, ferramentas e melhores práticas para projetos</p>
                        </div>
                    </div>
                </div>

                <div class="chat-area" id="chatArea">
                    <div class="messages-container" id="messagesContainer">
                        <!-- Mensagens aparecerão aqui -->
                    </div>
                    
                    <div class="loading-indicator" id="loadingIndicator">
                        <div class="loading-avatar"></div>
                        <span>LIDIA está processando sua solicitação...</span>
                        <div class="typing-animation">
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                        </div>
                    </div>

                    <div class="input-container">
                        <div class="input-wrapper">
                            <textarea 
                                class="message-input" 
                                id="messageInput" 
                                placeholder="Responder à LIDIA..."
                                rows="1"
                                onkeydown="handleKeyDown(event)"
                                oninput="autoResize(this)"
                            ></textarea>
                            <button class="send-button" id="sendButton" onclick="sendMessage()">➤</button>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    </div>

    <script>
        let currentChatId = null;
        let messageHistory = [];
        let userInfo = null;

        // Verificar autenticação ao carregar
        document.addEventListener('DOMContentLoaded', function() {
            checkAuthentication();
            updateGreeting();
        });

        async function checkAuthentication() {
            try {
                const response = await fetch('/api/user');
                if (response.ok) {
                    userInfo = await response.json();
                    showMainApp();
                } else {
                    showLoginPage();
                }
            } catch (error) {
                showLoginPage();
            }
        }

        function showLoginPage() {
            document.getElementById('loginPage').style.display = 'flex';
            document.getElementById('mainApp').classList.remove('active');
        }

        function showMainApp() {
            document.getElementById('loginPage').style.display = 'none';
            document.getElementById('mainApp').classList.add('active');
            
            if (userInfo && userInfo.is_admin) {
                document.getElementById('adminPanel').classList.add('show');
                loadCosts();
            }
        }

        function handleLoginKeyDown(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                login();
            }
        }

        async function login() {
            const email = document.getElementById('emailInput').value.trim();
            const loginButton = document.getElementById('loginButton');
            const alertDiv = document.getElementById('loginAlert');
            
            if (!email) {
                showAlert('Por favor, digite seu email', 'error');
                return;
            }

            loginButton.disabled = true;
            loginButton.textContent = 'Entrando...';

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email: email })
                });

                const data = await response.json();

                if (data.success) {
                    userInfo = { email: email, is_admin: data.is_admin };
                    showMainApp();
                } else {
                    showAlert(data.message, 'error');
                }
            } catch (error) {
                showAlert('Erro de conexão. Tente novamente.', 'error');
            } finally {
                loginButton.disabled = false;
                loginButton.textContent = 'Acessar LIDIA';
            }
        }

        function showAlert(message, type) {
            const alertDiv = document.getElementById('loginAlert');
            alertDiv.className = `alert alert-${type}`;
            alertDiv.textContent = message;
            alertDiv.style.display = 'block';
            
            setTimeout(() => {
                alertDiv.style.display = 'none';
            }, 5000);
        }

        async function logout() {
            try {
                await fetch('/api/logout', { method: 'POST' });
                userInfo = null;
                currentChatId = null;
                messageHistory = [];
                document.getElementById('messagesContainer').innerHTML = '';
                showLoginPage();
            } catch (error) {
                console.error('Erro ao fazer logout:', error);
            }
        }

        async function loadCosts() {
            try {
                const response = await fetch('/api/costs');
                if (response.ok) {
                    const costs = await response.json();
                    document.getElementById('adminCostText').textContent = 
                        `Admin: Custo mensal: R$ ${costs.total.toFixed(2)} | Perguntas: ${costs.questions} | Orçamento usado: ${costs.budget_used.toFixed(1)}%`;
                }
            } catch (error) {
                console.error('Erro ao carregar custos:', error);
            }
        }

        function updateGreeting() {
            const now = new Date();
            const hour = now.getHours();
            const greetingElement = document.getElementById('greetingText');
            
            if (hour >= 5 && hour < 12) {
                greetingElement.textContent = 'Bom dia';
            } else if (hour >= 12 && hour < 18) {
                greetingElement.textContent = 'Boa tarde';
            } else {
                greetingElement.textContent = 'Boa noite';
            }
        }

        function autoResize(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = textarea.scrollHeight + 'px';
        }

        function handleKeyDown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        function startNewChat() {
            currentChatId = 'chat_' + Date.now();
            messageHistory = [];
            
            document.getElementById('welcomeScreen').style.display = 'none';
            document.getElementById('chatArea').classList.add('active');
            document.getElementById('messagesContainer').innerHTML = '';
            document.getElementById('messageInput').focus();
        }

        function startChatWithPrompt(prompt) {
            startNewChat();
            setTimeout(() => {
                document.getElementById('messageInput').value = prompt;
                sendMessage();
            }, 100);
        }

        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;

            if (!currentChatId) {
                startNewChat();
            }

            // Adicionar mensagem do usuário
            addMessage(message, 'user');
            input.value = '';
            input.style.height = 'auto';

            // Mostrar indicador de carregamento
            showLoading();

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });

                if (response.ok) {
                    const data = await response.json();
                    hideLoading();
                    addMessage(data.response, 'assistant');
                    
                    // Atualizar custos se for admin
                    if (userInfo && userInfo.is_admin) {
                        loadCosts();
                    }
                } else {
                    hideLoading();
                    addMessage('Desculpe, ocorreu um erro. Tente novamente.', 'assistant');
                }
            } catch (error) {
                hideLoading();
                addMessage('Erro de conexão. Verifique sua internet e tente novamente.', 'assistant');
            }
        }

        function addMessage(content, sender) {
            const container = document.getElementById('messagesContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            if (sender === 'user') {
                avatar.textContent = 'U';
            }
            
            const messageContent = document.createElement('div');
            messageContent.className = 'message-content';
            messageContent.textContent = content;
            
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(messageContent);
            container.appendChild(messageDiv);
            
            // Scroll para a mensagem mais recente
            container.scrollTop = container.scrollHeight;
            
            // Adicionar ao histórico
            messageHistory.push({ content, sender, timestamp: new Date() });
        }

        function showLoading() {
            document.getElementById('loadingIndicator').classList.add('show');
            document.getElementById('sendButton').disabled = true;
            
            // Scroll para mostrar o loading
            const container = document.getElementById('messagesContainer');
            setTimeout(() => {
                container.scrollTop = container.scrollHeight;
            }, 100);
        }

        function hideLoading() {
            document.getElementById('loadingIndicator').classList.remove('show');
            document.getElementById('sendButton').disabled = false;
        }
    </script>
</body>
</html>
