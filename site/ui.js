(function () {
  var button = document.getElementById("tmgDdBtn");
  var menu = document.getElementById("tmgDdMenu");

  if (!button || !menu) {
    return;
  }

  function closeMenu() {
    menu.classList.remove("open");
    button.classList.remove("open");
    button.setAttribute("aria-expanded", "false");
  }

  button.addEventListener("click", function (event) {
    event.stopPropagation();
    var isOpen = menu.classList.toggle("open");
    button.classList.toggle("open", isOpen);
    button.setAttribute("aria-expanded", isOpen ? "true" : "false");
  });

  menu.addEventListener("click", function (event) {
    event.stopPropagation();
  });

  document.addEventListener("click", closeMenu);

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeMenu();
      button.focus();
    }
  });
})();
