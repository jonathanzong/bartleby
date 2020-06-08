var inputs = document.querySelectorAll("form input");
var textareas = document.querySelectorAll("form textarea");

// restore in-progress answers from localstorage
function populateFromLocalstorage() {
  for (var i = 0, len = inputs.length; i < len; i++) {
    var val = localStorage.getItem(inputs[i].name);
    switch(inputs[i].type) {
      case 'checkbox':
        inputs[i].checked = val == 'true';
        if (inputs[i].name === 'opt_out') {
          document.querySelector(".opt-out-checkbox").style.background = inputs[i].checked ? "#ffeeee" : "#f3f3f3";
        }
        break;
      case 'radio':
      default:
        if (inputs[i].value == val) {
          inputs[i].checked = true;
        }
        break;
      // add here if there are other input types
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
  switch(this.type) {
    case 'checkbox':
      localStorage.setItem(this.name, this.checked);
      submit(this.name, this.checked);
      if (this.name === 'opt_out') {
        document.querySelector(".opt-out-checkbox").style.background = this.checked ? "#ffeeee" : "#f3f3f3";
      }
      break;
    case 'radio':
    default:
      localStorage.setItem(this.name, this.value);
      submit(this.name, this.value);
      break;
    // add here if there are other input types
  }
}

for (var i = 0, len = inputs.length; i < len; i++) {
  inputs[i].addEventListener('change', onChange);
}

for (var i = 0, len = textareas.length; i < len; i++) {
  textareas[i].addEventListener('input', debounce(onChange, 500));
}

///

function debounce(func, wait, immediate) {
  var timeout;
  return function() {
    var context = this, args = arguments;
    var later = function() {
      timeout = null;
      if (!immediate) func.apply(context, args);
    };
    var callNow = immediate && !timeout;
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
    if (callNow) func.apply(context, args);
  };
};

function submit(name, value) {
  var data = {};
  data[name] = value;
  data = JSON.stringify(data);

  var request = new XMLHttpRequest();
  request.open('POST', window.location.pathname, true);
  request.setRequestHeader('Content-Type', 'application/json');
  request.setRequestHeader('X-CSRFToken', document.getElementById('csrf_token').value);
  request.send(data);
}
