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

            var text = d.label;
            if (d.value != undefined)
                text += ' (' + d.value + ')';
            var text = document.createTextNode(text);
            title.appendChild(text);
        });
    }

    function translate(data) {
        var dataset = data.datasets || data;
        $(dataset).each(function(i, e) {
            e.label = msg(e.label);
        });
        return data;
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

    var day_freq_data = translate({
        labels: labels,
        datasets: [
            {
                label: "Accepted",
                fillColor: "rgba(70,191,189,0.7)",
                strokeColor: "rgba(70,191,189,1)",
                pointColor: "rgba(70,191,189,1)",
                pointStrokeColor: "#fff",
                pointHighlightFill: "#fff",
                pointHighlightStroke: "rgba(70,191,189,1)",
                data: day_ac_freq,
            },
            {
                label: "Rejected",
                fillColor: "rgba(247,70,74,0.7)",
                strokeColor: "rgba(247,70,74,1)",
                pointColor: "rgba(247,70,74,1)",
                pointStrokeColor: "#fff",
                pointHighlightFill: "#fff",
                pointHighlightStroke: "rgba(247,70,74,1)",
                data: day_rj_freq,
            }
        ]
    });

    // Prepare for various pie charts
    function pieData(raw, colors=[]) {
        var N = raw.length;
        var data = [];

        $(raw).each(function(i, e) {
            var hue = colors[i] || Math.floor(i * 360 / N);
            data.push({
                value: e[1],
                color: "hsla(" + hue + ",75%,50%,0.7)",
                highlight: "hsla(" + hue + ",75%,50%,1)",
                label: e[0]
            });
        });

        return translate(data);
    }
    var acc_reject_data = pieData(
        window.chart_data['acc_reject'],
        [110, 360]
    );
    var reject_brief_data = pieData(window.chart_data['reject_brief']);

    // The drawing method of the charts.
    function redraw() {
        // Everyday Submissions
        var dayfreq =
            new Chart($("#dayfreq").get(0).getContext("2d")).StackedBar(
                day_freq_data);
        legend($('#dayfreq-legend').get(0), day_freq_data);

        // Accepted and Rejected
        var acc_reject =
            new Chart($("#acc-reject").get(0).getContext("2d")).Pie(
                acc_reject_data);
        legend($('#acc-reject-legend').get(0), acc_reject_data);

        // Reject Category
        var reject_brief =
            new Chart($("#reject-brief").get(0).getContext("2d")).Pie(
                reject_brief_data);
        legend($('#reject-brief-legend').get(0), reject_brief_data);
    }

    // Update the canvas properties when resizing window
    function resizeCanvas() {
        $("canvas").each(function(i, e) {
            var new_canvasWidth = $(e).parent().width();
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
