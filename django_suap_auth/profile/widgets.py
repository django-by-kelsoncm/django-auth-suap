from django_json_widget.widgets import JSONEditorWidget


class InlineJSONEditorWidget(JSONEditorWidget):
    """JSONEditorWidget que também funciona em linhas adicionadas a inlines do Django Admin.

    O widget original inicializa o editor por um ``<script>`` inline. No formulário-modelo vazio do
    inline (``__prefix__``) esse script roda sobre o modelo e, ao clicar em "Adicionar outro(a)", o
    admin apenas clona o HTML: o editor clonado fica inerte e os scripts clonados não executam.
    Aqui a inicialização fica num JS estático que ignora o formulário-modelo e trata o evento
    ``formset:added``.
    """

    template_name = "django_suap_auth_profile/widgets/inline_json_editor.html"

    class Media:
        js = ("django_suap_auth_profile/js/inline_json_editor.js",)
