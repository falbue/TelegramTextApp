document.addEventListener('DOMContentLoaded', function() {
  fetch('/data')
    .then(response => response.json())
    .then(data => buildGraph(data));
});

function buildGraph(data) {
  const container = document.getElementById('graph');
  const nodes = [];
  const edges = [];
  const visited = new Set();

  function traverseMenu(currentMenuName) {
    if (visited.has(currentMenuName)) return;
    visited.add(currentMenuName);

    const menu = data.menus[currentMenuName];
    nodes.push({ id: currentMenuName, label: currentMenuName });

    // Обработка кнопок (buttons)
    if (menu.buttons) {
      for (const [nextMenu, buttonTextKey] of Object.entries(menu.buttons)) {
        let buttonText = buttonTextKey;
        if (data.var_buttons[buttonTextKey]) {
          const varButton = data.var_buttons[buttonTextKey];
          if (typeof varButton === 'object' && varButton.text) {
            buttonText = varButton.text;
          } else if (typeof varButton === 'string') {
            buttonText = varButton;
          }
        }
        edges.push({
          from: currentMenuName,
          to: nextMenu,
          label: buttonText
        });
        traverseMenu(nextMenu);
      }
    }

    // Обработка кнопки "return"
    if (menu.return) {
      const nextMenuReturn = menu.return;
      const buttonTextReturn = data.var_buttons["return"] || "‹ Назад";
      edges.push({
        from: currentMenuName,
        to: nextMenuReturn
      });
      traverseMenu(nextMenuReturn);
    }

    // Обработка handler.menu
    if (menu.handler && menu.handler.menu) {
      const nextMenuHandler = menu.handler.menu;
      edges.push({
        from: currentMenuName,
        to: nextMenuHandler,
        label: 'handler'
      });
      traverseMenu(nextMenuHandler);
    }
  }

  // Начинаем с начального меню из commands.start.menu
  const startMenu = data.commands.start.menu;
  traverseMenu(startMenu);

  // Настройка графа с помощью vis.js
  const networkData = {
    nodes: new vis.DataSet(nodes),
    edges: new vis.DataSet(edges)
  };

  const options = {
    nodes: {
      shape: 'box',
      margin: 10,
      font: {
        size: 14
      }
    },
    edges: {
      arrows: 'to',
      font: {
        align: 'middle',
        size: 12
      }
    },
    interaction: {
      dragView: true,
      zoomView: true
    },
    layout: {
      hierarchical: {
        direction: 'UD' // Вертикальное направление
      }
    }
  };

  const network = new vis.Network(container, networkData, options);

  // Добавляем обработчик двойного клика
  network.on("doubleClick", function(params) {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0];
      window.location.href = '/' + encodeURIComponent(nodeId);
    }
  });
}