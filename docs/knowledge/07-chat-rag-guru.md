# Chat RAG — Guru

## Visão Geral

O **Guru** é o assistente inteligente do DR AI Workforce. Ele utiliza uma arquitetura **RAG (Retrieval-Augmented Generation)** para responder perguntas dos usuários com base nos documentos do projeto. Em vez de confiar apenas no conhecimento geral da IA, o Guru busca informações relevantes nos documentos carregados e gerados, fornecendo respostas contextualizadas e com referências.

---

## O que é RAG?

**RAG** = Retrieval-Augmented Generation

É uma técnica que combina:
1. **Retrieval (Busca)**: Encontra documentos relevantes para a pergunta
2. **Augmented (Aumento)**: Adiciona esses documentos ao contexto da IA
3. **Generation (Geração)**: A IA gera uma resposta fundamentada nos documentos

### Vantagens:
- Respostas baseadas em **dados reais do projeto**
- Sem "alucinações" — tudo é fundamentado em documentos
- **Referências** indicam de onde a informação veio
- Atualização automática quando novos documentos são adicionados

---

## Arquitetura do Sistema

### Fluxo Completo:
```
Pergunta do Usuário
       │
       ▼
┌──────────────────┐
│ 1. Processamento  │
│    da Pergunta    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 2. Geração de    │
│    Embedding     │
│    (OpenAI)      │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────┐
│ 3. Busca Híbrida (pgvector)      │
│    ├─ Busca Semântica (vetores)  │
│    └─ Busca Textual (palavras)   │
│    → Combina resultados          │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────┐
│ 4. Construção do │
│    Contexto      │
│    (documentos   │
│     relevantes)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 5. Geração de    │
│    Resposta      │
│    (GPT-4o)      │
└────────┬─────────┘
         │
         ▼
Resposta com Referências
```

---

## Sistema de Indexação

### Como os documentos são indexados:

1. **Chunking**: Documentos são divididos em trechos (chunks) menores
2. **Embedding**: Cada chunk é convertido em um vetor numérico via OpenAI
3. **Armazenamento**: Vetores são salvos no PostgreSQL com pgvector
4. **Metadados**: Cada chunk mantém referência ao documento original

### Estratégia de Chunking:
- Documentos são divididos respeitando parágrafos/seções
- Tamanho otimizado para equilibrar contexto e precisão
- Overlap entre chunks para não perder contexto entre divisões

### Tabela de Embeddings:
| Campo | Descrição |
|---|---|
| `id` | Identificador único |
| `content` | Texto do chunk |
| `embedding` | Vetor numérico (dimensionalidade da OpenAI) |
| `document_id` | Referência ao documento original |
| `chunk_index` | Posição do chunk no documento |
| `metadata` | Metadados adicionais (tipo, projeto, etc.) |

---

## Busca Híbrida

O Guru utiliza **busca híbrida** combinando dois métodos:

### 1. Busca Semântica (Vector Search)
- Converte a pergunta em embedding
- Busca chunks com vetores mais similares (cosine similarity)
- Entende o **significado** da pergunta, não apenas palavras-chave

### 2. Busca Textual (Full-Text Search)
- Busca por palavras-chave e termos exatos
- Usa índices de texto completo do PostgreSQL
- Útil para nomes específicos, códigos, termos técnicos

### Combinação:
Os resultados dos dois métodos são combinados com pesos configuráveis, garantindo que tanto a semântica quanto termos exatos sejam considerados.

---

## Conversas

### Estrutura:
- Cada conversa tem um **título** e um **histórico** de mensagens
- As conversas são persistidas no banco de dados
- O histórico completo é enviado como contexto para cada nova pergunta
- O usuário pode ter múltiplas conversas em paralelo

### Funcionalidades:
- **Criar nova conversa**: Iniciar um novo tópico
- **Continuar conversa**: Retomar de onde parou
- **Histórico**: Ver todas as conversas anteriores
- **Deletar**: Remover conversas antigas

### Segurança:
- Conversas são isoladas por projeto (`project_id`)
- Apenas membros do projeto podem acessar as conversas
- Dados não são compartilhados entre projetos

---

## Referências nas Respostas

Cada resposta do Guru inclui:
- **Fonte**: Qual documento foi usado
- **Trecho**: Parte relevante do documento original
- **Link**: Possibilidade de navegar ao documento completo

Isso permite ao usuário:
- Verificar a fonte da informação
- Navegar ao documento original para mais contexto
- Confiar na resposta sabendo de onde veio

---

## Acesso ao Guru

O Guru está disponível:
- No **rodapé da sidebar** (ícone de chat)
- Como **modal/painel** que abre sobre o conteúdo atual
- Pode ser acessado de **qualquer página** da aplicação

---

## Boas Práticas

### Para melhores resultados:

1. **Seja específico**: "Quais são os requisitos de autenticação do módulo X?" é melhor que "Fale sobre autenticação"

2. **Use contexto do projeto**: O Guru já filtra pelo projeto ativo, então pergunte sobre o contexto atual

3. **Documente bem**: Quanto mais documentos bem escritos no projeto, melhores as respostas

4. **Faça upload de documentos**: Documentos de referência, PRDs, especificações — tudo é indexado

5. **Revise as referências**: Sempre verifique as fontes indicadas pelo Guru

### Limitações:
- O Guru só responde com base nos documentos do projeto
- Se não houver documentos relevantes, ele indicará que não encontrou informação
- Respostas são geradas por IA e podem conter imprecisões — sempre verifique as fontes
- O histórico da conversa é limitado para controle de tokens

---

## Infraestrutura Técnica

### Componentes:
| Componente | Tecnologia | Função |
|---|---|---|
| Embeddings | OpenAI (text-embedding) | Converter texto em vetores |
| Armazenamento | PostgreSQL + pgvector | Armazenar e buscar vetores |
| Geração | OpenAI GPT-4o | Gerar respostas |
| Chunking | Custom logic | Dividir documentos em trechos |
| Busca | Hybrid (vector + FTS) | Encontrar documentos relevantes |

### Performance:
- Embeddings são gerados no momento do upload do documento
- Busca é otimizada por índices pgvector (IVFFlat ou HNSW)
- Contexto é limitado para manter resposta rápida
- Cache de conversas para evitar reprocessamento
