# Geração de Documentos com IA

## Visão Geral

O DR AI Workforce utiliza a **OpenAI API** (GPT-4o e GPT-4o-mini) para gerar documentação técnica e funcional automaticamente. O sistema é executado via **Edge Functions** no Supabase, garantindo segurança das chaves de API e rastreamento de custos.

---

## Arquitetura v2.0 (Edge Functions)

### Fluxo de Geração:
```
Usuário (Frontend)
    │
    ▼
generateDocumentAPI()  ← Serviço frontend
    │
    ▼
Edge Function (Supabase/Deno)
    │
    ├─▶ OpenAI API (GPT-4o / GPT-4o-mini)
    │
    ├─▶ Salva documento em generated_documents
    │
    └─▶ Registra uso em ai_interactions
    │
    ▼
Retorna documento + response_id para o frontend
```

### Benefícios desta arquitetura:
- ✅ Chaves de API seguras no servidor (nunca expostas ao cliente)
- ✅ Rastreamento automático de tokens e custos
- ✅ Tratamento centralizado de erros
- ✅ Otimização de modelo (GPT-4o para complexo, GPT-4o-mini para simples)
- ✅ Formato de resposta consistente

---

## Tipos de Documentos

| Tipo | Edge Function | Descrição |
|---|---|---|
| **PRD** | `create-prd` | Product Requirements Document — requisitos completos do produto |
| **User Stories** | `create-user-story` | Histórias de usuário com critérios de aceitação |
| **Notas de Reunião** | `create-meeting-notes` | Resumo estruturado com decisões e action items |
| **Especificações Técnicas** | `create-technical-specs` | Detalhes de implementação técnica |
| **Casos de Teste** | `create-test-cases` | Cenários de teste e validação |
| **Testes Unitários** | `create-unit-tests` | Sugestões de testes unitários |
| **Análise de Transcrição** | `analyze-transcript` | Análise avançada de conteúdo |

---

## API de Geração de Documentos

### Uso no Frontend:
```typescript
import { generateDocumentAPI } from '@/lib/services/document-generation-service';

const result = await generateDocumentAPI(
  'user-stories',        // Tipo do documento
  transcriptContent,     // Conteúdo de entrada (transcrição/texto)
  projectId,            // ID do projeto
  meetingTranscriptId,  // ID da transcrição (opcional)
  userId                // ID do usuário (opcional)
);

if (result.success) {
  console.log('Documento gerado:', result.document);
  console.log('Response ID:', result.response_id);
}
```

### Formato de Requisição:
```typescript
interface EdgeFunctionRequest {
  content: string;                  // Conteúdo de entrada
  project_id: string;              // ID do projeto
  meeting_transcript_id?: string;  // ID da transcrição (opcional)
  user_id?: string;                // ID do usuário (opcional)
  system_prompt?: string;          // Prompt customizado (opcional)
  user_prompt?: string;            // Prompt do usuário (opcional)
  previous_response_id?: string;   // Continuidade de conversa
  model?: string;                  // Modelo override (opcional)
  temperature?: number;            // Temperatura (opcional)
  token_limit?: number;            // Limite de tokens (opcional)
}
```

### Formato de Resposta:
```typescript
interface EdgeFunctionResponse {
  success: boolean;        // Status da operação
  document?: string;       // Documento gerado (Markdown)
  response_id?: string;    // ID da resposta OpenAI (para continuidade)
  error?: string;          // Mensagem de erro (se houver)
}
```

---

## Sistema de Conversação Contínua

Usando a **OpenAI Responses API**, o sistema mantém contexto entre gerações:

### Como funciona:
1. Primeira geração recebe um `response_id`
2. Próximas gerações enviam o `previous_response_id`
3. A IA mantém o contexto da conversa anterior
4. Não é necessário reenviar todo o conteúdo

### Benefícios:
- **Redução de 71-75% no uso de tokens**
- Contexto preservado entre gerações
- Documentos mais coesos quando gerados em sequência

### Exemplo prático:
```
1. Gera PRD a partir da transcrição → response_id: "resp_abc123"
2. Gera User Stories usando previous_response_id: "resp_abc123"
   → A IA já conhece o PRD e gera stories alinhadas
3. Gera Casos de Teste usando o response_id anterior
   → A IA conhece PRD + User Stories e gera testes completos
```

---

## Templates de Prompts

Os templates ficam em `src/prompts/document-templates/` e usam sintaxe **Handlebars**:

| Template | Arquivo |
|---|---|
| PRD | `requirements.md` |
| User Stories | `user-stories.md` |
| Especificação Técnica | `technical-spec.md` |
| Planejamento de Sprint | `sprint-planning.md` |

### Características:
- Versionamento com flag `is_current_version` no banco
- Carregados pelas Edge Functions (não pelo frontend)
- Podem ser customizados por projeto

---

## Versionamento de Documentos

Documentos gerados por IA são automaticamente versionados:

- Cada geração cria uma nova versão
- A versão mais recente é marcada como atual
- Histórico completo é mantido
- O usuário pode comparar versões

---

## Rastreamento de Custos

Toda geração é registrada na tabela `ai_interactions`:

| Campo | Descrição |
|---|---|
| Tokens de entrada | Tokens usados no prompt |
| Tokens de saída | Tokens gerados na resposta |
| Modelo utilizado | GPT-4o ou GPT-4o-mini |
| Custo estimado | Baseado nos tokens e modelo |
| Response ID | Para continuidade de conversa |
| Tipo de documento | Qual documento foi gerado |

Isso permite:
- Acompanhar gastos por projeto
- Analisar eficiência de prompts
- Otimizar uso de modelos

---

## Tratamento de Erros

As Edge Functions retornam erros estruturados:

| Erro | Significado | Ação do usuário |
|---|---|---|
| `API key not configured` | Chave não configurada | Contatar admin |
| `Rate limit exceeded` | Limite de requisições | Aguardar e tentar novamente |
| `Invalid request` | Requisição inválida | Verificar dados enviados |
| Erro genérico | Falha interna | Tentar novamente |

---

## Deploy de Edge Functions

```bash
# Deploy individual
supabase functions deploy create-prd
supabase functions deploy create-user-story
supabase functions deploy create-meeting-notes
supabase functions deploy create-technical-specs
supabase functions deploy create-test-cases

# Deploy de novas funções
supabase functions deploy create-unit-tests
supabase functions deploy analyze-transcript
```

---

## Código Compartilhado

As Edge Functions compartilham infraestrutura em:
```
supabase/functions/_shared/document-generation/
├── types.ts        # Interfaces TypeScript
├── utils.ts        # Funções utilitárias
└── business-logic  # Lógica de negócio compartilhada
```

Isso garante:
- Consistência entre funções
- Manutenção centralizada
- Reutilização de lógica (retry, autenticação, tracking)
