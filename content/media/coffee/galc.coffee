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
        that = this
        cclient.create(() ->
            cclient.post_assigns(assigns, () ->
                cclient.post_gold_labels(gold_labels, () ->
                    $("#img-load").show()
                    $("#response").hide()
                    $(that).text('Computing..')
                    $('#menuTab li:nth-child(2) a').attr("data-toggle", "tab").tab('show')

                    cclient.compute(() ->
                        $(that).removeClass('disabled').text(button_text)
                        $("#url pre").text(document.URL + "?id=" + cclient.id)
                        cclient.collect_predicted_labels(() ->
                            cclient.collect_workers_statistics(()->
                                console.log cclient.predicted_labels
                                console.log cclient.worker_stats
                            )
                        )
                    )
                )
            )
        )
    $(@).one('click', process_handler)



cclient = new App.ContinuousClient()
cclient.ajax_error = (jqXHR, textStatus, errorThrown) ->
    $(".alert p").text("Troia server error (" + errorThrown.toString() + ").")
    $(".alert").show()

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
