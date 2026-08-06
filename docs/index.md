# django-suap-auth

Backend de autenticação OAuth2 do Django para **SUAP** (Sistema Unificado de Administração Pública), o sistema de gestão acadêmica do IFRN.

## Funcionalidades

- Fluxo de autorização de código OAuth2 com SUAP
- Escopos configuráveis (`identificacao`, `email`, `documentos_pessoais`, `dados_academicos`, `dados_pessoais`, `reitoria`)
- Mapeamento flexível de atributos da resposta SUAP para campos do modelo de usuário do Django
- Armazenamento opcional em campo JSON para a resposta completa do SUAP
- Página de login intermediária configurável (`SUAP_AUTH['DIRECT_REDIRECT']`)
- Proteção CSRF via validação do parâmetro de estado

## Links Rápidos

- [Instalação](installation.md)
- [Configuração](configuration.md)
- [Escopos](scopes.md)
- [Mapeamento de atributos](attribute-mapping.md)
- [Pipeline de perfil de usuário](user-info-pipeline.md)
- [Fetchers (Busca de dados)](fetchers.md)
- [Mappers (Mapeamento)](mappers.md)
- [Fluxo de autenticação](auth-flow.md)
- [Sandboxes](sandboxes.md)
- [Desenvolvimento](development.md)
- [Release](release.md)
