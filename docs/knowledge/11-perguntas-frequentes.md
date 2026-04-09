# Perguntas Frequentes (FAQ)

---

## Geral

### O que é o DR AI Workforce?
É uma plataforma de gestão de projetos de desenvolvimento de software com Inteligência Artificial, desenvolvida pela Digital Republic. Ela permite planejar projetos, gerenciar equipes, gerar documentação automaticamente e conversar com seus documentos via chat inteligente (Guru).

### Para quem é destinado?
Equipes de desenvolvimento de software que precisam de uma ferramenta integrada para planejamento, documentação, gestão de tarefas e análise de projetos.

### Preciso instalar algo?
Não. O DR AI Workforce é uma aplicação web — basta acessar pelo navegador. Para desenvolvimento local, é necessário Node.js 18+ e uma conta no Supabase.

### Quais idiomas são suportados?
Português (BR) e Inglês (US). A troca pode ser feita pelo seletor de idioma no rodapé da sidebar.

### Funciona em dispositivos móveis?
A interface é responsiva, mas foi otimizada para uso em desktop.

---

## Projetos

### Como crio um novo projeto?
Acesse o seletor de projetos e clique em "Novo Projeto". Preencha nome, descrição e visibilidade.

### Posso ter múltiplos projetos?
Sim. Você pode criar e alternar entre projetos. Todos os dados são isolados por projeto.

### Como alterno entre projetos?
Use o seletor de projetos na barra de navegação. Ao trocar, todos os dados (tarefas, documentos, etc.) são atualizados automaticamente.

### Posso convidar outras pessoas para meu projeto?
Sim. Como admin do projeto, você pode convidar membros por e-mail e definir seus papéis (admin, membro, visualizador).

### O que acontece se eu não selecionar um projeto?
A interface exibirá um aviso e funcionalidades como tarefas e documentos não estarão disponíveis até que um projeto seja selecionado.

---

## IA e Geração de Documentos

### Quais tipos de documentos a IA pode gerar?
- PRD (Product Requirements Document)
- User Stories
- Notas de Reunião
- Especificações Técnicas
- Casos de Teste
- Testes Unitários
- Análise de Transcrição

### A geração de documentos é automática?
Não totalmente. Você seleciona a transcrição ou conteúdo de entrada, escolhe o tipo de documento e confirma. A IA faz a geração, mas o usuário tem controle.

### Posso gerar vários documentos de uma vez?
Sim. Usando o sistema de conversação contínua, você pode gerar um PRD e depois User Stories na mesma sessão, e a IA mantém o contexto entre as gerações.

### Quanto custa a geração de documentos?
O custo depende do uso de tokens da OpenAI. O sistema rastreia automaticamente os gastos por projeto, que podem ser consultados no dashboard de métricas.

### Posso editar os documentos gerados?
Sim. Documentos gerados por IA podem ser editados pelo usuário. Cada geração cria uma nova versão, mantendo o histórico.

### Qual modelo de IA é utilizado?
GPT-4o para documentos complexos e GPT-4o-mini para tarefas mais simples. A seleção é automática baseada na complexidade.

---

## Chat Guru (RAG)

### O que é o Guru?
É um chat inteligente que responde perguntas com base nos documentos do seu projeto. Ele usa a técnica RAG (Retrieval-Augmented Generation) para buscar informações relevantes e gerar respostas fundamentadas.

### O Guru tem acesso a todos os meus dados?
O Guru acessa apenas os documentos do **projeto ativo**. Dados de outros projetos não são visíveis.

### As respostas do Guru são confiáveis?
O Guru baseia suas respostas nos documentos do projeto e **indica as fontes**. Sempre verifique as referências para confirmar a precisão.

### Posso confiar 100% nas respostas?
Como qualquer sistema de IA, podem ocorrer imprecisões. Use as referências para verificar e sempre consulte os documentos originais para informações críticas.

### Como melhorar as respostas do Guru?
1. Faça upload de documentos relevantes para o projeto
2. Use perguntas específicas em vez de vagas
3. Mantenha os documentos atualizados
4. Use nomenclatura consistente

### Onde encontro o Guru?
No rodapé da sidebar, acessível de qualquer página.

---

## Upload e Documentos

### Quais formatos de arquivo são aceitos?
- Texto: `.txt`, `.md`
- Documentos: `.pdf`, `.docx`, `.xlsx`
- Imagens: `.png`, `.jpg`, `.svg`
- Outros formatos também podem ser suportados

### Qual o tamanho máximo de arquivo?
O limite varia por tipo de arquivo e configuração do projeto. Arquivos muito grandes podem demorar mais para processar.

### O que acontece após o upload?
O sistema processa o arquivo automaticamente:
- Textos são indexados para busca e Guru
- PDFs têm o texto extraído e o arquivo original é preservado
- Binários são armazenados no S3

### Posso deletar um documento?
Sim, como admin ou dono do upload. A exclusão é permanente.

---

## Equipes

### Como convido alguém para minha equipe?
Como admin, acesse a gestão da equipe e envie um convite por e-mail. O convidado receberá um link para aceitar.

### Quais são os papéis disponíveis?
- **Admin**: Gerencia equipe e projetos, convida membros
- **Membro**: Participa de projetos, cria e edita conteúdo
- **Visualizador**: Apenas visualiza dados

### Existe limite de membros?
Sim, o limite é definido pelo plano de assinatura da equipe.

---

## Tarefas e Sprints

### Quais são os status de tarefa?
- `todo` — A fazer
- `in_progress` — Em progresso
- `done` — Concluída
- `blocked` — Bloqueada

### Posso gerar tarefas automaticamente?
Sim. A IA pode sugerir tarefas a partir de transcrições e User Stories. Você revisa e confirma as sugestões.

### O que são Story Points?
Uma estimativa de esforço relativa para completar uma tarefa. Usada para calcular a velocidade da equipe.

### Como funciona o backlog?
O backlog é a lista de todas as tarefas que ainda não foram alocadas em uma sprint. Ele serve como reservatório para planejamento futuro.

---

## Técnico

### Qual é o stack tecnológico?
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS + Shadcn/ui
- **Backend**: Supabase (PostgreSQL + Auth + Storage + Edge Functions)
- **IA**: OpenAI API (GPT-4o, GPT-4o-mini, Embeddings)
- **Busca**: pgvector (busca semântica)

### Onde ficam as chaves de API?
As chaves da OpenAI são armazenadas como **Supabase Secrets**, nunca no código ou no cliente. Isso garante segurança.

### O sistema é seguro?
Sim. Utiliza Row Level Security (RLS) no PostgreSQL, JWT para autenticação, chaves de API protegidas no servidor e isolamento de dados por projeto.

### Como rodar localmente?
```bash
npm install
cp .env.sample .env  # Configure as variáveis
npm run dev
```
Acesse em `http://localhost:5173`

### Onde encontro o schema do banco?
Em `docs/schema/tables/` (29 tabelas) e `docs/schema/views/` (22 views).

---

## Suporte

### Como obtenho ajuda?
- Consulte esta documentação do helpbot
- Acesse o Guru dentro da plataforma
- Entre em contato: contato@digitalrepublic.com.br
- Website: [digitalrepublic.com.br](https://digitalrepublic.com.br)

### Como reporto um bug?
Envie um e-mail para contato@digitalrepublic.com.br com:
- Descrição do problema
- Passos para reproduzir
- Screenshots (se possível)
- Navegador e versão
