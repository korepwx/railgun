(function() {
  // Initialize the TOC for manual pages.
  function init_toc() {
    if ($("#toc-navigate").size() > 0) {
      var toc_nav = $("#toc-navigate > ul");
      var sections = $("section");
      var htmlSections = [];

      sections.each(function(i, e) {
        var subsections = $("subsection", e);
        var h2 = $('h2', e);

        // Make the item head
        if (i == 0) {
          htmlSections.push('<li class="active">');
        } else {
          htmlSections.push('<li class="">');
        }
        htmlSections.push('<a href="#' + h2.prop('id') + '">' + $(h2).html() +
                          '</a>');

        // Build sub items.
        if (subsections.size() > 0) {
          var htmlSubSections = [];
          subsections.each(function(i2, e2) {
            var h3 = $('h3', e2);
            htmlSubSections.push('<li><a href="#' + h3.prop('id') + '">' +
                                 $(h3).html() + '</a></li>');
          });
          htmlSections.push('<ul class="nav">');
          htmlSections.push(htmlSubSections.join(''));
          htmlSections.push('</ul>');
        }

        // Make item tail
        htmlSections.push('</li>');
      });

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
