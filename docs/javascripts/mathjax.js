window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true
  },
  options: {
    ignoreHtmlClass: ".*",
    processHtmlClass: "arithmatex"
  }
};

document.addEventListener("DOMContentLoaded", () => { 
  MathJax.typesetPromise();
});

/* Support for MkDocs Material's instant loading feature */
if (typeof app !== "undefined") {
  app.document$.subscribe(() => {
    MathJax.typesetPromise();
  });
}
