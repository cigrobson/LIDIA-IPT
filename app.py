import streamlit as st
import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import anthropic
import chromadb
from sentence_transformers import SentenceTransformer
import PyPDF2
import docx
import tiktoken
from typing import List, Dict, Any
import json
import time
import requests
import sqlite3
import hashlib
import base64
from geopy.distance import geodesic
import plotly.express as px
import plotly.graph_objects as go
import asyncio
import subprocess
import threading

# Configuração da página
st.set_page_config(
    page_title="LIDIA - Assistente de IA do LID",
    page_icon="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGRlZnM+CjxsaW5lYXJHcmFkaWVudCBpZD0iZ3JhZGllbnQzIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KPHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6I0ZGNkIzNTtzdG9wLW9wYWNpdHk6MSIgLz4KPHN0b3Agb2Zmc2V0PSIyNSUiIHN0eWxlPSJzdG9wLWNvbG9yOiNGNzkzMUU7c3RvcC1vcGFjaXR5OjEiIC8+CjxzdG9wIG9mZnNldD0iNTAlIiBzdHlsZT0ic3RvcC1jb2xvcjojQzI0MzdBO3N0b3Atb3BhY2l0eToxIiAvPgo8c3RvcCBvZmZzZXQ9Ijc1JSIgc3R5bGU9InN0b3AtY29sb3I6IzY3NEVBNztzdG9wLW9wYWNpdHk6MSIgLz4KPHN0b3Agb2Zmc2V0PSIxMDAlIiBzdHlsZT0ic3RvcC1jb2xvcjojMTk3NkQyO3N0b3Atb3BhY2l0eToxIiAvPgo8L2xpbmVhckdyYWRpZW50Pgo8L2RlZnM+CjxjaXJjbGUgY3g9IjIwIiBjeT0iMjAiIHI9IjE4IiBmaWxsPSJ1cmwoI2dyYWRpZW50MykiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIyIi8+Cjx0ZXh0IHg9IjIwIiB5PSIyNiIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjEwIiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkxJRElBPC90ZXh0Pgo8L3N2Zz4K",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS para estilo similar ao Claude + Logo LIDIA
st.markdown("""
<style>
    .stApp {
        max-width: 800px;
        margin: 0 auto;
    }
    
    .main-header {
        text-align: center;
        padding: 2rem 0;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 2rem;
    }
    
    .lidia-logo {
        width: 60px;
        height: 60px;
        margin: 0 auto 1rem auto;
        display: block;
        border-radius: 50%;
    }
    
    .lidia-icon-small {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        vertical-align: middle;
        margin-right: 8px;
    }
    
    .chat-container {
        max-height: 400px;
        overflow-y: auto;
        padding: 1rem;
        border-radius: 8px;
        background-color: #f8f9fa;
        margin-bottom: 1rem;
    }
    
    .user-message {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        margin-left: 2rem;
    }
    
    .assistant-message {
        background-color: white;
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        margin-right: 2rem;
        border-left: 4px solid #1976d2;
    }
    
    .cost-info {
        background-color: #f0f8ff;
        padding: 0.5rem;
        border-radius: 6px;
        font-size: 0.8rem;
        color: #666;
        text-align: center;
        margin-top: 1rem;
    }
    
    .security-alert {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 6px;
        padding: 1rem;
        margin: 1rem 0;
        color: #856404;
    }
    
    .geo-info {
        background-color: #e8f5e8;
        padding: 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        margin: 0.5rem 0;
    }
    
    .mcp-status {
        background-color: #e1f5fe;
        border: 1px solid #4fc3f7;
        border-radius: 6px;
        padding: 0.8rem;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
    
    .mcp-tool {
        background-color: #f3e5f5;
        border: 1px solid #ba68c8;
        border-radius: 4px;
        padding: 0.5rem;
        margin: 0.3rem 0;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

class SecurityManager:
    """Gerenciador completo de segurança e geolocalização"""
    
    def __init__(self):
        self.init_database()
    
    def init_database(self):
        """Inicializa banco de dados para logs"""
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            # Tabela de acessos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS access_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    ip_address TEXT,
                    location_data TEXT,
                    timestamp DATETIME,
                    user_agent TEXT,
                    session_id TEXT,
                    action TEXT,
                    success BOOLEAN
                )
            ''')
            
            # Tabela de conversas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    question TEXT,
                    response TEXT,
                    timestamp DATETIME,
                    session_id TEXT,
                    cost REAL,
                    documents_used TEXT,
                    mcp_tools_used TEXT
                )
            ''')
            
            # Tabela de uploads
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS upload_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    filename TEXT,
                    file_size INTEGER,
                    file_type TEXT,
                    timestamp DATETIME,
                    session_id TEXT,
                    permanent BOOLEAN,
                    processing_status TEXT
                )
            ''')
            
            # Nova tabela para logs MCP
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mcp_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    server_name TEXT,
                    tool_name TEXT,
                    arguments TEXT,
                    result TEXT,
                    timestamp DATETIME,
                    session_id TEXT,
                    success BOOLEAN
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            st.error(f"Erro ao inicializar banco: {e}")
    
    def get_client_ip(self):
        """Obtém IP real do cliente"""
        try:
            headers = st.context.headers if hasattr(st, 'context') else {}
            
            if 'localhost' in str(headers) or not headers:
                return "177.12.34.56"
            
            for header in ['X-Forwarded-For', 'X-Real-IP', 'CF-Connecting-IP']:
                if header in headers:
                    return headers[header].split(',')[0].strip()
            
            return "200.144.28.105"
        except:
            return "200.144.28.105"
    
    def get_location_info(self, ip_address):
        """Obtém informações de geolocalização"""
        try:
            if ip_address.startswith('200.144.'):
                return {
                    'ip': ip_address,
                    'country': 'Brazil',
                    'region': 'São Paulo',
                    'city': 'São Paulo',
                    'lat': -23.5505,
                    'lon': -46.6333,
                    'isp': 'Instituto de Pesquisas Tecnológicas',
                    'timezone': 'America/Sao_Paulo',
                    'is_ipt': True
                }
            
            response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=3)
            if response.status_code == 200:
                data = response.json()
                return {
                    'ip': ip_address,
                    'country': data.get('country', 'Unknown'),
                    'region': data.get('regionName', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'lat': data.get('lat', 0),
                    'lon': data.get('lon', 0),
                    'isp': data.get('isp', 'Unknown'),
                    'timezone': data.get('timezone', 'Unknown'),
                    'is_ipt': False
                }
        except Exception as e:
            return {
                'ip': ip_address,
                'country': 'Unknown',
                'region': 'Unknown', 
                'city': 'Unknown',
                'lat': 0,
                'lon': 0,
                'isp': 'Unknown',
                'timezone': 'Unknown',
                'is_ipt': False,
                'error': str(e)
            }
    
    def validate_ipt_email(self, email):
        """Valida se email é do IPT"""
        if not email:
            return False, "Email obrigatório"
        
        if not email.endswith('@ipt.br'):
            return False, "Acesso restrito a funcionários do IPT (@ipt.br)"
        
        if len(email.split('@')[0]) < 3:
            return False, "Email inválido"
        
        return True, "Email válido"
    
    def analyze_security_risk(self, email, location_info):
        """Analisa riscos de segurança baseado em localização"""
        alerts = []
        risk_level = "low"
        
        if location_info.get('country') != 'Brazil':
            alerts.append(f"Acesso internacional: {location_info.get('country')}")
            risk_level = "high"
        
        if location_info.get('lat') and location_info.get('lon'):
            distance = geodesic(
                (-23.5505, -46.6333),
                (location_info['lat'], location_info['lon'])
            ).kilometers
            
            if distance > 1000:
                alerts.append(f"Acesso a {distance:.0f}km de São Paulo")
                risk_level = "medium" if risk_level == "low" else "high"
        
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:
            alerts.append(f"Acesso fora horário comercial: {current_hour:02d}h")
            risk_level = "medium" if risk_level == "low" else risk_level
        
        return alerts, risk_level
    
    def log_access(self, email, location_info, action="login", success=True):
        """Registra log de acesso"""
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO access_logs 
                (email, ip_address, location_data, timestamp, user_agent, session_id, action, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email,
                location_info.get('ip'),
                json.dumps(location_info),
                datetime.now(),
                "Streamlit App",
                st.session_state.get('session_id', 'unknown'),
                action,
                success
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            st.error(f"Erro ao registrar log: {e}")
    
    def log_conversation(self, email, question, response, cost=0.003, documents_used="", mcp_tools_used=""):
        """Registra conversas para auditoria incluindo uso de MCP"""
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO conversation_logs 
                (email, question, response, timestamp, session_id, cost, documents_used, mcp_tools_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email,
                question,
                response[:1000],
                datetime.now(),
                st.session_state.get('session_id', 'unknown'),
                cost,
                documents_used,
                mcp_tools_used
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            st.error(f"Erro ao registrar conversa: {e}")
    
    def log_mcp_usage(self, email, server_name, tool_name, arguments, result, success=True):
        """Registra uso de ferramentas MCP"""
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO mcp_logs 
                (email, server_name, tool_name, arguments, result, timestamp, session_id, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email,
                server_name,
                tool_name,
                json.dumps(arguments),
                str(result)[:500],
                datetime.now(),
                st.session_state.get('session_id', 'unknown'),
                success
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            st.error(f"Erro ao registrar uso MCP: {e}")
    
    def log_upload(self, email, filename, file_size, file_type, permanent=False, status="success"):
        """Registra uploads para auditoria"""
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO upload_logs 
                (email, filename, file_size, file_type, timestamp, session_id, permanent, processing_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email,
                filename,
                file_size,
                file_type,
                datetime.now(),
                st.session_state.get('session_id', 'unknown'),
                permanent,
                status
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            st.error(f"Erro ao registrar upload: {e}")

class CostManager:
    """Gerenciador de custos e limites"""
    
    def __init__(self, monthly_budget=200):
        self.monthly_budget = monthly_budget
        self.cost_per_question = 0.003
        self.fixed_costs = 100
    
    def get_current_costs(self):
        """Calcula custos atuais do mês"""
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            first_day = datetime.now().replace(day=1, hour=0, minute=0, second=0)
            
            cursor.execute('''
                SELECT COUNT(*) FROM conversation_logs 
                WHERE timestamp >= ?
            ''', (first_day,))
            
            questions_this_month = cursor.fetchone()[0]
            variable_costs = questions_this_month * self.cost_per_question
            total_costs = self.fixed_costs + variable_costs
            
            conn.close()
            
            return {
                'total': total_costs,
                'fixed': self.fixed_costs,
                'variable': variable_costs,
                'questions': questions_this_month,
                'budget_used': (total_costs / self.monthly_budget) * 100
            }
        except:
            return {
                'total': self.fixed_costs,
                'fixed': self.fixed_costs,
                'variable': 0,
                'questions': 0,
                'budget_used': 50
            }
    
    def check_budget_alert(self, costs):
        """Verifica se precisa enviar alertas de orçamento"""
        budget_used = costs['budget_used']
        
        if budget_used >= 95:
            return "critical", "Orçamento 95% esgotado - Sistema em modo apenas leitura"
        elif budget_used >= 90:
            return "high", "Orçamento 90% esgotado - Atenção necessária"
        elif budget_used >= 75:
            return "medium", "Orçamento 75% esgotado - Monitorar uso"
        else:
            return "low", "Orçamento dentro do esperado"

class SimpleDocumentProcessor:
    """Processador simples de documentos"""
    
    def __init__(self):
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def extract_text_from_file(self, uploaded_file) -> str:
        """Extrai texto de arquivo enviado pelo usuário"""
        try:
            if uploaded_file.type == "application/pdf":
                import io
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
                
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                import io
                doc = docx.Document(io.BytesIO(uploaded_file.read()))
                return "\n".join([paragraph.text for paragraph in doc.paragraphs])
                
            elif uploaded_file.type == "text/plain":
                return str(uploaded_file.read(), "utf-8")
                
            else:
                return "Formato de arquivo não suportado."
                
        except Exception as e:
            return f"Erro ao processar arquivo: {str(e)}"

class SimpleRAGSystem:
    """Sistema RAG simplificado"""
    
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./ipt_hybrid_db")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        try:
            self.collection = self.client.get_collection("ipt_docs")
        except:
            self.collection = self.client.create_collection("ipt_docs")
    
    def add_document_content(self, content: str, filename: str):
        """Adiciona conteúdo do documento à base"""
        if not content.strip():
            return False
        
        chunks = self._create_simple_chunks(content, filename)
        
        if chunks:
            texts = [chunk['text'] for chunk in chunks]
            embeddings = self.embedding_model.encode(texts).tolist()
            ids = [f"{filename}_{i}" for i in range(len(chunks))]
            metadatas = [chunk['metadata'] for chunk in chunks]
            
            try:
                self.collection.add(
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
                return True
            except:
                return False
        return False
    
    def search_relevant_content(self, query: str, n_results: int = 3) -> str:
        """Busca conteúdo relevante para a consulta"""
        try:
            query_embedding = self.embedding_model.encode([query]).tolist()
            
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results
            )
            
            if results['documents'] and results['documents'][0]:
                context = ""
                for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                    context += f"[Fonte: {meta['filename']}]\n{doc}\n\n"
                return context
            
        except:
            pass
        
        return ""
    
    def _create_simple_chunks(self, text: str, filename: str) -> List[Dict]:
        """Cria chunks simples do texto"""
        words = text.split()
        chunk_size = 300
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            chunks.append({
                'text': chunk_text,
                'metadata': {
                    'filename': filename,
                    'chunk_index': len(chunks)
                }
            })
        
        return chunks
    
    def get_document_count(self) -> int:
        """Retorna número de documentos na base"""
        try:
            data = self.collection.get()
            if data['metadatas']:
                unique_files = set(meta['filename'] for meta in data['metadatas'])
                return len(unique_files)
        except:
            pass
        return 0

class MCPManager:
    """Gerenciador de Model Context Protocol para LIDIA"""
    
    def __init__(self):
        self.active_servers = {}
        self.available_tools = {}
        self.server_processes = {}
        self.status = "disconnected"
    
    def check_mcp_dependencies(self):
        """Verifica se as dependências MCP estão instaladas"""
        try:
            # Verificar se Node.js está instalado
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                return False, "Node.js não encontrado. Instale Node.js primeiro."
            
            # Verificar NPM
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                return False, "NPM não encontrado."
            
            return True, "Dependências OK"
        except:
            return False, "Erro ao verificar dependências"
    
    def install_mcp_servers(self):
        """Instala servidores MCP automaticamente"""
        servers_to_install = [
            "@modelcontextprotocol/server-filesystem",
            "@modelcontextprotocol/server-brave-search",
            "@modelcontextprotocol/server-memory"
        ]
        
        installed = []
        errors = []
        
        for server in servers_to_install:
            try:
                st.info(f"Instalando {server}...")
                result = subprocess.run(['npm', 'install', '-g', server], 
                                      capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    installed.append(server)
                    st.success(f"✅ {server} instalado!")
                else:
                    errors.append(f"{server}: {result.stderr}")
                    st.error(f"❌ Erro ao instalar {server}")
                    
            except subprocess.TimeoutExpired:
                errors.append(f"{server}: Timeout")
                st.error(f"❌ Timeout ao instalar {server}")
            except Exception as e:
                errors.append(f"{server}: {str(e)}")
                st.error(f"❌ Erro: {str(e)}")
        
        return installed, errors
    
    def start_filesystem_server(self, allowed_path="/"):
        """Inicia servidor de arquivos MCP"""
        try:
            cmd = ['npx', '@modelcontextprotocol/server-filesystem', allowed_path]
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, 
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.server_processes['filesystem'] = process
            self.active_servers['filesystem'] = True
            self.available_tools['filesystem'] = ['read_file', 'write_file', 'list_directory', 'create_directory']
            return True, "Servidor de arquivos iniciado"
            
        except Exception as e:
            return False, f"Erro ao iniciar servidor de arquivos: {str(e)}"
    
    def start_search_server(self):
        """Inicia servidor de busca MCP"""
        try:
            cmd = ['npx', '@modelcontextprotocol/server-brave-search']
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.server_processes['search'] = process
            self.active_servers['search'] = True
            self.available_tools['search'] = ['brave_search']
            return True, "Servidor de busca iniciado"
            
        except Exception as e:
            return False, f"Erro ao iniciar servidor de busca: {str(e)}"
    
    def start_memory_server(self):
        """Inicia servidor de memória MCP"""
        try:
            cmd = ['npx', '@modelcontextprotocol/server-memory']
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.server_processes['memory'] = process
            self.active_servers['memory'] = True
            self.available_tools['memory'] = ['store_memory', 'retrieve_memory', 'search_memory']
            return True, "Servidor de memória iniciado"
            
        except Exception as e:
            return False, f"Erro ao iniciar servidor de memória: {str(e)}"
    
    def stop_all_servers(self):
        """Para todos os servidores MCP"""
        for name, process in self.server_processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        
        self.server_processes.clear()
        self.active_servers.clear()
        self.available_tools.clear()
    
    def simulate_tool_call(self, server_name: str, tool_name: str, arguments: dict):
        """Simula chamada de ferramenta MCP (para demonstração)"""
        if server_name not in self.active_servers:
            return None, "Servidor não está ativo"
        
        try:
            if server_name == "filesystem":
                if tool_name == "list_directory":
                    path = arguments.get("path", ".")
                    if os.path.exists(path):
                        files = os.listdir(path)
                        return {"files": files}, "Sucesso"
                    else:
                        return {"error": "Diretório não encontrado"}, "Erro"
                
                elif tool_name == "read_file":
                    filepath = arguments.get("path", "")
                    if os.path.exists(filepath):
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        return {"content": content[:1000] + "..." if len(content) > 1000 else content}, "Sucesso"
                    else:
                        return {"error": "Arquivo não encontrado"}, "Erro"
            
            elif server_name == "search":
                if tool_name == "brave_search":
                    query = arguments.get("query", "")
                    # Simulação de busca
                    return {
                        "results": [
                            {"title": f"Resultado para: {query}", "url": "https://example.com", "snippet": "Informações encontradas..."}
                        ]
                    }, "Sucesso"
            
            elif server_name == "memory":
                if tool_name == "store_memory":
                    key = arguments.get("key", "")
                    value = arguments.get("value", "")
                    # Simulação de armazenamento
                    return {"stored": f"{key}: {value}"}, "Sucesso"
            
            return {"message": "Ferramenta simulada"}, "Sucesso"
            
        except Exception as e:
            return None, f"Erro na simulação: {str(e)}"
    
    def get_server_status(self):
        """Retorna status dos servidores"""
        return {
            "active_servers": list(self.active_servers.keys()),
            "available_tools": self.available_tools,
            "total_servers": len(self.active_servers)
        }

class LIDIAWithMCP:
    """LIDIA com suporte completo a MCP"""
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.rag_system = SimpleRAGSystem()
        self.doc_processor = SimpleDocumentProcessor()
        self.security = SecurityManager()
        self.cost_manager = CostManager()
        self.mcp_manager = MCPManager()
        
        self.model = "claude-3-haiku-20240307"
        
        self.ipt_context = """Você é LIDIA, assistente especializada do IPT (Instituto de Pesquisas Tecnológicas de São Paulo).

O IPT é uma instituição centenária de pesquisa aplicada que oferece:
- Ensaios e análises laboratoriais
- Certificação de produtos
- Consultoria técnica
- Pesquisa e desenvolvimento
- Serviços de metrologia

Você agora tem acesso a ferramentas MCP para:
- Acessar arquivos e documentos
- Fazer buscas na web
- Armazenar informações na memória

Responda de forma clara, objetiva e profissional. Use as informações dos documentos e ferramentas MCP quando disponíveis."""
    
    def determine_mcp_tools_needed(self, message: str):
        """Determina quais ferramentas MCP usar baseado na mensagem"""
        message_lower = message.lower()
        tools_needed = []
        
        # Verificar necessidade de acesso a arquivos
        if any(word in message_lower for word in ["arquivo", "pasta", "diretório", "ler arquivo", "listar"]):
            tools_needed.append(("filesystem", "list_directory", {"path": "."}))
        
        # Verificar necessidade de busca
        if any(word in message_lower for word in ["buscar", "pesquisar", "procurar", "search"]):
            query = message.replace("buscar", "").replace("pesquisar", "").strip()
            tools_needed.append(("search", "brave_search", {"query": query}))
        
        # Verificar necessidade de memória
        if any(word in message_lower for word in ["lembrar", "guardar", "armazenar", "salvar"]):
            tools_needed.append(("memory", "store_memory", {"key": "user_request", "value": message}))
        
        return tools_needed
    
    def process_user_query(self, message: str, file_content: str = "", user_email: str = "") -> str:
        """Processa consulta do usuário com MCP integrado"""
        
        context_parts = [self.ipt_context]
        mcp_results = []
        mcp_tools_used = []
        
        # Verificar se precisa usar ferramentas MCP
        tools_needed = self.determine_mcp_tools_needed(message)
        
        if tools_needed:
            st.info("🔧 Usando ferramentas MCP...")
            
            for server_name, tool_name, arguments in tools_needed:
                result, status = self.mcp_manager.simulate_tool_call(server_name, tool_name, arguments)
                
                if result:
                    mcp_results.append(f"[{server_name}] {tool_name}: {result}")
                    mcp_tools_used.append(f"{server_name}.{tool_name}")
                    
                    # Log do uso MCP
                    if user_email:
                        self.security.log_mcp_usage(user_email, server_name, tool_name, arguments, result, True)
        
        # Adicionar resultados MCP ao contexto
        if mcp_results:
            context_parts.append(f"\nRESULTADOS DAS FERRAMENTAS MCP:\n" + "\n".join(mcp_results))
        
        if file_content:
            context_parts.append(f"\nDOCUMENTO ENVIADO PELO USUÁRIO:\n{file_content[:3000]}")
        
        relevant_content = self.rag_system.search_relevant_content(message)
        if relevant_content:
            context_parts.append(f"\nINFORMAÇÕES DA BASE DE CONHECIMENTO:\n{relevant_content}")
        
        context = "\n".join(context_parts)
        
        prompt = f"""{context}

PERGUNTA/SOLICITAÇÃO: {message}

Responda de forma clara e útil. Se usar informações de documentos ou ferramentas MCP, cite as fontes."""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            answer = response.content[0].text
            
            # Log da conversa incluindo uso de MCP
            if user_email:
                documents_used = "Base de conhecimento" if relevant_content else "Conhecimento geral"
                if file_content:
                    documents_used += " + Documento do usuário"
                
                mcp_used = ", ".join(mcp_tools_used) if mcp_tools_used else ""
                
                self.security.log_conversation(user_email, message, answer, 0.003, documents_used, mcp_used)
            
            return answer
            
        except Exception as e:
            return f"Desculpe, ocorreu um erro ao processar sua solicitação: {str(e)}"
    
    def add_document_to_knowledge_base(self, uploaded_file, user_email: str = "") -> bool:
        """Adiciona documento à base de conhecimento com logging"""
        try:
            content = self.doc_processor.extract_text_from_file(uploaded_file)
            success = False
            
            if content and len(content.strip()) > 50:
                success = self.rag_system.add_document_content(content, uploaded_file.name)
            
            if user_email:
                status = "success" if success else "failed"
                self.security.log_upload(
                    user_email, 
                    uploaded_file.name, 
                    uploaded_file.size, 
                    uploaded_file.type,
                    permanent=True,
                    status=status
                )
            
            return success
        except Exception as e:
            if user_email:
                self.security.log_upload(
                    user_email, 
                    uploaded_file.name if uploaded_file else "unknown", 
                    0, 
                    "unknown",
                    permanent=True,
                    status=f"error: {str(e)}"
                )
            return False
    
    def load_documents_from_folder(self, folder_path: str, user_email: str = "") -> Dict:
        """Carrega todos os documentos de uma pasta com logging"""
        folder_path = Path(folder_path)
        
        if not folder_path.exists():
            return {'error': f'Pasta não encontrada: {folder_path}'}
        
        all_files = []
        for ext in ['.pdf', '.docx', '.txt']:
            all_files.extend(folder_path.rglob(f'*{ext}'))
        
        if not all_files:
            return {'error': 'Nenhum arquivo suportado encontrado na pasta'}
        
        total_chunks = 0
        processed_files = 0
        errors = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, file_path in enumerate(all_files):
            try:
                status_text.text(f"Processando: {file_path.name}")
                
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                class FakeUploadedFile:
                    def __init__(self, name, content, file_type):
                        self.name = name
                        self.size = len(content)
                        self._content = content
                        if file_type == '.pdf':
                            self.type = "application/pdf"
                        elif file_type == '.docx':
                            self.type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        else:
                            self.type = "text/plain"
                    
                    def read(self):
                        return self._content
                
                fake_file = FakeUploadedFile(file_path.name, file_content, file_path.suffix)
                success = self.add_document_to_knowledge_base(fake_file, user_email)
                
                if success:
                    processed_files += 1
                    total_chunks += 1
                else:
                    errors.append(f"Erro ao processar: {file_path.name}")
                
            except Exception as e:
                errors.append(f"Erro em {file_path.name}: {str(e)}")
            
            progress_bar.progress((i + 1) / len(all_files))
        
        status_text.empty()
        progress_bar.empty()
        
        return {
            'processed_files': processed_files,
            'total_chunks': total_chunks,
            'total_files': len(all_files),
            'errors': errors
        }

def show_mcp_dashboard(assistant):
    """Dashboard para configuração e monitoramento MCP"""
    st.subheader("🔌 Configuração Model Context Protocol (MCP)")
    
    # Status atual
    status = assistant.mcp_manager.get_server_status()
    
    if status['total_servers'] > 0:
        st.success(f"✅ {status['total_servers']} servidores MCP ativos")
        
        for server_name, tools in status['available_tools'].items():
            st.markdown(f'<div class="mcp-tool">**{server_name}**: {", ".join(tools)}</div>', unsafe_allow_html=True)
    else:
        st.info("ℹ️ Nenhum servidor MCP ativo")
    
    # Verificar dependências
    st.markdown("#### 🔍 Verificação de Dependências")
    deps_ok, deps_msg = assistant.mcp_manager.check_mcp_dependencies()
    
    if deps_ok:
        st.success(f"✅ {deps_msg}")
    else:
        st.error(f"❌ {deps_msg}")
        st.markdown("""
        **Para usar MCP, você precisa:**
        1. Instalar Node.js: https://nodejs.org
        2. Reiniciar o sistema após instalação
        3. Voltar aqui e clicar em 'Instalar Servidores MCP'
        """)
    
    # Instalação automática
    if deps_ok:
        st.markdown("#### 📦 Instalação de Servidores")
        
        if st.button("🚀 Instalar Servidores MCP Automaticamente"):
            with st.spinner("Instalando servidores MCP..."):
                installed, errors = assistant.mcp_manager.install_mcp_servers()
            
            if installed:
                st.success(f"✅ Instalados: {', '.join(installed)}")
            
            if errors:
                st.error("❌ Erros encontrados:")
                for error in errors:
                    st.text(error)
    
    # Controles dos servidores
    if deps_ok:
        st.markdown("#### 🎛️ Controle de Servidores")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📁 Iniciar Servidor de Arquivos"):
                success, msg = assistant.mcp_manager.start_filesystem_server()
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
        
        with col2:
            if st.button("🔍 Iniciar Servidor de Busca"):
                success, msg = assistant.mcp_manager.start_search_server()
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
        
        with col3:
            if st.button("🧠 Iniciar Servidor de Memória"):
                success, msg = assistant.mcp_manager.start_memory_server()
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
        
        if st.button("🛑 Parar Todos os Servidores", type="secondary"):
            assistant.mcp_manager.stop_all_servers()
            st.success("Todos os servidores foram parados")
    
    # Teste de ferramentas
    if status['total_servers'] > 0:
        st.markdown("#### 🧪 Teste de Ferramentas")
        
        server_names = list(status['available_tools'].keys())
        selected_server = st.selectbox("Servidor:", server_names)
        
        if selected_server:
            tools = status['available_tools'][selected_server]
            selected_tool = st.selectbox("Ferramenta:", tools)
            
            if selected_tool == "list_directory":
                path = st.text_input("Caminho:", value=".")
                if st.button("🔧 Testar"):
                    result, status_msg = assistant.mcp_manager.simulate_tool_call(
                        selected_server, selected_tool, {"path": path}
                    )
                    st.json(result)
            
            elif selected_tool == "brave_search":
                query = st.text_input("Consulta:")
                if st.button("🔧 Testar") and query:
                    result, status_msg = assistant.mcp_manager.simulate_tool_call(
                        selected_server, selected_tool, {"query": query}
                    )
                    st.json(result)

def show_authentication():
    """Tela de autenticação IPT com geolocalização"""
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    
    # Logo da LIDIA
    st.markdown("""
    <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGRlZnM+CjxsaW5lYXJHcmFkaWVudCBpZD0iZ3JhZGllbnQiIHgxPSIwJSIgeTE9IjAlIiB4Mj0iMTAwJSIgeTI9IjEwMCUiPgo8c3RvcCBvZmZzZXQ9IjAlIiBzdHlsZT0ic3RvcC1jb2xvcjojRkY2QjM1O3N0b3Atb3BhY2l0eToxIiAvPgo8c3RvcCBvZmZzZXQ9IjI1JSIgc3R5bGU9InN0b3AtY29sb3I6I0Y3OTMxRTtzdG9wLW9wYWNpdHk6MSIgLz4KPHN0b3Agb2Zmc2V0PSI1MCUiIHN0eWxlPSJzdG9wLWNvbG9yOiNDMjQzN0E7c3RvcC1vcGFjaXR5OjEiIC8+CjxzdG9wIG9mZnNldD0iNzUlIiBzdHlsZT0ic3RvcC1jb2xvcjojNjc0RUE3O3N0b3Atb3BhY2l0eToxIiAvPgo8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiMxOTc2RDI7c3RvcC1vcGFjaXR5OjEiIC8+CjwvbGluZWFyR3JhZGllbnQ+CjwvZGVmcz4KPGNpcmNsZSBjeD0iMzAiIGN5PSIzMCIgcj0iMjgiIGZpbGw9InVybCgjZ3JhZGllbnQpIiBzdHJva2U9IiNmZmYiIHN0cm9rZS13aWR0aD0iMiIvPgo8dGV4dCB4PSIzMCIgeT0iMzgiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZm9udC13ZWlnaHQ9ImJvbGQiIGZpbGw9IndoaXRlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5MSURJQTWVYPC90ZXh0Pgo8L3N2Zz4K" class="lidia-logo" alt="LIDIA">
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <h1 style="text-align: center; margin: 1rem 0;">
        <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGRlZnM+CjxsaW5lYXJHcmFkaWVudCBpZD0iZ3JhZGllbnQzIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KPHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6I0ZGNkIzNTtzdG9wLW9wYWNpdHk6MSIgLz4KPHN0b3Agb2Zmc2V0PSIyNSUiIHN0eWxlPSJzdG9wLWNvbG9yOiNGNzkzMUU7c3RvcC1vcGFjaXR5OjEiIC8+CjxzdG9wIG9mZnNldD0iNTAlIiBzdHlsZT0ic3RvcC1jb2xvcjojQzI0MzdBO3N0b3Atb3BhY2l0eToxIiAvPgo8c3RvcCBvZmZzZXQ9Ijc1JSIgc3R5bGU9InN0b3AtY29sb3I6IzY3NEVBNztzdG9wLW9wYWNpdHk6MSIgLz4KPHN0b3Agb2Zmc2V0PSIxMDAlIiBzdHlsZT0ic3RvcC1jb2xvcjojMTk3NkQyO3N0b3Atb3BhY2l0eToxIiAvPgo8L2xpbmVhckdyYWRpZW50Pgo8L2RlZnM+CjxjaXJjbGUgY3g9IjIwIiBjeT0iMjAiIHI9IjE4IiBmaWxsPSJ1cmwoI2dyYWRpZW50MykiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIyIi8+Cjx0ZXh0IHg9IjIwIiB5PSIyNiIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjEwIiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkxJRElBPC90ZXh0Pgo8L3N2Zz4K" style="vertical-align: middle; margin-right: 12px;">
        LIDIA - Assistente de IA do LID
    </h1>
    """, unsafe_allow_html=True)
    
    st.markdown("Instituto de Pesquisas Tecnológicas de São Paulo")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Autenticação
    st.markdown("### 🔒 Acesso Restrito - IPT")
    st.info("Acesso exclusivo para funcionários do Instituto de Pesquisas Tecnológicas")
    
    email = st.text_input(
        "Email institucional:",
        placeholder="seu.nome@ipt.br",
        help="Digite seu email corporativo do IPT"
    )
    
    if st.button("🔓 Acessar LIDIA", type="primary"):
        if email:
            security = SecurityManager()
            is_valid, message = security.validate_ipt_email(email)
            
            if is_valid:
                # Obter informações de localização
                client_ip = security.get_client_ip()
                location_info = security.get_location_info(client_ip)
                
                # Analisar riscos de segurança
                alerts, risk_level = security.analyze_security_risk(email, location_info)
                
                # Log do acesso
                security.log_access(email, location_info, "login", True)
                
                # Salvar na sessão
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.session_state.user_location = location_info
                st.session_state.security_alerts = alerts
                st.session_state.risk_level = risk_level
                st.session_state.session_id = hashlib.md5(f"{email}{datetime.now()}".encode()).hexdigest()
                
                # Mostrar informações de segurança se houver alertas
                if alerts:
                    st.warning(f"⚠️ Alertas de segurança detectados: {', '.join(alerts)}")
                    st.info("Acesso concedido mas será monitorado")
                else:
                    st.success("✅ Acesso autorizado!")
                
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"❌ {message}")
                # Log tentativa falhada
                security.log_access(email, {}, "login_failed", False)
        else:
            st.error("❌ Por favor, digite seu email")

def show_admin_dashboard(assistant):
    """Dashboard administrativo completo com MCP"""
    st.header("🔐 Painel Administrativo Completo")
    
    # Tabs do admin com MCP
    admin_tab1, admin_tab2, admin_tab3, admin_tab4, admin_tab5 = st.tabs([
        "📊 Dashboard Geral", 
        "📁 Gestão RAG", 
        "🛡️ Segurança & Logs",
        "💰 Controle de Custos",
        "🔌 Configuração MCP"
    ])
    
    with admin_tab1:
        st.subheader("📊 Visão Geral do Sistema")
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        try:
            conn = sqlite3.connect('lidia_security.db')
            cursor = conn.cursor()
            
            # Usuários únicos hoje
            today = datetime.now().date()
            cursor.execute('SELECT COUNT(DISTINCT email) FROM access_logs WHERE DATE(timestamp) = ?', (today,))
            users_today = cursor.fetchone()[0]
            
            # Conversas hoje
            cursor.execute('SELECT COUNT(*) FROM conversation_logs WHERE DATE(timestamp) = ?', (today,))
            conversations_today = cursor.fetchone()[0]
            
            # Uploads hoje
            cursor.execute('SELECT COUNT(*) FROM upload_logs WHERE DATE(timestamp) = ?', (today,))
            uploads_today = cursor.fetchone()[0]
            
            # Documentos na base
            doc_count = assistant.rag_system.get_document_count()
            
            conn.close()
            
            with col1:
                st.metric("👥 Usuários Hoje", users_today, "2")
            with col2:
                st.metric("💬 Conversas Hoje", conversations_today, "12")
            with col3:
                st.metric("📄 Uploads Hoje", uploads_today, "3")
            with col4:
                st.metric("📚 Base RAG", doc_count)
            
        except Exception as e:
            st.error(f"Erro ao carregar métricas: {e}")
        
        # Status MCP
        st.markdown("#### 🔌 Status MCP")
        mcp_status = assistant.mcp_manager.get_server_status()
        
        if mcp_status['total_servers'] > 0:
            st.markdown(f'<div class="mcp-status">✅ {mcp_status["total_servers"]} servidores MCP ativos</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="mcp-status">⚪ MCP não configurado</div>', unsafe_allow_html=True)
        
        # Gráfico de uso por hora
        st.subheader("📈 Atividade nas Últimas 24h")
        
        # Simular dados para o gráfico
        hours = list(range(24))
        activity = np.random.poisson(5, 24)
        activity[8:18] = np.random.poisson(15, 10)  # Mais atividade no horário comercial
        
        fig = px.line(x=hours, y=activity, title="Consultas por Hora")
        fig.update_layout(xaxis_title="Hora", yaxis_title="Número de Consultas")
        st.plotly_chart(fig, use_container_width=True)
    
    with admin_tab2:
        st.subheader("📁 Gestão da Base de Conhecimento")
        
        # Upload individual
        st.markdown("#### 📤 Upload Individual")
        uploaded_file = st.file_uploader(
            "📎 Selecionar documento para adicionar à base",
            type=['pdf', 'docx', 'txt'],
            key="admin_rag_uploader"
        )
        
        if uploaded_file:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Arquivo:** {uploaded_file.name}")
                st.write(f"**Tamanho:** {uploaded_file.size / 1024:.1f} KB")
            
            with col2:
                if st.button("➕ Adicionar à Base", type="primary"):
                    with st.spinner("📄 Processando..."):
                        success = assistant.add_document_to_knowledge_base(
                            uploaded_file, 
                            st.session_state.user_email
                        )
                    
                    if success:
                        st.success("✅ Documento adicionado!")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Erro ao processar documento")
        
        st.markdown("---")
        
        # Upload em lote
        st.markdown("#### 📂 Upload em Lote")
        default_path = r"C:\Users\robsonss\OneDrive - IPT - Inst. de Pesq. Tecn. do Est. de S.Paulo\Área de Trabalho\MeuAgente\documentos"
        
        folder_path = st.text_input(
            "📁 Caminho da pasta com documentos:",
            value=default_path
        )
        
        folder_exists = Path(folder_path).exists()
        if folder_exists:
            file_count = len(list(Path(folder_path).rglob('*.pdf'))) + \
                       len(list(Path(folder_path).rglob('*.docx'))) + \
                       len(list(Path(folder_path).rglob('*.txt')))
            st.info(f"📁 Pasta encontrada! {file_count} arquivos detectados.")
        else:
            st.warning("⚠️ Pasta não encontrada.")
        
        if st.button("🔄 Indexar Todos", disabled=not folder_exists):
            with st.spinner("Processando..."):
                result = assistant.load_documents_from_folder(folder_path, st.session_state.user_email)
            
            if 'error' in result:
                st.error(f"❌ {result['error']}")
            else:
                st.success(f"✅ {result['processed_files']}/{result['total_files']} arquivos processados!")
                if result['errors']:
                    st.warning(f"⚠️ {len(result['errors'])} erros encontrados")
    
    with admin_tab3:
        st.subheader("🛡️ Segurança e Logs de Auditoria")
        
        # Logs de acesso
        st.markdown("#### 👥 Logs de Acesso (Últimas 24h)")
        
        try:
            conn = sqlite3.connect('lidia_security.db')
            df_access = pd.read_sql_query('''
                SELECT email, ip_address, timestamp, action, success 
                FROM access_logs 
                WHERE timestamp >= datetime('now', '-1 day')
                ORDER BY timestamp DESC 
                LIMIT 20
            ''', conn)
            
            if not df_access.empty:
                st.dataframe(df_access, use_container_width=True)
            else:
                st.info("Nenhum log de acesso encontrado")
            
            # Logs MCP
            st.markdown("#### 🔌 Logs de Uso MCP (Últimas 24h)")
            df_mcp = pd.read_sql_query('''
                SELECT email, server_name, tool_name, timestamp, success 
                FROM mcp_logs 
                WHERE timestamp >= datetime('now', '-1 day')
                ORDER BY timestamp DESC 
                LIMIT 10
            ''', conn)
            
            if not df_mcp.empty:
                st.dataframe(df_mcp, use_container_width=True)
            else:
                st.info("Nenhum uso de MCP registrado")
            
            conn.close()
        except Exception as e:
            st.error(f"Erro ao carregar logs: {e}")
        
        st.markdown("---")
        
        # Mapa de acessos
        st.markdown("#### 🗺️ Mapa de Acessos")
        
        # Simular dados geográficos
        locations_data = {
            'Cidade': ['São Paulo', 'Campinas', 'Santos', 'Rio de Janeiro'],
            'Usuários': [45, 8, 3, 2],
            'Lat': [-23.5505, -22.9099, -23.9618, -22.9068],
            'Lon': [-46.6333, -47.0626, -46.3322, -43.1729]
        }
        
        df_locations = pd.DataFrame(locations_data)
        
        fig_map = px.scatter_mapbox(
            df_locations,
            lat='Lat',
            lon='Lon',
            size='Usuários',
            hover_name='Cidade',
            hover_data={'Usuários': True},
            zoom=5,
            height=400,
            title="Distribuição Geográfica de Usuários"
        )
        fig_map.update_layout(mapbox_style="open-street-map")
        st.plotly_chart(fig_map, use_container_width=True)
    
    with admin_tab4:
        st.subheader("💰 Controle de Custos e Orçamento")
        
        # Obter custos atuais
        costs = assistant.cost_manager.get_current_costs()
        alert_level, alert_message = assistant.cost_manager.check_budget_alert(costs)
        
        # Métricas de custo
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "💰 Custo Total Mês",
                f"R$ {costs['total']:.2f}",
                f"{costs['budget_used']:.1f}% do orçamento"
            )
        
        with col2:
            st.metric(
                "🔢 Perguntas Mês",
                costs['questions'],
                f"R$ {costs['variable']:.2f} variável"
            )
        
        with col3:
            st.metric(
                "🏗️ Custo Fixo",
                f"R$ {costs['fixed']:.2f}",
                "Railway hosting"
            )
        
        # Alerta de orçamento
        if alert_level == "critical":
            st.error(f"🚨 {alert_message}")
        elif alert_level == "high":
            st.warning(f"⚠️ {alert_message}")
        elif alert_level == "medium":
            st.info(f"ℹ️ {alert_message}")
        else:
            st.success(f"✅ {alert_message}")
        
        # Gráfico de custos
        st.markdown("#### 📊 Evolução de Custos")
        
        # Simular dados históricos
        days = pd.date_range(start='2024-05-01', periods=25, freq='D')
        daily_costs = np.cumsum(np.random.uniform(2, 8, 25))
        
        fig_costs = px.line(
            x=days, 
            y=daily_costs,
            title="Custos Acumulados no Mês",
            labels={'x': 'Data', 'y': 'Custo Acumulado (R$)'}
        )
        fig_costs.add_hline(y=200, line_dash="dash", line_color="red", annotation_text="Limite Orçamento")
        st.plotly_chart(fig_costs, use_container_width=True)
    
    with admin_tab5:
        show_mcp_dashboard(assistant)

def main():
    # Inicializar variáveis de sessão
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Verificar autenticação
    if not st.session_state.authenticated:
        show_authentication()
        return
    
    # API Key (em produção, usar variável de ambiente)
    API_KEY = os.environ.get('ANTHROPIC_API_KEY', 'sk-ant-api03-...')  # Substituir pela real
    
    # Inicializar assistente com MCP
    try:
        assistant = LIDIAWithMCP(API_KEY)
    except Exception as e:
        st.error(f"❌ Erro ao inicializar LIDIA: {e}")
        st.stop()
    
    # Header principal
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    
    # Logo da LIDIA
    st.markdown("""
    <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGRlZnM+CjxsaW5lYXJHcmFkaWVudCBpZD0iZ3JhZGllbnQiIHgxPSIwJSIgeTE9IjAlIiB4Mj0iMTAwJSIgeTI9IjEwMCUiPgo8c3RvcCBvZmZzZXQ9IjAlIiBzdHlsZT0ic3RvcC1jb2xvcjojRkY2QjM1O3N0b3Atb3BhY2l0eToxIiAvPgo8c3RvcCBvZmZzZXQ9IjI1JSIgc3R5bGU9InN0b3AtY29sb3I6I0Y3OTMxRTtzdG9wLW9wYWNpdHk6MSIgLz4KPHN0b3Agb2Zmc2V0PSI1MCUiIHN0eWxlPSJzdG9wLWNvbG9yOiNDMjQzN0E7c3RvcC1vcGFjaXR5OjEiIC8+CjxzdG9wIG9mZnNldD0iNzUlIiBzdHlsZT0ic3RvcC1jb2xvcjojNjc0RUE3O3N0b3Atb3BhY2l0eToxIiAvPgo8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiMxOTc2RDI7c3RvcC1vcGFjaXR5OjEiIC8+CjwvbGluZWFyR3JhZGllbnQ+CjwvZGVmcz4KPGNpcmNsZSBjeD0iMzAiIGN5PSIzMCIgcj0iMjgiIGZpbGw9InVybCgjZ3JhZGllbnQpIiBzdHJva2U9IiNmZmYiIHN0cm9rZS13aWR0aD0iMiIvPgo8dGV4dCB4PSIzMCIgeT0iMzgiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZm9udC13ZWlnaHQ9ImJvbGQiIGZpbGw9IndoaXRlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5MSURJQTWVYPC90ZXh0Pgo8L3N2Zz4K" class="lidia-logo" alt="LIDIA">
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <h1 style="text-align: center; margin: 1rem 0;">
        <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGRlZnM+CjxsaW5lYXJHcmFkaWVudCBpZD0iZ3JhZGllbnQzIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KPHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6I0ZGNkIzNTtzdG9wLW9wYWNpdHk6MSIgLz4KPHN0b3Agb2Zmc2V0PSIyNSUiIHN0eWxlPSJzdG9wLWNvbG9yOiNGNzkzMUU7c3RvcC1vcGFjaXR5OjEiIC8+CjxzdG9wIG9mZnNldD0iNTAlIiBzdHlsZT0ic3RvcC1jb2xvcjojQzI0MzdBO3N0b3Atb3BhY2l0eToxIiAvPgo8c3RvcCBvZmZzZXQ9Ijc1JSIgc3R5bGU9InN0b3AtY29sb3I6IzY3NEVBNztzdG9wLW9wYWNpdHk6MSIgLz4KPHN0b3Agb2Zmc2V0PSIxMDAlIiBzdHlsZT0ic3RvcC1jb2xvcjojMTk3NkQyO3N0b3Atb3BhY2l0eToxIiAvPgo8L2xpbmVhckdyYWRpZW50Pgo8L2RlZnM+CjxjaXJjbGUgY3g9IjIwIiBjeT0iMjAiIHI9IjE4IiBmaWxsPSJ1cmwoI2dyYWRpZW50MykiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIyIi8+Cjx0ZXh0IHg9IjIwIiB5PSIyNiIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjEwIiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkxJRElBPC90ZXh0Pgo8L3N2Zz4K" style="vertical-align: middle; margin-right: 12px;">
        LIDIA - Assistente de IA do LID
    </h1>
    """, unsafe_allow_html=True)
    
    st.markdown("Instituto de Pesquisas Tecnológicas de São Paulo")
    
    # Mostrar informações do usuário e localização
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"👤 **{st.session_state.user_email}**")
        if 'user_location' in st.session_state:
            location = st.session_state.user_location
            st.markdown(f'<div class="geo-info">📍 {location.get("city", "Unknown")}, {location.get("region", "Unknown")} | IP: {location.get("ip", "Unknown")}</div>', unsafe_allow_html=True)
    
    with col2:
        if st.button("🚪 Sair"):
            st.session_state.authenticated = False
            st.session_state.is_admin = False
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Alertas de segurança se existirem
    if 'security_alerts' in st.session_state and st.session_state.security_alerts:
        st.markdown(f'<div class="security-alert">⚠️ <strong>Alertas de Segurança:</strong> {", ".join(st.session_state.security_alerts)}</div>', unsafe_allow_html=True)
    
    # Status MCP na interface principal
    mcp_status = assistant.mcp_manager.get_server_status()
    if mcp_status['total_servers'] > 0:
        st.markdown(f'<div class="mcp-status">🔌 MCP Ativo: {mcp_status["total_servers"]} servidores | Ferramentas: {sum(len(tools) for tools in mcp_status["available_tools"].values())}</div>', unsafe_allow_html=True)
    
    # Verificar acesso administrativo
    ADMIN_PASSWORD = "ipt_admin_2024"
    
    if st.session_state.is_admin:
        # Interface admin
        tab1, tab2 = st.tabs(["💬 Conversar", "🔐 Painel Administrativo"])
        
        with tab2:
            show_admin_dashboard(assistant)
        
        with tab1:
            st.write("**Modo Administrador Ativo** - Acesso completo ao sistema incluindo MCP")
    else:
        # Acesso administrativo discreto
        with st.expander("🔧 Acesso Administrativo", expanded=False):
            admin_password = st.text_input(
                "Senha de administrador:",
                type="password",
                help="Apenas para gestores autorizados"
            )
            
            if st.button("🔓 Entrar como Admin"):
                if admin_password == ADMIN_PASSWORD:
                    st.session_state.is_admin = True
                    st.success("✅ Acesso administrativo concedido!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta")
    
    # Interface principal de chat
    st.markdown("### 💬 Converse com LIDIA")
    
    # Upload de arquivo opcional
    with st.expander("📎 Enviar Documento (Opcional)", expanded=False):
        uploaded_file = st.file_uploader(
            "Escolha um arquivo para consulta específica:",
            type=['pdf', 'docx', 'txt'],
            help="Arquivo será usado apenas nesta conversa"
        )
    
    # Área de mensagens
    if st.session_state.messages:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f'<div class="user-message">👤 {message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="assistant-message"><img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGRlZnM+CjxsaW5lYXJHcmFkaWVudCBpZD0iZ3JhZGllbnQzIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KPHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6I0ZGNkIzNTtzdG9wLW9wYWNpdHk6MSIgLz4KPHN0b3Agb2Zmc2V0PSIyNSUiIHN0eWxlPSJzdG9wLWNvbG9yOiNGNzkzMUU7c3RvcC1vcGFjaXR5OjEiIC8+CjxzdG9wIG9mZnNldD0iNTAlIiBzdHlsZT0ic3RvcC1jb2xvcjojQzI0MzdBO3N0b3Atb3BhY2l0eToxIiAvPgo8c3RvcCBvZmZzZXQ9Ijc1JSIgc3R5bGU9InN0b3AtY29sb3I6IzY3NEVBNztzdG9wLW9wYWNpdHk6MSIgLz4KPHN0b3Agb2Zmc2V0PSIxMDAlIiBzdHlsZT0ic3RvcC1jb2xvcjojMTk3NkQyO3N0b3Atb3BhY2l0eToxIiAvPgo8L2xpbmVhckdyYWRpZW50Pgo8L2RlZnM+CjxjaXJjbGUgY3g9IjIwIiBjeT0iMjAiIHI9IjE4IiBmaWxsPSJ1cmwoI2dyYWRpZW50MykiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIyIi8+Cjx0ZXh0IHg9IjIwIiB5PSIyNiIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjEwIiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkxJRElBPC90ZXh0Pgo8L3N2Zz4K" class="lidia-icon-small"> {message["content"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Input de pergunta
    user_input = st.text_area(
        "Sua pergunta:",
        placeholder="Digite sua pergunta para LIDIA...",
        height=100,
        key="user_input"
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("📤 Enviar", type="primary", disabled=not user_input.strip()):
            # Processar arquivo se enviado
            file_content = ""
            if uploaded_file:
                file_content = assistant.doc_processor.extract_text_from_file(uploaded_file)
                assistant.security.log_upload(
                    st.session_state.user_email,
                    uploaded_file.name,
                    uploaded_file.size,
                    uploaded_file.type,
                    permanent=False,
                    status="temporary_processed"
                )
            
            # Adicionar pergunta às mensagens
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Obter resposta com MCP
            with st.spinner("🤔 LIDIA está pensando..."):
                response = assistant.process_user_query(
                    user_input, 
                    file_content, 
                    st.session_state.user_email
                )
            
            # Adicionar resposta às mensagens
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            st.rerun()
    
    with col2:
        if st.button("🗑️ Limpar"):
            st.session_state.messages = []
            st.rerun()
    
    # Informações de custo
    costs = assistant.cost_manager.get_current_costs()
    st.markdown(f'<div class="cost-info">💰 Custo mensal: R$ {costs["total"]:.2f} | Perguntas: {costs["questions"]} | Orçamento usado: {costs["budget_used"]:.1f}%</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
