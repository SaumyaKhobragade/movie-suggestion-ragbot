const TRANSITION_DURATION = 260;

function isInternalLink(anchor) {
  const href = anchor.getAttribute("href");
  if (!href || href.startsWith("#") || href.startsWith("mailto:") || href.startsWith("tel:")) {
    return false;
  }
  if (anchor.target && anchor.target !== "_self") {
    return false;
  }
  const url = new URL(href, window.location.href);
  return url.origin === window.location.origin;
}

function setupExitTransitions(anchors) {
  const body = document.body;

  anchors.forEach((anchor) => {
    anchor.addEventListener("click", (event) => {
      if (
        event.defaultPrevented ||
        event.button !== 0 ||
        event.metaKey ||
        event.ctrlKey ||
        event.shiftKey ||
        event.altKey ||
        !isInternalLink(anchor) ||
        new URL(anchor.href, window.location.href).pathname === window.location.pathname
      ) {
        return;
      }

      event.preventDefault();
      body.classList.add("is-exiting");
      setTimeout(() => {
        window.location.href = anchor.href;
      }, TRANSITION_DURATION);
    });
  });
}

function enablePageTransitions() {
  const body = document.body;
  if (!body) return;

  body.classList.add("transition-enabled");
  requestAnimationFrame(() => {
    body.classList.add("is-loaded");
  });

  const anchors = Array.from(document.querySelectorAll("a[href]"));
  setupExitTransitions(anchors);

  window.addEventListener("pageshow", (event) => {
    if (event.persisted) {
      body.classList.remove("is-exiting");
      body.classList.add("is-loaded");
    }
  });
}

document.addEventListener("DOMContentLoaded", enablePageTransitions);
