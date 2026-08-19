========================================================================
Modelos Prontos de Perfil (`django_suap_auth.profile`)
========================================================================

O submódulo ``django_suap_auth.profile`` oferece uma estrutura de modelos Django pré-construídos para armazenar os dados de perfil do SUAP de forma imediata nos seus projetos, dispensando a necessidade de mapear campos manualmente.

Visão Geral dos Modelos
=======================

O submódulo define 3 modelos principais:

1. ``Perfil``: Modelo 1-para-1 vinculado ao modelo ``User`` do Django (via ``user.suap_profile``). Armazena dados pessoais, acadêmicos e funcionais.
2. ``DadosBrutos``: Modelo 1-para-1 vinculado ao ``Perfil`` (via ``perfil.raw_data``). Armazena em um campo ``JSONField`` a resposta completa em JSON retornada pelas APIs do SUAP.
3. ``Vinculo``: Modelo 1-para-Muitos vinculado ao ``Perfil`` (via ``perfil.vinculos``). Armazena a lista de vínculos do usuário com a instituição (ex: servidor, aluno, estagiário).

Instalação e Configuração
=========================

1. Adicione ``django_suap_auth.profile`` ao seu ``INSTALLED_APPS`` no ``settings.py``:

.. code-block:: python

   INSTALLED_APPS = [
       # ...
       "django_suap_auth",
       "django_suap_auth.profile",
   ]

2. Ative o backend de autenticação com sincronização automática de perfil no ``settings.py``:

.. code-block:: python

   AUTHENTICATION_BACKENDS = [
       "django_suap_auth.profile.backends.SuapProfileAuthBackend",
       "django.contrib.auth.backends.ModelBackend",
   ]

3. Execute as migrações do banco de dados:

.. code-block:: bash

   python manage.py migrate

Atributos do Modelo ``Perfil`` por Tipo de Usuário
===================================================

O modelo ``Perfil`` reúne em uma única tabela todos os atributos suportados pelas APIs do SUAP, organizados de forma clara:

1. Atributos Comuns (Presentes em Todos os Usuários)
----------------------------------------------------

Estes atributos são compartilhados por **Servidores**, **Alunos** e **Usuários Externos**:

.. list-table::
   :widths: 30 20 50
   :header-rows: 1

   * - Campo
     - Tipo
     - Descrição
   * - ``suap_id``
     - IntegerField
     - ID interno do usuário no SUAP.
   * - ``matricula``
     - CharField
     - Matrícula funcional ou acadêmica.
   * - ``nome_usual``
     - CharField
     - Nome de exibição/usual no SUAP.
   * - ``nome_social``
     - CharField
     - Nome social registrado.
   * - ``cpf``
     - CharField
     - CPF formatado ou numérico.
   * - ``rg``
     - CharField
     - Registro Geral (RG) com órgão expedidor.
   * - ``filiacao``
     - JSONField
     - Lista com nomes dos pais/responsáveis.
   * - ``data_nascimento``
     - DateField
     - Data de nascimento.
   * - ``naturalidade``
     - CharField
     - Cidade e UF de nascimento.
   * - ``tipo_sanguineo``
     - CharField
     - Tipo sanguíneo (ex: A+, O-).
   * - ``sexo``
     - CharField
     - Sexo ("M" ou "F").
   * - ``passaporte``
     - CharField
     - Número do passaporte (quando aplicável).
   * - ``campus``
     - CharField
     - Sigla ou nome do Campus de vinculação.
   * - ``email_secundario``
     - EmailField
     - E-mail pessoal/secundário.
   * - ``email_google_classroom``
     - EmailField
     - E-mail da conta Google Workspace da instituição.
   * - ``email_academico``
     - EmailField
     - E-mail institucional.
   * - ``email_preferencial``
     - EmailField
     - E-mail preferencial de contato.
   * - ``url_foto_75x100``
     - URLField
     - URL da foto de perfil (miniatura).
   * - ``url_foto_150x200``
     - URLField
     - URL da foto de perfil (média).
   * - ``tipo_usuario``
     - CharField
     - Tipo do usuário (ex: Servidor, Aluno, Usuário Externo).
   * - ``tipo_vinculo``
     - CharField
     - Vínculo principal (ex: Docente, Técnico-Administrativo).
   * - ``telefones_institucionais``
     - JSONField
     - Lista de telefones de contato.
   * - ``curriculo_lattes``
     - CharField
     - URL ou ID do Currículo Lattes.

