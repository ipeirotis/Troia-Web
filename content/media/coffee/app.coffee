class App.Application

    _post_loading: () ->

    _before_create: () ->

    on_tab_change: (e) ->

    _post_populate_results_table: () ->

    constructor: () ->
        # Assign the process_hander function to the first click event.
        $('#send_data').one('click', @process_handler)

        App.set_textarea_maxrows(20000)
        id = App.get_url_parameter('id')
        @client = new @_client_type(id)
        @client._ajax_error = (jqXHR, textStatus, errorThrown) ->
            console.log "error", textStatus
            $(".alert p").text("Troia server error (" + errorThrown.toString() + ").")
            $(".alert").show()

        $("#download_zip_btn").click(() ->
            @client.download_zip())

        # Prepare an URL for the 'see results later' link.
        url = document.URL
        base_url = url.replace(/\?.*/g, ($0) -> '')
        base_url = base_url.replace(/\#.*/g, ($0) -> '')

        if @client.ping()
            if id
                # Show the results tab at first.
                $('#menuTab li:nth-child(2) a').tab('show')
                $("#url").hide()
                @populate_results_tables()
                @client.get_assigns((res) =>
                    $('#id_data').val(@client.assigns.map(@client._assign_to_text).join('\n')))

                @client.get_gold_objects((res) =>
                    $('#id_gold_data').val(@client.gold_objects.map(@client._gold_object_to_text).join('\n')))
            else
                # Disable the results tab.
                $("#menuTab li:nth-child(2) a").attr("data-toggle", "").css("cursor",  "not-allowed")
                @client.get_example_job(1,
                    (data) ->
                        $('#id_data').val(data)
                    (data) ->
                        $('#id_gold_data').val(data)
                    () =>
                        @_post_loading()
                )

        $('a[data-toggle="tab"]').on('shown', (e) =>
            $(".alert").hide()
            @on_tab_change(e)
        )

    _parse_input: (input_el, control_el, text_el, tab_el, condition, error_msg) ->
        control_el.removeClass('error')
        text_el.text('')
        data = []
        for line, ind in input_el.val().split(/\n/)
            parsed_line = line.split(/\s+/)
            if condition(parsed_line)
                control_el.addClass('error')
                text_el.text(error_msg + ' Check your ' + (ind+1).toString() + ' line.')
                tab_el.tab('show')
                return false
            data.push(parsed_line)
        return data

    parse_assigns: () ->
        @_parse_input(
            $("#id_data")
            $("#data .control-group")
            $("#data span")
            $('#dataTab li:nth-child(1) a')
            (line) ->
                line.length != 3
            'Only 3 words per line allowed.')

    parse_gold_labels: () =>
        @_parse_input(
            $("#id_gold_data")
            $("#gold .control-group")
            $("#gold span")
            $('#dataTab li:nth-child(2) a')
            @gold_objects_validator
            @gold_objects_validation_message)

    populate_results_tables: () =>
        @client.get_prediction(
            () =>
                $("#objects").html(_.template(
                    $("#objects_template").html(),
                    {objects: @client.objects_prediction, headers: @client.objects_headers})
                )
            () =>
                $("#workers").html(_.template(
                    $("#workers_template").html(),
                    {workers: @client.workers_prediction, headers: @client.workers_headers})
                )
            () =>
                $("#img-load").hide()
                $("#response").show()
                @_post_populate_results_table()
        )

    process_handler: () =>
        $(".alert").hide()
        assigns = @parse_assigns()
        gold_labels = @parse_gold_labels()
        if assigns and gold_labels
            button_text = $('#send_data').text()
            $('#send_data').addClass('disabled').text('Sending data..')
            @_before_create()
            @client.create(() =>
                @client.post_assigns(assigns, () =>
                    @client.post_gold_objects(gold_labels, () =>
                        $("#url pre").text(App.get_job_url(@client.id))
                        $("#url").show()
                        $("#img-load").show()
                        $("#response").hide()
                        $('#send_data').text('Computing..')
                        $('#menuTab li:nth-child(2) a').attr("data-toggle", "tab").tab('show')
                        @client.compute(() =>
                            $('#send_data').removeClass('disabled').text(button_text)
                            @populate_results_tables()
                        )
                    )
                )
            )
        # Assign the function to the next next click event.
        $('#send_data').one('click', @process_handler)
