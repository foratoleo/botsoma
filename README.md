# Botsoma - Bot de Suporte com Triagem IA para Microsoft Teams

Bot de suporte para Microsoft Teams que classifica mensagens automaticamente:

- **Erro/Problema** → escala para um humano no Teams
- **Pergunta/Informacao** → responde baseado na documentacao configurada

## Arquitetura

```
Usuario Teams
     |
     v
Azure Bot Service
     |
     v
Botsoma (Python + Bot Framework)
     |
     +-- classify_message() → LLM classifica: erro ou pergunta?
     |
     +-- [ERRO] → escalation_service → envia notificacao proativa para suporte
     |
     +-- [PERGUNTA] → knowledge_base → busca docs relevantes
     |                    |
     |                    v
     |               llm_service → gera explicacao baseada nos docs
     |
     v
Usuario recebe resposta
```

## Estrutura do Projeto

```
botsoma/
├── bot/
│   ├── __init__.py
│   ├── app.py                  # Bot principal (ActivityHandler + triage)
│   ├── config.py               # Configuracao de ambiente
│   └── services/
│       ├── __init__.py
│       ├── llm_service.py      # Classificacao LLM + geracao de explicacao
│       ├── knowledge_base.py   # Carregamento e busca em documentos .md/.txt
│       └── escalation_service.py # Mensagens proativas para humanos no Teams
├── docs/
│   └── knowledge/              # Documentacao que o bot usa (adicione .md aqui)
│       ├── README.md
│       └── exemplo-documentacao.md
├── manifest/
│   ├── manifest.json           # Teams App Manifest (substitua botId)
│   ├── icon-color.png          # (adicione seu icone)
│   └── icon-outline.png        # (adicione seu icone)
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

### 1. Clonar e instalar dependencias

```bash
cd botsoma
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Configurar variaveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` com seus valores:

| Variavel                  | Descricao                                                      |
| ------------------------- | -------------------------------------------------------------- |
| `MICROSOFT_APP_ID`        | App ID do Azure AD (App Registration)                          |
| `MICROSOFT_APP_PASSWORD`  | Client Secret do Azure AD                                      |
| `MICROSOFT_APP_TENANT_ID` | Tenant ID do Azure AD                                          |
| `ZAI_API_KEY`             | Chave de API do provedor LLM                                   |
| `ZAI_MODEL`               | Modelo LLM (default: GLM-4.5-Air)                              |
| `SUPPORT_USER_IDS`        | IDs dos usuarios de suporte no Teams (separados por virgula)   |
| `KNOWLEDGE_BASE_DIR`      | Caminho para a pasta de documentacao (default: docs/knowledge) |

### 3. Adicionar documentacao

Coloque seus arquivos `.md` ou `.txt` em `docs/knowledge/`. O bot carrega automaticamente ao iniciar.

### 4. Rodar localmente

```bash
python -m bot.app
# Bot disponivel em http://localhost:3978/api/messages
```

### 5. Configurar ngrok (para testes)

```bash
ngrok http 3978
# Use a URL do ngrok como endpoint no Azure Bot Service
```

## Azure Bot Service Setup

1. **App Registration** no Azure AD
   - Criar novo registration
   - Gerar client secret → `MICROSOFT_APP_PASSWORD`
   - Copiar Application (client) ID → `MICROSOFT_APP_ID`
   - Copiar Directory (tenant) ID → `MICROSOFT_APP_TENANT_ID`

2. **Azure Bot Service**
   - Criar recurso "Azure Bot"
   - Tipo: Multi Tenant
   - Endpoint de mensagens: `https://<seu-dominio>/api/messages`

3. **Canal Microsoft Teams**
   - No Azure Bot, habilitar o canal "Microsoft Teams"

4. **Teams App Manifest**
   - Edite `manifest/manifest.json` e substitua `REPLACE_WITH_YOUR_BOT_ID` pelo bot ID do Azure
   - Adicione seus icones em `manifest/`
   - Carregue o manifest no Teams Admin Center ou sideload no Teams

## Deploy com Docker

```bash
docker build -t botsoma .
docker run -p 3978:3978 --env-file .env botsoma
```

## Como funciona a triagem

### Classificacao (LLM)

O bot envia a mensagem do usuario para o LLM com um prompt de classificacao. O LLM retorna:

```json
{
  "is_error": true,
  "confidence": 0.9,
  "reason": "usuario relata que sistema nao funciona"
}
```

- `is_error=true` + `confidence >= 0.6` → **escalacao**
- Caso contrario → **explicacao baseada em docs**

### Escalacao

Quando um erro e detectado:

1. O bot responde ao usuario: "Vou escalar para a equipe..."
2. Envia mensagem proativa na conversa do Teams com detalhes do erro
3. A notificacao inclui: usuario, horario, mensagem original, confianca da classificacao

### Explicacao

Quando nao e um erro:

1. Busca secoes relevantes na base de conhecimento
2. Envia contexto + pergunta para o LLM
3. Responde ao usuario com a explicacao e fonte

## Configuracao da Escalacao

Defina no `.env`:

```env
# Um unico usuario de suporte
SUPPORT_USER_IDS=29:1A...abc

# Multiplos usuarios de suporte
SUPPORT_USER_IDS=29:1A...abc,29:1B...def,29:1C...ghi
```

Para encontrar o user ID de alguem no Teams:

1. Envie uma mensagem para o bot
2. O ID aparece no log: `Message from Nome (conversation_id: ...)`
