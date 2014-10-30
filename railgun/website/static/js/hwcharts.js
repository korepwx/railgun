$(document).ready(function() {
    // Set global options
    // Chart.defaults.global.responsive = true;

    // Utility to do translation
    function msg(text) {
        return window.chart_i18n[text] || text;
    }

    // Utility to create a chart
    function legend(parent, data) {
        parent.className = 'legend';
        var datas = data.hasOwnProperty('datasets') ? data.datasets : data;

        // remove possible children of the parent
        while(parent.hasChildNodes()) {
            parent.removeChild(parent.lastChild);
        }

        datas.forEach(function(d) {
            var title = document.createElement('span');
            title.className = 'title';
            title.style.borderColor = d.hasOwnProperty('strokeColor') ? d.strokeColor : d.color;
            title.style.borderStyle = 'solid';
            parent.appendChild(title);

            var text = document.createTextNode(d.label);
            title.appendChild(text);
        });
    }

    // Prepare for the date histogram.
    var labels = [];
    var day_freq = [];
    var day_ac_freq = [];
    var day_rj_freq = [];

    $(window.chart_data["day_freq"]).each(function(i, e) {
        var itm = e;
        var key = itm[0];
        var freq = itm[1];
        key = key[0] + '/' + key[1];
        labels.push(key);
        day_freq.push(freq[0]);
        day_ac_freq.push(freq[1]);
        day_rj_freq.push(freq[2]);
    });

    var day_freq_data = {
        labels: labels,
        datasets: [
            {
                label: msg("Accepted"),
                fillColor: "rgba(70,191,189,0.7)",
                strokeColor: "rgba(70,191,189,1)",
                pointColor: "rgba(70,191,189,1)",
                pointStrokeColor: "#fff",
                pointHighlightFill: "#fff",
                pointHighlightStroke: "rgba(70,191,189,1)",
                data: day_ac_freq,
            },
            {
                label: msg("Rejected"),
                fillColor: "rgba(247,70,74,0.7)",
                strokeColor: "rgba(247,70,74,1)",
                pointColor: "rgba(247,70,74,1)",
                pointStrokeColor: "#fff",
                pointHighlightFill: "#fff",
                pointHighlightStroke: "rgba(247,70,74,1)",
                data: day_rj_freq,
            }
        ]
    };

    // The drawing method of the charts.
    function redraw() {
        var dayfreq =
            new Chart($("#dayfreq").get(0).getContext("2d")).StackedBar(
                day_freq_data);
        legend($('#dayfreq-legend').get(0), day_freq_data);
    }

    // Update the canvas properties when resizing window
    function resizeCanvas() {
        $("canvas").each(function(i, e) {
            var new_canvasWidth = $(e).parent().width();
            console.log(new_canvasWidth);
            if (new_canvasWidth != $(e).width()) {
                $(e).attr('width', new_canvasWidth);
            }
        })
        redraw();
    }
    $(window).resize(resizeCanvas);

    // Initialize the size of canvas
    resizeCanvas();
});
