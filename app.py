from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import sqlite3
from datetime import datetime
import uuid
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'lidia-ipt-secret-key-2024')

# Configurações
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
ADMIN_USERS = ['robsonss@ipt.br']

class SecurityManager:
    def __init__(self):
        self.init_database()
    
    def init_database(self):
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            # Tabela de conversas com mais detalhes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    chat_id TEXT,
                    question TEXT,
                    response TEXT,
                    timestamp DATETIME,
                    session_id TEXT,
                    cost REAL
                )
            ''')
            
            # Tabela de chats
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT UNIQUE,
                    email TEXT,
                    title TEXT,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''')
            
            # Tabela de acessos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS access_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    ip_address TEXT,
                    timestamp DATETIME,
                    action TEXT,
                    success BOOLEAN
                )
            ''')
            
            # Tabela de uploads
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    filename TEXT,
                    file_size INTEGER,
                    upload_time DATETIME,
                    chat_id TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erro ao inicializar banco: {e}")
    
    def validate_ipt_email(self, email):
        if not email:
            return False, "Email obrigatório"
        
        if not email.endswith('@ipt.br'):
            return False, "Acesso exclusivo para colaboradores do IPT"
        
        if len(email.split('@')[0]) < 3:
            return False, "Email inválido"
        
        return True, "Email válido"
    
    def log_conversation(self, email, chat_id, question, response, cost=0.003):
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO conversation_logs 
                (email, chat_id, question, response, timestamp, session_id, cost)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                email,
                chat_id,
                question,
                response[:1000],
                datetime.now(),
                session.get('session_id', 'unknown'),
                cost
            ))
            
            # Atualizar ou criar chat
            cursor.execute('''
                INSERT OR REPLACE INTO chats 
                (chat_id, email, title, created_at, updated_at)
                VALUES (?, ?, ?, 
                    COALESCE((SELECT created_at FROM chats WHERE chat_id = ?), ?),
                    ?)
            ''', (
                chat_id,
                email,
                question[:50] + "..." if len(question) > 50 else question,
                chat_id,
                datetime.now(),
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erro ao registrar conversa: {e}")
    
    def get_user_chats(self, email):
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT chat_id, title, updated_at 
                FROM chats 
                WHERE email = ? 
                ORDER BY updated_at DESC 
                LIMIT 20
            ''', (email,))
            
            chats = cursor.fetchall()
            conn.close()
            
            return [{'chat_id': chat[0], 'title': chat[1], 'updated_at': chat[2]} for chat in chats]
        except:
            return []
    
    def get_chat_messages(self, email, chat_id):
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT question, response, timestamp 
                FROM conversation_logs 
                WHERE email = ? AND chat_id = ? 
                ORDER BY timestamp ASC
            ''', (email, chat_id))
            
            messages = cursor.fetchall()
            conn.close()
            
            result = []
            for msg in messages:
                result.append({'content': msg[0], 'sender': 'user', 'timestamp': msg[2]})
                result.append({'content': msg[1], 'sender': 'assistant', 'timestamp': msg[2]})
            
            return result
        except:
            return []
    
    def log_access(self, email, ip_address, action="login", success=True):
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO access_logs 
                (email, ip_address, timestamp, action, success)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                email,
                ip_address,
                datetime.now(),
                action,
                success
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erro ao registrar acesso: {e}")

class LIDIAAssistant:
    def __init__(self):
        self.model = "claude-3-haiku-20240307"
        self.client = None
        
        self.ipt_context = """Você é LIDIA, a Inteligência Artificial do Laboratório de Inovação Digital do Instituto de Pesquisas Tecnológicas (IPT).

Como assistente conversacional, você pode ajudar colaboradores do IPT com:
- Auxílio na estruturação de metodologias de pesquisa
- Suporte na redação de relatórios e documentação técnica
- Orientação sobre tecnologias e ferramentas disponíveis
- Interpretação e discussão de resultados de pesquisa
- Sugestões de melhores práticas em projetos
- Resposta a dúvidas técnicas e conceituais

IMPORTANTE: Apenas responda sobre o que você é se o usuário perguntar especificamente. Nesse caso, use: "Entendido, sou a assistente LIDIA do IPT (Instituto de Pesquisas Tecnológicas de São Paulo)".

Responda de forma clara, objetiva e profissional."""
    
    def get_client(self):
        if self.client is None:
            try:
                import anthropic
                if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == '':
                    return None
                self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            except Exception as e:
                print(f"Erro ao inicializar Anthropic: {e}")
                return None
        return self.client
    
    def process_query(self, message, user_email=""):
        client = self.get_client()
        
        if not client:
            return self.get_fallback_response(message)
        
        prompt = f"""{self.ipt_context}

PERGUNTA: {message}

Responda de forma clara e útil."""
        
        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"Erro na API Anthropic: {e}")
            return self.get_fallback_response(message)
    
    def get_fallback_response(self, message):
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['o que é', 'quem é', 'como funciona', 'lidia']):
            return "Entendido, sou a assistente LIDIA do IPT (Instituto de Pesquisas Tecnológicas de São Paulo). Sou uma assistente conversacional criada para apoiar colaboradores do IPT com orientações sobre pesquisa, redação técnica, tecnologias e metodologias. Como posso ajudá-lo hoje?"
        
        if any(word in message_lower for word in ['dados', 'análise', 'resultados']):
            return "Posso ajudá-lo a interpretar dados e discutir abordagens analíticas. Se você compartilhar seus resultados, posso sugerir interpretações e orientar sobre métodos adequados. Que tipo de dados você está analisando?"
        
        if any(word in message_lower for word in ['pesquisa', 'metodologia']):
            return "Posso auxiliá-lo na estruturação de metodologias de pesquisa e organização de ideias. Conte-me sobre seu projeto - qual é o objetivo e que tipo de orientação você precisa?"
        
        if any(word in message_lower for word in ['relatório', 'redação', 'documento']):
            return "Posso ajudá-lo na elaboração de relatórios técnicos e estruturação de documentos. Que tipo de documento você precisa elaborar? Posso sugerir estruturas e orientar sobre boas práticas de redação técnica."
        
        if any(word in message_lower for word in ['tecnologia', 'ferramenta', 'software']):
            return "Posso orientá-lo sobre tecnologias e ferramentas para projetos. Conte-me sobre seu projeto - que tipo de solução você está buscando? Posso sugerir tecnologias adequadas e discutir diferentes abordagens."
        
        return "Olá! Sou sua assistente LIDIA do IPT. Posso ajudá-lo com orientações sobre pesquisa, redação técnica, tecnologias e metodologias. Como posso apoiá-lo em seu trabalho hoje? (Nota: Sistema funcionando em modo básico)"

# Inicializar componentes
security = SecurityManager()
assistant = LIDIAAssistant()

def get_current_costs():
    try:
        conn = sqlite3.connect('lidia_security.db')
        cursor = conn.cursor()
        
        first_day = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        
        cursor.execute('''
            SELECT COUNT(*) FROM conversation_logs 
            WHERE timestamp >= ?
        ''', (first_day,))
        
        questions_this_month = cursor.fetchone()[0]
        variable_costs = questions_this_month * 0.003
        fixed_costs = 100
        total_costs = fixed_costs + variable_costs
        budget_used = (total_costs / 200) * 100
        
        conn.close()
        
        return {
            'total': total_costs,
            'fixed': fixed_costs,
            'variable': variable_costs,
            'questions': questions_this_month,
            'budget_used': budget_used
        }
    except:
        return {
            'total': 100,
            'fixed': 100,
            'variable': 0,
            'questions': 0,
            'budget_used': 50
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip()
    
    is_valid, message = security.validate_ipt_email(email)
    
    if is_valid:
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        security.log_access(email, client_ip, "login", True)
        
        session['authenticated'] = True
        session['user_email'] = email
        session['is_admin'] = email in ADMIN_USERS
        session['session_id'] = str(uuid.uuid4())
        
        print(f"Login: {email}, Admin: {session['is_admin']}")  # Debug
        
        return jsonify({
            'success': True,
            'message': 'Login realizado com sucesso',
            'is_admin': session['is_admin']
        })
    else:
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        security.log_access(email, client_ip, "login_failed", False)
        
        return jsonify({
            'success': False,
            'message': message
        }), 400

@app.route('/api/chat', methods=['POST'])
def chat():
    if not session.get('authenticated'):
        return jsonify({'error': 'Não autenticado'}), 401
    
    data = request.get_json()
    message = data.get('message', '').strip()
    chat_id = data.get('chat_id', '')
    
    if not message:
        return jsonify({'error': 'Mensagem vazia'}), 400
    
    if not chat_id:
        chat_id = 'chat_' + str(uuid.uuid4())
    
    try:
        response = assistant.process_query(message, session['user_email'])
        
        security.log_conversation(
            session['user_email'], 
            chat_id,
            message, 
            response
        )
        
        return jsonify({
            'response': response,
            'chat_id': chat_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/chats')
def get_chats():
    if not session.get('authenticated'):
        return jsonify({'error': 'Não autenticado'}), 401
    
    chats = security.get_user_chats(session['user_email'])
    return jsonify(chats)

@app.route('/api/chats/<chat_id>')
def get_chat(chat_id):
    if not session.get('authenticated'):
        return jsonify({'error': 'Não autenticado'}), 401
    
    messages = security.get_chat_messages(session['user_email'], chat_id)
    return jsonify(messages)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if not session.get('authenticated'):
        return jsonify({'error': 'Não autenticado'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    # Por enquanto, apenas simular upload
    return jsonify({
        'success': True,
        'filename': file.filename,
        'size': len(file.read()),
        'message': f'Arquivo {file.filename} recebido com sucesso! Funcionalidade de processamento será implementada em breve.'
    })

@app.route('/api/costs')
def costs():
    if not session.get('authenticated') or not session.get('is_admin'):
        return jsonify({'error': 'Acesso negado'}), 403
    
    costs_data = get_current_costs()
    return jsonify(costs_data)

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/user')
def user_info():
    if not session.get('authenticated'):
        return jsonify({'error': 'Não autenticado'}), 401
    
    return jsonify({
        'email': session['user_email'],
        'is_admin': session.get('is_admin', False),
        'authenticated': True
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
