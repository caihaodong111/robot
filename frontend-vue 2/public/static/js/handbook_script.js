var NavigationDelay = 150;

var disableToggleExpander = false;
function ToggleExpander(id) {
  if (disableToggleExpander)
    return;

  var module = document.getElementById(id);
  if (module == null)
    return;

  var toggleButton = document.getElementById(id + '.toggleButton');
  var content = document.getElementById(id + '.content');

  if (toggleButton != null && toggleButton != undefined && content != null && content != undefined) {
    var collapsed = (content.style.display == 'none');
    if (collapsed) {
      content.style.display = '';
      if (toggleButton.src != null && toggleButton.src != undefined) {
		var src = toggleButton.src;
		// console.log(src.lastIndexOf("/"));
		// console.log(src.length - 1);
		if(src.lastIndexOf("/") == src.length - 1){
			src = src.substring(0,src.length -1);
		}
        var baseDir = '';
        var baseDirLength = src.lastIndexOf('/');
        if (baseDirLength >= 0)
          baseDir = src.substring(0, src.lastIndexOf('/') + 1);

        var extension = '';
        var extensionLength = src.lastIndexOf('.');
        if (extensionLength >= 0)
          extension = src.substring(extensionLength);

        toggleButton.src = baseDir + 'Expanded' + extension;
      }
    }
    else {
      content.style.display = 'none';
      if (toggleButton.src != null && toggleButton.src != undefined) {
		var src = toggleButton.src;
		// console.log(src.lastIndexOf("/"));
		// console.log(src.length - 1);
		if(src.lastIndexOf("/") == src.length - 1){
			src = src.substring(0,src.length -1);
		}
        var baseDir = '';
        var baseDirLength = src.lastIndexOf('/');
        if (baseDirLength >= 0)
          baseDir = src.substring(0, src.lastIndexOf('/') + 1);

        var extension = '';
        var extensionLength = src.lastIndexOf('.');
        if (extensionLength >= 0)
          extension = src.substring(extensionLength);

        toggleButton.src = baseDir + 'Collapsed' + extension;
      }
    }
  }
}

var delayedNavigationTimer = null;
var delayedNavigationTarget = null;
function DelayedNavigation(url, highlightId) {
  if (delayedNavigationTimer != null)
    return true;
  //clearTimeout(delayedNavigationTimer);

  delayedNavigationTarget = url;
  delayedNavigationTimer = setTimeout("DelayedNavigationCallback()", NavigationDelay);
  disableToggleExpander = true;

  self.document.body.style.cursor = 'wait';

  var highlightElement = null;
  if (highlightId)
    highlightElement = document.getElementById(highlightId);
  if (!highlightElement && window.event && window.event.srcElement)
    highlightElement = window.event.srcElement;

  if (highlightElement)
    highlightElement.style.backgroundColor = '#22BBFF';

  return true;
}

function DelayedImageNavigation(url, imageId, hoverImage) {
  if (delayedNavigationTimer != null)
    return true;
  //clearTimeout(delayedNavigationTimer);

  delayedNavigationTarget = url;
  delayedNavigationTimer = setTimeout("DelayedNavigationCallback()", NavigationDelay);
  disableToggleExpander = true;

  self.document.body.style.cursor = 'wait';

  var imageElement = null;
  if (imageId)
    imageElement = document.getElementById(imageId);
  if (!imageElement && window.event && window.event.srcElement)
    imageElement = window.event.srcElement;

  if (imageElement) {
    imageElement.style.backgroundColor = '#22BBFF';
    if (hoverImage && hoverImage.length > 0)
      imageElement.src = hoverImage;
    else {
      imageElement.style.opacity = 0.4;
      imageElement.style.filter = 'alpha(opacity=40)';
    }
  }

  return true;
}

function DelayedNavigationCallback() {
  self.parent.location = delayedNavigationTarget;
}

function DelayedNavigationOnMouseOver(id) {
  var element = null;
  if (id)
    element = document.getElementById(id);
  if (!element && window.event && window.event.srcElement)
    element = window.event.srcElement;

  if (element)
    element.style.cursor = 'hand';
}

function DelayedNavigationOnMouseOut(id) {
  var element = null;
  if (id)
    element = document.getElementById(id);
  if (!element && window.event && window.event.srcElement)
    element = window.event.srcElement;

  if (element)
    element.style.cursor = 'auto';
}
