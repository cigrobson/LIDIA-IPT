from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import sqlite3
from datetime import datetime, timedelta
import uuid
import json
import PyPDF2
import docx
from werkzeug.utils import secure_filename
import io
import hashlib
import time
from functools import wraps
import bleach
from collections import defaultdict
import threading

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'lidia-ipt-secret-key-2024-enhanced')

# Configurações Railway
PORT = int(os.environ.get('PORT', 5000))
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
INITIAL_ADMIN = os.environ.get('INITIAL_ADMIN', 'robsonss@ipt.br')
MAX_FILE_SIZE = int(os.environ.get('MAX_FILE_SIZE', 10 * 1024 * 1024))
MAX_REQUESTS_PER_HOUR = int(os.environ.get('MAX_REQUESTS_PER_HOUR', 100))
MAX_REQUESTS_PER_MINUTE = int(os.environ.get('MAX_REQUESTS_PER_MINUTE', 20))

# Lista explícita de administradores (como no código original)
ADMIN_USERS = [
    'robsonss@ipt.br',
    # Adicionar outros emails @ipt.br conforme necessário
]

IS_RAILWAY = os.environ.get('RAILWAY_ENVIRONMENT') is not None

# Cache simples
class SimpleCache:
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
        self.lock = threading.Lock()
    
    def get(self, key, ttl=3600):
        with self.lock:
            if key in self.cache:
                if time.time() - self.timestamps[key] < ttl:
                    return self.cache[key]
                else:
                    del self.cache[key]
                    del self.timestamps[key]
            return None
    
    def set(self, key, value):
        with self.lock:
            self.cache[key] = value
            self.timestamps[key] = time.time()

cache = SimpleCache()

# Rate limiting
class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_allowed(self, email, max_per_hour=100, max_per_minute=20):
        with self.lock:
            now = time.time()
            hour_ago = now - 3600
            minute_ago = now - 60
            
            self.requests[email] = [req_time for req_time in self.requests[email] if req_time > hour_ago]
            recent_requests = [req_time for req_time in self.requests[email] if req_time > minute_ago]
            
            if len(self.requests[email]) >= max_per_hour:
                return False, "Limite de requisições por hora excedido"
            
            if len(recent_requests) >= max_per_minute:
                return False, "Limite de requisições por minuto excedido"
            
            self.requests[email].append(now)
            return True, "OK"

rate_limiter = RateLimiter()

