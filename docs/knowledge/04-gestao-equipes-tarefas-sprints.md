# Gestão de Equipes, Tarefas e Sprints

## Equipes (Teams)

### Visão Geral
O sistema permite criar e gerenciar equipes de trabalho. Cada equipe pode ter múltiplos projetos e membros.

### Operações
- **Criar equipe**: Nome, descrição e configurações iniciais
- **Convidar membros**: Por e-mail, definindo papel (role)
- **Gerenciar permissões**: Admin pode alterar papéis e remover membros
- **Limite de membros**: Controlado pelo plano de assinatura

### Contexto de Equipe
O `TeamContext` fornece informações da equipe ativa em toda a aplicação:
```typescript
const { currentTeam, teamMembers } = useTeam();
```

### Papéis na Equipe
| Papel | Permissões |
|---|---|
| **Admin** | Gerenciar equipe, convites, configurações |
| **Membro** | Participar de projetos, criar/editar conteúdo |
| **Visualizador** | Apenas leitura |

---

## Tarefas (Dev Tasks)

### Visão Geral
As tarefas são a unidade fundamental de trabalho. Elas podem ser criadas manualmente ou geradas automaticamente por IA a partir de transcrições e documentos.

### Status de Tarefas
| Status | Descrição |
|---|---|
| `todo` | A fazer — tarefa pendente |
| `in_progress` | Em progresso — alguém está trabalhando |
| `done` | Concluída |
| `blocked` | Bloqueada — dependência ou impedimento |

### Prioridades
| Prioridade | Descrição |
|---|---|
| `critical` | Crítica — precisa de atenção imediata |
| `high` | Alta — importante e urgente |
| `medium` | Média — importante mas não urgente |
| `low` | Baixa — pode esperar |

### Campos de uma Tarefa
| Campo | Descrição |
|---|---|
| Título | Nome descritivo da tarefa |
| Descrição | Detalhes do que precisa ser feito |
| Status | Estado atual (todo/in_progress/done/blocked) |
| Prioridade | Nível de urgência |
| Responsável | Membro da equipe designado |
| Sprint | Sprint à qual a tarefa pertence |
| Story Points | Estimativa de esforço |
| Tags | Categorização livre |
| Projeto | Projeto ao qual pertence (obrigatório) |

### Geração de Tarefas por IA
As tarefas podem ser geradas automaticamente:
1. A partir de uma **transcrição de reunião**, o sistema sugere tarefas
2. A partir de **User Stories**, o sistema quebra em tarefas técnicas
3. O usuário revisa, edita e confirma as tarefas sugeridas

### Visualizações
- **Lista**: Visualização em tabela com filtros e ordenação
- **Kanban**: Board com colunas por status (todo → in_progress → done)
- **Filtros**: Por status, prioridade, responsável, sprint

---

## Sprints

### Visão Geral
Sprints são períodos de trabalho definidos (geralmente 1-4 semanas) onde um conjunto de tarefas é selecionado para execução.

### Criação de Sprint
1. Defina o **nome** da sprint
2. Estabeleça as **datas de início e fim**
3. Defina o **objetivo** da sprint
4. Selecione as **tarefas** que farão parte

### Campos de uma Sprint
| Campo | Descrição |
|---|---|
| Nome | Identificação da sprint |
| Objetivo | Meta principal do período |
| Data de início | Quando a sprint começa |
| Data de fim | Quando a sprint termina |
| Status | Planejada / Em andamento / Concluída |
| Tarefas | Lista de tarefas incluídas |
| Velocidade | Story points completados |

### Métricas de Sprint
- **Velocidade**: Story points entregues por sprint
- **Burndown**: Progresso ao longo do tempo
- **Taxa de conclusão**: % de tarefas concluídas
- **Distribuição por prioridade**: Como as tarefas estão distribuídas

### Fluxo de Sprint
```
Planejamento          Execução           Revisão
┌──────────┐     ┌──────────┐      ┌──────────┐
│ Definir   │     │ Trabalhar│      │ Retrospec.│
│ objetivo  │────▶│ nas      │─────▶│ Review    │
│ Selecionar│     │ tarefas  │      │ Métricas  │
│ tarefas   │     │ Daily    │      │ Lições    │
└──────────┘     └──────────┘      └──────────┘
```

---

## Backlog

### Visão Geral
O backlog é a lista completa de todas as tarefas do projeto que ainda não foram alocadas em uma sprint. Ele serve como reservatório de trabalho a ser priorizado.

### Gerenciamento
- **Ordenar por prioridade**: Tarefas mais importantes primeiro
- **Filtrar por tags/categorias**: Encontrar tarefas relacionadas
- **Estimar story points**: Planejar capacidade futura
- **Mover para sprint**: Alocar tarefas na sprint atual

---

## Integração entre Equipes, Tarefas e Sprints

```
┌─────────────┐
│   EQUIPE    │
│ (membros,  │
│  papéis)    │
└──────┬──────┘
       │ trabalha em
       ▼
┌─────────────┐      ┌─────────────┐
│  TAREFAS    │─────▶│   SPRINTS   │
│ (unidade    │      │ (períodos   │
│  de trabalho│      │  de tempo)  │
└─────────────┘      └──────┬──────┘
                            │
                            ▼
                     ┌─────────────┐
                     │  MÉTRICAS   │
                     │ (velocidade,│
                     │  burndown)  │
                     └─────────────┘
```

Todas as entidades são filtradas pelo `project_id` do projeto ativo, garantindo isolamento de dados entre projetos.

---

## Tarefas por Voz

O sistema inclui um componente **VoiceTaskRecorder** que permite criar tarefas por comando de voz. A gravação é transcrita e processada por IA para extrair a tarefa automaticamente.
