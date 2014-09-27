(function() {
  // Initialize the TOC for manual pages.
  function init_toc() {
    if ($("#toc-navigate").size() > 0) {
      var toc_nav = $("#toc-navigate > ul");
      var sections = $('#manual > *[id^="_"]');
      var htmlSections = [];
      var lastLevel = 2;
      var firstTitle = true;

      sections.each(function(i, e) {
        var level = parseInt(e.tagName.substr(1));
        if (level == 1)
          return;

        // If level steps in, add <ul>
        if (level > lastLevel) {
          htmlSections.push('<ul class="nav">');
        }

        // Otherwise if level steps out, add </ul>.
        if (level < lastLevel) {
          htmlSections.push('</ul>');
        }

        // Steps out or keep the same level, we should add </li>
        htmlSections.push('</li>');

        // First, add <li> to html.
        if (firstTitle) {
          htmlSections.push('<li class="active">');
          firstTitle = false;
        } else {
          htmlSections.push('<li class="">');
        }
        htmlSections.push('<a href="#' + $(e).prop('id') + '">' + $(e).html() +
                          '</a>');
        

        // Record current level
        lastLevel = level;
      });

      // Add the missing </li>
      htmlSections.push('</li>');

      // Set toc-navigate
      console.log(htmlSections.join(''));
      toc_nav.html(htmlSections.join(''));
    }
  };

  // Bind DOM events using jQuery
  $(document).ready(function() {
    init_toc();
    $('[data-spy="scroll"]').each(function () {
      var $spy = $(this).scrollspy('refresh')
    });
  });
})();
