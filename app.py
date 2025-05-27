from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import sqlite3
from datetime import datetime
import uuid
import json
import PyPDF2
import docx
from werkzeug.utils import secure_filename
import io

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'lidia-ipt-secret-key-2024')

# Configurações
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
ADMIN_USERS = ['robsonss@ipt.br']  # Lista explícita de administradores

class DocumentProcessor:
    """Processador de documentos"""
    
    @staticmethod
    def extract_text_from_file(file_storage):
        """Extrai texto de arquivo enviado"""
        try:
            filename = file_storage.filename.lower()
            file_content = file_storage.read()
            
            if filename.endswith('.pdf'):
                return DocumentProcessor.extract_from_pdf(file_content)
            elif filename.endswith('.docx'):
                return DocumentProcessor.extract_from_docx(file_content)
            elif filename.endswith('.txt'):
                return file_content.decode('utf-8', errors='ignore')
            else:
                return "Formato de arquivo não suportado para extração de texto."
                
        except Exception as e:
            return f"Erro ao processar arquivo: {str(e)}"
    
    @staticmethod
    def extract_from_pdf(file_content):
        """Extrai texto de PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text if text.strip() else "Não foi possível extrair texto do PDF."
        except:
            return "Erro ao processar PDF."
    
    @staticmethod
    def extract_from_docx(file_content):
        """Extrai texto de DOCX"""
        try:
            doc = docx.Document(io.BytesIO(file_content))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text if text.strip() else "Documento DOCX vazio."
        except:
            return "Erro ao processar documento Word."

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
                    cost REAL,
                    document_context TEXT
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
                    updated_at DATETIME,
                    has_document BOOLEAN DEFAULT 0,
                    document_name TEXT
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
                    chat_id TEXT,
                    file_content TEXT
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
    
    def is_admin(self, email):
        """Verifica se email é administrador"""
        result = email in ADMIN_USERS
        print(f"DEBUG: Verificando admin para {email}: {result}")
        return result
    
    def log_conversation(self, email, chat_id, question, response, cost=0.003, document_context=""):
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO conversation_logs 
                (email, chat_id, question, response, timestamp, session_id, cost, document_context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email,
                chat_id,
                question,
                response[:1000],
                datetime.now(),
                session.get('session_id', 'unknown'),
                cost,
                document_context[:500] if document_context else ""
            ))
            
            # Atualizar ou criar chat
            cursor.execute('''
                INSERT OR REPLACE INTO chats 
                (chat_id, email, title, created_at, updated_at, has_document, document_name)
                VALUES (?, ?, ?, 
                    COALESCE((SELECT created_at FROM chats WHERE chat_id = ?), ?),
                    ?, ?, ?)
            ''', (
                chat_id,
                email,
                question[:50] + "..." if len(question) > 50 else question,
                chat_id,
                datetime.now(),
                datetime.now(),
                bool(document_context),
                ""
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erro ao registrar conversa: {e}")
    
    def store_document(self, email, chat_id, filename, file_content, extracted_text):
        """Armazena documento processado"""
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO file_uploads 
                (email, filename, file_size, upload_time, chat_id, file_content)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                email,
                filename,
                len(file_content),
                datetime.now(),
                chat_id,
                extracted_text[:5000]  # Limitar tamanho
            ))
            
            # Atualizar chat para indicar que tem documento
            cursor.execute('''
                UPDATE chats 
                SET has_document = 1, document_name = ?
                WHERE chat_id = ?
            ''', (filename, chat_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao armazenar documento: {e}")
            return False
    
    def get_document_context(self, chat_id):
        """Recupera contexto do documento para o chat"""
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT file_content, filename FROM file_uploads 
                WHERE chat_id = ? 
                ORDER BY upload_time DESC 
                LIMIT 1
            ''', (chat_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0], result[1]
            return None, None
        except:
            return None, None
    
    def get_user_chats(self, email):
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT chat_id, title, updated_at, has_document, document_name 
                FROM chats 
                WHERE email = ? 
                ORDER BY updated_at DESC 
                LIMIT 20
            ''', (email,))
            
            chats = cursor.fetchall()
            conn.close()
            
            return [{
                'chat_id': chat[0], 
                'title': chat[1], 
                'updated_at': chat[2],
                'has_document': bool(chat[3]),
                'document_name': chat[4]
            } for chat in chats]
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
- Análise de documentos enviados pelos usuários

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
    
    def process_query(self, message, user_email="", document_context="", filename=""):
        client = self.get_client()
        
        if not client:
            return self.get_fallback_response(message, document_context, filename)
        
        # Construir prompt com contexto do documento se disponível
        prompt_parts = [self.ipt_context]
        
        if document_context:
            prompt_parts.append(f"\nDOCUMENTO ENVIADO PELO USUÁRIO ({filename}):\n{document_context[:3000]}\n")
        
        prompt_parts.append(f"\nPERGUNTA: {message}\n\nResponda de forma clara e útil.")
        
        prompt = "\n".join(prompt_parts)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"Erro na API Anthropic: {e}")
            return self.get_fallback_response(message, document_context, filename)
    
    def get_fallback_response(self, message, document_context="", filename=""):
        message_lower = message.lower()
        
        if document_context:
            return f"Recebi o documento '{filename}' com sucesso. Posso ajudá-lo a analisar o conteúdo, responder perguntas sobre o documento ou auxiliar com interpretações. O que gostaria de saber sobre este documento?"
        
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
    
    print(f"DEBUG: Tentativa de login para: {email}")
    
    is_valid, message = security.validate_ipt_email(email)
    
    if is_valid:
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        security.log_access(email, client_ip, "login", True)
        
        is_admin = security.is_admin(email)
        
        session['authenticated'] = True
        session['user_email'] = email
        session['is_admin'] = is_admin
        session['session_id'] = str(uuid.uuid4())
        
        print(f"DEBUG: Login sucesso - Email: {email}, Admin: {is_admin}")
        
        return jsonify({
            'success': True,
            'message': 'Login realizado com sucesso',
            'is_admin': is_admin
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
        # Verificar se há documento no contexto
        document_context, filename = security.get_document_context(chat_id)
        
        response = assistant.process_query(
            message, 
            session['user_email'],
            document_context or "",
            filename or ""
        )
        
        security.log_conversation(
            session['user_email'], 
            chat_id,
            message, 
            response,
            document_context=document_context or ""
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
    
    chat_id = request.form.get('chat_id', 'chat_' + str(uuid.uuid4()))
    
    try:
        # Extrair texto do arquivo
        extracted_text = DocumentProcessor.extract_text_from_file(file)
        
        # Armazenar documento
        success = security.store_document(
            session['user_email'],
            chat_id,
            secure_filename(file.filename),
            file.read(),
            extracted_text
        )
        
        if success:
            return jsonify({
                'success': True,
                'filename': file.filename,
                'chat_id': chat_id,
                'message': f'Documento "{file.filename}" processado com sucesso! Agora você pode fazer perguntas sobre o conteúdo.',
                'extracted_length': len(extracted_text)
            })
        else:
            return jsonify({'error': 'Erro ao processar documento'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Erro ao processar arquivo: {str(e)}'}), 500

@app.route('/api/costs')
def costs():
    if not session.get('authenticated'):
        return jsonify({'error': 'Não autenticado'}), 401
    
    print(f"DEBUG: Verificando custos - User: {session['user_email']}, Admin: {session.get('is_admin')}")
    
    if not session.get('is_admin'):
        return jsonify({'error': 'Acesso negado - apenas administradores'}), 403
    
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
    
    user_data = {
        'email': session['user_email'],
        'is_admin': session.get('is_admin', False),
        'authenticated': True
    }
    
    print(f"DEBUG: User info response: {user_data}")
    
    return jsonify(user_data)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
