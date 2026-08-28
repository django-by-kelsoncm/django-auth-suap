======================
Escopos OAuth2 do SUAP
======================

Escopos Disponíveis
===================

.. list-table::
   :widths: 25 30 45
   :header-rows: 1

   * - Escopo
     - Descrição
     - Atributos Chave
   * - ``identificacao``
     - Identificação básica
     - ``matricula``, ``nome_usual``, ``campus``, ``tipo_usuario``, ``url_foto_75x100``
   * - ``email``
     - Endereço de email
     - ``email``
   * - ``documentos_pessoais``
     - Documentos pessoais
     - ``cpf``, ``rg``
   * - ``dados_academicos``
     - Dados acadêmicos
     - ``curso``, ``situacao``, ``periodo_atual``
   * - ``dados_pessoais``
     - Dados pessoais
     - ``data_nascimento``, ``naturalidade``, ``tipo_sanguineo``, ``filiacao``
   * - ``reitoria``
     - Dados de nível institucional
     - Campos específicos da instituição

Exemplo de Resposta SUAP
========================

.. code-block:: json

   {
     "id": 12345,
     "matricula": "20211234567",
     "nome_usual": "João Silva",
     "cpf": "12345678901",
     "rg": "1234567",
     "filiacao": ["Maria Silva", "José Silva"],
     "data_nascimento": "1995-01-15",
     "naturalidade": "Natal/RN",
     "tipo_sanguineo": "A+",
     "email": "joao.silva@academico.ifrn.edu.br",
     "url_foto_75x100": "https://suap.ifrn.edu.br/media/...",
     "tipo_usuario": "Aluno",
     "campus": "Natal-Central",
     "curso": "Tecnologia em Análise e Desenvolvimento de Sistemas",
     "situacao": "Matriculado"
   }

Configurando Escopos
====================

.. code-block:: python

   SUAP_AUTH = {
       "SCOPES": ["identificacao", "email", "dados_academicos"],
   }
