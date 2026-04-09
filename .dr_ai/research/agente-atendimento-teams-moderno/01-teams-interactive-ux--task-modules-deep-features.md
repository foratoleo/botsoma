# Teams Interactive UX - Task Modules e Features Avancadas

**Data de criacao:** 2026-04-08
**Ultima atualizacao:** 2026-04-08

---

## Task Modules

Task Modules sao modais (pop-ups) que abrem dentro do Teams, ideais para formularios multi-step e coleta de informacoes estruturadas sem sair do contexto da conversa.

### Invocacao via Adaptive Card

```json
{
  "type": "Action.Submit",
  "title": "Reportar problema",
  "data": {
    "msteams": {
      "type": "invoke",
      "value": {
        "type": "task/fetch"
      }
    },
    "action": "report_problem"
  }
}
```

### Handler no Python (botbuilder)

```python
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import Activity, ActivityTypes, TaskModuleResponse, TaskModuleResponseInfo

class TriageBot(ActivityHandler):
    async def on_invoke_activity(self, turn_context: TurnContext):
        activity = turn_context.activity

        if activity.name == "composeExtension/query":
            # Messaging Extension query
            return await self._handle_messaging_extension(turn_context)

        if activity.value and activity.value.get("type") == "task/fetch":
            # Abertura do Task Module
            return await self._handle_task_fetch(turn_context, activity.value)

        if activity.value and activity.value.get("type") == "task/submit":
            # Submissao do Task Module
            return await self._handle_task_submit(turn_context, activity.value)

    async def _handle_task_fetch(self, turn_context, value):
        """Retorna a card que sera exibida no modal."""
        action = value.get("action", "")

        if action == "report_problem":
            card = self._build_problem_form_card()
        elif action == "feedback":
            card = self._build_feedback_card()
        else:
            card = self._build_generic_form_card()

        return TaskModuleResponse(
            task=TaskModuleResponseInfo(
                type="continue",
                value=card
            )
        )

    async def _handle_task_submit(self, turn_context, value):
        """Processa dados submetidos no modal."""
        # value contem os campos do formulario
        category = value.get("problem_category", "")
        description = value.get("problem_description", "")
        urgency = value.get("urgency", "normal")

        # Processar via triage flow
        step = await process_turn(
            session=self._get_session(turn_context),
            user_message=f"[Form] {category}: {description}"
        )

        # Fechar o modal e enviar resposta na conversa
        return TaskModuleResponse(
            task=TaskModuleResponseInfo(
                type="message",
                value=step.message
            )
        )
```

### Card de Formulario para Task Module

```json
{
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    {
      "type": "TextBlock",
      "text": "Reportar Problema",
      "weight": "Bolder",
      "size": "Large"
    },
    {
      "type": "Input.ChoiceSet",
      "id": "problem_category",
      "label": "Categoria",
      "choices": [
        { "title": "Acesso / Login", "value": "access" },
        { "title": "Funcionalidade nao funciona", "value": "feature_broken" },
        { "title": "Erro no sistema", "value": "system_error" },
        { "title": "Duvida de uso", "value": "howto" }
      ],
      "style": "expanded"
    },
    {
      "type": "Input.Text",
      "id": "problem_description",
      "label": "Descreva o problema",
      "isMultiline": true,
      "maxLength": 500,
      "placeholder": "O que aconteceu? O que voce tentou fazer?"
    },
    {
      "type": "Input.ChoiceSet",
      "id": "urgency",
      "label": "Urgencia",
      "choices": [
        { "title": "Baixa - posso esperar", "value": "baixa" },
        { "title": "Normal - preciso hoje", "value": "normal" },
        { "title": "Urgente - estou bloqueado", "value": "urgente" }
      ],
      "value": "normal"
    }
  ],
  "actions": [
    {
      "type": "Action.Submit",
      "title": "Enviar",
      "data": { "type": "task/submit", "action": "report_problem" }
    }
  ]
}
```

## Messaging Extensions

Messaging Extensions permitem interacoes diretas na area de composicao de mensagens do Teams. Ideais para:
- Busca rapida de documentos da base de conhecimento
- Compartilhamento de respostas prontas

### Configuracao no Manifest

```json
{
  "composeExtensions": [
    {
      "botId": "b0ab8623-36a4-48d4-8b74-818941b0ae69",
      "canUpdateConfiguration": false,
      "commands": [
        {
          "id": "searchDocs",
          "title": "Buscar documento",
          "description": "Pesquise na base de conhecimento",
          "type": "query",
          "parameters": [
            {
              "name": "query",
              "title": "Termo de busca",
              "description": "O que voce procura?"
            }
          ]
        },
        {
          "id": "quickHelp",
          "title": "Ajuda rapida",
          "description": "Respostas rapidas para duvidas comuns",
          "type": "query",
          "parameters": [
            {
              "name": "topic",
              "title": "Topico",
              "description": "Sobre o que precisa de ajuda?"
            }
          ]
        }
      ]
    }
  ]
}
```

### Handler de Query

```python
async def _handle_messaging_extension(self, turn_context):
    query = turn_context.activity.value
    command_id = query.command_id
    search_text = query.parameters[0].value if query.parameters else ""

    if command_id == "searchDocs":
        results = self._search_knowledge_base(search_text)
        attachments = [
            {
                "contentType": "application/vnd.microsoft.card.thumbnail",
                "content": {
                    "title": r["title"],
                    "text": r["summary"][:200],
                    "buttons": [
                        {
                            "type": "openUrl",
                            "title": "Ver completo",
                            "value": r["source"]
                        }
                    ]
                }
            }
            for r in results[:5]
        ]
        return {
            "composeExtension": {
                "type": "result",
                "attachmentLayout": "list",
                "attachments": attachments
            }
        }
```

## Deep Linking

Deep links permitem abrir o bot diretamente com parametros pre-definidos:

```
https://teams.microsoft.com/l/chat/0/0?users=28:b0ab8623-36a4-48d4-8b74-818941b0ae69&message=Preciso%20de%20ajuda%20com%20login
```

Isso e util para botoes em emails, intranet, ou outros sistemas que direcionam o usuario direto ao bot com contexto inicial.

## Tipos de Card e Quando Usar

| Tipo de Card | Uso Recomendado | Complexidade |
|-------------|-----------------|-------------|
| **Adaptive Card** | Formularios, menus, dados dinamicos | Media-Alta |
| **Hero Card** | CTAs simples, uma imagem + botoes | Baixa |
| **Thumbnail Card** | Lista de resultados com preview | Baixa |
| **OAuth Card** | Fluxo de autenticacao OAuth | Media |
| **Receipt Card** | Resumo de acoes tomadas | Media |

## Fluxo de Conversa Recomendado

```
Usuario envia mensagem
    |
    v
Bot detecta saudacao → WELCOME CARD com menu principal (4 botoes)
    |
    v
Usuario clica "Nao consigo acessar"
    |
    v
Bot envia EXPLANATION CARD com passos + "Ajudou? Sim / Nao"
    |
    v
Sim → Card de feedback ("Otimo! Precisa de mais algo?")
Nao  → Card com "Quer detalhar melhor? Abre TASK MODULE com formulario"
    |
    v
Formulario enviado → RAG busca explicacao + Card de resolucao
    |
    v
Resolvido → Card de feedback final
Nao resolvido → Card de escalacao com resumo automatico
```

Este fluxo maximiza o uso de cards interativos mantendo a opcao de texto livre a qualquer momento.
