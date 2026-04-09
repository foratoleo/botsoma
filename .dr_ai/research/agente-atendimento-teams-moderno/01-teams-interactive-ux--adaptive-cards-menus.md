# Teams Interactive UX - Adaptive Cards e Menus

**Data de criacao:** 2026-04-08
**Ultima atualizacao:** 2026-04-08

---

## Adaptive Cards no Microsoft Teams

Adaptive Cards sao o padrao de facto para interfaces interativas dentro do Teams. Elas permitem criar menus, formularios e acoes clicaveis que substituem a necessidade de comandos textuais.

### Action.Execute vs Action.Submit

| Aspecto | Action.Execute | Action.Submit |
|---------|---------------|---------------|
| Bot Framework SDK | v4.10+ (moderno) | v4.0+ (legado) |
| Manipulacao | `on_invoke_activity` com `adaptiveCard/action` | `on_message_activity` via turn_context |
| Resposta automatica | Suporta `invokeResponse` com card atualizada | Necessita envio manual de nova activity |
| Refresh automatico | Suportado (modelos de usuario) | Nao suportado |
| Recomendacao | **Sim - padrao atual** | Manter para compatibilidade |

### Card JSON para Menu de Atendimento

Exemplo de card para classificacao inicial de duvida:

```json
{
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    {
      "type": "TextBlock",
      "text": "Como posso te ajudar?",
      "weight": "Bolder",
      "size": "Large",
      "wrap": true
    },
    {
      "type": "TextBlock",
      "text": "Selecione uma opcao abaixo ou descreva seu problema:",
      "isSubtle": true,
      "wrap": true
    }
  ],
  "actions": [
    {
      "type": "Action.Execute",
      "title": "Nao consigo acessar",
      "verb": "login_issue",
      "data": { "category": "access" }
    },
    {
      "type": "Action.Execute",
      "title": "Duvida sobre funcionalidade",
      "verb": "feature_question",
      "data": { "category": "howto" }
    },
    {
      "type": "Action.Execute",
      "title": "Erro no sistema",
      "verb": "system_error",
      "data": { "category": "bug" }
    },
    {
      "type": "Action.Execute",
      "title": "Outro assunto",
      "verb": "other",
      "data": { "category": "other" }
    }
  ]
}
```

### Manipulacao no Python (botbuilder)

```python
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import Activity, ActivityTypes

class TriageBot(ActivityHandler):
    async def on_invoke_activity(self, turn_context: TurnContext):
        activity = turn_context.activity

        if activity.name == "adaptiveCard/action":
            action_data = activity.value
            verb = action_data.get("verb", "")
            data = action_data.get("data", {})

            if verb == "login_issue":
                return await self._handle_login_issue(turn_context, data)
            elif verb == "feature_question":
                return await self._handle_feature_question(turn_context, data)
            elif verb == "system_error":
                return await self._handle_system_error(turn_context, data)

    async def _handle_login_issue(self, turn_context, data):
        # Retornar card de explica sobre login baseado em RAG
        card = self._build_explanation_card(
            title="Acesso a plataforma",
            explanation="Aqui estao os passos para acessar...",
            sources=["docs/login.md"]
        )
        return await self._send_card_response(turn_context, card)
```

### Padrao de Navegacao com Drill-Down

Para menus complexos, use o padrao de drill-down com breadcrumb:

```json
{
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    {
      "type": "TextBlock",
      "text": "Menu > Acesso > Senha",
      "isSubtle": true,
      "size": "Small",
      "spacing": "None"
    },
    {
      "type": "TextBlock",
      "text": "Problemas com senha",
      "weight": "Bolder",
      "size": "Medium"
    },
    {
      "type": "FactSet",
      "facts": [
        { "title": "Esqueci minha senha:", "value": "Clique em 'Esqueci a senha' na tela de login" },
        { "title": "Senha expirada:", "value": "Acesse o portal de senhas corporativo" },
        { "title": "Conta bloqueada:", "value": "Aguarde 30 minutos ou contate o TI" }
      ]
    }
  ],
  "actions": [
    {
      "type": "Action.Execute",
      "title": "Voltar ao menu",
      "verb": "back_to_menu",
      "data": { "level": "access" }
    },
    {
      "type": "Action.Execute",
      "title": "Falar com atendente",
      "verb": "escalate",
      "data": { "reason": "senha_nao_resolvido" }
    }
  ]
}
```

### Hero Cards (Alternativa Simples)

Para CTAs simples sem necessidade de formularios:

```python
from botbuilder.schema import HeroCard, CardAction, Attachment

def build_quick_actions_card() -> Attachment:
    card = HeroCard(
        title="Workforce Help",
        text="Escolha uma opcao rapida:",
        buttons=[
            CardAction(
                type="messageBack",
                title="Ver documentacao",
                text="Quero ver a documentacao",
                display_text="Ver documentacao"
            ),
            CardAction(
                type="messageBack",
                title="Falar com suporte",
                text="Preciso falar com alguem",
                display_text="Falar com suporte"
            ),
        ]
    )
    return Attachment(
        content_type="application/vnd.microsoft.card.hero",
        content=card.serialize()
    )
```

### Suggested Actions no Teams

O Teams **NÃO suporta** `suggestedActions` nativamente (diferente do Web Chat e Bot Framework Emulator). A solucao e usar Adaptive Cards com botoes `Action.Execute` ou `Action.Submit` para simular o mesmo comportamento.

### Boas Praticas de UX para Cards

1. **Limite de botoes**: 3-5 por card para nao sobrecarregar o usuario
2. **Labels claros**: Texto do botao deve ser autoexplicativo (max 2-3 palavras)
3. **Feedback visual**: Ao clicar, atualizar o card com estado de processamento
4. **Fallback text**: Sempre incluir `fallbackText` para clientes que nao suportam cards
5. **Responsividade**: Usar `wrap: true` em TextBlocks para adaptar a telas menores

### Universal Action Model

O Universal Action Model (disponivel no Teams) permite que uma unica acao funcione tanto no Teams quanto no Outlook. Utilize `Action.Execute` para compatibilidade universal.

Para habilitar refresh automatico:

```json
{
  "type": "AdaptiveCard",
  "version": "1.5",
  "refresh": {
    "action": {
      "type": "Action.Execute",
      "verb": "refresh",
      "data": {}
    },
    "userIds": ["<user_aad_object_id>"]
  },
  "body": [...]
}
```

---

## Integracao com o Triage Flow Atual

O `triage_flow.py` atual opera apenas com texto. A integracao com Adaptive Cards requer:

1. **Nova rota no bot**: Detectar se a resposta do triage deve ser texto ou card
2. **Mapeamento de decisao**: `explain` → card com explicacao + "Ajudou?"; `ask` → card com pergunta + botoes de resposta rapida; `escalate` → card de confirmacao antes de transferir
3. **Handler de callbacks**: Processar `adaptiveCard/action` como input do triage

### Exemplo de Integracao

```python
# Em triage_flow.py - estender TriageStep
@dataclass
class TriageStep:
    decision: Decision
    message: str
    reason: str
    sources: list[str]
    urgency: str | None = None
    error_summary: str | None = None
    suggested_actions: list[dict] | None = None  # NOVO: botoes sugeridos
```

```python
# Em app.py - enviar card ou texto baseado na decisao
async def _send_triage_response(self, turn_context, step: TriageStep):
    if step.suggested_actions:
        card = self._build_interactive_card(step)
        await turn_context.send_activity(
            Activity(
                type=ActivityTypes.message,
                attachments=[card]
            )
        )
    else:
        await turn_context.send_activity(step.message)
```
