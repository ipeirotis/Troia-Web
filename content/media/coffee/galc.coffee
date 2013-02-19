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
        $("#id_gold_data")
        $("#gold .control-group")
        $("#gold span")
        $('#dataTab li:nth-child(2) a')
        (line) ->
            line.length != 3
        'Only 3 words per line allowed.')

    if assigns and gold_labels and cclient.ping
        button_text = $(@).text()
        $(@).addClass('disabled').text('Sending data..')
        that = this
        cclient.create(() ->
            cclient.post_assigns(assigns, () ->
                cclient.post_gold_objects(gold_labels, () ->
                    $("#img-load").show()
                    $("#response").hide()
                    $(that).text('Computing..')
                    $('#menuTab li:nth-child(2) a').attr("data-toggle", "tab").tab('show')

                    cclient.compute(() ->
                        $(that).removeClass('disabled').text(button_text)
                        $("#url pre").text(document.URL + "?id=" + cclient.id)
                        cclient.get_objects_prediction(() ->
                            cclient.get_workers_prediction(()->
                                $("#img-load").hide()
                                $("#objects").html(_.template($("#objects_template").html(), {objects: cclient.objects_prediction}))
                                $("#workers").html(_.template($("#workers_template").html(), {workers: cclient.workers_prediction}))
                                $("#response").show()
                                console.log cclient.objects_prediction
                                console.log cclient.workers_prediction
                            )
                        )
                    )
                )
            )
        )
    $(@).one('click', process_handler)


cclient = new App.ContinuousClient()
id = App.get_url_parameter('id')

if id
    success = (response) ->
        job = $.parseJSON(response.responseText).result
        eval_result = ''
        for assign in job.assigns
            eval_result += assign.worker + '\t' + assign.object + '\t' + assign.label.value + '\n'
        assigns = job.assigns.map((a) -> [a.worker, a.object, a.label.value].join('\t')).join('\n')
        objects = job.goldObjects.map((o) ->
            v = o.goldLabel.value
            [o.name, v.value, v.zeta].join('\t')).join('\n')
        $('#id_data').val(assigns)
        $('#id_gold_data').val(objects)

    cclient.get_job(id, success)
else
    cclient.get_example_job(1,
        (data) ->
            $('#id_data').val(data)
        (data) ->
            $('#id_gold_data').val(data)
    )

cclient.ajax_error = (jqXHR, textStatus, errorThrown) ->
    $(".alert p").text("Troia server error (" + errorThrown.toString() + ").")
    $(".alert").show()

#disable results tab
$("#menuTab li:nth-child(2) a").attr("data-toggle", "").css("cursor",  "not-allowed")

App.set_textarea_maxrows(20000)
$('#send_data').one('click', process_handler)