2. Atributos Específicos de Servidores
---------------------------------------

Preenchidos exclusivamente quando o usuário é um **Servidor** (Docente ou Técnico-Administrativo):

.. list-table::
   :widths: 30 20 50
   :header-rows: 1

   * - Campo
     - Tipo
     - Descrição
   * - ``categoria``
     - CharField
     - Categoria funcional (ex: "Docente", "Técnico-Administrativo").
   * - ``cargo``
     - CharField
     - Nome do cargo efetivo (ex: "Professor EBTT", "Analista de TI").
   * - ``setor_suap``
     - CharField
     - Sigla do setor de lotação no SUAP.
   * - ``setor_siape``
     - CharField
     - Código ou descrição do setor no SIAPE.
   * - ``jornada_trabalho``
     - CharField
     - Regime de trabalho (ex: "40 horas", "Dedicação Exclusiva").
   * - ``disciplina_ingresso``
     - CharField
     - Área/disciplina de concurso de ingresso.

3. Atributos Específicos de Alunos
-----------------------------------

Preenchidos exclusivamente quando o usuário é um **Aluno**:

.. list-table::
   :widths: 30 20 50
   :header-rows: 1

   * - Campo
     - Tipo
     - Descrição
   * - ``curso``
     - CharField
     - Nome do curso matriculado.
   * - ``turno``
     - CharField
     - Turno do curso do aluno (ex: "EAD", "Matutino").
   * - ``matriz``
     - CharField
     - Código/nome da matriz curricular.
   * - ``situacao``
     - CharField
     - Situação da matrícula (ex: "Não concluído", "Matriculado", "Formado").
   * - ``situacao_sistemica``
     - CharField
     - Situação sistêmica geral do aluno no SUAP.
   * - ``ira``
     - CharField
     - Índice de Rendimento Acadêmico (IRA).
   * - ``ingresso``
     - CharField
     - Período de ingresso no curso (ex: "2021.1").
   * - ``periodo_referencia``
     - IntegerField
     - Período letivo atual do aluno.
   * - ``qtd_periodos``
     - IntegerField
     - Quantidade total de períodos do curso.
   * - ``data_migracao``
     - CharField
     - Data de migração do registro de aluno.
   * - ``impressao_digital``
     - BooleanField
     - Indica se a digital está cadastrada.
   * - ``emitiu_diploma``
     - BooleanField
     - Indica se o diploma foi emitido.
   * - ``matricula_regular``
     - BooleanField
     - Indica se a matrícula do aluno é regular.
   * - ``educasenso``
     - CharField
     - Código do aluno no Educacenso / INEP.
   * - ``cota_sistec``
     - CharField
     - Cota Sistec associada ao aluno.
   * - ``cota_mec``
     - CharField
     - Cota MEC associada ao aluno.
   * - ``linha_pesquisa``
     - CharField
     - Linha de pesquisa do aluno (pós-graduação / pesquisa).

4. Usuários Externos / Prestadores de Serviço
---------------------------------------------

Para **Usuários Externos** ou prestadores de serviço terceirizados:
- Os atributos de Servidor e Aluno permanecem vazios/nulos.
- O campo ``tipo_usuario`` registra ``"Usuário Externo"`` ou ``"Prestador de Serviço"``.
- Os dados básicos de identificação, fotos, e-mails e CPF são devidamente sincronizados nos atributos comuns.

Sincronização Automática
========================

Ao utilizar o backend ``SuapProfileAuthBackend``, em todo login (ou criação de usuário) os seguintes procedimentos são executados automaticamente:

1. Uma instância de ``Perfil`` é criada/atualizada para o usuário.
2. A resposta JSON completa acumulada da API do SUAP é salva em ``DadosBrutos`` (acessível via ``user.suap_profile.raw_data.data``).
3. A lista de vínculos em ``Vinculo`` é sincronizada (acessível via ``user.suap_profile.vinculos.all()``).
