document.addEventListener('DOMContentLoaded', function() {
  fetch('/data')
  .then(response => response.json())
  .then(data => buildGraph(data))
  .catch(error => console.error('Ошибка при загрузке данных:', error));
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

    // Проверка на существование меню
    if (!menu) {
      nodes.push({
        id: currentMenuName,
        label: currentMenuName,
        color: { 
          background: 'red',
          highlight: {
            background: '#9f0000', // Светло-серый фон при подсветке
            border: '#333' // Темно-серая рамка при подсветке
          }
        },
        classes: 'not-found' // Добавляем класс для стилизации
      });
      return; // Прерываем обработку, если меню не существует
    }

    nodes.push({ id: currentMenuName, label: currentMenuName,});

    // Обработка кнопок (buttons)
    if (menu.buttons) {
      for (const [nextMenu, buttonTextKey] of Object.entries(menu.buttons)) {
    // Проверяем, если nextMenu равно "return", пропускаем этот шаг
        if (nextMenu === "return") {
          continue;
        }

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
          label: buttonText,
      // Добавим уникальный класс для обычных кнопок
          classes: 'regular-edge'
        });
        traverseMenu(nextMenu);
      }
    }

    // Обработка кнопки "return" (убираем текст и добавляем стиль)
    if (menu.return) {
      const nextMenuReturn = menu.return;
      const buttonTextReturn = data.var_buttons["return"] || "‹ Назад";
      edges.push({
        from: currentMenuName,
        to: nextMenuReturn,
        // Убираем текст
        label: '',
        // Серый цвет и пунктирная линия для отличия
        color: { color: 'gray' },
        dashes: true, // Пунктирная линия
        arrows: { to: { enabled: true } },
        // Добавляем уникальный класс для return
        classes: 'return-edge'
      });
      traverseMenu(nextMenuReturn);
    }

    // Обработка handler.menu
    if (menu.handler && menu.handler.menu) {
      const nextMenuHandler = menu.handler.menu;
      edges.push({
        from: currentMenuName,
        to: nextMenuHandler,
        label: 'handler',
        // Добавим класс для handler
        classes: 'handler-edge'
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
      },
      // Добавляем стили для класса 'not-found'
      color: {
        background: '#fff', // Белый фон по умолчанию
        border: '#000', // Черная рамка по умолчанию
        highlight: {
          background: '#e6e6e6', // Светло-серый фон при подсветке
          border: '#333' // Темно-серая рамка при подсветке
        }
      },
      borderWidth: 1,
      borderWidthSelected: 2,
      shadow: true
    },
    edges: {
      arrows: 'to',
      font: {
        align: 'middle',
        size: 12
      },
      // Стили для классов ребер
      color: {
        inherit: 'from'
      },
      smooth: {
        type: 'continuous'
      },
    },
    interaction: {
      dragView: true,
      zoomView: true
    },

    layout: {
      randomSeed: 42,
      improvedLayout: true,
      clusterThreshold: 150
    },
    physics: {
      enabled: true,
      barnesHut: {
        gravitationalConstant: -8000,
        springLength: 200,
        springConstant: 0.04, 
        damping: 0.09
      }
    }
  };

  const network = new vis.Network(container, networkData, options);

  // Добавляем обработчик двойного клика
  network.on("doubleClick", function(params) {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0];
      window.location.href = '/menu/' + encodeURIComponent(nodeId);
    }
  });
}