class DocumentProcessor:
    """Processador de documentos CORRIGIDO"""
    
    @staticmethod
    def validate_file(file_storage):
        """Valida arquivo antes do processamento"""
        if not file_storage or not file_storage.filename:
            return False, "Arquivo inválido"
        
        # Verificar tamanho
        file_storage.seek(0, 2)
        size = file_storage.tell()
        file_storage.seek(0)
        
        if size > MAX_FILE_SIZE:
            return False, f"Arquivo muito grande. Máximo: {MAX_FILE_SIZE/1024/1024:.1f}MB"
        
        # Verificar extensão
        allowed_extensions = ['.pdf', '.docx', '.txt']
        filename = file_storage.filename.lower()
        
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            return False, "Tipo de arquivo não suportado. Use: PDF, DOCX ou TXT"
        
        return True, "Arquivo válido"
    
    @staticmethod
    def extract_text_from_file(file_storage):
        """Extrai texto de arquivo - VERSÃO CORRIGIDA"""
        try:
            print(f"🔍 Iniciando extração de: {file_storage.filename}")
            
            # Validar arquivo primeiro
            is_valid, message = DocumentProcessor.validate_file(file_storage)
            if not is_valid:
                print(f"❌ Validação falhou: {message}")
                return f"Erro de validação: {message}"
            
            filename = file_storage.filename.lower()
            file_storage.seek(0)  # Garantir que está no início
            file_content = file_storage.read()
            
            print(f"📄 Arquivo lido: {len(file_content)} bytes")
            
            if filename.endswith('.pdf'):
                text = DocumentProcessor.extract_from_pdf(file_content)
            elif filename.endswith('.docx'):
                text = DocumentProcessor.extract_from_docx(file_content)
            elif filename.endswith('.txt'):
                text = file_content.decode('utf-8', errors='ignore')
            else:
                return "Formato de arquivo não suportado."
            
            print(f"✅ Texto extraído: {len(text)} caracteres")
            
            if not text or len(text.strip()) < 10:
                return "Não foi possível extrair texto suficiente do arquivo. Verifique se o arquivo não está vazio ou corrompido."
            
            return text
                
        except Exception as e:
            print(f"❌ Erro na extração: {str(e)}")
            return f"Erro ao processar arquivo: {str(e)}"
    
    @staticmethod
    def extract_from_pdf(file_content):
        """Extrai texto de PDF - VERSÃO APRIMORADA"""
        try:
            print("📖 Processando PDF...")
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            
            if len(pdf_reader.pages) > 50:
                return "PDF muito grande. Máximo de 50 páginas suportadas."
            
            text = ""
            successful_pages = 0
            
            for i, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text += f"\n=== PÁGINA {i+1} ===\n"
                        text += page_text.strip() + "\n"
                        successful_pages += 1
                    else:
                        text += f"\n=== PÁGINA {i+1} (sem texto detectado) ===\n"
                except Exception as e:
                    print(f"⚠️ Erro na página {i+1}: {e}")
                    text += f"\n=== PÁGINA {i+1} (erro na leitura) ===\n"
            
            print(f"📊 PDF processado: {successful_pages}/{len(pdf_reader.pages)} páginas com texto")
            
            if not text.strip():
                return "PDF não contém texto extraível. Pode ser um arquivo de imagem ou estar corrompido."
            
            return text
            
        except Exception as e:
            print(f"❌ Erro no PDF: {e}")
            return f"Erro ao processar PDF: {str(e)}"
    
    @staticmethod
    def extract_from_docx(file_content):
        """Extrai texto de DOCX - VERSÃO APRIMORADA"""
        try:
            print("📝 Processando DOCX...")
            doc = docx.Document(io.BytesIO(file_content))
            
            text = ""
            
            # Extrair parágrafos
            for i, paragraph in enumerate(doc.paragraphs):
                if paragraph.text.strip():
                    text += paragraph.text.strip() + "\n"
            
            # Extrair texto de tabelas
            for table_num, table in enumerate(doc.tables):
                text += f"\n=== TABELA {table_num + 1} ===\n"
                for row_num, row in enumerate(table.rows):
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        text += " | ".join(row_text) + "\n"
            
            print(f"📊 DOCX processado: {len(text)} caracteres extraídos")
            
            if not text.strip():
                return "Documento DOCX vazio ou sem texto extraível."
            
            return text
            
        except Exception as e:
            print(f"❌ Erro no DOCX: {e}")
            return f"Erro ao processar documento Word: {str(e)}"

