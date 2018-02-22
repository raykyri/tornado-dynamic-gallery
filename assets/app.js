var ws = new WebSocket("ws://localhost:8000/websocket");

ws.onopen = function(evt) {
  console.log("WebSocket opened");
}

ws.onclose = function(evt) {
  console.log("WebSocket closed");
}

ws.onerror = function(evt) {
  console.log("WebSocket error");
}

ws.onmessage = function(evt) {
  console.log("WebSocket message, updating gallery contents now")
  var galleryContainer = document.querySelector(".gallery");
  galleryContainer.innerHTML = "";
  if (evt.data === "") {
    // Nothing in the gallery
  } else {
    var galleryImages = evt.data.split(",");
    for (var i = 0; i < galleryImages.length; i++) {
      galleryContainer.innerHTML += '<img src="gallery/' + galleryImages[i] + '">';
    }
  }
};

window.onbeforeunload = function() {
  ws.close()
};
