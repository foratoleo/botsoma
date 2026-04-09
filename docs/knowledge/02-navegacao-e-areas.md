# Navegação e Áreas de Trabalho

## Visão Geral da Navegação

O DR AI Workforce utiliza um sistema de navegação hierárquico baseado em **4 fases do ciclo de desenvolvimento de software**. Cada área tem uma identidade visual própria com cores temáticas (compatíveis com WCAG), facilitando a orientação do usuário dentro da plataforma.

A navegação principal é feita através de uma **sidebar colapsável** à esquerda, que se adapta ao contexto da área selecionada. No rodapé da sidebar ficam o **Guru** (chat IA), o **menu de usuário** e o **seletor de idioma**.

---

## As 4 Áreas de Trabalho

### 🟡 Planejamento (Dark Gold)
- **Cor primária**: `#B8860B` (Dark Gold)
- **Cor de destaque**: `#DAA520` (Goldenrod)
- **Fundo**: Amarelado suave `rgba(255, 249, 230, 0.4)`

**Contém**:
- Reuniões e Transcrições
- Time (equipe)
- Tarefas de planejamento
- Detalhes do Projeto
- Requisitos

**Quando usar**: Na fase inicial do projeto, onde se define escopo, requisitos, reuniões de alinhamento e organização da equipe.

---

### ⚪ Desenvolvimento (Gray/Silver)
- **Cor primária**: `#9E9E9E` (Gray)
- **Cor de destaque**: `#C0C0C0` (Silver)
- **Fundo**: Cinza claro `rgba(245, 245, 245, 0.4)`

**Contém**:
- Tarefas de desenvolvimento
- Sprints
- Métricas de desenvolvimento
- Código e implementação

**Quando usar**: Durante a fase de codificação e implementação das funcionalidades planejadas.

---

### 🟤 Homologação / Testes (Bronze)
- **Cor primária**: `#CD7F32` (Bronze)
- **Cor de destaque**: `#D4A574` (Light Bronze)
- **Fundo**: Pêssego suave `rgba(255, 245, 235, 0.4)`

**Contém**:
- Tarefas de QA e testes
- Validação de entregas
- Casos de teste
- Homologação

**Quando usar**: Na fase de verificação e validação, onde as funcionalidades são testadas antes de ir para produção.

---

### 🟢 Governança (Dark Green)
- **Cor primária**: `#1B4332` (Dark Green)
- **Cor de destaque**: `#2D6A4F` (Forest Green)
- **Fundo**: Verde suave `rgba(240, 247, 244, 0.4)`

**Contém**:
- Documentos do projeto
- Base de conhecimento
- Relatórios e analytics
- Auditoria e compliance

**Quando usar**: Para gestão documental, base de conhecimento, relatórios e governança do projeto como um todo.

---

## Sidebar

### Estrutura
```
┌─────────────────────────┐
│  🏠 Dashboard           │
│─────────────────────────│
│  🟡 Planejamento     ▸  │
│    ├─ Reuniões          │
│    ├─ Time              │
│    ├─ Tarefas           │
│    └─ Projeto           │
│─────────────────────────│
│  ⚪ Desenvolvimento   ▸  │
│    ├─ Tarefas           │
│    ├─ Sprints           │
│    └─ Métricas          │
│─────────────────────────│
│  🟤 Testes           ▸   │
│    ├─ QA                │
│    └─ Validação         │
│─────────────────────────│
│  🟢 Governança       ▸  │
│    ├─ Documentos        │
│    └─ Conhecimento      │
│─────────────────────────│
│  🤖 Guru (Chat IA)      │
│  👤 Menu do Usuário     │
│  🌐 Seletor de Idioma   │
└─────────────────────────┘
```

### Funcionalidades da Sidebar
- **Colapsável**: Pode ser recolhida para dar mais espaço à área de trabalho
- **Contextual**: Mostra opções relevantes para a área selecionada
- **Identidade visual**: As cores mudam conforme a área ativa
- **Acesso rápido**: Guru, configurações e idioma sempre disponíveis no rodapé

---

## Dashboard Principal

O dashboard oferece uma visão geral do estado atual do projeto:

- **Projetos ativos**: Lista de projetos com status resumido
- **Indicadores de desempenho**: Métricas de produtividade da equipe
- **Tarefas recentes**: Últimas tarefas criadas ou atualizadas
- **Sprint atual**: Progresso da sprint em andamento
- **Atividades recentes**: Log das últimas ações no projeto

---

## Seleção de Projeto

Antes de navegar pelas áreas, o usuário seleciona um projeto ativo. Essa seleção é persistida via `ProjectSelectionContext` e **todos os dados são filtrados automaticamente** pelo projeto selecionado.

### Como funciona:
1. O usuário acessa o **Seletor de Projetos**
2. Escolhe ou cria um projeto
3. A partir desse momento, todas as queries (tarefas, sprints, transcrições, documentos) são filtradas por `project_id`
4. Se nenhum projeto estiver selecionado, a interface exibe um aviso

### Propriedades do contexto:
- `selectedProject` — Objeto completo do projeto ativo
- `setSelectedProject(project)` — Trocar de projeto
- `clearSelectedProject()` — Limpar seleção
- `isProjectMode` — Se há um projeto ativo
- `projectHistory` — Histórico de projetos recentes

---

## Internacionalização (i18n)

A plataforma suporta **dois idiomas**:

| Idioma | Arquivo |
|---|---|
| Português (BR) | `src/locales/pt-br.ts` |
| Inglês (US) | `src/locales/en-us.ts` |

### Uso nos componentes:
```typescript
import { useI18n } from '@/hooks/useI18n';

const { t } = useI18n('namespace');

// Tradução simples
<h1>{t('titulo')}</h1>

// Com parâmetros
<p>{t('boas.vindas', { nome: 'João' })}</p>
```

### Estrutura das traduções:
As traduções são organizadas por **namespace** (área funcional), como `team`, `tasks`, `planning`, etc.

---

## Tema Claro/Escuro

O sistema suporta alternância entre tema claro e escuro. A preferência é salva e persistida entre sessões. Todas as cores das áreas de trabalho são adaptadas para funcionar corretamente em ambos os temas.
