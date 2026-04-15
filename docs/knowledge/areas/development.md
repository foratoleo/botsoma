# Development Area

Created: 2026-04-10
Last Updated: 2026-04-10

## Theme

- **Primary**: Gray/Silver (#9E9E9E)
- **Accent**: #C0C0C0
- **Background**: rgba(245, 245, 245, 0.4)
- **CSS Variable**: `[data-area="development"]`

## Navigation Items

| ID | Route | Icon | Description |
|----|-------|------|-------------|
| sprints | `/sprints` | Layers | Sprint management |
| tasks | `/tasks` | CheckSquare | Task management |
| documents | `/documents?area=development` | FileText | Technical documents |
| bug-tracking | `/quality/bugs?area=development` | Bug | Bug tracking |
| repositories | `/development/repositories` | GitBranch | Code repositories |
| pull-requests | `/development/pull-requests` | GitPullRequest | Pull requests |
| pr-metrics | `/development/pr-metrics` | Gauge | PR metrics |
| code-review | `/development/code-review` | UserCheck | Code review metrics |
| dev-performance | `/development/dev-performance` | TrendingUp | Developer performance |
| analysis-reports | `/development/analysis-reports` | FileBarChart | Analysis reports |
| ai-agents | `/development/ai-agents` | Bot | AI agent configuration |
| style-guides | `/development/style-guides` | BookText | Code style guides |
| legacy-code | `/development/legacy-code` | Wrench | Legacy code management |

## Key Components

| Directory | Purpose |
|-----------|---------|
| `src/components/development/` | Analysis reports, dev performance |
| `src/components/ai-agents/` | AI agent configuration (10 subdirs: tabs, fields) |
| `src/components/style-guides/` | Style guide management (17 files) |
| `src/components/legacy-code/` | Legacy code management (8 files) |
| `src/components/jira/` | Jira integration UI (11 files) |
| `src/components/github/` | GitHub integration UI |

### AI Agent Configuration

The AI agent system allows configuring AI assistants for development tasks:

| Component | Purpose |
|-----------|---------|
| `AgentCard.tsx` | Agent card display |
| `AgentConfigTabs.tsx` | Configuration tabs container |
| `AgentAuditLog.tsx` | Audit trail for config changes |
| `AgentExportImportDialog.tsx` | Import/export agent configs |
| `AgentTemplateDialog.tsx` | Agent template selection |

**Config Tabs** (each a separate component):
`AutonomyConfigTab`, `CodingConfigTab`, `CommunicationConfigTab`, `DocumentationConfigTab`, `GitConfigTab`, `IntegrationConfigTab`, `LearningConfigTab`, `PerformanceConfigTab`, `SchedulingConfigTab`, `SecurityConfigTab`

**Field Types**: `ArrayField`, `BooleanField`, `EnumField`, `JsonField`, `NumberField`, `StringField`, `SettingField`, `SettingSection`, `SettingsGrid`

## Key Hooks

| Hook | Purpose |
|------|---------|
| `useDevPerformance` | Developer performance metrics |
| `useAnalysisReports` | Code analysis reports |
| `useCodeReviewMetrics` | Code review statistics |
| `useAgentConfig` | AI agent configuration CRUD |
| `useAgentConfigAudit` | Agent config change history |
| `useAgentConfigTemplates` | Agent templates |
| `useAIAgents` | AI agent listing |
| `useGitRepositories` | Git repository management (16k lines) |
| `useGitHubPRMetrics` | PR metrics from GitHub |
| `useGitHubPullRequests` | PR listing |
| `useGitHubAccountMappings` | GitHub account to team member mapping |
| `useStyleGuideChatSettings` | Style guide chat configuration |

## Key Services

| Service | Purpose |
|---------|---------|
| `dev-performance-service.ts` | Developer performance calculations |
| `analysis-reports-service.ts` | Analysis report generation |
| `code-review-metrics-service.ts` | Code review metrics aggregation |
| `agent-config-service.ts` | AI agent config management |
| `style-guide-service.ts` | Style guide CRUD |
| `git-repository-service.ts` | Git repository CRUD |
| `github-pr-service.ts` | GitHub PR operations |
| `github-pr-metrics-service.ts` | PR metrics calculation |
| `github-sync-config-service.ts` | GitHub sync configuration |

## Pages

| Page | Route | File |
|------|-------|------|
| Development Landing | `/development` | `pages/areas/DevelopmentLanding.tsx` |
| Pull Requests | `/development/pull-requests` | `pages/development/PullRequestsDashboard.tsx` |
| PR Metrics | `/development/pr-metrics` | `pages/development/PRMetricsDashboard.tsx` |
| Code Review | `/development/code-review` | `pages/development/CodeReviewMetricsPage.tsx` |
| Dev Performance | `/development/dev-performance` | `pages/development/DevPerformanceDashboard.tsx` |
| Refactor Insights | `/development/refactor-insights` | `pages/development/RefactorInsightsPage.tsx` |
| Repositories | `/development/repositories` | `pages/RepositoriesListingPage.tsx` |
| Analysis Reports | `/development/analysis-reports` | `pages/development/AnalysisReportsPage.tsx` |
| AI Agents List | `/development/ai-agents` | `pages/development/AIAgentsListPage.tsx` |
| AI Agent Config | `/development/ai-agents/:id` | `pages/development/AIAgentConfigPage.tsx` |
| Style Guides | `/development/style-guides` | `pages/development/StyleGuidesPage.tsx` |
| Legacy Code | `/development/legacy-code` | `pages/legacy-code/CodeHealthDashboard.tsx` |
