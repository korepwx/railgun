$(document).ready(function() {
    // Set global options
    // Chart.defaults.global.responsive = true;

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
                label: "Total",
                fillColor: "rgba(220,220,220,0.2)",
                strokeColor: "rgba(220,220,220,1)",
                pointColor: "rgba(220,220,220,1)",
                pointStrokeColor: "#fff",
                pointHighlightFill: "#fff",
                pointHighlightStroke: "rgba(220,220,220,1)",
                data: day_freq,
            },
            {
                label: "Accepted",
                label: "My Second dataset",
                fillColor: "rgba(151,187,205,0.2)",
                strokeColor: "rgba(151,187,205,1)",
                pointColor: "rgba(151,187,205,1)",
                pointStrokeColor: "#fff",
                pointHighlightFill: "#fff",
                pointHighlightStroke: "rgba(151,187,205,1)",
                data: day_ac_freq,
            },
            {
                label: "Rejected",
                fillColor: "rgba(220,220,220,0.2)",
                strokeColor: "rgba(220,220,220,1)",
                pointColor: "rgba(220,220,220,1)",
                pointStrokeColor: "#fff",
                pointHighlightFill: "#fff",
                pointHighlightStroke: "rgba(220,220,220,1)",
                data: day_rj_freq,
            }
        ]
    };

    // The drawing method of the charts.
    function redraw() {
        new Chart($("#dayfreq").get(0).getContext("2d")).Line(day_freq_data);
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
