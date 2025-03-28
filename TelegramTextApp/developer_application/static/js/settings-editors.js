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

function insertTextIntoEditor(editor, text) {
    if (editor) {
        editor.setValue(text);
    } else {
        console.error("Editor is not initialized.");
    }
}

function GetCode() {
    const currentUrl = window.location.href;
    const urlParts = currentUrl.split('/'); 
    const menuName = urlParts[urlParts.length - 1];
    const url = `/menu/${menuName}`;

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(jsonString => {
        const codeEditor = document.getElementById('codeEditor1');
        const data = JSON.parse(jsonString);

        if (data.menu.function) {
            const SectionFunction = document.getElementById("function");
            SectionFunction.classList.remove("none");
            fetch(`/function/${data.menu.function}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(CodeFunction => {
                console.log(CodeFunction)
                insertTextIntoEditor(editor2, CodeFunction);
            })

        }

        if (data.menu.handler) {
            const SectionFunction = document.getElementById("handler");
            SectionFunction.classList.remove("none");
            fetch(`/function/${data.menu.handler.function}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(CodeFunction => {
                console.log(CodeFunction)
                insertTextIntoEditor(editor3, CodeFunction);
            })
        }

        const code = JSON.stringify(data.menu, null, 4);
        insertTextIntoEditor(editor1, code);

        const Name = document.getElementById("menu-name");
        Name.textContent = menuName;

    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to load menu data.');
    });
}

GetCode()