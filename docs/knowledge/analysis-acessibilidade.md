# Analise de Acessibilidade - Chatbot Botsoma

**Data de criacao**: 2026-04-06  
**Ultima atualizacao**: 2026-04-06  
**Analista**: Camila - Especialista em Acessibilidade Digital  
**Arquivo analisado**: test-results.md (15 testes)

---

## Resumo Executivo

O chatbot Botsoma apresenta **deficiencias criticas de acessibilidade** que impedem o uso efetivo por pessoas com baixa escolaridade, pouca familiaridade tecnologica, necessidades de suporte em lingua inglesa, e usuarios em estado emocional vulneravel.

**Classificacao geral**: Acessibilidade INSUFICIENTE (requer revisoes significativas)

---

## 1. Barreira Linguistica: Usuario Anglofono

**Teste 6 - Usuario em Ingles**
- **Problema**: Usuario escreve em ingles, bot responde em portugues sem reconhecer o idioma
- **Impacto**: Usuarios que nao falam portugues estao completamente excluidos do sistema
- **Gravidade**: CRITICA

**Recomendacao**: Implementar deteccao de idioma (language detection) no primeiro turno de conversacao e responder no idioma do usuario. Se nao houver suporte para o idioma, fornecer mensagem de fallback clara: "I apologize, I can only assist in Portuguese. Would you like me to transfer you to a human agent who speaks English?"

---

## 2. Barreira Cognitiva: Jargao Tecnico

**Teste 6 - Resposta Tecnica**
- **Problema**: Bot responde com jargao tecnico ("tabela 'projects' no banco de dados") para usuario iniciante
- **Impacto**: Pessoas com baixa escolaridade ou sem formacao tecnica nao compreendem as instrucoes
- **Gravidade**: ALTA

**Recomendacao**: Adotar sistema de **explicacao multi-nivel**:
- Nivel 1 (Basico): Linguagem simples, analogias do dia a dia, evitar termos tecnicos
- Nivel 2 (Intermediario): Termos tecnicos com explicacao entre parenteses
- Nivel 3 (Avancado): Linguagem tecnica completa

O bot deve detectar o nivel do usuario pela complexidade da pergunta e ajustar a resposta automaticamente.

---

## 3. Barreira Emocional: Ausencia de Empatia

**Teste 9 - Usuario Emocional**
- **Problema**: Usuario expressa tristeza e frustracao ("Estou muito triste e frustrada"), bot ignora completamente a emocao
- **Impacto**: Usuario se sente desvalorizado, aumenta ansiedade, reduz confianca no sistema
- **Gravidade**: ALTA

**Recomendacao**: Implementar **camada de reconhecimento emocional**:
- Detectar palavras emocionais (triste, frustrado, preocupado, anxioso)
- Responder com validacao antes de entrar na solucao tecnica: "Sinto muito que esteja passando por essa dificuldade. Vou te ajudar a resolver isso."
- Oferecer suporte humano imediato quando usuario demonstra alto estresse emocional

---

## 4. Barreira Cognitiva: Sobrecarga de Informacao

**Teste 12 - Multiplas Perguntas**
- **Problema**: Usuario pede orientacao sobre 4 topicos, bot oferece "resumo breve" generico
- **Impacto**: Usuario recebe informacao insuficiente para executar nenhuma das tarefas
- **Gravidade**: MEDIA-ALTA

**Recomendacao**: Implementar **decomposicao guiada**:
- Reconhecer multiplas solicitacoes explicitamente
- Oferecer menu de opcoes: "Entendi que voce precisa de ajuda com 4 topicos. Podemos abordar um de cada vez. Qual e a sua prioridade?"
- Apos resolver um topico, oferecer: "Podemos continuar com o proximo topico da sua lista?"

---

## 5. Barreira de Atencao: Mensagens Longas

**Teste 14 - Mensagem Longa e Detalhada**
- **Problema**: Usuario envia 5 perguntas especificas, bot responde de forma generica simplificada
- **Impacto**: Usuario se esforca para detalhar o contexto, mas recebe resposta que ignora a complexidade
- **Gravidade**: MEDIA

**Recomendacao**: Bot deve **confirmar recebimento de mensagem longa** e fazer perguntas de confirmacao: "Recebi sua mensagem com varios pontos. Para garantir que eu entendi corretamente, sua prioridade principal e a configuracao de permissoes para os 3 squads. Isso esta correto?"

---

## 6. Aspecto Positivo: Seguranca contra Prompt Injection

