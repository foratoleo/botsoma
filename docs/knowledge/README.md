# Base de Conhecimento

Coloque aqui os arquivos `.md` ou `.txt` que o bot deve usar para responder perguntas.

## Como funciona

1. O bot carrega todos os arquivos `.md` e `.txt` deste diretorio (inclusive subdiretorios) ao iniciar
2. Os arquivos sao divididos em secoes por headings (`##` e `###`)
3. Quando um usuario faz uma pergunta, o bot busca as secoes mais relevantes por keyword overlap
4. As secoes encontradas sao enviadas como contexto para o LLM gerar a resposta

## Formato recomendado

Use markdown com headings para organizar o conteudo:

```markdown
# Titulo do Documento

## Funcionalidade X

Descricao da funcionalidade X...

## Funcionalidade Y

Descricao da funcionalidade Y...
```

## Exemplos

- `guia-usuario.md` - Guia do usuario do sistema
- `faq.md` - Perguntas frequentes
- `configuracao.md` - Guia de configuracao
- `troubleshooting.md` - Problemas comuns e solucoes
