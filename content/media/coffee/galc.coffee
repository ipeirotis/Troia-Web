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

    if assigns and gold_labels
        button_text = $(@).text()
        $(@).addClass('disabled').text('Sending data..')
        that = this
        cclient.create(() ->
            cclient.post_assigns(assigns, () ->
                cclient.post_gold_objects(gold_labels, () ->
                    $("#url pre").text(App.get_job_url(cclient.id))
                    $("#url").show()
                    $("#img-load").show()
                    $("#response").hide()
                    $(that).text('Computing..')
                    $('#menuTab li:nth-child(2) a').attr("data-toggle", "tab").tab('show')
                    cclient.compute(() ->
                        $('#send_data').removeClass('disabled').text(button_text)
                        cclient.get_prediction(
                            () ->
                                $("#objects").html(_.template(
                                    $("#objects_template").html(),
                                    {objects: cclient.objects_prediction})
                                )
                            () ->
                                $("#workers").html(_.template(
                                    $("#workers_template").html(),
                                    {workers: cclient.workers_prediction})
                                )
                            () ->
                                $("#img-load").hide()
                                $("#response").show()
                        )
                    )
                )
            )
        )
    # Assign the function to the next next click event.
    $(@).one('click', process_handler)

# Assign the process_hander function to the first click event.
$('#send_data').one('click', process_handler)

App.set_textarea_maxrows(20000)
id = App.get_url_parameter('id')
cclient = new App.ContinuousClient(id)
cclient._ajax_error = (jqXHR, textStatus, errorThrown) ->
    console.log "error"
    $(".alert p").text("Troia server error (" + errorThrown.toString() + ").")
    $(".alert").show()
$("#download_zip_btn").click(() ->
    cclient.download_zip())
# Prepare an URL for the 'see results later' link.
url = document.URL
base_url = url.replace(/\?.*/g, ($0) -> '')
base_url = base_url.replace(/\#.*/g, ($0) -> '')

if cclient.ping()
    if id
        # Show the results tab at first.
        $('#menuTab li:nth-child(2) a').tab('show')
        $("#url").hide()
        cclient.get_prediction(
            () ->
                $("#objects").html(_.template($("#objects_template").html(), {objects: cclient.objects_prediction}))
            () ->
                $("#workers").html(_.template($("#workers_template").html(), {workers: cclient.workers_prediction}))
            () ->
                $("#img-load").hide()
                $("#response").show()
        )
        cclient.get_job((response) ->
            job = $.parseJSON(response.responseText).result
            assigns = job.assigns.map((a) -> [a.worker, a.object, a.label.value].join('\t')).join('\n')
            objects = job.goldObjects.map((o) ->
                l = o.goldLabel
                [o.name, l.value, l.zeta].join('\t')).join('\n')
            $('#id_data').val(assigns)
            $('#id_gold_data').val(objects)
        )
    else
        # Disable the results tab.
        $("#menuTab li:nth-child(2) a").attr("data-toggle", "").css("cursor",  "not-allowed")
        cclient.get_example_job(1,
            (data) ->
                $('#id_data').val(data)
            (data) ->
                $('#id_gold_data').val(data)
        )
