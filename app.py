from flask import Flask, render_template, request, jsonify, session
import os
import sqlite3
import hashlib
from datetime import datetime, timedelta
import anthropic
import json
from pathlib import Path
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'lidia-ipt-secret-key-2024')

# Configurações
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', 'sk-ant-api03-placeholder')
ADMIN_USERS = ['robsonss@ipt.br']

class SecurityManager:
    def __init__(self):
        self.init_database()
    
    def init_database(self):
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    question TEXT,
                    response TEXT,
                    timestamp DATETIME,
                    session_id TEXT,
                    cost REAL
                )
            ''')
            
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
    
    def log_conversation(self, email, question, response, cost=0.003):
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO conversation_logs 
                (email, question, response, timestamp, session_id, cost)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                email,
                question,
                response[:1000],
                datetime.now(),
                session.get('session_id', 'unknown'),
                cost
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erro ao registrar conversa: {e}")
    
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
    def __init__(self, api_key):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-haiku-20240307"
        
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
    
    def process_query(self, message, user_email=""):
        prompt = f"""{self.ipt_context}

PERGUNTA: {message}

Responda de forma clara e útil."""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            answer = response.content[0].text
            return answer
            
        except Exception as e:
            return f"Desculpe, ocorreu um erro ao processar sua solicitação: {str(e)}"

# Inicializar componentes
security = SecurityManager()
assistant = LIDIAAssistant(ANTHROPIC_API_KEY)

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
    
    if not message:
        return jsonify({'error': 'Mensagem vazia'}), 400
    
    try:
        response = assistant.process_query(message, session['user_email'])
        
        security.log_conversation(
            session['user_email'], 
            message, 
            response
        )
        
        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

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