class SecurityManager:
    def __init__(self):
        self.init_database()
    
    def init_database(self):
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            # Verificar tabelas existentes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            print(f"📊 Tabelas existentes: {existing_tables}")
            
            # Tabela de conversas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    chat_id TEXT,
                    question TEXT,
                    response TEXT,
                    timestamp DATETIME,
                    session_id TEXT,
                    cost REAL DEFAULT 0.003,
                    document_context TEXT,
                    processing_time REAL DEFAULT 0,
                    ip_address TEXT
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
                    document_name TEXT,
                    message_count INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0
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
                    success BOOLEAN,
                    user_agent TEXT,
                    details TEXT
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
                    file_content TEXT,
                    file_hash TEXT,
                    processing_status TEXT DEFAULT 'processed'
                )
            ''')
            
            # Adicionar colunas se não existirem (migração automática)
            self.migrate_table_if_needed(cursor, 'conversation_logs', [
                ('processing_time', 'REAL DEFAULT 0'),
                ('ip_address', 'TEXT'),
                ('document_context', 'TEXT')
            ])
            
            self.migrate_table_if_needed(cursor, 'chats', [
                ('message_count', 'INTEGER DEFAULT 0'),
                ('total_cost', 'REAL DEFAULT 0')
            ])
            
            conn.commit()
            conn.close()
            print("✅ Banco de dados inicializado com sucesso")
            
        except Exception as e:
            print(f"❌ Erro ao inicializar banco: {e}")
    
    def migrate_table_if_needed(self, cursor, table_name, columns):
        """Adiciona colunas se não existirem"""
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            for column_name, column_def in columns:
                if column_name not in existing_columns:
                    cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}')
                    print(f"✅ Coluna {column_name} adicionada à {table_name}")
        except Exception as e:
            print(f"⚠️ Erro na migração de {table_name}: {e}")
    
    def validate_ipt_email(self, email):
        if not email:
            return False, "Email obrigatório"
        
        email = bleach.clean(email.strip().lower(), tags=[], strip=True)
        
        if not email.endswith('@ipt.br'):
            return False, "Acesso exclusivo para colaboradores do IPT"
        
        if len(email.split('@')[0]) < 3:
            return False, "Email inválido"
        
        return True, "Email válido"
    
    def is_admin(self, email):
        """Verifica se email é administrador (lista explícita + dinâmica)"""
        # Lista estática original
        if email in ADMIN_USERS:
            return True
        
        # Lista dinâmica no banco (funcionalidade nova)
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE,
                    granted_by TEXT,
                    granted_at DATETIME,
                    is_active BOOLEAN DEFAULT 1,
                    permissions TEXT DEFAULT 'full'
                )
            ''')
            
            # Inserir admins da lista estática se não existirem
            for admin_email in ADMIN_USERS:
                cursor.execute('''
                    INSERT OR IGNORE INTO admin_users (email, granted_by, granted_at, is_active, permissions)
                    VALUES (?, 'SYSTEM', ?, 1, 'full')
                ''', (admin_email, datetime.now()))
            
            cursor.execute('''
                SELECT permissions FROM admin_users 
                WHERE email = ? AND is_active = 1
            ''', (email,))
            
            result = cursor.fetchone()
            conn.commit()
            conn.close()
            
            return result is not None
        except:
            return email in ADMIN_USERS  # Fallback para lista estática
    
    def add_admin(self, new_admin_email, granted_by_email, permissions='full'):
        """Adiciona novo administrador"""
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO admin_users 
                (email, granted_by, granted_at, is_active, permissions)
                VALUES (?, ?, ?, 1, ?)
            ''', (new_admin_email, granted_by_email, datetime.now(), permissions))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Admin adicionado: {new_admin_email}")
            return True
        except Exception as e:
            print(f"❌ Erro ao adicionar admin: {e}")
            return False
    
    def get_all_admins(self):
        """Retorna lista de todos os administradores"""
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            # Garantir que tabela existe
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE,
                    granted_by TEXT,
                    granted_at DATETIME,
                    is_active BOOLEAN DEFAULT 1,
                    permissions TEXT DEFAULT 'full'
                )
            ''')
            
            # Inserir admins da lista estática se não existirem
            for admin_email in ADMIN_USERS:
                cursor.execute('''
                    INSERT OR IGNORE INTO admin_users (email, granted_by, granted_at, is_active, permissions)
                    VALUES (?, 'SYSTEM', ?, 1, 'full')
                ''', (admin_email, datetime.now()))
            
            cursor.execute('''
                SELECT email, granted_by, granted_at, is_active, permissions
                FROM admin_users
                ORDER BY granted_at DESC
            ''')
            
            admins = cursor.fetchall()
            conn.commit()
            conn.close()
            
            return [{
                'email': admin[0],
                'granted_by': admin[1],
                'granted_at': admin[2],
                'is_active': bool(admin[3]),
                'permissions': admin[4]
            } for admin in admins]
        except Exception as e:
            print(f"❌ Erro ao listar admins: {e}")
            # Fallback para lista estática
            return [{
                'email': email,
                'granted_by': 'SYSTEM',
                'granted_at': datetime.now().isoformat(),
                'is_active': True,
                'permissions': 'full'
            } for email in ADMIN_USERS]
    
    def log_conversation(self, email, chat_id, question, response, cost=0.003, document_context="", processing_time=0):
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            # Sanitizar dados
            question = bleach.clean(question, tags=[], strip=True)
            response = bleach.clean(response, tags=[], strip=True)
            
            cursor.execute('''
                INSERT INTO conversation_logs 
                (email, chat_id, question, response, timestamp, session_id, cost, document_context, processing_time, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email,
                chat_id,
                question,
                response[:2000],
                datetime.now(),
                session.get('session_id', 'unknown'),
                cost,
                document_context[:1000] if document_context else "",
                processing_time,
                request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            ))
            
            # Atualizar ou criar chat
            cursor.execute('''
                INSERT OR REPLACE INTO chats 
                (chat_id, email, title, created_at, updated_at, has_document, document_name, message_count, total_cost)
                VALUES (?, ?, ?, 
                    COALESCE((SELECT created_at FROM chats WHERE chat_id = ?), ?),
                    ?, ?, ?,
                    COALESCE((SELECT message_count FROM chats WHERE chat_id = ?), 0) + 1,
                    COALESCE((SELECT total_cost FROM chats WHERE chat_id = ?), 0) + ?)
            ''', (
                chat_id,
                email,
                question[:50] + "..." if len(question) > 50 else question,
                chat_id,
                datetime.now(),
                datetime.now(),
                bool(document_context),
                "",
                chat_id,
                chat_id,
                cost
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Erro ao registrar conversa: {e}")
    
    def store_document(self, email, chat_id, filename, file_content, extracted_text):
        """Armazena documento processado"""
        try:
            file_hash = hashlib.md5(file_content).hexdigest()
            
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO file_uploads 
                (email, filename, file_size, upload_time, chat_id, file_content, file_hash, processing_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email,
                filename,
                len(file_content),
                datetime.now(),
                chat_id,
                extracted_text[:15000],  # Aumentar limite para documentos maiores
                file_hash,
                'processed'
            ))
            
            # Atualizar chat
            cursor.execute('''
                UPDATE chats 
                SET has_document = 1, document_name = ?
                WHERE chat_id = ?
            ''', (filename, chat_id))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Documento armazenado: {filename} ({len(extracted_text)} chars)")
            return True
        except Exception as e:
            print(f"❌ Erro ao armazenar documento: {e}")
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
                print(f"📄 Contexto recuperado: {result[1]} ({len(result[0])} chars)")
                return result[0], result[1]
            return None, None
        except Exception as e:
            print(f"❌ Erro ao recuperar contexto: {e}")
            return None, None
    
    def get_user_chats(self, email):
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT chat_id, title, updated_at, has_document, document_name, message_count, total_cost
                FROM chats 
                WHERE email = ? 
                ORDER BY updated_at DESC 
                LIMIT 50
            ''', (email,))
            
            chats = cursor.fetchall()
            conn.close()
            
            return [{
                'chat_id': chat[0], 
                'title': chat[1], 
                'updated_at': chat[2],
                'has_document': bool(chat[3]),
                'document_name': chat[4],
                'message_count': chat[5] or 0,
                'total_cost': chat[6] or 0
            } for chat in chats]
        except:
            return []
    
    def get_chat_messages(self, email, chat_id):
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT question, response, timestamp, processing_time
                FROM conversation_logs 
                WHERE email = ? AND chat_id = ? 
                ORDER BY timestamp ASC
            ''', (email, chat_id))
            
            messages = cursor.fetchall()
            conn.close()
            
            result = []
            for msg in messages:
                result.append({
                    'content': msg[0], 
                    'sender': 'user', 
                    'timestamp': msg[2],
                    'processing_time': msg[3]
                })
                result.append({
                    'content': msg[1], 
                    'sender': 'assistant', 
                    'timestamp': msg[2],
                    'processing_time': msg[3]
                })
            
            return result
        except:
            return []
    
    def get_system_stats(self):
        """Estatísticas do sistema"""
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            stats = {}
            
            # Total de usuários únicos
            cursor.execute('SELECT COUNT(DISTINCT email) FROM conversation_logs')
            stats['total_users'] = cursor.fetchone()[0] or 0
            
            # Total de conversas
            cursor.execute('SELECT COUNT(*) FROM conversation_logs')
            stats['total_conversations'] = cursor.fetchone()[0] or 0
            
            # Total de documentos
            cursor.execute('SELECT COUNT(*) FROM file_uploads')
            stats['total_documents'] = cursor.fetchone()[0] or 0
            
            # Custos totais
            cursor.execute('SELECT SUM(cost) FROM conversation_logs')
            result = cursor.fetchone()[0]
            stats['total_costs'] = result if result else 0
            
            # Usuários ativos (últimos 30 dias)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            cursor.execute('''
                SELECT COUNT(DISTINCT email) FROM conversation_logs 
                WHERE timestamp > ?
            ''', (thirty_days_ago,))
            stats['active_users_30d'] = cursor.fetchone()[0] or 0
            
            # Conversas hoje
            today = datetime.now().date()
            cursor.execute('''
                SELECT COUNT(*) FROM conversation_logs 
                WHERE DATE(timestamp) = ?
            ''', (today,))
            stats['conversations_today'] = cursor.fetchone()[0] or 0
            
            # Top usuários
            cursor.execute('''
                SELECT email, COUNT(*) as count 
                FROM conversation_logs 
                GROUP BY email 
                ORDER BY count DESC 
                LIMIT 10
            ''')
            stats['top_users'] = [{'email': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            # Atividade por dia (últimos 7 dias)
            activity_by_day = []
            for i in range(7):
                day = datetime.now().date() - timedelta(days=i)
                cursor.execute('''
                    SELECT COUNT(*) FROM conversation_logs 
                    WHERE DATE(timestamp) = ?
                ''', (day,))
                count = cursor.fetchone()[0] or 0
                activity_by_day.append({
                    'date': day.strftime('%Y-%m-%d'),
                    'count': count
                })
            
            stats['activity_by_day'] = list(reversed(activity_by_day))
            
            conn.close()
            return stats
        except Exception as e:
            print(f"❌ Erro ao obter estatísticas: {e}")
            return {
                'total_users': 0,
                'total_conversations': 0,
                'total_documents': 0,
                'total_costs': 0,
                'active_users_30d': 0,
                'conversations_today': 0,
                'top_users': [],
                'activity_by_day': []
            }

class LIDIAAssistant:
    def __init__(self):
        self.model = "claude-3-haiku-20240307"
        self.client = None
        
        # CONTEXTO ORIGINAL RESTAURADO
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

Responda de forma clara, objetiva e profissional. Se um documento foi enviado, analise-o cuidadosamente e responda com base no conteúdo fornecido."""
    
    def get_client(self):
        if self.client is None:
            try:
                import anthropic
                if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == '':
                    print("⚠️ ANTHROPIC_API_KEY não configurada")
                    return None
                self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                print("✅ Cliente Anthropic inicializado")
            except Exception as e:
                print(f"❌ Erro ao inicializar Anthropic: {e}")
                return None
        return self.client
    
    def process_query(self, message, user_email="", document_context="", filename=""):
        start_time = time.time()
        
        print(f"🤖 Processando query de {user_email}")
        print(f"📝 Mensagem: {message[:100]}...")
        if document_context:
            print(f"📄 Documento: {filename} ({len(document_context)} chars)")
        
        # Verificar cache primeiro
        cache_key = hashlib.md5(f"{message}{document_context}".encode()).hexdigest()
        cached_response = cache.get(cache_key)
        
        if cached_response:
            processing_time = time.time() - start_time
            print(f"💾 Resposta do cache em {processing_time:.2f}s")
            return cached_response, processing_time
        
        client = self.get_client()
        
        if not client:
            response = self.get_fallback_response(message, document_context, filename)
            processing_time = time.time() - start_time
            return response, processing_time
        
        # PROMPT MELHORADO PARA ANÁLISE DE DOCUMENTOS
        prompt_parts = [self.ipt_context]
        
        if document_context:
            prompt_parts.append(f"""
DOCUMENTO ANEXADO PELO USUÁRIO:
Arquivo: {filename}
Conteúdo:
{document_context}

INSTRUÇÕES ESPECIAIS:
- Analise cuidadosamente o conteúdo do documento acima
- Use as informações do documento para responder à pergunta do usuário
- Se a pergunta não se relaciona ao documento, responda sobre o documento mesmo assim
- Seja específico e cite trechos relevantes quando apropriado
""")
        
        prompt_parts.append(f"""
PERGUNTA DO USUÁRIO: {message}

Responda de forma clara, objetiva e profissional. Se há um documento anexado, base sua resposta no conteúdo fornecido.""")
        
        prompt = "\n".join(prompt_parts)
        
        try:
            print("🔄 Enviando para API Anthropic...")
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = response.content[0].text
            
            # Cache da resposta
            cache.set(cache_key, result)
            
            processing_time = time.time() - start_time
            print(f"✅ Resposta gerada em {processing_time:.2f}s")
            
            return result, processing_time
            
        except Exception as e:
            print(f"❌ Erro na API Anthropic: {e}")
            response = self.get_fallback_response(message, document_context, filename)
            processing_time = time.time() - start_time
            return response, processing_time
    
    def get_fallback_response(self, message, document_context="", filename=""):
        message_lower = message.lower()
        
        if document_context:
            return f"""Recebi o documento '{filename}' com sucesso e posso analisá-lo!

📄 **Documento recebido:** {filename}
📊 **Tamanho do conteúdo:** {len(document_context)} caracteres

Baseado no conteúdo do documento, posso ajudá-lo com:
- Resumo do documento
- Análise de pontos específicos
- Resposta a perguntas sobre o conteúdo
- Identificação de informações relevantes

O que gostaria de saber sobre este documento? (Nota: Sistema funcionando em modo básico - API Anthropic indisponível)"""
        
        # Respostas fallback originais mantidas
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

# Decoradores
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'error': 'Não autenticado'}), 401
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'error': 'Não autenticado'}), 401
        if not session.get('is_admin'):
            return jsonify({'error': 'Acesso negado - apenas administradores'}), 403
        return f(*args, **kwargs)
    return decorated_function

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('authenticated'):
            email = session['user_email']
            allowed, message = rate_limiter.is_allowed(email)
            if not allowed:
                return jsonify({'error': message}), 429
        return f(*args, **kwargs)
    return decorated_function

def get_current_costs():
    try:
        conn = sqlite3.connect('lidia_security.db')
        cursor = conn.cursor()
        
        first_day = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        
        cursor.execute('''
            SELECT COUNT(*), SUM(cost) FROM conversation_logs 
            WHERE timestamp >= ?
        ''', (first_day,))
        
        result = cursor.fetchone()
        questions_this_month = result[0] if result[0] else 0
        actual_costs = result[1] if result[1] else 0
        
        fixed_costs = 100
        total_costs = fixed_costs + actual_costs
        budget_used = (total_costs / 500) * 100
        
        conn.close()
        
        return {
            'total': total_costs,
            'fixed': fixed_costs,
            'variable': actual_costs,
            'questions': questions_this_month,
            'budget_used': min(budget_used, 100)
        }
    except:
        return {
            'total': 100,
            'fixed': 100,
            'variable': 0,
            'questions': 0,
            'budget_used': 20
        }

# Rotas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin_panel():
    """Painel administrativo"""
    if not session.get('authenticated') or not session.get('is_admin'):
        return redirect(url_for('index'))
    
    return render_template('admin.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip()
    
    print(f"🔐 Tentativa de login: {email}")
    
    is_valid, message = security.validate_ipt_email(email)
    
    if is_valid:
        is_admin = security.is_admin(email)
        
        session['authenticated'] = True
        session['user_email'] = email
        session['is_admin'] = is_admin
        session['session_id'] = str(uuid.uuid4())
        
        print(f"✅ Login sucesso - Email: {email}, Admin: {is_admin}")
        
        return jsonify({
            'success': True,
            'message': 'Login realizado com sucesso',
            'is_admin': is_admin
        })
    else:
        print(f"❌ Login falhou: {message}")
        return jsonify({
            'success': False,
            'message': message
        }), 400

@app.route('/api/chat', methods=['POST'])
@require_auth
@rate_limit
def chat():
    data = request.get_json()
    message = data.get('message', '').strip()
    chat_id = data.get('chat_id', '')
    
    if not message:
        return jsonify({'error': 'Mensagem vazia'}), 400
    
    # Sanitizar entrada
    message = bleach.clean(message, tags=[], strip=True)
    
    if not chat_id:
        chat_id = 'chat_' + str(uuid.uuid4())
    
    try:
        # Verificar se há documento no contexto
        document_context, filename = security.get_document_context(chat_id)
        
        response, processing_time = assistant.process_query(
            message, 
            session['user_email'],
            document_context or "",
            filename or ""
        )
        
        # Calcular custo estimado
        estimated_cost = len(message + response) * 0.000001
        
        security.log_conversation(
            session['user_email'], 
            chat_id,
            message, 
            response,
            cost=estimated_cost,
            document_context=document_context or "",
            processing_time=processing_time
        )
        
        return jsonify({
            'response': response,
            'chat_id': chat_id,
            'timestamp': datetime.now().isoformat(),
            'processing_time': round(processing_time, 2)
        })
        
    except Exception as e:
        print(f"❌ Erro no chat: {e}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/chats')
@require_auth
def get_chats():
    chats = security.get_user_chats(session['user_email'])
    return jsonify(chats)

@app.route('/api/chats/<chat_id>')
@require_auth
def get_chat(chat_id):
    messages = security.get_chat_messages(session['user_email'], chat_id)
    return jsonify(messages)

@app.route('/api/upload', methods=['POST'])
@require_auth
@rate_limit
def upload_file():
    print("📤 Upload iniciado")
    
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    chat_id = request.form.get('chat_id', 'chat_' + str(uuid.uuid4()))
    
    try:
        # Extrair texto do arquivo
        print(f"🔍 Extraindo texto de: {file.filename}")
        extracted_text = DocumentProcessor.extract_text_from_file(file)
        
        # Verificar se houve erro na extração
        if extracted_text.startswith('Erro'):
            print(f"❌ Erro na extração: {extracted_text}")
            return jsonify({'error': extracted_text}), 400
        
        # Ler conteúdo do arquivo para hash
        file.seek(0)
        file_content = file.read()
        
        # Armazenar documento
        success = security.store_document(
            session['user_email'],
            chat_id,
            secure_filename(file.filename),
            file_content,
            extracted_text
        )
        
        if success:
            print(f"✅ Upload concluído: {file.filename}")
            return jsonify({
                'success': True,
                'filename': file.filename,
                'chat_id': chat_id,
                'message': f'✅ Documento "{file.filename}" processado com sucesso!\n\n📄 **Conteúdo extraído:** {len(extracted_text)} caracteres\n\nAgora você pode fazer perguntas sobre o documento. Exemplo:\n- "Faça um resumo deste documento"\n- "Quais são os pontos principais?"\n- "O que este documento diz sobre...?"',
                'extracted_length': len(extracted_text)
            })
        else:
            return jsonify({'error': 'Erro ao armazenar documento no banco de dados'}), 500
            
    except Exception as e:
        print(f"❌ Erro no upload: {e}")
        return jsonify({'error': f'Erro ao processar arquivo: {str(e)}'}), 500

# Rotas administrativas (TODAS AS FUNCIONALIDADES ORIGINAIS)
@app.route('/api/costs')
@require_admin
def costs():
    costs_data = get_current_costs()
    return jsonify(costs_data)

@app.route('/api/admin/stats')
@require_admin
def admin_stats():
    """Estatísticas detalhadas"""
    stats = security.get_system_stats()
    costs = get_current_costs()
    
    return jsonify({
        'stats': stats,
        'costs': costs,
        'generated_at': datetime.now().isoformat()
    })

@app.route('/api/admin/users')
@require_admin
def admin_users():
    """Lista todos os usuários"""
    try:
        conn = sqlite3.connect('lidia_security.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                email,
                COUNT(DISTINCT chat_id) as total_chats,
                COUNT(*) as total_messages,
                SUM(cost) as total_cost,
                MAX(timestamp) as last_activity,
                MIN(timestamp) as first_activity
            FROM conversation_logs 
            GROUP BY email
            ORDER BY total_messages DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'email': row[0],
                'total_chats': row[1],
                'total_messages': row[2],
                'total_cost': row[3] if row[3] else 0,
                'last_activity': row[4],
                'first_activity': row[5]
            })
        
        conn.close()
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/admins')
@require_admin
def admin_list():
    """Lista administradores"""
    admins = security.get_all_admins()
    return jsonify(admins)

@app.route('/api/admin/admins', methods=['POST'])
@require_admin
def add_admin():
    """Adiciona administrador"""
    data = request.get_json()
    new_admin_email = data.get('email', '').strip()
    permissions = data.get('permissions', 'full')
    
    # Validar email
    is_valid, message = security.validate_ipt_email(new_admin_email)
    if not is_valid:
        return jsonify({'error': message}), 400
    
    # Adicionar admin
    success = security.add_admin(new_admin_email, session['user_email'], permissions)
    
    if success:
        return jsonify({'message': f'Administrador {new_admin_email} adicionado com sucesso'})
    else:
        return jsonify({'error': 'Erro ao adicionar administrador'}), 500

@app.route('/api/admin/documents')
@require_admin
def admin_documents():
    """Lista documentos"""
    try:
        conn = sqlite3.connect('lidia_security.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                email, filename, file_size, upload_time, 
                chat_id, file_hash, processing_status
            FROM file_uploads 
            ORDER BY upload_time DESC 
            LIMIT 200
        ''')
        
        documents = []
        for row in cursor.fetchall():
            documents.append({
                'email': row[0],
                'filename': row[1],
                'file_size': row[2],
                'upload_time': row[3],
                'chat_id': row[4],
                'file_hash': row[5],
                'processing_status': row[6]
            })
        
        conn.close()
        return jsonify(documents)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/conversations')
