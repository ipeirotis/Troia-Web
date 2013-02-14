process_handler = () ->
    $(".alert").hide()

    assigns = App.parse_input(
        $("#id_data")
        $("#data .control-group")
        $("#data span")
        $('#dataTab li:nth-child(1) a')
        (line) ->
            line.length != 3
        'Only 3 words per line allowed.')

    gold_labels = App.parse_input(
        $("#id_gold_labels")
        $("#gold .control-group")
        $("#gold span")
        $('#dataTab li:nth-child(2) a')
        (line) ->
            line.length != 3
        'Only 3 words per line allowed.')

    if assigns and gold_labels and cclient.ping
        button_text = $(@).text();
        $(@).addClass('disabled').text('Sending data..');
        cclient.create(() ->
            cclient.post_assigns(assigns, () ->
                cclient.post_gold_labels(gold_labels, () ->
                    console.log 'data loaded')))
    $(@).one('click', process_handler)



cclient = new App.ContinuousClient()

#disable results tab
$("#menuTab li:nth-child(2) a").attr("data-toggle", "").css("cursor",  "not-allowed");

cclient.get_test_data(1,
    (data) ->
        $('#id_data').val(data)
    (data) ->
        $('#id_gold_labels').val(data)
)
App.set_textarea_maxrows 20000
$('#send_data').one('click', process_handler)
