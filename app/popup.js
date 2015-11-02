document.addEventListener('DOMContentLoaded',init);
function $(id) {
  return document.getElementById(id);
}

var current_url;

function init() {
  getCurrentTabUrl(function(url) {
    getQuality(url);
    current_url = url;
  });
  $("launch_button").onclick = function() {
    if (typeof current_url != "undefined"){
      var selector = $("quality_selector");
      var quality = selector.options[selector.selectedIndex].value;
      startStream(current_url, quality);
    } else {
      renderError("Bad url");
    }
  }
}

function show_spinner(){
  $("spinner").style.display = "block";
}

function hide_spinner(){
  $("spinner").style.display = "none";
}

function getCurrentTabUrl(callback) {
  var queryInfo = {
    active: true,
    currentWindow: true
  };

  chrome.tabs.query(queryInfo, function(tabs) {
    var tab = tabs[0];
    var url = tab.url;
    console.assert(typeof url == 'string', 'tab.url should be a string');
    callback(url);
  });
}

function renderStatus(statusText) {
  $('status').textContent = statusText;
}

function renderError(statusText) {
  $('error').textContent = "Error: " + statusText;
  $('error_img').style.display = "inline";
}

function getQuality(url) {
  chrome.runtime.sendNativeMessage('livestreamer_launcher',
      {
        "action": "getQuality",
        "args": {
          "url": url
        }
      },
      getQualityCallback
    );
  show_spinner();
  renderStatus("Getting available quality options...")
}

function getQualityCallback(response) {
  hide_spinner();
  if (typeof response == "undefined") {
    renderError("Bad response from native App");
    return;
  }
  if (response.result == true) {
    var select = $("quality_selector");
    var i, len, list;
    list = response.data;
    for (i=0, len = list.length; i<len; ++i) {
      var opt = document.createElement("option");
      opt.value = list[i];
      opt.innerHTML = list[i];
      select.appendChild(opt);
    }
    select.selectedIndex = len - 1;
    renderStatus("Select qaulity:");
    $("stream_controls").style.display = "block";
  } else {
    renderError(response.message);
  }
}


function startStream(url, quality) {
  chrome.runtime.sendNativeMessage('livestreamer_launcher',
      {
        "action": "startStream",
        "args": {
          "url": url,
          "quality": quality
        }
      },
      startStreamCallback
    );
  show_spinner();
  renderStatus("Trying to start stream...");
}

function startStreamCallback(response) {
  hide_spinner();
  if (typeof response == "undefined") {
    renderError("Bad response from native App");
    return;
  }
  if (response.result == true) {
    renderStatus("Stream starting...");
  } else {
    renderError("Couldn't start stream!");
  }
}
