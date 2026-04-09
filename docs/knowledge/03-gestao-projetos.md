# Gestão de Projetos

## Visão Geral

O sistema de gestão de projetos é o alicerce do DR AI Workforce. **Todos os dados na plataforma são organizados e isolados por projeto**, garantindo que cada equipe trabalhe apenas com informações relevantes ao seu contexto.

---

## Criando um Projeto

### Passos:
1. Acesse a página de **Seleção de Projetos**
2. Clique em **"Novo Projeto"**
3. Preencha as informações:
   - **Nome** do projeto
   - **Descrição** (opcional)
   - **Visibilidade** (público ou privado)
4. Confirme a criação

Após criado, o projeto torna-se o **projeto ativo** e todos os dados subsequentes são vinculados a ele.

---

## Seleção de Projeto Ativo

O sistema utiliza o `ProjectSelectionContext` para gerenciar qual projeto está ativo. Isso é fundamental porque:

> **TODOS os dados (tarefas, sprints, transcrições, documentos, uploads) são filtrados pelo `project_id` do projeto ativo.**

### Como funciona:
```
┌──────────────────┐
│  Seletor de      │
│  Projetos        │──────┐
└──────────────────┘      │
                          ▼
┌──────────────────────────────────────┐
│  ProjectSelectionContext             │
│                                      │
│  selectedProject = {                 │
│    id: "uuid-do-projeto",            │
│    name: "Meu Projeto",              │
│    ...                               │
│  }                                   │
│                                      │
│  → Filtra todas as queries           │
│    .eq('project_id', selectedProject.id) │
└──────────────────────────────────────┘
```

### Propriedades disponíveis:

| Propriedade | Tipo | Descrição |
|---|---|---|
| `selectedProject` | `Project \| null` | Objeto completo do projeto |
| `setSelectedProject(project)` | Function | Trocar de projeto |
| `clearSelectedProject()` | Function | Limpar seleção |
| `isProjectMode` | `boolean` | Se há projeto ativo |
| `projectHistory` | `Project[]` | Histórico de projetos recentes |
| `addToHistory(project)` | Function | Adicionar ao histórico |
| `clearHistory()` | Function | Limpar histórico |

### ⚠️ Padrão correto de uso:
```typescript
// ✅ CORRETO
const { selectedProject } = useProjectSelection();
const projectId = selectedProject?.id;

// ❌ INCORRETO — essa propriedade NÃO existe
const { selectedProjectId } = useProjectSelection();
```

---

## Colaboradores e Permissões

### Convite de Membros
- O admin do projeto pode convidar membros por e-mail
- Os convites podem incluir definição de papel (role)

### Papéis (Roles)
| Papel | Permissões |
|---|---|
| **Admin** | Gerenciar projeto, convidar membros, alterar configurações |
| **Membro** | Criar/editar tarefas, documentos, transcrições |
| **Visualizador** | Apenas visualizar dados do projeto |

### Limites
- O número de membros pode ser limitado pelo plano de assinatura da equipe

---

## Documentos do Projeto

Cada projeto pode ter documentos de referência associados:

### Tipos de documento:
- **Documentos carregados** (upload manual)
- **Documentos gerados por IA** (PRDs, User Stories, etc.)
- **Transcrições de reuniões**
- **Base de conhecimento**

### Gestão:
- Todos os documentos ficam acessíveis na área de **Governança**
- O histórico de versões é mantido para documentos gerados por IA
- Documentos podem ser referenciados no chat Guru

---

## Histórico de Atividades

O sistema mantém um registro de todas as ações relevantes no projeto:

- Criação e edição de tarefas
- Geração de documentos
- Alterações em sprints
- Entrada/saída de membros
- Uploads realizados

Esse histórico é útil para auditoria e acompanhamento.

---

## Estrutura no Banco de Dados

A tabela principal é `projects` com os seguintes campos relevantes:

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | Identificador único |
| `name` | text | Nome do projeto |
| `description` | text | Descrição |
| `owner_id` | UUID | Referência ao criador (team_members) |
| `visibility` | text | Público ou privado |
| `created_at` | timestamp | Data de criação |
| `updated_at` | timestamp | Última atualização |

---

## Fluxo Típico de Uso

```
1. Usuário faz login
       │
       ▼
2. Seleciona ou cria um projeto
       │
       ▼
3. Convida membros (opcional)
       │
       ▼
4. Faz upload de documentos/referências
       │
       ▼
5. Cria transcrições ou grava reuniões
       │
       ▼
6. Gera documentação com IA
       │
       ▼
7. Planeja sprints e tarefas
       │
       ▼
8. Acompanha via dashboard e métricas
```