**Teste 8 - Tentativa de Prompt Injection**
- **Observacao**: Bot identificou corretamente tentativa de acesso nao autorizado
- **Nota**: Este comportamento protege o sistema, mas pode ser interpretado como "robô teimoso" por usuarios legitimos com perguntas fora do escopo

**Recomendacao**: Suavizar mensagem de recusa: "Entendo sua curiosidade sobre como funciona o sistema, mas essa informacao nao esta disponivel neste canal. Como posso te ajudar a usar a plataforma hoje?"

---

## 7. Barreira de Comunicacao: Off-topic sem Resposta

**Teste 11 - Off-topic (Horario e RH)**
- **Problema**: Usuario pergunta sobre horario da empresa e RH, bot NAO responde a pergunta
- **Impacto**: Usuario recebe informacao sobre o produto, mas sua necessidade real (informacao corporativa) e ignorada
- **Gravidade**: MEDIA

**Recomendacao**: Bot deve **reconhecer limites do escopo de forma clara**: "Essa informacao sobre horario e RH nao estou autorizado a fornecer. Sugiro entrar em contato pelo email contato@digitalrepublic.com.br. Posso te ajudar com alguma duvida sobre o uso da plataforma?"

---

## 8. Barreira de Usabilidade: Inputs Invalidos

**Teste 7 - Input Sem Sentido**
- **Problema**: Usuario envia caracteres aleatorios, bot escala imediatamente sem perguntas
- **Comportamento**: Escalacao pode ser apropriada, mas desperdiza recurso humano

**Recomendacao**: Implementar **mensagem de reconhecimento de erro** antes de escalar: "Nao consegui entender sua mensagem. Poderia reformular sua pergunta? Se precisar de ajuda urgente, posso te transferir para um humano."

---

## Recomendacoes Gerais de Acessibilidade

### Linguagem Acessivel
- **Use linguagem simples**: Evitar jargao, siglas, termos tecnicos sem explicacao
- **Estrutura clara**: Uma ideia por frase, paragrafos curtos
- **Exemplos concretos**: "Clique no botao azul 'Criar Projeto'" em vez de "Utilize a funcionalidade de criacao"

### Suporte a Diferentes Niveis Tecnicos
- **Detecao automatica**: Analisar complexidade da pergunta do usuario
- **Perguntas de clarificacao**: "Voce ja usou sistemas de gestao de projetos antes?"
- **Caminhos de onboarding**: Oferecer tutorial passo a passo para iniciantes

### Inclusao de Pessoas com Deficiencia
- **Suporte a leitores de tela**: Garantir que a interface do chat seja compativel
- **Contraste adequado**: Seguir WCAG 2.1 nivel AA
- **Tempo de resposta**: Considerar usuarios com dificuldade motora que digitam lentamente

### Design Inclusivo
- **Nomes de agentes diversos**: "Joana Martins" repetidamente pode criar associacao negativa com a pessoa
- **Tone of voice empatico**: Validar emocoes do usuario antes de solucoes tecnicas
- **Opcao de falar com humano**: Sempre disponivel, sem julgamento

---

## Priorizacao de Melhorias

### Prioridade CRITICA (implementar imediatamente)
1. Detecao de idioma para usuarios anglofonos
2. Camada de empatia e reconhecimento emocional

### Prioridade ALTA (implementar em 2-4 semanas)
3. Sistema de explicacao multi-nivel (basico/intermediario/avancado)
4. Tratamento de off-topic com resposta explicita aos limites

### Prioridade MEDIA (implementar em 1-2 meses)
5. Decomposicao guiada de multiplas perguntas
6. Confirmacao de entendimento para mensagens longas

### Prioridade BAIXA (melhorias continuas)
7. Mensagem de erro para inputs sem sentido antes de escalar
8. Suavizacao de mensagens de seguranca

---

## Conclusao

O chatbot Botsoma possui uma base solida de triagem e escalacao, mas apresenta **deficiencias significativas de acessibilidade** que excluem usuarios anglofonos, pessoas com baixa escolaridade, e usuarios em estado emocional vulneravel.

As recomendacoes priorizam inclusao digital e experiencia humana centrada, alinhadas aos principios de WCAG 2.1 e design inclusivo. Implementar essas melhorias aumentara significativamente a usabilidade para todos os usuarios, nao apenas para aqueles com necessidades especificas de acessibilidade.

---

**Analise concluida por Camila - Especialista em Acessibilidade Digital**