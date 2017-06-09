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

function getNearestForm(element) {
  var form = element;
  if (form.nodeName != 'FORM') {
    while ((form = form.parentElement) && (form.nodeName != 'FORM'));
  }
  return form;
}

function editObject(element) {
  var form = getNearestForm(element);
  $('#'+form.id+'_edit_button').hide();
  $('#'+form.id+' *').filter(':input').each(function() {
    $(this).show();
    var display = $('#display_' + this.name);
    display.hide();
  });
}

function displayObject(element) {
  var form = getNearestForm(element);
  $('#'+form.id+' *').filter(':input').each(function() {
    $(this).hide();
    var display = $('#display_' + this.name);
    display.text(this.value);
    display.show();
  });
  $('#'+form.id+'_edit_button').show();
}

function submitEmbeddedForm(event) {
  event.preventDefault();
  let form = event.currentTarget;

  // see if this embedded form is in a modal or not
  let modal = form;
  while ((modal = modal.parentElement) && !modal.classList.contains('modal'));

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
      if (modal) {
        manageModal(modal);
      } else {
        // TODO: non-modal is already "ready" to edit... need to re-init js tho
        // manageEmbed(form)
      }
    } else {
      if (modal) {
        $(modal).modal('hide');

        // original implementation tries to refresh formset related to object
        // changed... having it look up the page's formset for now since we are
        // not designing this to allow editing of inline formset objects (yet)
        // let formset_id = '#' + form.id + 'set';
        // let formset = document.body.querySelector(formset_id);
        let formset = document.body.querySelector('.formset');
        form.outerHTML = '';
        refreshEmbed(formset);
      } else {
        form.outerHTML = data;
        displayObject(form);
      }
    }
  }).fail(function(jqXHR, textStatus, errorThrown) {
    form.innerHTML = '<p>Sorry there has been an error.  Please try back later.</p>';
  });
}

/* FOR REFERENCE: BUILT IN TEMPLATE SPACE
function manageEmbeddedForm(form) {
  form.addEventListener("submit", submitEmbeddedForm);
}

function manageModal(modal) {
  let form = modal.querySelector('form');
  manageEmbeddedForm(form);
}
*/

function openPopup(event) {
  let target = event.currentTarget;

  // determine if initiator is already in a modal
  let modal = target;
  while ((modal = modal.parentElement) && !modal.classList.contains('modal'));

  // launch a modal or popup window, as appropriate
  if (modal) {
    let url = target.getAttribute('data-url');
    window.open(url);
    // TODO: manage popped up window
  } else {
    let url = target.getAttribute('data-embed-url');

    /* get the embedded form and render it */
    $.ajax({
      type: "GET",
      url: url,
      contentType: "text/html; charset=utf-8",
    }).done(function(data, textStatus, jqXHR) {
      let modal = document.body.querySelector('#modal-container');
      let modalContent = modal.querySelector('.modal-content');
      modalContent.innerHTML = data ? data : '';
      manageModal(modal);
      refreshPage();
      $(modal).modal('show');
    });
  }
}

function initPopupListeners() {
  let popupControls = document.body.querySelectorAll('.popup-trigger');
  for (var ctrl of popupControls) {
    ctrl.addEventListener("click", openPopup);
  }
}

/* FOR REFERENCE: BUILT IN TEMPLATE SPACE
function refreshPage() {
  initPopupListeners();
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
    refreshPage();
  }).fail(function(jqXHR, textStatus, errorThrown) {
    form.innerHTML = '<p>Sorry there has been an error.  Please try back later.</p>';
  });
}

function onLoad() {
  refreshPage();
}

window.onload = onLoad;
*/