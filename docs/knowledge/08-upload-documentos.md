# Upload de Documentos

## Visão Geral

O sistema de upload do DR AI Workforce suporta múltiplos formatos e possui **4 fluxos de armazenamento distintos**, otimizados para diferentes tipos de conteúdo. Todo arquivo uploaded é associado ao projeto ativo e pode ser utilizado pelo Guru (chat RAG) e pela geração de documentos por IA.

---

## Formatos Suportados

| Formato | Extensão | Tipo de Armazenamento |
|---|---|---|
| Texto simples | `.txt` | Banco de dados (texto) |
| Markdown | `.md` | Banco de dados (texto) |
| PDF | `.pdf` | S3 + Banco de dados (dual) |
| Documentos Office | `.docx`, `.xlsx` | S3 (binário) |
| Imagens | `.png`, `.jpg`, `.svg` | S3 (binário) |
| Outros arquivos | diversos | S3 (binário) |

---

## Os 4 Fluxos de Armazenamento

### Fluxo 1: Armazenamento Binário (S3)

Para arquivos que não são texto puro (imagens, Office, etc.).

```
Arquivo (binário)
    │
    ▼
Upload para Supabase Storage (S3)
    │
    ├─▶ URL pública/assinada gerada
    ├─▶ Metadados salvos no banco (nome, tipo, tamanho, URL)
    └─▶ Referência vinculada ao projeto
```

**Quando usar**: Imagens, documentos Office, arquivos compactados.

---

### Fluxo 2: Armazenamento de Texto (Banco de Dados)

Para arquivos de texto puro que precisam ser pesquisáveis.

```
Arquivo (.txt, .md)
    │
    ▼
Leitura do conteúdo
    │
    ├─▶ Conteúdo salvo diretamente no banco de dados
    ├─▶ Texto indexado para busca
    └─▶ Disponível para o Guru (RAG)
```

**Quando usar**: Arquivos de texto, markdown, transcrições.

---

### Fluxo 3: Armazenamento Dual — PDF

PDFs recebem tratamento especial: armazenamento duplo.

```
Arquivo PDF
    │
    ├──────────────────────────────┐
    ▼                              ▼
Extração de texto            Upload do PDF
    │                         para S3
    ▼                              │
Conteúdo salvo no           URL do arquivo
banco de dados              no S3
    │                              │
    └──────────────┬───────────────┘
                   ▼
    Referência completa no banco
    (texto extraído + URL do PDF original)
```

**Vantagens**:
- Texto pesquisável pelo Guru e pelo sistema de busca
- PDF original disponível para download
- Melhor dos dois mundos

---

### Fluxo 4: Armazenamento de Conteúdo Gerado por IA

Documentos gerados pela IA (PRDs, User Stories, etc.) são salvos automaticamente.

```
Geração por IA (Edge Function)
    │
    ▼
Conteúdo gerado (Markdown)
    │
    ├─▶ Salvo na tabela generated_documents
    ├─▶ Versionado automaticamente
    ├─▶ Vinculado à transcrição de origem (se houver)
    ├─▶ Indexado para o Guru (RAG)
    └─▶ Uso de tokens registrado em ai_interactions
```

---

## Componentes do Sistema de Upload

### Componente Principal
O upload é gerenciado por componentes React que lidam com:
- Seleção de arquivo (drag & drop e botão)
- Validação de formato e tamanho
- Barra de progresso
- Tratamento de erros
- Preview do arquivo (quando aplicável)

### Validações
| Validação | Regra |
|---|---|
| Formato | Apenas extensões permitidas |
| Tamanho | Limite configurável por tipo |
| Conteúdo | Verificação básica de integridade |
| Projeto | Obrigatório ter projeto selecionado |

---

## Processamento Pós-Upload

Após o upload, o sistema pode executar ações automáticas:

### 1. Indexação para RAG
- Documentos de texto são divididos em chunks
- Embeddings são gerados via OpenAI
- Chunks são armazenados no pgvector
- O documento fica pesquisável pelo Guru

### 2. Extração de Texto (PDF)
- Texto é extraído do PDF
- Salvo no banco de dados para busca
- PDF original preservado no S3

### 3. Geração de Thumbnails
- Para imagens e PDFs
- Thumbnails são gerados para preview na interface

---

## Gestão de Documentos

### Visualização
- **Lista**: Todos os documentos do projeto com filtros
- **Grid**: Visualização em cards com thumbnails
- **Detalhes**: Informações completas, preview, download

### Operações
- **Download**: Baixar o arquivo original
- **Visualizar**: Preview no navegador (quando suportado)
- **Deletar**: Remover documento (com confirmação)
- **Tags**: Categorizar com tags personalizadas
- **Associar**: Vincular a transcrições ou tarefas

### Permissões
- Apenas membros do projeto podem fazer upload
- Admin pode deletar qualquer documento
- Membros podem gerenciar seus próprios uploads

---

## Estrutura no Banco de Dados

### Tabela `project_knowledge_base`

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | Identificador único |
| `project_id` | UUID | Projeto vinculado |
| `title` | text | Título do documento |
| `content` | text | Conteúdo textual (se aplicável) |
| `file_url` | text | URL do arquivo no S3 |
| `file_type` | text | Tipo do arquivo |
| `file_size` | bigint | Tamanho em bytes |
| `source` | text | Origem (upload, ai_generation) |
| `tags` | text[] | Tags de categorização |
| `created_at` | timestamp | Data de upload |
| `updated_at` | timestamp | Última atualização |

---

## Fluxo de Upload — Visão do Usuário

```
1. Clica em "Upload" ou arrasta arquivo
       │
       ▼
2. Sistema valida formato e tamanho
       │
       ▼
3. Barra de progresso exibida
       │
       ▼
4. Upload concluído
       │
       ├─▶ Se texto: indexado automaticamente
       ├─▶ Se PDF: texto extraído + arquivo salvo
       └─▶ Se binário: salvo no S3
       │
       ▼
5. Documento aparece na listagem
       │
       ▼
6. Disponível para Guru e geração de documentos
```

---

## Boas Práticas

1. **Nomenclatura**: Use nomes descritivos para os arquivos
2. **Tags**: Adicione tags relevantes para facilitar a busca
3. **Formato**: Prefira PDF ou Markdown para melhor indexação
4. **Tamanho**: Mantenha arquivos dentro dos limites para melhor performance
5. **Revisão**: Revise o conteúdo após upload para garantir que a extração de texto ficou correta
