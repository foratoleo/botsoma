# Rules

## Interaction
- Do not over explain the execution steps or reasoning unless explicitly asked.
- When the user asks a question, only answer and do not edit or create anything unless explicitly requested.
- List all created or changed files (full path)

## Code Quality
- Follow existing project patterns and conventions
- Always apply the DRY (Don't Repeat Yourself) principle.
- Always apply the Single Responsibility principle (each function or method must have only one responsibility).
- Break down code into small, reusable components when possible.
- Keep all functions and methods short and concise (few lines only).
- Always use English naming conventions for methods and variables.
- Never use magic numbers in the code. Store them in a dedicated constants file with clear naming.
- Never Suppress Silently: All errors must be logged, handled, or escalated appropriately

## Git
- Do NOT Auto-commit changes
- NEVER mention or co-author Claude or Claude Code
- Do not mention tests in PRs unless have evidences, like screenshots or reports
- For git operations invoke the git-specialist agent using Task tool with subagent_type="dr:git-specialist". ALL git operations MUST be delegated to this agent.


## Database Queries
- ALWAYS review table names and column names before writing a query
- Database schema can be find in docs/schema
- When queries involve one or more JOINs, ALWAYS create a database view instead of writing complex queries in the frontend.

## Documentation
- Do not use emojis in any document.
- Do not add non-functional comments or instructions inside source code.
