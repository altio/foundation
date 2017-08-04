function manageModal(modal) {
  {% block manageModal %}{% endblock %}
}

function manageEmbeddedForm(element) {
  refreshControls();
  let form = getNearestForm(element);
  form.addEventListener("submit", submitEmbeddedForm);

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