@require_admin
def admin_conversations():
    """Lista conversas"""
    try:
        conn = sqlite3.connect('lidia_security.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                email, chat_id, question, response, timestamp, 
                cost, processing_time, ip_address
            FROM conversation_logs 
            ORDER BY timestamp DESC 
            LIMIT 100
        ''')
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                'email': row[0],
                'chat_id': row[1],
                'question': row[2][:100] + "..." if len(row[2]) > 100 else row[2],
                'response': row[3][:100] + "..." if len(row[3]) > 100 else row[3],
                'timestamp': row[4],
                'cost': row[5],
                'processing_time': row[6],
                'ip_address': row[7]
            })
        
        conn.close()
        return jsonify(conversations)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/user')
@require_auth
def user_info():
    user_data = {
        'email': session['user_email'],
        'is_admin': session.get('is_admin', False),
        'authenticated': True
    }
    
    return jsonify(user_data)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'version': '2.0-railway-fixed',
        'environment': 'railway' if IS_RAILWAY else 'local'
    })

@app.route('/migration-status')
def migration_status():
    """Status da migração"""
    try:
        conn = sqlite3.connect('lidia_security.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        stats = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'migration_status': 'success',
            'tables': tables,
            'record_counts': stats,
            'timestamp': datetime.now().isoformat(),
            'admin_system': 'active',
            'document_processing': 'enhanced'
        })
        
    except Exception as e:
        return jsonify({
            'migration_status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    print("🚀 INICIANDO LIDIA v2.0 - VERSÃO CORRIGIDA")
    print(f"🌍 Ambiente: {'Railway' if IS_RAILWAY else 'Local'}")
    print(f"📊 Porta: {PORT}")
    print(f"🔑 Admins: {ADMIN_USERS}")
    print(f"🤖 Anthropic API: {'✅ Configurada' if ANTHROPIC_API_KEY else '❌ Não configurada'}")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
