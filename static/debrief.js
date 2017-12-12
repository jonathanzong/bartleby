var inputs = document.querySelectorAll("form input");
var textareas = document.querySelectorAll("form textarea");

// restore in-progress answers from localstorage
function populateFromLocalstorage() {
  for (var i = 0, len = inputs.length; i < len; i++) {
    var val = localStorage.getItem(inputs[i].name);
    if (val) {
      switch(inputs[i].type) {
        case 'radio':
          if (inputs[i].value == val) {
            inputs[i].checked = true;
          }
          break;
        // TODO: if there are other input types
      }
    }
  }
  for (var i = 0, len = textareas.length; i < len; i++) {
    var val = localStorage.getItem(textareas[i].name);
    if (val) {
      textareas[i].value = val;
    }
  }
}

populateFromLocalstorage();

// save in-progress answers in local storage
function onChange (evt) {
  localStorage.setItem(this.name, this.value);
}

for (var i = 0, len = inputs.length; i < len; i++) {
  inputs[i].addEventListener('change', onChange);
}

for (var i = 0, len = textareas.length; i < len; i++) {
  textareas[i].addEventListener('input', onChange);
}
