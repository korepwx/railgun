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

        if (data.labels) {
            $(data.labels).each(function(i, e) {
                data.labels[i] = msg(e);
            });
        }
        return data;
    }

    // Prepare for the date histogram.
    var day_freq_data = null;

    (function() {
        var labels = [];
        var day_freq = [];
        var day_ac_freq = [];
        var day_rj_freq = [];

        $(window.chart_data["day_freq"]).each(function(i, itm) {
            var key = itm[0];
            var freq = itm[1];
            key = key[0] + '/' + key[1];
            labels.push(key);
            day_freq.push(freq[0]);
            day_ac_freq.push(freq[1]);
            day_rj_freq.push(freq[2]);
        });

        day_freq_data = translate({
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
    })();

    // Prepare for the day author count
    var day_author_data = null;

    (function() {
        var labels = [];
        var data = [];

        $(window.chart_data["day_author"]).each(function(i, e) {
            var key = e[0];
            key = key[0] + '/' + key[1];
            labels.push(key);
            data.push(e[1]);
        });

        day_author_data = translate({
            labels: labels,
            datasets: [
                {
                    label: "User",
                    fillColor: "rgba(151,187,205,0.7)",
                    strokeColor: "rgba(151,187,205,1)",
                    pointColor: "rgba(151,187,205,1)",
                    pointStrokeColor: "#fff",
                    pointHighlightFill: "#fff",
                    pointHighlightStroke: "rgba(151,187,205,1)",
                    data: data
                }
            ]
        });
    })();

    // Prepare for the user submits
    var user_submit_data = null;

    (function() {
        var labels = [];
        var data = [];

        $(window.chart_data["user_submit"]).each(function(i, e) {
            labels.push(e[0]);
            data.push(e[1]);
        });

        user_submit_data = translate({
            labels: labels,
            datasets: [
                {
                    label: "Count of Users",
                    fillColor: "rgba(253,180,92,0.7)",
                    strokeColor: "rgba(253,180,92,1)",
                    pointColor: "rgba(253,180,92,1)",
                    pointStrokeColor: "#fff",
                    pointHighlightFill: "#fff",
                    pointHighlightStroke: "rgba(151,187,205,1)",
                    data: data
                }
            ]
        });
    })();

    // Prepare for the final scores
    var final_score_data = null;

    (function() {
        var labels = [];
        var data = [];

        $(window.chart_data["final_score"]).each(function(i, e) {
            labels.push(e[0]);
            data.push(e[1]);
        });

        final_score_data = translate({
            labels: labels,
            datasets: [
                {
                    label: "Final Scores",
                    fillColor: "rgba(70,191,189,0.7)",
                    strokeColor: "rgba(70,191,189,1)",
                    pointColor: "rgba(70,191,189,1)",
                    pointStrokeColor: "#fff",
                    pointHighlightFill: "#fff",
                    pointHighlightStroke: "rgba(151,187,205,1)",
                    data: data
                }
            ]
        });
    })();

    // Prepare for various pie charts
    function pieData(raw, colors) {
        var N = raw.length;
        var data = [];
        colors = colors || [];

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
    function Charts() {
        // Everyday Submissions
        var acc_reject = null;
        var reject_brief = null;
        var day_freq = null;
        var day_author = null;
        var user_submit = null;
        var final_score = null;

        // Function to (re)create the canvas
        this.createAll = function() {
            if (acc_reject)
                acc_reject.destroy();
            if (reject_brief)
                reject_brief.destroy();
            if (day_freq)
                day_freq.destroy();
            if (day_author)
                day_author.destroy();
            if (user_submit)
                user_submit.destroy();
            if (final_score)
                final_score.destroy();

            acc_reject = new Chart($("#acc-reject").get(0).getContext("2d")).Pie(acc_reject_data);
            reject_brief = new Chart($("#reject-brief").get(0).getContext("2d")).Pie(reject_brief_data);
            day_freq = new Chart($("#day-freq").get(0).getContext("2d")).StackedBar(day_freq_data);
            day_author = new Chart($("#day-author").get(0).getContext("2d")).Bar(day_author_data);
            user_submit = new Chart($("#user-submit").get(0).getContext("2d")).Bar(user_submit_data);
            final_score = new Chart($("#final-score").get(0).getContext("2d")).Bar(final_score_data);
        };
        this.createAll();

        // Create the legends
        legend($('#acc-reject-legend').get(0), acc_reject_data);
        legend($('#reject-brief-legend').get(0), reject_brief_data);
        legend($('#day-freq-legend').get(0), day_freq_data);
        /*
        legend($('#day-author-legend').get(0), day_author_data);
        legend($('#user-submit-legend').get(0), user_submit_data);
        legend($('#final-score-legend').get(0), final_score_data);
        */

        return this;
    }
    var charts = new Charts();

    // Update the canvas properties when resizing window
    function resizeCanvas() {
        var updated = false;
        $("canvas").each(function(i, e) {
            var new_canvasWidth = $(e).parent().width();
            if (new_canvasWidth != $(e).width()) {
                $(e).attr('width', new_canvasWidth);
                updated = true;
            }
        });
        if (updated) {
            charts.createAll();
        }
    }
    $(window).resize(resizeCanvas);

    // Initialize the size of canvas
    resizeCanvas();
});
