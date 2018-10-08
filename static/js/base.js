$(function() {
    $.getJSON("/json/etf", function(json) {
        $("#etfSearch").autocomplete({
            source: json.names,
            minLength: 2
        });

    });
});