/* The functions contained herein deserve a little explanation.
 * Per the design, we expect one of four interactions for CRUDL type operations.
 * Non-embed, non-popup: The default mode (i.e. page view).
 * Non-embed, popup: Access a secondary object from a secondary object when
 * in-page popup (i.e. modal) is not available. (i.e. page view in new window)
 * Embed, non-popup: Access a secondary object that the view is aware of but
 * has its own processing on another URL (e.g. AJAX, AHAH)
 * Embed, popup: Access a primary or secondary object on an in-page popup that
 * has its own processing on another URL (i.e. modal using AJAX/AHAH)
 */

function getModal(element) {
  while ((element = element.parentElement) && !element.classList.contains('modal'));
  return element;
}

function refreshEmbed(form) {
  let url = form.action;
  let target = form.parentElement;
  loadEmbed(url, target);
}

function onSubmitSuccess(form, data) {
  // TODO: handle close of window
  // if a window, close, then refresh page

  let modal = getModal(form);
  if (modal) {
    $(modal).modal('hide');

    // original implementation tries to refresh formset related to object
    // changed... having it look up the page's formset for now since we are
    // not designing this to allow editing of inline formset objects (yet)
    // let formset_id = '#' + form.id + 'set';
    // let formset = document.body.querySelector(formset_id);
    let formset = document.body.querySelector('form.formset');
    form.outerHTML = '';
    refreshEmbed(formset);
  } else {
    form.outerHTML = data;
    displayForm(form);
  }
  refreshPage();
}

function submitEmbeddedForm(event) {
  event.preventDefault();
  let form = event.currentTarget;

  /* post the embedded form and render errors or dismiss */
  //$.ajaxPrefilter(function (settings, originalOptions, xhr) {
  //    xhr.setRequestHeader('X-CSRFToken', '{{ csrf_token }}');
  //});

  /* post the embedded form and render errors or dismiss */
  $.ajax({
    type: "POST",
    url: form.action,
    data: new FormData(form),
    contentType: false,
    processData: false,
  }).done(function(data, textStatus, jqXHR) {
    if (data.search('form-errors') != -1) {
      form.outerHTML = data;
      // get clean copy of element
      form = document.getElementById(form.id);
      manageEmbeddedForm(form, true);
    } else {
      onSubmitSuccess(form, data);
    }
  }).fail(function(jqXHR, textStatus, errorThrown) {
    form.innerHTML = '<p>Sorry there has been an error.  Please try back later.</p>';
  });
}

function editForm(form) {
  form.classList.add("edit");
  form.addEventListener("submit", submitEmbeddedForm);
}

function displayForm(form) {
  form.classList.remove("edit");
}

function getNearestForm(element) {
  let form = element ? element : $('#content form')[0];
  if (form.nodeName != 'FORM') {
    while ((form = form.parentElement) && (form.nodeName != 'FORM'));
  }
  return form;
}

// function manageEmbeddedForm(element, edit) in base.js
// => refreshControls()
// => [edit|display]Form()
// => if modal: manageModal()

function showModal(modal, target) {
  target.innerHTML = '<div class="modal-body text-center"><i class="fa fa-spinner fa-pulse fa-3x fa-fw"></i><span class="sr-only">Loading...</span></div>';
  $(modal).modal('show');
}

function loadEmbed(url, target) {
  // get the embedded form and render it
  $.ajax({
    type: "GET",
    url: url,
    contentType: "text/html; charset=utf-8",
  }).done(function(data, textStatus, jqXHR) {
    target.innerHTML = data;
    let form = target.querySelector('form');
    manageEmbeddedForm(form, false);
  }).fail(function(jqXHR, textStatus, errorThrown) {
    target.innerHTML = '<p>Sorry there has been an error.  Please try back later.</p>';
  });
}

function openPopup(element) {
  // determine if initiator is already in a modal
  let modal = getModal(element);

  // launch a modal or popup window, as appropriate
  if (modal) {
    let url = target.getAttribute('data-url');
    window.open(url);
    // TODO: manage popped up window
  } else {
    let url = element.getAttribute('data-embed-url');
    let modal = document.body.querySelector('#modal-container');
    let target = modal.querySelector('.modal-content');
    showModal(modal, target);
    loadEmbed(url, target);
  }
}

function initButtons() {
  // attach click listener to all buttons that launch a popup
  for (var ctrl of document.body.querySelectorAll('.popup-trigger')) {
    ctrl.addEventListener("click", function(event) {
      let button = event.currentTarget;
      openPopup(button);
    });
  }
  // attach click listener to all buttons that transition to edit mode
  for (var ctrl of document.body.querySelectorAll('.edit-this-form')) {
    ctrl.addEventListener("click", function(event) {
      let button = event.currentTarget;
      let form = getNearestForm(button);
      editForm(form);
    });
  }
}

// function refreshControls() in base.js
// => initButtons()

// function refreshPage() in base.js
// => refreshControls()

// function onLoad() in base.js
// => refreshPage()

// window.onload = onLoad in base.js