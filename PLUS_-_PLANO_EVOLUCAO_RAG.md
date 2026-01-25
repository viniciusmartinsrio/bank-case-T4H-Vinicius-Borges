# Plano de Implementação RAG - Banco Ágil

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura Atual vs. Futura](#arquitetura-atual-vs-futura)
3. [Pré-requisitos](#pré-requisitos)
4. [Fase 1: Infraestrutura Cloud Storage](#fase-1-infraestrutura-cloud-storage)
5. [Fase 2: Vector Store](#fase-2-vector-store)
6. [Fase 3: Pipeline de Processamento](#fase-3-pipeline-de-processamento)
7. [Fase 4: Novo Agente RAG](#fase-4-novo-agente-rag)
8. [Fase 5: Integração com LangGraph](#fase-5-integração-com-langgraph)
9. [Fase 6: Interface e UX](#fase-6-interface-e-ux)
10. [Fase 7: Testes e Validação](#fase-7-testes-e-validação)
11. [Fase 8: Otimização e Produção](#fase-8-otimização-e-produção)
12. [Estimativas de Custo](#estimativas-de-custo)
13. [Cronograma Sugerido](#cronograma-sugerido)
14. [Troubleshooting e Boas Práticas](#troubleshooting-e-boas-práticas)

---

## Visão Geral

### Objetivo

Evoluir o sistema Banco Ágil de uma arquitetura baseada em CSV para uma solução híbrida que combine:
- **Dados estruturados** (CSV/Database) para operações transacionais
- **RAG (Retrieval Augmented Generation)** para análise de documentos não estruturados

### Casos de Uso RAG

1. **Análise de Crédito Avançada**
   - Ler histórico de extratos bancários em PDF
   - Analisar contratos anteriores
   - Verificar comprovantes de renda
   - Consultar histórico de reclamações

2. **Compliance e Auditoria**
   - Buscar políticas e regulamentos aplicáveis
   - Verificar conformidade com normas do Banco Central
   - Documentar decisões de crédito

3. **Atendimento Inteligente**
   - Responder perguntas sobre produtos bancários
   - Consultar FAQs e base de conhecimento
   - Recuperar informações de manuais internos

### Benefícios Esperados

✅ **Análises mais ricas**: Contexto completo além de score numérico
✅ **Decisões fundamentadas**: Citação de fontes documentais
✅ **Redução de fraudes**: Validação cruzada de informações
✅ **Compliance**: Rastreabilidade de decisões
✅ **Escalabilidade**: Suporta milhares de documentos por cliente

---

## Arquitetura Atual vs. Futura

### Arquitetura Atual (Sem RAG)

```
┌─────────────────────────────────────────────┐
│  Streamlit UI (app_cred_ai.py)         │
└──────────────────┬──────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────┐
│  BancoAgilLangGraph (orquestrador)          │
│  • EstadoConversacao                        │
│  • Roteamento entre agentes                 │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────────┐
        │                         │
        ↓                         ↓
┌──────────────────┐    ┌──────────────────────┐
│ Agentes LLM      │    │ Agentes LLM          │
│ • TriagemAgent   │    │ • CreditoAgent       │
│ • CambioAgent    │    │ • EntrevistaAgent    │
└────────┬─────────┘    └──────────┬───────────┘
         │                         │
         └──────────┬──────────────┘
                    │
                    ↓
┌─────────────────────────────────────────────┐
│  DataManager (tools/data_manager.py)        │
│  • authenticate_client()                    │
│  • get_client_by_cpf()                      │
│  • update_client_score()                    │
└──────────────────┬──────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────┐
│  Arquivos CSV (data/)                       │
│  • clientes.csv                             │
│  • score_limite.csv                         │
│  • solicitacoes_aumento_limite.csv          │
└─────────────────────────────────────────────┘
```

### Arquitetura Futura (Com RAG)

```
┌─────────────────────────────────────────────────────────┐
│  Streamlit UI (app_cred_ai.py)                     │
│  + RAG Results Panel (fontes, trechos relevantes)       │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────┐
│  BancoAgilLangGraph (orquestrador expandido)            │
│  • EstadoConversacao + rag_context                      │
│  • Novo nó: analise_credito_rag                         │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴───────────────────┐
        │                              │
        ↓                              ↓
┌────────────────────┐       ┌──────────────────────────┐
│ Agentes Legados    │       │ NOVO: RAG Agent          │
│ (mantém CSV)       │       │ • AnaliseCreditoRAG      │
└────────┬───────────┘       │ • DocumentRetrieval      │
         │                   └──────────┬───────────────┘
         │                              │
         │                    ┌─────────┴─────────┐
         │                    │                   │
         ↓                    ↓                   ↓
┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐
│ DataManager     │  │ RAG Pipeline    │  │ Cloud Storage    │
│ (CSV)           │  │ • Retriever     │  │ • AWS S3 ou      │
└─────────────────┘  │ • Embeddings    │  │   Azure Blob     │
                     │ • Reranker      │  └──────────────────┘
                     └────────┬────────┘
                              │
                              ↓
                     ┌─────────────────┐
                     │ Vector Store    │
                     │ • Pinecone      │
                     │ • Chroma        │
                     │ • FAISS         │
                     └─────────────────┘
```

---

## Pré-requisitos

### Software e Bibliotecas

```bash
# Adicionar ao requirements.txt

# RAG Core
langchain-community>=0.0.20
langchain-pinecone>=0.0.3         # ou langchain-chroma
sentence-transformers>=2.2.0      # Embeddings locais

# Cloud Storage
boto3>=1.28.0                     # AWS S3
azure-storage-blob>=12.19.0       # Azure Blob Storage

# Document Processing
pypdf>=3.17.0                     # PDF parsing
python-docx>=1.0.0                # Word docs
openpyxl>=3.1.0                   # Excel
unstructured>=0.10.0              # Multi-format loader

# Vector Stores (escolher um)
pinecone-client>=2.2.0            # Opção cloud (paga)
chromadb>=0.4.0                   # Opção local (grátis)
faiss-cpu>=1.7.4                  # Opção local sem servidor

# Opcional: Embeddings API
openai>=1.0.0                     # OpenAI embeddings (paga)
cohere>=4.0.0                     # Cohere embeddings (paga)
```

### Contas e Credenciais

**Opção 1: AWS (Recomendado para S3)**
- Conta AWS (free tier disponível)
- IAM User com permissões S3
- Access Key ID e Secret Access Key

**Opção 2: Azure**
- Azure Subscription
- Storage Account criado
- Connection String ou SAS Token

**Opção 3: Vector Store Cloud (Opcional)**
- Conta Pinecone (free tier: 1 índice, 5GB)
- API Key

### Variáveis de Ambiente

```bash
# Adicionar ao .env

# Cloud Storage (escolher AWS ou Azure)
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
AWS_S3_BUCKET_NAME=banco-agil-documentos
AWS_REGION=us-east-1

# ou

AZURE_STORAGE_CONNECTION_STRING=your_connection_string
AZURE_STORAGE_CONTAINER_NAME=documentos-clientes

# Vector Store (se usar Pinecone)
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=us-west1-gcp-free
PINECONE_INDEX_NAME=banco-agil-docs

# Embeddings (se usar OpenAI)
OPENAI_API_KEY=your_openai_key  # Opcional, pode usar Hugging Face grátis
```

---

## Fase 1: Infraestrutura Cloud Storage

### Objetivos
- Configurar storage em nuvem (S3 ou Azure Blob)
- Organizar estrutura de pastas
- Implementar upload/download básico
- Criar dados de teste

### Passo 1.1: Escolher Provedor

**Critérios de Decisão:**

| Critério | AWS S3 | Azure Blob Storage |
|----------|--------|-------------------|
| **Free Tier** | 5GB por 12 meses | 5GB LRS + 20k operações/mês |
| **Custo após free** | $0.023/GB/mês | $0.018/GB/mês |
| **Facilidade Python** | boto3 (excelente) | azure-storage-blob (boa) |
| **LangChain Support** | Nativo | Nativo |
| **Latência Brasil** | São Paulo region | Brasil Sul region |

**Recomendação**: AWS S3 (melhor integração com LangChain)

### Passo 1.2: Criar Bucket/Container

**AWS S3:**
```bash
# Via AWS CLI
aws s3 mb s3://banco-agil-documentos --region us-east-1

# Configurar lifecycle (opcional)
aws s3api put-bucket-lifecycle-configuration \
  --bucket banco-agil-documentos \
  --lifecycle-configuration file://lifecycle.json
```

**Azure Blob:**
```bash
# Via Azure CLI
az storage container create \
  --name documentos-clientes \
  --account-name bancoagilstorage
```

### Passo 1.3: Estrutura de Pastas

```
banco-agil-documentos/
├── clientes/
│   ├── 12345678901/              # CPF do cliente
│   │   ├── comprovantes_renda/
│   │   │   ├── 2024-01-contracheque.pdf
│   │   │   └── 2024-02-contracheque.pdf
│   │   ├── extratos_bancarios/
│   │   │   ├── 2024-01-extrato.pdf
│   │   │   └── 2024-02-extrato.pdf
│   │   ├── contratos/
│   │   │   └── contrato_credito_2023.pdf
│   │   └── documentos_pessoais/
│   │       ├── rg.pdf
│   │       └── comprovante_residencia.pdf
│   └── 98765432100/
│       └── ...
├── base_conhecimento/            # Documentos gerais do banco
│   ├── politicas/
│   │   ├── politica_credito.pdf
│   │   └── normas_bacen.pdf
│   ├── produtos/
│   │   ├── cartoes.pdf
│   │   └── investimentos.pdf
│   └── faqs/
│       └── perguntas_frequentes.pdf
└── templates/
    ├── contrato_padrao.docx
    └── termo_aceite.pdf
```

### Passo 1.4: Implementar Storage Manager

**Criar arquivo: `tools/storage_manager.py`**

```python
"""
Gerenciador de armazenamento em nuvem para documentos do Banco Ágil.
Suporta AWS S3 e Azure Blob Storage.
"""

import os
from typing import List, Optional, BinaryIO
from enum import Enum
import boto3
from botocore.exceptions import ClientError
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv()


class StorageProvider(Enum):
    """Provedores de storage suportados."""
    AWS_S3 = "s3"
    AZURE_BLOB = "azure"


class StorageManager:
    """
    Gerenciador unificado para storage em nuvem.

    Suporta AWS S3 e Azure Blob Storage com interface comum.
    """

    def __init__(self, provider: str = "s3"):
        """
        Inicializa o gerenciador de storage.

        Args:
            provider: 's3' para AWS ou 'azure' para Azure Blob
        """
        self.provider = StorageProvider(provider)

        if self.provider == StorageProvider.AWS_S3:
            self._init_s3()
        elif self.provider == StorageProvider.AZURE_BLOB:
            self._init_azure()

    def _init_s3(self):
        """Inicializa cliente AWS S3."""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('AWS_S3_BUCKET_NAME', 'banco-agil-documentos')

    def _init_azure(self):
        """Inicializa cliente Azure Blob Storage."""
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'documentos-clientes')

    def upload_document(
        self,
        file_path: str,
        storage_path: str,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Faz upload de documento para o storage.

        Args:
            file_path: Caminho local do arquivo
            storage_path: Caminho no storage (ex: 'clientes/12345678901/extrato.pdf')
            metadata: Metadados opcionais (dict)

        Returns:
            True se sucesso, False caso contrário
        """
        try:
            if self.provider == StorageProvider.AWS_S3:
                extra_args = {'Metadata': metadata} if metadata else {}
                self.s3_client.upload_file(
                    file_path,
                    self.bucket_name,
                    storage_path,
                    ExtraArgs=extra_args
                )

            elif self.provider == StorageProvider.AZURE_BLOB:
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=storage_path
                )
                with open(file_path, 'rb') as data:
                    blob_client.upload_blob(data, overwrite=True, metadata=metadata)

            return True

        except Exception as e:
            print(f"Erro ao fazer upload: {e}")
            return False

    def download_document(self, storage_path: str, local_path: str) -> bool:
        """
        Baixa documento do storage.

        Args:
            storage_path: Caminho no storage
            local_path: Caminho local para salvar

        Returns:
            True se sucesso, False caso contrário
        """
        try:
            if self.provider == StorageProvider.AWS_S3:
                self.s3_client.download_file(
                    self.bucket_name,
                    storage_path,
                    local_path
                )

            elif self.provider == StorageProvider.AZURE_BLOB:
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=storage_path
                )
                with open(local_path, 'wb') as download_file:
                    download_file.write(blob_client.download_blob().readall())

            return True

        except Exception as e:
            print(f"Erro ao baixar documento: {e}")
            return False

    def list_documents(self, prefix: str = "") -> List[str]:
        """
        Lista documentos no storage.

        Args:
            prefix: Prefixo para filtrar (ex: 'clientes/12345678901/')

        Returns:
            Lista de caminhos dos documentos
        """
        documents = []

        try:
            if self.provider == StorageProvider.AWS_S3:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix
                )
                if 'Contents' in response:
                    documents = [obj['Key'] for obj in response['Contents']]

            elif self.provider == StorageProvider.AZURE_BLOB:
                container_client = self.blob_service_client.get_container_client(
                    self.container_name
                )
                blobs = container_client.list_blobs(name_starts_with=prefix)
                documents = [blob.name for blob in blobs]

        except Exception as e:
            print(f"Erro ao listar documentos: {e}")

        return documents

    def delete_document(self, storage_path: str) -> bool:
        """
        Deleta documento do storage.

        Args:
            storage_path: Caminho no storage

        Returns:
            True se sucesso, False caso contrário
        """
        try:
            if self.provider == StorageProvider.AWS_S3:
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=storage_path
                )

            elif self.provider == StorageProvider.AZURE_BLOB:
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=storage_path
                )
                blob_client.delete_blob()

            return True

        except Exception as e:
            print(f"Erro ao deletar documento: {e}")
            return False

    def get_document_url(self, storage_path: str, expiration: int = 3600) -> Optional[str]:
        """
        Gera URL temporária para acesso ao documento.

        Args:
            storage_path: Caminho no storage
            expiration: Tempo de expiração em segundos (padrão: 1 hora)

        Returns:
            URL pré-assinada ou None se erro
        """
        try:
            if self.provider == StorageProvider.AWS_S3:
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': storage_path
                    },
                    ExpiresIn=expiration
                )
                return url

            elif self.provider == StorageProvider.AZURE_BLOB:
                from azure.storage.blob import generate_blob_sas, BlobSasPermissions
                from datetime import datetime, timedelta

                sas_token = generate_blob_sas(
                    account_name=self.blob_service_client.account_name,
                    container_name=self.container_name,
                    blob_name=storage_path,
                    permission=BlobSasPermissions(read=True),
                    expiry=datetime.utcnow() + timedelta(seconds=expiration)
                )

                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=storage_path
                )
                return f"{blob_client.url}?{sas_token}"

        except Exception as e:
            print(f"Erro ao gerar URL: {e}")
            return None

    def get_client_documents(self, cpf: str) -> List[dict]:
        """
        Lista todos os documentos de um cliente.

        Args:
            cpf: CPF do cliente

        Returns:
            Lista de dicionários com informações dos documentos
        """
        prefix = f"clientes/{cpf}/"
        document_paths = self.list_documents(prefix)

        documents = []
        for path in document_paths:
            # Extrai tipo do documento do caminho
            parts = path.split('/')
            if len(parts) >= 3:
                doc_type = parts[2]  # ex: 'comprovantes_renda'
                file_name = parts[-1]

                documents.append({
                    'path': path,
                    'tipo': doc_type,
                    'nome': file_name,
                    'url': self.get_document_url(path)
                })

        return documents


# ========== FUNÇÕES AUXILIARES ==========

def upload_client_document(
    cpf: str,
    document_type: str,
    file_path: str,
    provider: str = "s3"
) -> bool:
    """
    Função helper para upload de documento de cliente.

    Args:
        cpf: CPF do cliente
        document_type: Tipo do documento (comprovantes_renda, extratos_bancarios, etc.)
        file_path: Caminho local do arquivo
        provider: Provedor de storage ('s3' ou 'azure')

    Returns:
        True se sucesso
    """
    storage = StorageManager(provider)
    file_name = os.path.basename(file_path)
    storage_path = f"clientes/{cpf}/{document_type}/{file_name}"

    metadata = {
        'cpf': cpf,
        'tipo': document_type,
        'upload_date': datetime.now().isoformat()
    }

    return storage.upload_document(file_path, storage_path, metadata)


def get_client_document_paths(cpf: str, provider: str = "s3") -> List[str]:
    """
    Retorna lista de caminhos de documentos de um cliente.

    Args:
        cpf: CPF do cliente
        provider: Provedor de storage

    Returns:
        Lista de caminhos completos
    """
    storage = StorageManager(provider)
    return storage.list_documents(f"clientes/{cpf}/")
```

### Passo 1.5: Script de Teste

**Criar arquivo: `scripts/test_storage.py`**

```python
"""
Script de teste para validar integração com storage.
"""

import os
from tools.storage_manager import StorageManager, upload_client_document

def test_storage_connection():
    """Testa conexão com storage."""
    print("🔍 Testando conexão com storage...")

    storage = StorageManager(provider="s3")  # ou "azure"

    # Tenta listar raiz
    docs = storage.list_documents()
    print(f"✅ Conexão OK. Documentos encontrados: {len(docs)}")

    return True


def test_upload_download():
    """Testa upload e download."""
    print("\n📤 Testando upload...")

    # Cria arquivo de teste
    test_file = "test_document.txt"
    with open(test_file, 'w') as f:
        f.write("Este é um documento de teste do Banco Ágil.")

    # Upload
    success = upload_client_document(
        cpf="12345678901",
        document_type="testes",
        file_path=test_file
    )

    if success:
        print("✅ Upload realizado com sucesso!")
    else:
        print("❌ Falha no upload")
        return False

    # Download
    print("\n📥 Testando download...")
    storage = StorageManager()
    downloaded_file = "test_downloaded.txt"

    success = storage.download_document(
        storage_path="clientes/12345678901/testes/test_document.txt",
        local_path=downloaded_file
    )

    if success:
        print("✅ Download realizado com sucesso!")
        with open(downloaded_file, 'r') as f:
            print(f"Conteúdo: {f.read()}")
    else:
        print("❌ Falha no download")
        return False

    # Cleanup
    os.remove(test_file)
    os.remove(downloaded_file)

    return True


def test_list_and_url():
    """Testa listagem e geração de URL."""
    print("\n📋 Testando listagem de documentos...")

    storage = StorageManager()
    docs = storage.get_client_documents("12345678901")

    print(f"Documentos do cliente: {len(docs)}")
    for doc in docs:
        print(f"  - {doc['tipo']}/{doc['nome']}")
        print(f"    URL: {doc['url'][:50]}...")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DE STORAGE - BANCO ÁGIL")
    print("=" * 60)

    try:
        test_storage_connection()
        test_upload_download()
        test_list_and_url()

        print("\n" + "=" * 60)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERRO NOS TESTES: {e}")
```

### Passo 1.6: Criar Dados de Teste

**Script: `scripts/setup_test_data.py`**

```python
"""
Cria documentos de teste para desenvolvimento.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from tools.storage_manager import upload_client_document

def create_test_pdf(filename: str, title: str, content: list):
    """Cria PDF de teste."""
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, title)

    c.setFont("Helvetica", 12)
    y = 700
    for line in content:
        c.drawString(100, y, line)
        y -= 20

    c.save()


def create_test_documents():
    """Cria documentos de teste para os clientes."""

    # Cliente 1: 12345678901
    print("Criando documentos para cliente 12345678901...")

    # Contracheque
    create_test_pdf(
        "contracheque_2024_01.pdf",
        "Contracheque - Janeiro 2024",
        [
            "Nome: João Silva",
            "CPF: 123.456.789-01",
            "Salário Bruto: R$ 8.500,00",
            "Descontos: R$ 1.200,00",
            "Salário Líquido: R$ 7.300,00"
        ]
    )
    upload_client_document("12345678901", "comprovantes_renda", "contracheque_2024_01.pdf")

    # Extrato bancário
    create_test_pdf(
        "extrato_2024_01.pdf",
        "Extrato Bancário - Janeiro 2024",
        [
            "Cliente: João Silva",
            "Conta: 12345-6",
            "Saldo Inicial: R$ 3.500,00",
            "Entradas: R$ 7.300,00",
            "Saídas: R$ 5.200,00",
            "Saldo Final: R$ 5.600,00"
        ]
    )
    upload_client_document("12345678901", "extratos_bancarios", "extrato_2024_01.pdf")

    # Cliente 2: 98765432100
    print("Criando documentos para cliente 98765432100...")

    create_test_pdf(
        "contracheque_maria_2024_01.pdf",
        "Contracheque - Janeiro 2024",
        [
            "Nome: Maria Santos",
            "CPF: 987.654.321-00",
            "Salário Bruto: R$ 12.000,00",
            "Descontos: R$ 2.100,00",
            "Salário Líquido: R$ 9.900,00"
        ]
    )
    upload_client_document("98765432100", "comprovantes_renda", "contracheque_maria_2024_01.pdf")

    # Cleanup local
    os.remove("contracheque_2024_01.pdf")
    os.remove("extrato_2024_01.pdf")
    os.remove("contracheque_maria_2024_01.pdf")

    print("✅ Documentos de teste criados com sucesso!")


if __name__ == "__main__":
    create_test_documents()
```

---

## Fase 2: Vector Store

### Objetivos
- Escolher e configurar vector database
- Implementar indexação de documentos
- Criar funções de busca semântica
- Gerenciar metadados

### Passo 2.1: Escolher Vector Store

**Comparação de Opções:**

| Vector Store | Tipo | Custo | Pros | Cons |
|--------------|------|-------|------|------|
| **FAISS** | Local (file-based) | Grátis | Zero config, rápido | Sem servidor, não escala |
| **Chroma** | Local/Server | Grátis | Fácil, persistente | Limitado para produção |
| **Pinecone** | Cloud (SaaS) | Free tier (1 índice) | Escalável, gerenciado | Custo após free tier |
| **Weaviate** | Self-hosted/Cloud | Grátis (self-host) | Híbrido, poderoso | Complexo de configurar |
| **Qdrant** | Self-hosted/Cloud | Grátis (self-host) | Performance, filtros | Menor ecossistema |

**Recomendação por Fase:**

- **Desenvolvimento:** Chroma (local, sem config)
- **MVP/Staging:** Chroma (server mode) ou Qdrant
- **Produção:** Pinecone (se budget) ou Qdrant (self-hosted)

### Passo 2.2: Configurar Chroma (Local)

**Instalar dependências:**
```bash
pip install chromadb
```

**Criar arquivo: `tools/vector_store_manager.py`**

```python
"""
Gerenciador de vector store para RAG.
Suporta Chroma, FAISS e Pinecone.
"""

import os
from typing import List, Dict, Optional, Any
from enum import Enum
import chromadb
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma, FAISS, Pinecone
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()


class VectorStoreType(Enum):
    """Tipos de vector stores suportados."""
    CHROMA = "chroma"
    FAISS = "faiss"
    PINECONE = "pinecone"


class VectorStoreManager:
    """
    Gerenciador unificado para vector stores.
    """

    def __init__(
        self,
        store_type: str = "chroma",
        collection_name: str = "banco_agil_docs",
        persist_directory: str = "./data/vector_store"
    ):
        """
        Inicializa o vector store.

        Args:
            store_type: Tipo do vector store ('chroma', 'faiss', 'pinecone')
            collection_name: Nome da coleção/índice
            persist_directory: Diretório para persistência (local stores)
        """
        self.store_type = VectorStoreType(store_type)
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # Inicializa embedding model
        self.embeddings = self._init_embeddings()

        # Inicializa vector store
        self.vectorstore = self._init_vectorstore()

    def _init_embeddings(self):
        """
        Inicializa modelo de embeddings.

        Opções:
        1. Hugging Face (grátis, local)
        2. OpenAI (paga, API)
        3. Cohere (paga, API)
        """
        # Usando Hugging Face (grátis)
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        # Alternativa: OpenAI (descomentar se preferir)
        # from langchain_openai import OpenAIEmbeddings
        # return OpenAIEmbeddings(
        #     model="text-embedding-3-small",
        #     openai_api_key=os.getenv("OPENAI_API_KEY")
        # )

    def _init_vectorstore(self):
        """Inicializa o vector store apropriado."""

        if self.store_type == VectorStoreType.CHROMA:
            return self._init_chroma()

        elif self.store_type == VectorStoreType.FAISS:
            return self._init_faiss()

        elif self.store_type == VectorStoreType.PINECONE:
            return self._init_pinecone()

    def _init_chroma(self):
        """Inicializa Chroma."""
        client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        return Chroma(
            client=client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings
        )

    def _init_faiss(self):
        """Inicializa FAISS."""
        index_path = os.path.join(self.persist_directory, "faiss_index")

        # Tenta carregar índice existente
        if os.path.exists(index_path):
            return FAISS.load_local(
                index_path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )

        # Cria novo índice vazio
        return None  # Será criado no primeiro add_documents

    def _init_pinecone(self):
        """Inicializa Pinecone."""
        import pinecone

        pinecone.init(
            api_key=os.getenv("PINECONE_API_KEY"),
            environment=os.getenv("PINECONE_ENVIRONMENT")
        )

        index_name = os.getenv("PINECONE_INDEX_NAME", self.collection_name)

        return Pinecone.from_existing_index(
            index_name=index_name,
            embedding=self.embeddings
        )

    def add_documents(
        self,
        documents: List[Document],
        batch_size: int = 100
    ) -> List[str]:
        """
        Adiciona documentos ao vector store.

        Args:
            documents: Lista de objetos Document do LangChain
            batch_size: Tamanho do batch para processamento

        Returns:
            Lista de IDs dos documentos adicionados
        """
        if not documents:
            return []

        ids = []

        # Processa em batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]

            if self.store_type == VectorStoreType.CHROMA:
                batch_ids = self.vectorstore.add_documents(batch)
                ids.extend(batch_ids)

            elif self.store_type == VectorStoreType.FAISS:
                if self.vectorstore is None:
                    # Cria índice inicial
                    self.vectorstore = FAISS.from_documents(batch, self.embeddings)
                else:
                    # Adiciona ao índice existente
                    self.vectorstore.add_documents(batch)
                ids.extend([str(i) for i in range(len(batch))])

            elif self.store_type == VectorStoreType.PINECONE:
                batch_ids = self.vectorstore.add_documents(batch)
                ids.extend(batch_ids)

        # Salva se for local
        if self.store_type == VectorStoreType.FAISS:
            self.save()

        return ids

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Busca documentos similares.

        Args:
            query: Query de busca
            k: Número de resultados
            filter: Filtros de metadata (ex: {'cpf': '12345678901'})

        Returns:
            Lista de documentos mais similares
        """
        if self.vectorstore is None:
            return []

        if filter:
            return self.vectorstore.similarity_search(
                query,
                k=k,
                filter=filter
            )
        else:
            return self.vectorstore.similarity_search(query, k=k)

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Document, float]]:
        """
        Busca com scores de similaridade.

        Returns:
            Lista de tuplas (documento, score)
        """
        if self.vectorstore is None:
            return []

        return self.vectorstore.similarity_search_with_score(
            query,
            k=k,
            filter=filter if filter else None
        )

    def delete_by_metadata(self, filter: Dict[str, Any]) -> bool:
        """
        Deleta documentos por metadata.

        Args:
            filter: Filtro de metadata (ex: {'cpf': '12345678901'})

        Returns:
            True se sucesso
        """
        try:
            if self.store_type == VectorStoreType.CHROMA:
                self.vectorstore._collection.delete(where=filter)
                return True

            # FAISS e Pinecone não suportam delete por metadata nativamente
            # Seria necessário reconstruir o índice

            return False

        except Exception as e:
            print(f"Erro ao deletar: {e}")
            return False

    def save(self):
        """Salva vector store (apenas para tipos locais)."""
        if self.store_type == VectorStoreType.FAISS:
            index_path = os.path.join(self.persist_directory, "faiss_index")
            os.makedirs(self.persist_directory, exist_ok=True)
            self.vectorstore.save_local(index_path)

        # Chroma salva automaticamente
        # Pinecone é cloud, não precisa salvar

    def get_collection_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da coleção."""
        stats = {
            "type": self.store_type.value,
            "collection_name": self.collection_name
        }

        if self.store_type == VectorStoreType.CHROMA:
            stats["count"] = self.vectorstore._collection.count()

        return stats


# ========== FUNÇÕES AUXILIARES ==========

def create_document_from_text(
    text: str,
    metadata: Dict[str, Any]
) -> Document:
    """
    Cria objeto Document do LangChain.

    Args:
        text: Conteúdo do documento
        metadata: Metadados (cpf, tipo_documento, data, etc.)

    Returns:
        Objeto Document
    """
    return Document(
        page_content=text,
        metadata=metadata
    )


def search_client_documents(
    cpf: str,
    query: str,
    vector_store: VectorStoreManager,
    k: int = 5
) -> List[Document]:
    """
    Busca documentos de um cliente específico.

    Args:
        cpf: CPF do cliente
        query: Pergunta/query
        vector_store: Instância do VectorStoreManager
        k: Número de resultados

    Returns:
        Lista de documentos relevantes
    """
    return vector_store.similarity_search(
        query=query,
        k=k,
        filter={"cpf": cpf}
    )
```

### Passo 2.3: Script de Teste Vector Store

**Criar arquivo: `scripts/test_vector_store.py`**

```python
"""
Testa funcionalidades do vector store.
"""

from tools.vector_store_manager import VectorStoreManager, create_document_from_text

def test_add_and_search():
    """Testa adicionar e buscar documentos."""
    print("🔍 Testando Vector Store...")

    # Inicializa
    vector_store = VectorStoreManager(
        store_type="chroma",
        collection_name="test_collection",
        persist_directory="./data/test_vector_store"
    )

    # Cria documentos de teste
    docs = [
        create_document_from_text(
            "João Silva tem renda mensal de R$ 7.500,00 comprovada por contracheque.",
            {"cpf": "12345678901", "tipo": "analise_renda", "data": "2024-01-15"}
        ),
        create_document_from_text(
            "Maria Santos possui saldo médio de R$ 12.000,00 nos últimos 6 meses.",
            {"cpf": "98765432100", "tipo": "extrato", "data": "2024-01-20"}
        ),
        create_document_from_text(
            "João Silva não possui dívidas ativas em seu CPF.",
            {"cpf": "12345678901", "tipo": "consulta_credito", "data": "2024-01-10"}
        )
    ]

    # Adiciona ao vector store
    print("\n📝 Adicionando documentos...")
    ids = vector_store.add_documents(docs)
    print(f"✅ {len(ids)} documentos adicionados")

    # Busca 1: Geral
    print("\n🔎 Busca 1: 'qual a renda do cliente?'")
    results = vector_store.similarity_search("qual a renda do cliente?", k=2)
    for i, doc in enumerate(results, 1):
        print(f"\n  Resultado {i}:")
        print(f"  Texto: {doc.page_content}")
        print(f"  CPF: {doc.metadata.get('cpf')}")

    # Busca 2: Filtrada por CPF
    print("\n🔎 Busca 2: Informações do João (CPF filtrado)")
    results = vector_store.similarity_search(
        "informações financeiras",
        k=3,
        filter={"cpf": "12345678901"}
    )
    print(f"  Encontrados: {len(results)} documentos do João")
    for doc in results:
        print(f"  - {doc.page_content[:60]}...")

    # Busca 3: Com scores
    print("\n🔎 Busca 3: Com scores de relevância")
    results_with_scores = vector_store.similarity_search_with_score(
        "dívidas do cliente",
        k=2
    )
    for doc, score in results_with_scores:
        print(f"\n  Score: {score:.4f}")
        print(f"  Texto: {doc.page_content}")

    # Estatísticas
    print("\n📊 Estatísticas da coleção:")
    stats = vector_store.get_collection_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n✅ TESTE CONCLUÍDO!")


if __name__ == "__main__":
    test_add_and_search()
```

---

## Fase 3: Pipeline de Processamento

### Objetivos
- Carregar documentos do storage
- Processar PDFs, Word, Excel
- Fazer chunking inteligente
- Indexar no vector store
- Gerenciar pipeline end-to-end

### Passo 3.1: Document Loaders

**Atualizar: `tools/document_processor.py`** (novo arquivo)

```python
"""
Processamento de documentos para RAG.
Carrega, divide (chunking) e prepara documentos para indexação.
"""

import os
from typing import List, Optional, Dict, Any
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredExcelLoader,
    TextLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from tools.storage_manager import StorageManager


class DocumentProcessor:
    """
    Processa documentos do storage para indexação.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        storage_provider: str = "s3"
    ):
        """
        Inicializa o processador.

        Args:
            chunk_size: Tamanho dos chunks (tokens aproximados)
            chunk_overlap: Overlap entre chunks
            storage_provider: Provedor de storage ('s3' ou 'azure')
        """
        self.storage = StorageManager(provider=storage_provider)

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def load_document(
        self,
        storage_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Carrega documento do storage.

        Args:
            storage_path: Caminho no storage
            metadata: Metadados adicionais

        Returns:
            Lista de objetos Document (já com chunking)
        """
        # Download temporário
        local_path = f"./temp/{os.path.basename(storage_path)}"
        os.makedirs("./temp", exist_ok=True)

        success = self.storage.download_document(storage_path, local_path)
        if not success:
            return []

        # Detecta tipo e carrega
        extension = os.path.splitext(local_path)[1].lower()

        try:
            if extension == '.pdf':
                loader = PyPDFLoader(local_path)
            elif extension in ['.docx', '.doc']:
                loader = UnstructuredWordDocumentLoader(local_path)
            elif extension in ['.xlsx', '.xls']:
                loader = UnstructuredExcelLoader(local_path)
            elif extension == '.txt':
                loader = TextLoader(local_path)
            else:
                print(f"Tipo não suportado: {extension}")
                return []

            # Carrega documento
            documents = loader.load()

            # Adiciona metadados
            if metadata:
                for doc in documents:
                    doc.metadata.update(metadata)
                    doc.metadata['source_path'] = storage_path

            # Faz chunking
            chunks = self.text_splitter.split_documents(documents)

            # Cleanup
            os.remove(local_path)

            return chunks

        except Exception as e:
            print(f"Erro ao processar documento: {e}")
            if os.path.exists(local_path):
                os.remove(local_path)
            return []

    def process_client_documents(
        self,
        cpf: str,
        document_types: Optional[List[str]] = None
    ) -> List[Document]:
        """
        Processa todos os documentos de um cliente.

        Args:
            cpf: CPF do cliente
            document_types: Tipos de documentos para processar (None = todos)

        Returns:
            Lista de chunks prontos para indexação
        """
        all_chunks = []

        # Lista documentos do cliente
        client_docs = self.storage.get_client_documents(cpf)

        for doc_info in client_docs:
            # Filtra por tipo se especificado
            if document_types and doc_info['tipo'] not in document_types:
                continue

            print(f"Processando: {doc_info['nome']}")

            # Metadados
            metadata = {
                'cpf': cpf,
                'tipo_documento': doc_info['tipo'],
                'nome_arquivo': doc_info['nome']
            }

            # Carrega e faz chunking
            chunks = self.load_document(doc_info['path'], metadata)
            all_chunks.extend(chunks)

        return all_chunks

    def process_and_index(
        self,
        cpf: str,
        vector_store_manager,
        document_types: Optional[List[str]] = None
    ) -> int:
        """
        Pipeline completo: processa e indexa documentos.

        Args:
            cpf: CPF do cliente
            vector_store_manager: Instância do VectorStoreManager
            document_types: Tipos de documentos (opcional)

        Returns:
            Número de chunks indexados
        """
        print(f"📄 Processando documentos do cliente {cpf}...")

        # Processa documentos
        chunks = self.process_client_documents(cpf, document_types)

        if not chunks:
            print("⚠️ Nenhum documento encontrado/processado")
            return 0

        print(f"✂️ Total de chunks criados: {len(chunks)}")

        # Indexa no vector store
        print("🔄 Indexando no vector store...")
        ids = vector_store_manager.add_documents(chunks)

        print(f"✅ {len(ids)} chunks indexados com sucesso!")

        return len(ids)


# ========== FUNÇÕES AUXILIARES ==========

def batch_process_all_clients(
    client_cpfs: List[str],
    vector_store_manager,
    storage_provider: str = "s3"
) -> Dict[str, int]:
    """
    Processa documentos de múltiplos clientes em batch.

    Args:
        client_cpfs: Lista de CPFs
        vector_store_manager: Instância do VectorStoreManager
        storage_provider: Provedor de storage

    Returns:
        Dicionário {cpf: num_chunks_indexados}
    """
    processor = DocumentProcessor(storage_provider=storage_provider)
    results = {}

    for cpf in client_cpfs:
        try:
            num_chunks = processor.process_and_index(cpf, vector_store_manager)
            results[cpf] = num_chunks
        except Exception as e:
            print(f"❌ Erro ao processar {cpf}: {e}")
            results[cpf] = 0

    return results


def reindex_client_documents(
    cpf: str,
    vector_store_manager,
    storage_provider: str = "s3"
) -> bool:
    """
    Re-indexa documentos de um cliente (remove antigos e adiciona novos).

    Args:
        cpf: CPF do cliente
        vector_store_manager: Instância do VectorStoreManager
        storage_provider: Provedor de storage

    Returns:
        True se sucesso
    """
    try:
        # Remove documentos antigos
        print(f"🗑️ Removendo índices antigos do cliente {cpf}...")
        vector_store_manager.delete_by_metadata({"cpf": cpf})

        # Re-indexa
        processor = DocumentProcessor(storage_provider=storage_provider)
        num_chunks = processor.process_and_index(cpf, vector_store_manager)

        return num_chunks > 0

    except Exception as e:
        print(f"❌ Erro ao re-indexar: {e}")
        return False
```

### Passo 3.2: Script de Indexação Inicial

**Criar: `scripts/index_documents.py`**

```python
"""
Script para indexação inicial de documentos.
Executa pipeline completo: storage → processing → vector store
"""

import sys
import argparse
from tools.vector_store_manager import VectorStoreManager
from tools.document_processor import DocumentProcessor, batch_process_all_clients
from tools.data_manager import DataManager


def index_all_clients():
    """Indexa documentos de todos os clientes do CSV."""
    print("=" * 60)
    print("INDEXAÇÃO DE DOCUMENTOS - BANCO ÁGIL")
    print("=" * 60)

    # Inicializa componentes
    print("\n🔧 Inicializando componentes...")
    vector_store = VectorStoreManager(
        store_type="chroma",
        collection_name="banco_agil_docs",
        persist_directory="./data/vector_store"
    )

    # Busca todos os clientes
    data_manager = DataManager()
    # Assumindo que você tem um método get_all_clients() no DataManager
    # Se não tiver, adicione ou use a lista manualmente

    client_cpfs = [
        "12345678901",
        "98765432100",
        "55555555555",
        # Adicione outros CPFs conforme necessário
    ]

    print(f"📋 Clientes a processar: {len(client_cpfs)}")

    # Processa em batch
    print("\n🚀 Iniciando processamento...\n")
    results = batch_process_all_clients(
        client_cpfs=client_cpfs,
        vector_store_manager=vector_store,
        storage_provider="s3"  # ou "azure"
    )

    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DA INDEXAÇÃO")
    print("=" * 60)

    total_chunks = 0
    for cpf, num_chunks in results.items():
        print(f"Cliente {cpf}: {num_chunks} chunks indexados")
        total_chunks += num_chunks

    print(f"\n✅ Total: {total_chunks} chunks indexados")

    # Estatísticas do vector store
    stats = vector_store.get_collection_stats()
    print(f"\n📊 Estatísticas do Vector Store:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


def index_single_client(cpf: str):
    """Indexa documentos de um único cliente."""
    print(f"📄 Indexando documentos do cliente {cpf}...\n")

    vector_store = VectorStoreManager(
        store_type="chroma",
        collection_name="banco_agil_docs",
        persist_directory="./data/vector_store"
    )

    processor = DocumentProcessor(storage_provider="s3")

    num_chunks = processor.process_and_index(cpf, vector_store)

    if num_chunks > 0:
        print(f"\n✅ Cliente {cpf}: {num_chunks} chunks indexados com sucesso!")
    else:
        print(f"\n⚠️ Nenhum documento encontrado para o cliente {cpf}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Indexação de documentos para RAG")
    parser.add_argument(
        "--cpf",
        type=str,
        help="CPF de um cliente específico (opcional)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Indexar todos os clientes"
    )

    args = parser.parse_args()

    if args.cpf:
        index_single_client(args.cpf)
    elif args.all:
        index_all_clients()
    else:
        print("Use --cpf <CPF> para indexar um cliente ou --all para todos")
        print("Exemplo: python scripts/index_documents.py --cpf 12345678901")
        print("Exemplo: python scripts/index_documents.py --all")
```

---

## Fase 4: Novo Agente RAG

### Objetivos
- Criar agente especializado em análise de documentos
- Implementar retrieval contextual
- Integrar com LLM
- Citar fontes nas respostas

### Passo 4.1: Criar Agente RAG

**Criar arquivo: `agents/analise_credito_rag_agent.py`**

```python
"""
Agente de Análise de Crédito com RAG.
Analisa documentos do cliente para fornecer insights e recomendações.
"""

from typing import List, Dict, Optional, Any
from langchain.chains import RetrievalQA
from langchain_groq import ChatGroq
from tools.vector_store_manager import VectorStoreManager, search_client_documents
from tools.llm_config import criar_llm_groq
from prompts.agent_prompts import ANALISE_CREDITO_RAG_PROMPT


class AnaliseCreditoRAGAgent:
    """
    Agente que usa RAG para análise avançada de crédito.
    """

    def __init__(self, vector_store_manager: VectorStoreManager):
        """
        Inicializa o agente RAG.

        Args:
            vector_store_manager: Instância do VectorStoreManager
        """
        self.vector_store = vector_store_manager
        self.llm = criar_llm_groq(
            temperatura=0.3,  # Mais factual
            max_tokens=500,
            top_p=0.85
        )

        # Cria retriever
        self.retriever = self.vector_store.vectorstore.as_retriever(
            search_kwargs={"k": 5}
        )

        # Cria chain RAG
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",  # Coloca todos os docs no contexto
            retriever=self.retriever,
            return_source_documents=True,
            chain_type_kwargs={
                "prompt": ANALISE_CREDITO_RAG_PROMPT
            }
        )

    def analisar_documentos_cliente(
        self,
        cpf: str,
        pergunta: str
    ) -> Dict[str, Any]:
        """
        Analisa documentos do cliente e responde pergunta.

        Args:
            cpf: CPF do cliente
            pergunta: Pergunta sobre o cliente

        Returns:
            Dicionário com resposta e fontes
        """
        # Busca documentos relevantes do cliente
        documentos = search_client_documents(
            cpf=cpf,
            query=pergunta,
            vector_store=self.vector_store,
            k=5
        )

        if not documentos:
            return {
                "resposta": f"⚠️ Não encontrei documentos indexados para o CPF {cpf}.",
                "fontes": [],
                "num_documentos": 0
            }

        # Executa RAG
        query_completa = f"Cliente CPF {cpf}: {pergunta}"
        result = self.qa_chain.invoke({"query": query_completa})

        # Extrai fontes
        fontes = []
        for doc in result.get("source_documents", []):
            fonte_info = {
                "texto": doc.page_content[:200] + "...",  # Preview
                "tipo_documento": doc.metadata.get("tipo_documento", "N/A"),
                "nome_arquivo": doc.metadata.get("nome_arquivo", "N/A"),
                "cpf": doc.metadata.get("cpf", "N/A")
            }
            fontes.append(fonte_info)

        return {
            "resposta": result["result"],
            "fontes": fontes,
            "num_documentos": len(fontes)
        }

    def recomendar_limite(self, cpf: str, score_atual: float) -> Dict[str, Any]:
        """
        Recomenda limite baseado em análise documental.

        Args:
            cpf: CPF do cliente
            score_atual: Score de crédito atual

        Returns:
            Recomendação com justificativa
        """
        pergunta = f"""
        Analise os documentos financeiros deste cliente (score atual: {score_atual}).

        Considere:
        1. Comprovantes de renda
        2. Histórico de extratos bancários
        3. Pagamentos regulares
        4. Comprometimento de renda

        Recomende um limite de crédito apropriado e justifique.
        """

        return self.analisar_documentos_cliente(cpf, pergunta)

    def verificar_inconsistencias(self, cpf: str) -> Dict[str, Any]:
        """
        Verifica inconsistências entre documentos.

        Args:
            cpf: CPF do cliente

        Returns:
            Relatório de inconsistências
        """
        pergunta = """
        Analise os documentos e identifique possíveis inconsistências:

        - Discrepâncias entre renda declarada e extratos
        - Diferenças entre endereços em diferentes documentos
        - Incompatibilidades em datas
        - Qualquer informação conflitante

        Liste as inconsistências encontradas ou confirme a consistência.
        """

        return self.analisar_documentos_cliente(cpf, pergunta)

    def resumir_situacao_financeira(self, cpf: str) -> Dict[str, Any]:
        """
        Cria resumo executivo da situação financeira.

        Args:
            cpf: CPF do cliente

        Returns:
            Resumo com principais insights
        """
        pergunta = """
        Crie um resumo executivo da situação financeira deste cliente:

        1. **Renda**: Valor médio e fontes
        2. **Despesas**: Comprometimento aproximado
        3. **Padrão de pagamento**: Regularidade
        4. **Pontos positivos**: Aspectos que favorecem crédito
        5. **Pontos de atenção**: Riscos identificados
        6. **Recomendação geral**: Aprovar/rejeitar/condicional

        Seja objetivo e baseie-se apenas nos documentos disponíveis.
        """

        return self.analisar_documentos_cliente(cpf, pergunta)


# ========== FERRAMENTAS PARA INTEGRAÇÃO COM LANGGRAPH ==========

def ferramenta_analise_rag(
    cpf: str,
    pergunta: str,
    vector_store_manager: VectorStoreManager
) -> str:
    """
    Função wrapper para uso como tool do LangChain.

    Args:
        cpf: CPF do cliente
        pergunta: Pergunta sobre o cliente
        vector_store_manager: Instância do VectorStoreManager

    Returns:
        Resposta formatada com fontes
    """
    agente = AnaliseCreditoRAGAgent(vector_store_manager)
    resultado = agente.analisar_documentos_cliente(cpf, pergunta)

    # Formata resposta
    resposta = f"**Análise Baseada em Documentos:**\n\n{resultado['resposta']}\n\n"

    if resultado['fontes']:
        resposta += f"**Fontes Consultadas ({resultado['num_documentos']} documentos):**\n"
        for i, fonte in enumerate(resultado['fontes'], 1):
            resposta += f"\n{i}. {fonte['tipo_documento']} - {fonte['nome_arquivo']}\n"
            resposta += f"   Trecho: \"{fonte['texto'][:100]}...\"\n"

    return resposta
```

### Passo 4.2: Adicionar Prompt RAG

**Atualizar: `prompts/agent_prompts.py`**

```python
# Adicionar ao final do arquivo

from langchain.prompts import PromptTemplate

ANALISE_CREDITO_RAG_PROMPT = PromptTemplate(
    template="""Você é um **Analista de Crédito Sênior** do Banco Ágil.

Sua função é analisar documentos financeiros de clientes e fornecer insights precisos e fundamentados para decisões de crédito.

## 📋 DIRETRIZES

1. **Base-se APENAS nos documentos fornecidos** - Não invente informações
2. **Cite as fontes** - Mencione qual documento suporta cada afirmação
3. **Seja objetivo e preciso** - Use números e fatos concretos
4. **Identifique riscos** - Aponte inconsistências ou red flags
5. **Justifique recomendações** - Explique o raciocínio

## 📄 CONTEXTO DOS DOCUMENTOS

{context}

## ❓ PERGUNTA DO USUÁRIO

{question}

## 💬 SUA ANÁLISE

Forneça uma análise profissional, estruturada e fundamentada nos documentos:

""",
    input_variables=["context", "question"]
)
```

### Passo 4.3: Integrar Tools RAG

**Atualizar: `tools/agent_tools.py`**

```python
# Adicionar ao final do arquivo

from langchain.tools import tool
from tools.vector_store_manager import VectorStoreManager
from agents.analise_credito_rag_agent import ferramenta_analise_rag

# Instância global do vector store (inicializada uma vez)
_vector_store = None

def get_vector_store():
    """Retorna instância singleton do vector store."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreManager(
            store_type="chroma",
            collection_name="banco_agil_docs",
            persist_directory="./data/vector_store"
        )
    return _vector_store


@tool
def analisar_documentos_cliente_rag(cpf: str, pergunta: str) -> str:
    """
    Analisa documentos do cliente usando RAG (Retrieval Augmented Generation).

    Use esta ferramenta quando precisar consultar documentos, contratos,
    extratos ou comprovantes do cliente para tomar decisões mais informadas.

    Args:
        cpf: CPF do cliente (11 dígitos)
        pergunta: Pergunta específica sobre os documentos do cliente

    Returns:
        Análise baseada nos documentos com citação de fontes

    Exemplos de uso:
    - "Qual a renda comprovada do cliente?"
    - "O cliente tem histórico de atrasos em pagamentos?"
    - "Existem inconsistências nos documentos?"
    """
    vector_store = get_vector_store()
    return ferramenta_analise_rag(cpf, pergunta, vector_store)


@tool
def recomendar_limite_baseado_documentos(cpf: str, score_atual: float) -> str:
    """
    Recomenda limite de crédito baseado em análise documental via RAG.

    Analisa comprovantes de renda, extratos bancários e outros documentos
    para recomendar um limite apropriado além do score numérico.

    Args:
        cpf: CPF do cliente
        score_atual: Score de crédito atual do cliente

    Returns:
        Recomendação de limite com justificativa documental
    """
    from agents.analise_credito_rag_agent import AnaliseCreditoRAGAgent

    vector_store = get_vector_store()
    agente = AnaliseCreditoRAGAgent(vector_store)

    resultado = agente.recomendar_limite(cpf, score_atual)

    resposta = f"{resultado['resposta']}\n\n"
    if resultado['fontes']:
        resposta += f"Baseado em {resultado['num_documentos']} documento(s) do cliente."

    return resposta
```

---

## Fase 5: Integração com LangGraph

### Objetivos
- Adicionar nó RAG ao grafo
- Criar transições para o agente RAG
- Atualizar estado conversacional
- Testar fluxo completo

### Passo 5.1: Atualizar State

**Atualizar: `state.py`**

```python
# Adicionar ao EstadoConversacao TypedDict

from typing import TypedDict, List, Dict, Optional, Literal, Any

class EstadoConversacao(TypedDict):
    mensagens: List[Dict[str, str]]
    mensagem_atual: str
    agente_ativo: Literal[
        "triagem",
        "credito",
        "entrevista_credito",
        "cambio",
        "analise_rag",  # NOVO
        "encerramento"
    ]
    cliente_autenticado: Optional[Dict[str, Any]]
    dados_temporarios: Dict[str, Any]
    contexto_agente: Dict[str, Any]
    rag_context: Optional[Dict[str, Any]]  # NOVO: Contexto recuperado via RAG
    conversa_ativa: bool
```

### Passo 5.2: Criar Nó RAG no LangGraph

**Atualizar: `banco_agil_langgraph.py`**

```python
# Adicionar import
from agents.analise_credito_rag_agent import AnaliseCreditoRAGAgent
from tools.vector_store_manager import VectorStoreManager

# Na classe BancoAgilLangGraph, adicionar no __init__:

def __init__(self):
    # ... código existente ...

    # Inicializa vector store e agente RAG
    self.vector_store = VectorStoreManager(
        store_type="chroma",
        collection_name="banco_agil_docs",
        persist_directory="./data/vector_store"
    )
    self.agente_rag = AnaliseCreditoRAGAgent(self.vector_store)

    # ... resto do código ...

# Adicionar novo nó:

def nodo_analise_rag(self, estado: EstadoConversacao) -> EstadoConversacao:
    """
    Nó que processa análises com RAG.
    """
    mensagem = estado["mensagem_atual"]
    cliente = estado["cliente_autenticado"]

    if not cliente:
        resposta = "⚠️ É necessário estar autenticado para análise de documentos."
        estado["mensagens"].append({
            "remetente": "sistema",
            "mensagem": resposta
        })
        return estado

    cpf = cliente["cpf"]

    # Identifica tipo de análise
    if "limite" in mensagem.lower() or "crédito" in mensagem.lower():
        resultado = self.agente_rag.recomendar_limite(
            cpf,
            cliente["score_credito"]
        )
    elif "inconsistência" in mensagem.lower() or "verificar" in mensagem.lower():
        resultado = self.agente_rag.verificar_inconsistencias(cpf)
    elif "resumo" in mensagem.lower() or "situação" in mensagem.lower():
        resultado = self.agente_rag.resumir_situacao_financeira(cpf)
    else:
        # Análise genérica
        resultado = self.agente_rag.analisar_documentos_cliente(cpf, mensagem)

    # Formata resposta
    resposta = f"**📊 Análise Documental**\n\n{resultado['resposta']}\n\n"

    if resultado['fontes']:
        resposta += f"**📄 Fontes ({resultado['num_documentos']} documentos):**\n"
        for i, fonte in enumerate(resultado['fontes'][:3], 1):  # Top 3
            resposta += f"{i}. {fonte['tipo_documento']} - {fonte['nome_arquivo']}\n"

    resposta += "\n\nDeseja voltar ao menu principal? (digite 'menu' ou 'voltar')"

    # Atualiza estado
    estado["mensagens"].append({
        "remetente": "analise_rag",
        "mensagem": resposta
    })
    estado["rag_context"] = resultado

    return estado

# Na função _construir_grafo, adicionar o nó:

def _construir_grafo(self):
    """Constrói o grafo de conversação."""

    # ... nós existentes ...

    # Adiciona nó RAG
    self.grafo.add_node("analise_rag", self.nodo_analise_rag)

    # Adiciona transições

    # Do menu principal (triagem) para RAG
    self.grafo.add_edge("triagem", "analise_rag",
                        condition=lambda x: "analis" in x["mensagem_atual"].lower() or
                                           "documento" in x["mensagem_atual"].lower() or
                                           "rag" in x["mensagem_atual"].lower())

    # De RAG de volta para menu
    self.grafo.add_edge("analise_rag", "triagem",
                        condition=lambda x: "menu" in x["mensagem_atual"].lower() or
                                           "voltar" in x["mensagem_atual"].lower())

    # De RAG para encerramento
    self.grafo.add_edge("analise_rag", "encerramento",
                        condition=lambda x: "encerrar" in x["mensagem_atual"].lower() or
                                           "sair" in x["mensagem_atual"].lower())

    # ... resto do código ...
```

### Passo 5.3: Atualizar Menu Principal

**Atualizar prompt do TriagemAgent para incluir nova opção:**

```python
# Em prompts/agent_prompts.py, atualizar TRIAGEM_PROMPT:

TRIAGEM_PROMPT = """
...

## 🎯 MENU DE SERVIÇOS (após autenticação)

Apresente as opções ao cliente:

1. **💳 Consultar Limite de Crédito** - Verificar limite atual e score
2. **📈 Solicitar Aumento de Limite** - Pedir aumento no limite
3. **📋 Entrevista Financeira** - Atualizar dados para recálculo de score
4. **💱 Consultar Câmbio** - Cotações de moedas estrangeiras
5. **📊 Análise Documental (RAG)** - Análise avançada baseada em documentos [NOVO]
6. **👋 Encerrar Atendimento** - Finalizar conversa

...
"""
```

---

## Fase 6: Interface e UX

### Objetivos
- Adicionar botão RAG na UI
- Mostrar fontes dos documentos
- Exibir preview de trechos
- Loading indicators para queries lentas

### Passo 6.1: Atualizar Streamlit UI

**Atualizar: `app_cred_ai.py`**

```python
# Na função mostrar_quick_replies(), adicionar botão RAG:

def mostrar_quick_replies():
    """Mostra botões de resposta rápida baseados no contexto."""
    estado = st.session_state.sistema.get_estado()
    agente_ativo = estado.get("agente_ativo", "triagem")
    cliente_autenticado = estado.get("cliente_autenticado")

    # Menu principal após autenticação
    if agente_ativo == "triagem" and cliente_autenticado:
        st.markdown("### 🎯 Escolha um serviço:")
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            if st.button("💳 Crédito", use_container_width=True):
                processar_mensagem_com_feedback("Quero consultar meu crédito", mostrar_validacao=False)

        with col2:
            if st.button("💱 Câmbio", use_container_width=True):
                processar_mensagem_com_feedback("Consultar cotações de moedas", mostrar_validacao=False)

        with col3:
            if st.button("📋 Entrevista", use_container_width=True):
                processar_mensagem_com_feedback("Fazer entrevista financeira", mostrar_validacao=False)

        with col4:
            if st.button("📊 Análise RAG", use_container_width=True, type="primary"):  # NOVO
                processar_mensagem_com_feedback("Quero análise baseada em documentos", mostrar_validacao=False)

        with col5:
            if st.button("👋 Encerrar", use_container_width=True, type="secondary"):
                st.session_state.aguardando_confirmacao = "encerrar"
                st.rerun()

    # Quick replies para agente RAG (NOVO)
    elif agente_ativo == "analise_rag":
        st.markdown("### 📊 Tipos de Análise RAG:")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("💰 Recomendação de Limite", use_container_width=True):
                processar_mensagem_com_feedback(
                    "Recomende um limite de crédito baseado nos meus documentos",
                    mostrar_validacao=False
                )

        with col2:
            if st.button("🔍 Verificar Inconsistências", use_container_width=True):
                processar_mensagem_com_feedback(
                    "Verifique se há inconsistências nos meus documentos",
                    mostrar_validacao=False
                )

        with col3:
            if st.button("📄 Resumo Financeiro", use_container_width=True):
                processar_mensagem_com_feedback(
                    "Faça um resumo da minha situação financeira",
                    mostrar_validacao=False
                )

        st.markdown("---")

        col_pergunta, col_voltar = st.columns([4, 1])

        with col_pergunta:
            if st.button("❓ Pergunta Personalizada", use_container_width=True):
                st.info("💡 Digite sua pergunta no campo de texto abaixo")

        with col_voltar:
            if st.button("↩️ Voltar", use_container_width=True):
                processar_mensagem_com_feedback("Voltar ao menu", mostrar_validacao=False)

# Adicionar função para exibir fontes RAG:

def exibir_fontes_rag(rag_context: dict):
    """Exibe fontes dos documentos consultados via RAG."""
    if not rag_context or not rag_context.get("fontes"):
        return

    st.markdown("### 📚 Documentos Consultados")

    with st.expander(f"Ver {len(rag_context['fontes'])} fonte(s)", expanded=False):
        for i, fonte in enumerate(rag_context['fontes'], 1):
            st.markdown(f"**{i}. {fonte['tipo_documento']}**")
            st.caption(f"Arquivo: {fonte['nome_arquivo']}")
            st.text(f"Trecho: \"{fonte['texto']}\"")
            st.markdown("---")

# Na função exibir_sidebar(), adicionar seção RAG:

def exibir_sidebar():
    """Exibe sidebar com informações contextuais."""
    with st.sidebar:
        # ... código existente ...

        # Informações contextuais por agente
        if agente_ativo == "analise_rag":
            st.subheader("📊 Análise RAG")
            st.write("""
            Sistema de análise avançada baseado em documentos usando RAG (Retrieval Augmented Generation).

            **O que posso analisar:**
            - 📄 Comprovantes de renda
            - 💳 Extratos bancários
            - 📋 Contratos e documentos
            - 🔍 Verificação de inconsistências
            - 💰 Recomendações de crédito
            """)

            # Mostra fontes se houver contexto RAG
            rag_context = estado.get("rag_context")
            if rag_context:
                exibir_fontes_rag(rag_context)

        # ... resto do código ...
```

### Passo 6.2: Adicionar Loading Indicator

```python
# Atualizar função processar_mensagem_com_feedback:

def processar_mensagem_com_feedback(mensagem: str, mostrar_validacao: bool = True):
    """Processa mensagem com feedback visual."""

    estado = st.session_state.sistema.get_estado()
    agente_ativo = estado.get("agente_ativo", "triagem")

    # ... validações ...

    # Processa com feedback visual apropriado
    try:
        # Loading message específico para RAG (mais lento)
        if agente_ativo == "analise_rag" or "analis" in mensagem.lower():
            loading_msg = "🔍 Analisando documentos e consultando base de conhecimento..."
        else:
            loading_msg = "🤖 Processando sua solicitação..."

        with st.spinner(loading_msg):
            resposta = st.session_state.sistema.processar_mensagem(mensagem)

        # ... resto do código ...
```

---

## Fase 7: Testes e Validação

### Objetivos
- Testar pipeline completo
- Validar qualidade das respostas
- Medir performance
- Identificar edge cases

### Passo 7.1: Suite de Testes RAG

**Criar: `tests/test_rag_pipeline.py`**

```python
"""
Testes para pipeline RAG.
"""

import pytest
from tools.storage_manager import StorageManager
from tools.vector_store_manager import VectorStoreManager
from tools.document_processor import DocumentProcessor
from agents.analise_credito_rag_agent import AnaliseCreditoRAGAgent


class TestRAGPipeline:
    """Testes do pipeline RAG completo."""

    @pytest.fixture
    def vector_store(self):
        """Fixture para vector store de teste."""
        return VectorStoreManager(
            store_type="chroma",
            collection_name="test_rag",
            persist_directory="./data/test_vector_store"
        )

    @pytest.fixture
    def agente_rag(self, vector_store):
        """Fixture para agente RAG."""
        return AnaliseCreditoRAGAgent(vector_store)

    def test_document_loading(self):
        """Testa carregamento de documentos."""
        processor = DocumentProcessor(storage_provider="s3")

        # Testa com cliente de teste
        chunks = processor.process_client_documents("12345678901")

        assert len(chunks) > 0, "Deve carregar ao menos um documento"
        assert chunks[0].metadata["cpf"] == "12345678901"

    def test_vector_store_indexing(self, vector_store):
        """Testa indexação no vector store."""
        from tools.vector_store_manager import create_document_from_text

        doc = create_document_from_text(
            "Cliente possui renda mensal de R$ 10.000,00",
            {"cpf": "99999999999", "tipo": "teste"}
        )

        ids = vector_store.add_documents([doc])

        assert len(ids) == 1

        # Testa busca
        results = vector_store.similarity_search("qual a renda do cliente?", k=1)

        assert len(results) > 0
        assert "10.000" in results[0].page_content

    def test_rag_query(self, agente_rag):
        """Testa query RAG."""
        # Supondo que já existem documentos indexados
        resultado = agente_rag.analisar_documentos_cliente(
            cpf="12345678901",
            pergunta="Qual a renda do cliente?"
        )

        assert "resposta" in resultado
        assert "fontes" in resultado
        assert resultado["num_documentos"] >= 0

    def test_limite_recommendation(self, agente_rag):
        """Testa recomendação de limite."""
        resultado = agente_rag.recomendar_limite(
            cpf="12345678901",
            score_atual=750
        )

        assert "resposta" in resultado
        assert len(resultado["resposta"]) > 50  # Resposta substantiva

    def test_inconsistency_check(self, agente_rag):
        """Testa verificação de inconsistências."""
        resultado = agente_rag.verificar_inconsistencias("12345678901")

        assert "resposta" in resultado
        # Deve mencionar se encontrou ou não inconsistências
        assert any(word in resultado["resposta"].lower()
                  for word in ["inconsistência", "consistente", "discrepância"])


# Testes de Performance

def test_query_latency(agente_rag):
    """Mede latência de queries RAG."""
    import time

    start = time.time()
    resultado = agente_rag.analisar_documentos_cliente(
        "12345678901",
        "Qual a situação financeira?"
    )
    latency = time.time() - start

    print(f"\n⏱️ Latência da query: {latency:.2f}s")

    # Assert de performance (ajustar conforme necessário)
    assert latency < 10.0, "Query RAG deve completar em menos de 10s"


def test_chunk_relevance():
    """Avalia relevância dos chunks recuperados."""
    from tools.vector_store_manager import VectorStoreManager

    vs = VectorStoreManager()

    results = vs.similarity_search_with_score(
        "comprovante de renda do cliente",
        k=5
    )

    # Primeiro resultado deve ter score alto (similaridade)
    if results:
        best_score = results[0][1]
        print(f"\n🎯 Melhor score de similaridade: {best_score:.4f}")

        # Em Chroma, scores mais baixos = mais similar
        # Ajustar threshold conforme seu vector store
        assert best_score < 1.5, "Primeiro resultado deve ser relevante"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
```

### Passo 7.2: Script de Validação Manual

**Criar: `scripts/validate_rag.py`**

```python
"""
Script interativo para validar respostas RAG.
"""

from tools.vector_store_manager import VectorStoreManager
from agents.analise_credito_rag_agent import AnaliseCreditoRAGAgent
from tools.data_manager import DataManager

def validar_rag_interativo():
    """Validação interativa do sistema RAG."""
    print("=" * 70)
    print("VALIDAÇÃO INTERATIVA DO SISTEMA RAG - BANCO ÁGIL")
    print("=" * 70)

    # Inicializa componentes
    print("\n🔧 Inicializando sistema RAG...")
    vector_store = VectorStoreManager()
    agente_rag = AnaliseCreditoRAGAgent(vector_store)
    data_manager = DataManager()

    print("✅ Sistema pronto!\n")

    # Lista clientes disponíveis
    print("📋 Clientes com documentos indexados:")
    print("  1. CPF: 12345678901 - João Silva")
    print("  2. CPF: 98765432100 - Maria Santos")
    print("  3. CPF: 55555555555 - Pedro Oliveira")

    # Loop interativo
    while True:
        print("\n" + "-" * 70)
        cpf = input("\n🔑 Digite o CPF do cliente (ou 'sair' para encerrar): ").strip()

        if cpf.lower() == 'sair':
            break

        # Valida CPF
        cliente = data_manager.get_client_by_cpf(cpf)
        if not cliente:
            print("❌ Cliente não encontrado. Tente novamente.")
            continue

        print(f"\n✅ Cliente: {cliente['nome']} (Score: {cliente['score_credito']})")

        # Menu de análises
        print("\n📊 Escolha o tipo de análise:")
        print("  1. Recomendação de Limite")
        print("  2. Verificar Inconsistências")
        print("  3. Resumo da Situação Financeira")
        print("  4. Pergunta Personalizada")

        opcao = input("\nOpção: ").strip()

        print("\n🔍 Analisando documentos...")

        if opcao == "1":
            resultado = agente_rag.recomendar_limite(cpf, cliente['score_credito'])
        elif opcao == "2":
            resultado = agente_rag.verificar_inconsistencias(cpf)
        elif opcao == "3":
            resultado = agente_rag.resumir_situacao_financeira(cpf)
        elif opcao == "4":
            pergunta = input("\n❓ Digite sua pergunta: ").strip()
            resultado = agente_rag.analisar_documentos_cliente(cpf, pergunta)
        else:
            print("Opção inválida.")
            continue

        # Exibe resultado
        print("\n" + "=" * 70)
        print("📄 RESPOSTA")
        print("=" * 70)
        print(resultado["resposta"])

        if resultado["fontes"]:
            print(f"\n📚 FONTES ({resultado['num_documentos']} documentos):")
            for i, fonte in enumerate(resultado["fontes"], 1):
                print(f"\n  {i}. {fonte['tipo_documento']} - {fonte['nome_arquivo']}")
                print(f"     Trecho: \"{fonte['texto'][:150]}...\"")

        # Avaliação opcional
        print("\n" + "=" * 70)
        avaliacao = input("\n⭐ Avalie a resposta (1-5 estrelas) ou Enter para pular: ").strip()

        if avaliacao:
            comentario = input("💬 Comentário (opcional): ").strip()
            print(f"✅ Avaliação registrada: {avaliacao} estrelas")
            if comentario:
                print(f"   Comentário: {comentario}")

    print("\n👋 Validação encerrada. Obrigado!")


if __name__ == "__main__":
    validar_rag_interativo()
```

---

## Fase 8: Otimização e Produção

### Objetivos
- Otimizar performance de queries
- Implementar caching
- Monitorar custos
- Preparar para escala

### Passo 8.1: Implementar Caching

**Criar: `tools/rag_cache.py`**

```python
"""
Sistema de cache para queries RAG.
Reduz custos e melhora latência.
"""

import hashlib
import json
import time
from typing import Optional, Dict, Any
from functools import wraps
from pathlib import Path


class RAGCache:
    """Cache em disco para respostas RAG."""

    def __init__(self, cache_dir: str = "./data/rag_cache", ttl: int = 86400):
        """
        Inicializa cache.

        Args:
            cache_dir: Diretório para armazenar cache
            ttl: Time to live em segundos (padrão: 24h)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl

    def _get_cache_key(self, cpf: str, query: str) -> str:
        """Gera chave de cache."""
        content = f"{cpf}:{query}".encode()
        return hashlib.md5(content).hexdigest()

    def get(self, cpf: str, query: str) -> Optional[Dict[str, Any]]:
        """
        Busca no cache.

        Returns:
            Resultado cacheado ou None se não encontrado/expirado
        """
        key = self._get_cache_key(cpf, query)
        cache_file = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            return None

        # Verifica expiração
        age = time.time() - cache_file.stat().st_mtime
        if age > self.ttl:
            cache_file.unlink()  # Remove cache expirado
            return None

        # Carrega cache
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def set(self, cpf: str, query: str, result: Dict[str, Any]):
        """Salva no cache."""
        key = self._get_cache_key(cpf, query)
        cache_file = self.cache_dir / f"{key}.json"

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    def clear(self, cpf: Optional[str] = None):
        """
        Limpa cache.

        Args:
            cpf: Se fornecido, limpa apenas cache deste CPF
        """
        if cpf:
            # Remove apenas caches que começam com hash do CPF
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                        if data.get("cpf") == cpf:
                            cache_file.unlink()
                except:
                    pass
        else:
            # Limpa todo o cache
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()


def cached_rag_query(cache: RAGCache):
    """
    Decorator para cachear queries RAG.

    Usage:
        @cached_rag_query(cache_instance)
        def analisar_documentos(cpf, pergunta):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(cpf: str, pergunta: str, *args, **kwargs):
            # Tenta buscar no cache
            cached_result = cache.get(cpf, pergunta)
            if cached_result:
                cached_result['_from_cache'] = True
                return cached_result

            # Executa função
            result = func(cpf, pergunta, *args, **kwargs)

            # Salva no cache
            cache.set(cpf, pergunta, result)
            result['_from_cache'] = False

            return result

        return wrapper
    return decorator


# Integração com AnaliseCreditoRAGAgent

def add_cache_to_agent(agente: 'AnaliseCreditoRAGAgent', cache: RAGCache):
    """
    Adiciona caching a um agente RAG existente.

    Args:
        agente: Instância do AnaliseCreditoRAGAgent
        cache: Instância do RAGCache
    """
    # Wrap método principal com cache
    original_method = agente.analisar_documentos_cliente

    @cached_rag_query(cache)
    def cached_method(cpf: str, pergunta: str):
        return original_method(cpf, pergunta)

    agente.analisar_documentos_cliente = cached_method
```

### Passo 8.2: Monitoramento de Custos

**Criar: `tools/cost_monitor.py`**

```python
"""
Monitor de custos para APIs e embeddings.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict


class CostMonitor:
    """Monitora custos de operações RAG."""

    # Custos aproximados (atualizar conforme provedor)
    COSTS = {
        "openai_embedding": 0.00013 / 1000,  # por 1k tokens
        "groq_llm": 0.0,  # Groq é grátis (por enquanto)
        "pinecone_read": 0.000002,  # por query
        "pinecone_write": 0.000004,  # por vector
    }

    def __init__(self, log_file: str = "./data/cost_log.json"):
        """Inicializa monitor."""
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Carrega log existente
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                self.log = json.load(f)
        else:
            self.log = {
                "total_cost": 0.0,
                "operations": []
            }

    def log_operation(
        self,
        operation_type: str,
        quantity: int,
        metadata: Dict = None
    ):
        """
        Registra operação e calcula custo.

        Args:
            operation_type: Tipo da operação (chave em COSTS)
            quantity: Quantidade (tokens, vectors, queries, etc.)
            metadata: Informações adicionais
        """
        cost = self.COSTS.get(operation_type, 0) * quantity

        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation_type,
            "quantity": quantity,
            "cost": cost,
            "metadata": metadata or {}
        }

        self.log["operations"].append(entry)
        self.log["total_cost"] += cost

        # Salva log
        with open(self.log_file, 'w') as f:
            json.dump(self.log, f, indent=2)

    def get_total_cost(self) -> float:
        """Retorna custo total acumulado."""
        return self.log["total_cost"]

    def get_cost_by_period(self, days: int = 30) -> float:
        """Retorna custo dos últimos N dias."""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)

        cost = sum(
            op["cost"]
            for op in self.log["operations"]
            if datetime.fromisoformat(op["timestamp"]) > cutoff
        )

        return cost

    def generate_report(self) -> str:
        """Gera relatório de custos."""
        report = f"""
📊 RELATÓRIO DE CUSTOS RAG - BANCO ÁGIL
{'=' * 60}

💰 Custo Total Acumulado: R$ {self.log['total_cost']:.4f}

📈 Custos por Período:
  - Últimos 7 dias:  R$ {self.get_cost_by_period(7):.4f}
  - Últimos 30 dias: R$ {self.get_cost_by_period(30):.4f}

🔢 Operações Registradas: {len(self.log['operations'])}

💡 Economia Estimada com Groq: ~R$ 50.00/mês
   (vs GPT-4 para LLM calls)
"""
        return report


# Integração com pipeline RAG

def wrap_with_cost_monitoring(func, monitor: CostMonitor, operation_type: str):
    """Wrapper para adicionar monitoramento de custos."""
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        # Estima quantidade (ajustar conforme necessário)
        if operation_type == "openai_embedding":
            # Estima tokens (rough)
            quantity = len(str(result)) // 4
        elif "pinecone" in operation_type:
            quantity = 1  # 1 query ou write
        else:
            quantity = 1

        monitor.log_operation(operation_type, quantity)

        return result

    return wrapper
```

### Passo 8.3: Dashboard de Monitoramento

**Criar: `scripts/monitoring_dashboard.py`**

```python
"""
Dashboard simples de monitoramento RAG.
"""

import streamlit as st
from tools.cost_monitor import CostMonitor
from tools.vector_store_manager import VectorStoreManager
from pathlib import Path
import json

def show_monitoring_dashboard():
    """Exibe dashboard de monitoramento."""
    st.set_page_config(
        page_title="Monitor RAG - Banco Ágil",
        page_icon="📊",
        layout="wide"
    )

    st.title("📊 Painel de Monitoramento RAG")

    # Custos
    st.header("💰 Custos")

    monitor = CostMonitor()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Custo Total", f"R$ {monitor.get_total_cost():.4f}")

    with col2:
        st.metric("Últimos 7 dias", f"R$ {monitor.get_cost_by_period(7):.4f}")

    with col3:
        st.metric("Últimos 30 dias", f"R$ {monitor.get_cost_by_period(30):.4f}")

    with st.expander("Ver Relatório Completo"):
        st.text(monitor.generate_report())

    # Vector Store Stats
    st.header("🗄️ Vector Store")

    try:
        vs = VectorStoreManager()
        stats = vs.get_collection_stats()

        st.json(stats)
    except Exception as e:
        st.error(f"Erro ao carregar stats: {e}")

    # Cache Stats
    st.header("⚡ Cache")

    cache_dir = Path("./data/rag_cache")
    if cache_dir.exists():
        cache_files = list(cache_dir.glob("*.json"))

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Entradas no Cache", len(cache_files))

        with col2:
            total_size = sum(f.stat().st_size for f in cache_files)
            st.metric("Tamanho Total", f"{total_size / 1024:.2f} KB")

        if st.button("🗑️ Limpar Cache"):
            for f in cache_files:
                f.unlink()
            st.success("Cache limpo!")
            st.rerun()
    else:
        st.info("Nenhum cache encontrado")

    # Últimas Operações
    st.header("📜 Últimas Operações")

    if monitor.log["operations"]:
        import pandas as pd

        df = pd.DataFrame(monitor.log["operations"][-20:])  # Últimas 20
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhuma operação registrada")


if __name__ == "__main__":
    show_monitoring_dashboard()
```

---

## Estimativas de Custo

### Custos Mensais Estimados

#### Configuração Econômica (Desenvolvimento)
| Componente | Opção | Custo/mês |
|------------|-------|-----------|
| Storage | AWS S3 (5GB free tier) | R$ 0,00 |
| Vector Store | Chroma (local) | R$ 0,00 |
| Embeddings | Hugging Face (local) | R$ 0,00 |
| LLM | Groq (gratuito) | R$ 0,00 |
| **TOTAL** | | **R$ 0,00** |

#### Configuração Produção (Escalável)
| Componente | Opção | Custo/mês |
|------------|-------|-----------|
| Storage | AWS S3 (50GB + transferências) | R$ 5,00 |
| Vector Store | Pinecone (1 índice, 100k vectors) | R$ 350,00 |
| Embeddings | OpenAI (1M tokens/mês) | R$ 0,65 |
| LLM | GPT-4 Turbo (500k tokens/mês) | R$ 75,00 |
| Infraestrutura | EC2 t3.medium | R$ 150,00 |
| **TOTAL** | | **~R$ 580,00** |

#### Configuração Híbrida (Recomendada)
| Componente | Opção | Custo/mês |
|------------|-------|-----------|
| Storage | AWS S3 (20GB) | R$ 2,00 |
| Vector Store | Qdrant (self-hosted) | R$ 0,00 |
| Embeddings | Hugging Face | R$ 0,00 |
| LLM | Groq + GPT-4 (fallback) | R$ 20,00 |
| Infraestrutura | Cloud Run (serverless) | R$ 50,00 |
| **TOTAL** | | **~R$ 72,00** |

---

## Cronograma Sugerido

### Sprint 1 (1-2 semanas): Infraestrutura
- [ ] Configurar AWS S3 ou Azure Blob
- [ ] Implementar StorageManager
- [ ] Fazer upload de documentos de teste
- [ ] Validar acesso e permissões

### Sprint 2 (1-2 semanas): Vector Store
- [ ] Escolher e configurar vector store
- [ ] Implementar VectorStoreManager
- [ ] Testar indexação e busca
- [ ] Validar qualidade dos embeddings

### Sprint 3 (2-3 semanas): Pipeline de Processamento
- [ ] Implementar document loaders
- [ ] Configurar chunking strategy
- [ ] Criar pipeline de indexação
- [ ] Indexar documentos de teste
- [ ] Validar retrieval quality

### Sprint 4 (2 semanas): Agente RAG
- [ ] Criar AnaliseCreditoRAGAgent
- [ ] Implementar ferramentas RAG
- [ ] Criar prompts otimizados
- [ ] Testar análises e recomendações

### Sprint 5 (1-2 semanas): Integração LangGraph
- [ ] Adicionar nó RAG ao grafo
- [ ] Criar transições
- [ ] Atualizar estado conversacional
- [ ] Testar fluxo completo

### Sprint 6 (1 semana): Interface
- [ ] Atualizar Streamlit UI
- [ ] Adicionar botões RAG
- [ ] Exibir fontes
- [ ] Implementar loading indicators

### Sprint 7 (1 semana): Testes e Otimização
- [ ] Executar suite de testes
- [ ] Validar respostas manualmente
- [ ] Implementar caching
- [ ] Otimizar performance

### Sprint 8 (1 semana): Produção
- [ ] Configurar monitoramento
- [ ] Deploy em ambiente staging
- [ ] Testes de carga
- [ ] Go-live

**Total estimado: 10-14 semanas (2,5 - 3,5 meses)**

---

## Troubleshooting e Boas Práticas

### Problemas Comuns

#### 1. "Vector store vazio" / "Nenhum documento encontrado"
**Causa**: Documentos não foram indexados
**Solução**:
```bash
python scripts/index_documents.py --all
```

#### 2. "Respostas genéricas" / "LLM não usa documentos"
**Causa**: Retrieval retornando docs irrelevantes
**Solução**:
- Melhorar chunking (reduzir chunk_size)
- Ajustar k (número de documentos recuperados)
- Usar reranker para melhor relevância

#### 3. "Queries muito lentas" (>10s)
**Causa**: Vector store ou LLM lento
**Solução**:
- Implementar caching
- Usar índice otimizado (HNSW no Pinecone/Qdrant)
- Reduzir número de documentos recuperados (k)

#### 4. "Custos altos de embedding"
**Causa**: Re-embedding de documentos existentes
**Solução**:
- Implementar incremental indexing
- Cachear embeddings
- Usar modelo local (Hugging Face)

#### 5. "Fontes incorretas citadas"
**Causa**: Metadata mal configurada
**Solução**:
- Garantir que todo Document tem metadata correto
- Validar metadata no momento da indexação

### Boas Práticas

#### Chunking
✅ **DO**:
- Use chunk_size = 800-1200 para documentos gerais
- Overlap de 100-200 caracteres
- Preserve parágrafos completos
- Adicione contexto no metadata

❌ **DON'T**:
- Chunks muito pequenos (<300 chars) perdem contexto
- Chunks muito grandes (>2000 chars) diluem relevância
- Quebrar no meio de sentenças

#### Prompts RAG
✅ **DO**:
- Instrua o LLM a citar fontes
- Peça para não inventar informações
- Forneça exemplos de respostas boas
- Use few-shot examples

❌ **DON'T**:
- Prompts vagos ("analise o cliente")
- Pedir informações não presentes nos docs
- Confiar cegamente na resposta

#### Metadata
✅ **DO**:
- Inclua: cpf, tipo_documento, data, nome_arquivo
- Use para filtros (buscar apenas extratos, por exemplo)
- Adicione informações de proveniência

❌ **DON'T**:
- Metadata excessivo (>10 campos)
- Informações sensíveis em plain text
- Metadata inconsistente entre documentos

#### Performance
✅ **DO**:
- Implemente caching agressivo
- Use índices otimizados (HNSW, IVF)
- Batch operations quando possível
- Monitor latências

❌ **DON'T**:
- Re-indexar desnecessariamente
- Fazer queries sem filtros em bases grandes
- Ignorar custos de embedding

---

## Próximos Passos

Após implementação completa, considere:

1. **Hybrid Search**: Combine busca semântica (vectors) com keyword search (BM25)
2. **Reranking**: Use modelo dedicado para reordenar resultados
3. **Multi-modal**: Adicione suporte a imagens (extrair texto de comprovantes escaneados)
4. **Feedback Loop**: Implemente sistema de feedback para melhorar retrieval
5. **A/B Testing**: Compare RAG vs não-RAG para métricas de negócio
6. **Auto-indexação**: Trigger automático quando novo documento é upado
7. **Multilingual**: Suporte para documentos em outros idiomas

---

## Recursos Adicionais

### Documentação
- [LangChain RAG Tutorial](https://python.langchain.com/docs/use_cases/question_answering/)
- [Pinecone Documentation](https://docs.pinecone.io/)
- [Chroma Documentation](https://docs.trychroma.com/)
- [AWS S3 Python SDK (boto3)](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)

### Artigos Recomendados
- "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (Paper original)
- "Advanced RAG Techniques" - LlamaIndex Blog
- "Chunking Strategies for RAG" - Pinecone

### Comunidades
- LangChain Discord
- r/MachineLearning (Reddit)
- Hugging Face Forums

---

## Conclusão

Este plano fornece um roteiro completo para adicionar capacidades RAG ao sistema Banco Ágil. A implementação permitirá:

✅ Análise de crédito baseada em documentos reais
✅ Decisões mais informadas e justificadas
✅ Escalabilidade para milhares de documentos
✅ Rastreabilidade e compliance
✅ Melhor experiência do usuário com respostas contextualizadas

**Recomendação**: Comece com a configuração econômica (Chroma + Hugging Face + Groq) para desenvolvimento e MVP. Escale para Pinecone + OpenAI apenas quando necessário.

Boa implementação! 🚀
