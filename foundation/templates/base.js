function manageModal(modal) {
  {% block manageModal %}{% endblock %}
}

function manageEmbeddedForm(element, edit) {
  refreshControls();
  let form = getNearestForm(element);
  if (edit) {
    editForm(form);
  } else {
    displayForm(form);
  }

  let modal = getModal(form);
  if (modal) {
    manageModal(modal)
  }
  {% block manageEmbeddedForm %}{% endblock %}
}

function refreshControls() {
  initButtons();
  {% block refreshControls %}{% endblock %}
}

function refreshPage() {
  refreshControls();
  {% block refreshPage %}{% endblock %}
}

function onLoad() {
  refreshPage();
  {% block onLoad %}{% endblock %}
}

window.onload = onLoad;