# Bot Framework Avancado - Microsoft Graph API Integration

**Data de criacao:** 2026-04-08
**Ultima atualizacao:** 2026-04-08

---

## Microsoft Graph API com Python

A Graph API permite ao bot interagir com usuarios, canais, equipes e mensagens do Microsoft 365.

### Configuracao de Autenticacao

```python
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient

class GraphService:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        self.client = GraphServiceClient(credential)

    async def get_user(self, user_id: str) -> dict:
        """Busca informacoes de um usuario."""
        user = await self.client.users.by_user_id(user_id).get()
        return {
            "display_name": user.display_name,
            "email": user.mail,
            "job_title": user.job_title,
            "department": user.department,
        }

    async def get_team_members(self, team_id: str) -> list[dict]:
        """Lista membros de um time."""
        members = await self.client.teams.by_team_id(team_id).members.get()
        return [
            {
                "id": m.id,
                "user_id": m.additional_data.get("userId", ""),
                "display_name": m.display_name,
                "roles": m.roles,
            }
            for m in members.value
        ]
```

### Permissoes Necessarias no Manifest

```json
{
  "webApplicationInfo": {
    "id": "b0ab8623-36a4-48d4-8b74-818941b0ae69",
    "resource": "https://graph.microsoft.com",
    "applicationPermissions": [
      "User.Read.All",
      "Team.ReadBasic.All",
      "Channel.ReadBasic.All",
      "Chat.ReadWrite.All"
    ]
  }
}
```

### Casos de Uso para o Bot de Suporte

#### 1. Enriquecimento de Contexto do Usuario

```python
async def enrich_user_context(self, user_aad_id: str) -> dict:
    """Adiciona informacoes do AD ao contexto da conversa."""
    user_info = await self.graph.get_user(user_aad_id)
    return {
        "name": user_info.get("display_name", ""),
        "email": user_info.get("email", ""),
        "department": user_info.get("department", ""),
        "role": user_info.get("job_title", ""),
    }
```

Isso permite ao triage flow personalizar respostas:
- "Ola {name}, vi que voce e do departamento {dept}..."
- Roteamento inteligente baseado no departamento (encaminhar para o time correto)

#### 2. Busca de Atendente Disponivel

```python
async def find_available_agent(self, support_channel_id: str) -> str | None:
    """Encontra um membro do canal de suporte online."""
    # Via Graph API: verificar presenca dos membros
    members = await self.graph.get_team_members(self.support_team_id)

    for member in members:
        # Verificar se esta online
        presence = await self.client.communications.presences.by_presence_id(
            member["user_id"]
        ).get()

        if presence and presence.availability == "Available":
            return member["user_id"]

    return None
```

#### 3. Criacao de Chat com Atendente

```python
async def create_support_chat(self, user_id: str, agent_id: str) -> str:
    """Cria um chat entre usuario e atendente."""
    chat = await self.client.chats.post(
        body={
            "chatType": "oneOnOne",
            "members": [
                {
                    "@odata.type": "#microsoft.graph.aadUserConversationMember",
                    "roles": ["owner"],
                    "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{user_id}')"
                },
                {
                    "@odata.type": "#microsoft.graph.aadUserConversationMember",
                    "roles": ["owner"],
                    "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{agent_id}')"
                }
            ]
        }
    )
    return chat.id
```

#### 4. Envio de Notificacao de Escalacao

```python
async def notify_agent(self, agent_id: str, context: EscalationContext):
    """Envia notificacao ao atendente com contexto da escalacao."""
    # Criar ou continuar conversa com o agente
    chat_id = await self.create_support_chat(context.user_id, agent_id)

    # Enviar card com contexto
    card = format_escalation_card(context)
    await self.client.chats.by_chat_id(chat_id).messages.post(
        body={
            "body": {
                "contentType": "html",
                "content": f"""
                <attachment>
                {json.dumps(card)}
                </attachment>
                """
            }
        }
    )
```

## Escalacao para Canal de Equipe

Alternativa a chats 1:1 - enviar para o canal de suporte da equipe:

```python
async def escalate_to_channel(self, context: EscalationContext):
    """Envia escalacao para o canal de suporte da equipe."""
    card = format_escalation_card(context)

    await self.client.teams.by_team_id(self.team_id).channels.by_channel_id(
        self.support_channel_id
    ).messages.post(
        body={
            "body": {
                "contentType": "html",
                "content": f"<attachment>{json.dumps(card)}</attachment>"
            }
        }
    )
```

## Dependencias

```
# requirements.txt - adicionar:
azure-identity==1.19.0
msgraph-sdk==1.14.0
```

## Variaveis de Ambiente Adicionais

```env
# config.py - adicionar:
AZURE_TENANT_ID=xxx
AZURE_CLIENT_ID=b0ab8623-36a4-48d4-8b74-818941b0ae69
AZURE_CLIENT_SECRET=xxx
SUPPORT_TEAM_ID=xxx
```

## Notas sobre Permissions

| Permissao | Tipo | Necessaria Para |
|-----------|------|----------------|
| User.Read.All | Application | Buscar info de usuarios |
| Team.ReadBasic.All | Application | Listar equipes |
| Channel.ReadBasic.All | Application | Listar canais |
| Chat.ReadWrite.All | Application | Criar/enviar chats |
| Presence.Read.All | Application | Verificar status online |
| TeamsActivity.Send | Application | Enviar notificacoes |

A maioria dessas permissoes exige consentimento do administrador do tenant Azure AD.
