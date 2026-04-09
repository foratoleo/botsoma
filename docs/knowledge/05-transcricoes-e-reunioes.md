# Transcrições e Reuniões

## Visão Geral

O sistema de transcrições permite capturar, armazenar e processar o conteúdo de reuniões. A partir dessas transcrições, a IA pode gerar documentação estruturada automaticamente.

---

## Fluxo Completo

```
1. Gravar/Upload da Reunião
       │
       ▼
2. Transcrição Processada
       │
       ▼
3. Visualização e Edição
       │
       ▼
4. Geração de Documentos por IA
   ├─ PRD
   ├─ User Stories
   ├─ Notas de Reunião
   ├─ Especificações Técnicas
   └─ Casos de Teste
       │
       ▼
5. Documentos Salvos e Versionados
```

---

## Integração com Microsoft Calendar

O sistema integra-se ao **Microsoft Calendar** para capturar informações de reuniões agendadas:

### Como funciona:
1. O usuário conecta sua conta Microsoft
2. Reuniões são sincronizadas automaticamente
3. O sistema utiliza **Recall.ai** para gravar as reuniões
4. A gravação é transcrita automaticamente
5. A transcrição fica disponível na plataforma

### Recall.ai
- Serviço de gravação e transcrição automatizada de reuniões
- Integra-se com as principais plataformas de videoconferência
- Fornece transcrições com identificação de falantes

---

## Upload de Transcrições

Além da gravação automática, o usuário pode fazer **upload manual** de transcrições:

### Formatos aceitos:
- Arquivos de texto (.txt)
- Arquivos de transcrição de ferramentas externas

### Processo:
1. Acesse a área de **Transcrições** (Planejamento)
2. Clique em **"Upload"**
3. Selecione o arquivo de transcrição
4. Informe dados complementares (título, data, participantes)
5. Confirme o upload

---

## Visualização de Transcrições

### Lista de Transcrições
- Visualização em lista com filtros e busca
- Filtros por data, projeto, status de processamento
- Indicadores de documentos gerados a partir de cada transcrição

### Detalhes da Transcrição
- Conteúdo completo da transcrição
- Informações de participantes e data
- Lista de documentos gerados a partir dela
- Opção de gerar novos documentos
- Histórico de ações

---

## Geração de Documentos a partir de Transcrições

A partir de uma transcrição, o usuário pode gerar múltiplos documentos:

### Tipos disponíveis:
| Documento | Descrição |
|---|---|
| **PRD** | Product Requirements Document — requisitos do produto |
| **User Stories** | Histórias de usuário com critérios de aceitação |
| **Notas de Reunião** | Resumo estruturado da reunião |
| **Especificações Técnicas** | Detalhes de implementação técnica |
| **Casos de Teste** | Cenários de teste e validação |

### Processo:
1. Selecione a transcrição
2. Escolha o tipo de documento (ou múltiplos)
3. Opcionalmente, customize o prompt
4. Clique em **"Gerar"**
5. A IA processa e gera o documento
6. O documento é salvo e versionado automaticamente

### Sistema de Conversação Contínua
Usando a **OpenAI Responses API**, o sistema mantém o contexto entre gerações:
- Gerar um PRD e depois User Stories na mesma sessão
- A IA "lembra" do conteúdo anterior
- Redução de 71-75% no uso de tokens

---

## Estrutura no Banco de Dados

### Tabela `meeting_transcripts`

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | Identificador único |
| `project_id` | UUID | Projeto vinculado |
| `title` | text | Título da reunião |
| `content` | text | Conteúdo da transcrição |
| `meeting_date` | timestamp | Data da reunião |
| `participants` | jsonb | Lista de participantes |
| `source` | text | Origem (upload, recall, manual) |
| `status` | text | Status do processamento |
| `created_at` | timestamp | Data de criação |

### Relacionamentos:
- Uma transcrição pode gerar **múltiplos documentos** (`generated_documents`)
- Uma transcrição pertence a **um projeto** (`projects`)
- Cada geração é rastreada em `ai_interactions` (uso de tokens e custo)

---

## Análise de Transcrições (Edge Function)

A Edge Function `analyze-transcript` permite análise avançada de transcrições:

- Extrair pontos-chave
- Identificar decisões tomadas
- Listar action items
- Identificar riscos mencionados
- Resumir automaticamente

---

## Boas Práticas

1. **Nomenclatura**: Use títulos descritivos para as transcrições
2. **Revisão**: Sempre revise a transcrição antes de gerar documentos
3. **Contexto**: Quanto mais contexto na transcrição, melhores os documentos gerados
4. **Múltiplos documentos**: Aproveite o sistema de conversação para gerar vários documentos de uma vez
5. **Versionamento**: Documentos são versionados — não tenha medo de gerar novamente
