function InitTimeZone(json_url) {
  var timezones = new Bloodhound({
    datumTokenizer: function (d) {
      return Bloodhound.tokenizers.whitespace(d['name'] + '\n' + d['display_name']);
    },
    queryTokenizer: Bloodhound.tokenizers.whitespace,
    limit: 10,
    prefetch: {
      // url points to a json file that contains an array of country names, see
      url: json_url,
      // the json file contains an array of strings, but the Bloodhound
      // suggestion engine expects JavaScript objects so this converts all of
      // those strings
      filter: function(list) {
        return $.map(list, function(tzinfo) {
          return { display_name: tzinfo[1], name: tzinfo[0] };
        });
      }
    }
  });
   
  // kicks off the loading/processing of `local` and `prefetch`
  timezones.initialize();
   
  // passing in `null` for the `options` arguments will result in the default
  // options being used
  $('#timezone').typeahead({
      hint: true,
      highlight: true,
      minLength: 1
    }, {
    name: 'timezones',
    displayKey: 'name',
    // `ttAdapter` wraps the suggestion engine in an adapter that
    // is compatible with the typeahead jQuery plugin
    source: timezones.ttAdapter(),
    // Customize the render template
    templates: {
      suggestion: Handlebars.compile(
        '<p><span>{{name}}</span> – <span class="text-muted">{{display_name}}</span></p>'
      )
    }
  });
}
