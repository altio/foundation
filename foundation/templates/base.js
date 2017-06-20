function manageEmbeddedForm(form) {
  form.addEventListener("submit", submitEmbeddedForm);
  {% block manageEmbeddedForm %}{% endblock %}
}

function manageModal(modal) {
  let form = modal.querySelector('form');
  manageEmbeddedForm(form);
  {% block manageModal %}{% endblock %}
}

function refreshPage() {
  initPopupListeners();
  {% block refreshPage %}{% endblock %}
}

function refreshEmbed(form) {
  let url = form.action;

  // get the embedded form and render it
  $.ajax({
    type: "GET",
    url: url,
    contentType: "text/html; charset=utf-8",
  }).done(function(data, textStatus, jqXHR) {
    form.outerHTML = data;
    {% block refreshEmbed %}{% endblock %}
    refreshPage();
  }).fail(function(jqXHR, textStatus, errorThrown) {
    form.innerHTML = '<p>Sorry there has been an error.  Please try back later.</p>';
  });
}

function onLoad() {
  refreshPage();
  {% block onLoad %}{% endblock %}
}

window.onload = onLoad;
