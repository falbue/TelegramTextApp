// Функция для создания редактора CodeMirror
function createCodeMirrorEditor(textareaId, mode = 'javascript', theme = 'monokai') {
    const textarea = document.getElementById(textareaId);
    if (!textarea) {
        console.error(`Textarea with id "${textareaId}" not found.`);
        return null;
    }

    const editor = CodeMirror.fromTextArea(textarea, {
        lineNumbers: true,
        mode: mode,
                theme: theme, // Используем указанную тему
                readOnly: false,
                lineWrapping: true,
                indentUnit: 4,
                tabSize: 4,
                smartIndent: true
            });

        // Функция для автоматической подстройки высоты редактора
    function adjustHeight(editor) {
        const scrollInfo = editor.getScrollInfo();
        const newHeight = scrollInfo.height + scrollInfo.top;
        editor.setSize(null, newHeight);
    }

    adjustHeight(editor);
    editor.on("change", () => adjustHeight(editor));

    return editor;
}

const editor1 = createCodeMirrorEditor('codeEditor1', 'javascript', 'dracula');
const editor2 = createCodeMirrorEditor('codeEditor2', 'python', 'monokai');
const editor3 = createCodeMirrorEditor('codeEditor3', 'python', 'monokai');