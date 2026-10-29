/*
 * Inicializa os editores do InlineJSONEditorWidget (django_suap_auth.profile.widgets).
 *
 * Ignora o formulário-modelo vazio dos inlines (id com "__prefix__") e inicializa as linhas
 * adicionadas no evento "formset:added" do Django Admin, que dispara depois de os ids e names
 * da linha nova terem sido renumerados.
 */
(function () {
    "use strict";

    function initEditor(container) {
        if (container.jsonEditor || container.id.indexOf("__prefix__") !== -1) {
            return;
        }
        const textarea = document.getElementById(container.id + "_textarea");
        if (!textarea) {
            return;
        }
        const dataScript = document.getElementById(textarea.name + "_data");
        const content = dataScript ? dataScript.textContent : "null";
        const options = JSON.parse(container.dataset.jsonEditorOptions || "{}");

        // Na linha clonada sobra o HTML do editor do formulário-modelo: descarta antes de criar o novo.
        container.replaceChildren();

        let editor;
        options.onChange = function () {
            try {
                textarea.value = JSON.stringify(editor.get());
            } catch (erro) {
                // JSON inválido em edição: envia o texto como está para o servidor validar o campo.
                textarea.value = editor.getText();
            }
        };
        editor = new JSONEditor(container, options);
        textarea.value = content;
        editor.set(JSON.parse(content));

        window[container.id + "_editor"] = editor;
        container.jsonEditor = editor;
    }

    function initAll(root) {
        root.querySelectorAll("[data-json-editor]").forEach(initEditor);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () {
            initAll(document);
        });
    } else {
        initAll(document);
    }
    document.addEventListener("formset:added", function (event) {
        initAll(event.target);
    });
})();
