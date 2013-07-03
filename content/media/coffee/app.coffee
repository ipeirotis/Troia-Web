class App.Application

    algorithm_info_dir: "/media/txt/algorithm_info/"

    _post_loading_test_data: () ->

    _before_create: () ->

    on_tab_change: (e) ->

    _post_populate_results_table: () ->

    _post_loading_results: () ->

    constructor: () ->
        # Assign the process_hander function to the first click event.
        $('#send_data').one('click', @process_handler)

        App.set_textarea_maxrows(20000)
        id = App.get_url_parameter('id')
        @client = new @_client_type(id)
        @client._ajax_error = (jqXHR, textStatus, errorThrown) =>
            console.log "error", errorThrown
            @show_error("Troia server error (" + errorThrown.toString() + "). " + $.parseJSON(jqXHR.responseText)["result"])
            $('#send_data').removeClass('disabled').text("Process")

        $("#download_zip_btn").click(() =>
            @client.download_zip())

        if @client.ping()
            if id
                @client.exists(
                    () =>
                        # Show the results tab at first.
                        $('#menuTab li:nth-child(2) a').tab('show')
                        @client.get_evaluation_objects((res) =>
                            @populate_results_tables()
                            $('#id_evaluation_data').val(@client.evaluation_objects.map(@client._evaluation_object_to_text).join('\n')))
                        @client.get_assigns((res) =>
                            $('#id_data').val(@client.assigns.map(@client._assign_to_text).join('\n')))
                        @client.get_gold_objects((res) =>
                            $('#id_gold_data').val(@client.gold_objects.map(@client._gold_object_to_text).join('\n')))
                        @_post_loading_results()
                    () =>
                        @show_error("Sorry, id=" + id + " hasn't been found.")
                        @disable_results_tab()
                )
            else
                @disable_results_tab()
                # @load_test_data(1)
                $('#id_data_choose').change(() =>
                    value = $('#id_data_choose :selected').val()
                    @load_test_data(value)
                )
                $('#id_algorithm_choose').change(() =>
                    value = $('#id_algorithm_choose :selected').val()
                    $('#id_algorithm_info').slideUp(400, ()=>
                        $.ajax(url: @algorithm_info_dir + value).always((data) =>
                            $('#id_algorithm_info').html(if not _.isObject(data) then data else "").slideDown()
                        )
                    )
                )
                $("#id_algorithm_choose").change()

        $('a[data-toggle="tab"]').on('shown', (e) =>
            $(".alert").hide()
            @on_tab_change(e)
        )

    show_error: (txt) ->
        $(".alert p").text(txt)
        $(".alert").show()

    show_loading_indicator: (percentage) ->
        $('#send_data').text("Sending assigned labels (" + percentage.toString() + "%)...")

    disable_results_tab: () ->
        $("#menuTab li:nth-child(2) a").attr("data-toggle", "").css("cursor",  "not-allowed")

    load_test_data: (type) ->
        _check_data = (data) =>
            if not _.isObject(data) then data else ""
        $('#id_data_info').slideUp(400, ()=>
            $.ajax(url: @data_dir + type).always((data) =>
                empty = _.isObject(data) or _.isEmpty(data)
                $('#id_data').val(_check_data(data))
                $.ajax(url: @gold_data_dir + type).always((data) =>
                    $('#id_gold_data').val(_check_data(data))
                    $.ajax(url: @evaluation_data_dir + type).always((data) =>
                        $('#id_evaluation_data').val(_check_data(data))
                        $.ajax(url: @data_info_dir + type).always((data) =>
                            $('#id_data_info').html(_check_data(data)).slideDown()
                            if not empty
                                @_post_loading_test_data()
                            )
                        )
                    )
                )
            )

    _parse_input: (input_el, control_el, text_el, tab_el, line_condition, line_error_msg, condition, error_msg) ->
        control_el.removeClass('error')
        text_el.text('')
        data = []
        for line, ind in input_el.val().split(/\n/)
            parsed_line = line.split(/\s+/)
            if line.length > 0 and line_condition(parsed_line)
                control_el.addClass('error')
                text_el.text(line_error_msg + ' Check your ' + (ind+1).toString() + ' line.')
                tab_el.tab('show')
                return false
            if line.length > 0
                data.push(parsed_line)
        if condition and condition(data)
            control_el.addClass('error')
            text_el.text(error_msg)
            tab_el.tab('show')
            return false
        return data

    parse_assigns: () ->
        @_parse_input(
            $("#id_data")
            $("#data .control-group")
            $("#data span")
            $('#dataTab li:nth-child(1) a')
            (line) ->
                line.length != 3
            'Only 3 words per line allowed.'
            (data) ->
                data.length == 0
            'There should be at least one assign.'
            )

    parse_gold_labels: () =>
        @_parse_input(
            $("#id_gold_data")
            $("#gold .control-group")
            $("#gold span")
            $('#dataTab li:nth-child(2) a')
            @objects_validator
            @objects_validation_message)

    parse_evaluation_labels: () =>
        if ($("#id_evaluation_data").length > 0)
            @_parse_input(
                $("#id_evaluation_data")
                $("#evaluation .control-group")
                $("#evaluation span")
                $('#dataTab li:nth-child(3) a')
                @objects_validator
                @objects_validation_message)
        else
            []



    populate_results_tables: () =>
        @client.get_results(
            () =>
                $("#objects").html(_.template(
                    $("#objects_template").html(),
                    {
                        objects: @client.objects_prediction,
                        headers: @client.objects_headers,
                        evaluation: @client.evaluationObjects})
                )
                options =
                    valueNames: ['object_name']
                new List('objects_table', options)
            () =>
                $("#workers").html(_.template(
                    $("#workers_template").html(),
                    {workers: @client.workers_prediction, headers: @client.workers_headers})
                )
                new List('workers_table', {valueNames: ['worker_name']})

            () =>
                $("#job_summary").html(
                    _.template($("#job_summary_template").html(), {
                        summary: @client.summary,
                        estimated_objects_quality_summary: @client.estimated_objects_quality_summary,
                        evaluated_objects_quality_summary: @client.evaluated_objects_quality_summary,
                        estimated_objects_cost_summary: @client.estimated_objects_cost_summary,
                        estimated_workers_summary: @client.estimated_workers_summary,
                        evaluated_workers_summary: @client.evaluated_workers_summary,
                        evaluated: not _.isEmpty(@client.evaluationObjects)}
                    )
                )
            () =>
                $("#img-load").hide()
                $("#response").show()
                $("#summary-inner").show()
                # $("#download_zip_btn").show()
                @_post_populate_results_table()
        )

    process_handler: () =>
        $(".alert").hide()
        assigns = @parse_assigns()
        gold_labels = @parse_gold_labels()
        evaluation_labels = @parse_evaluation_labels()
        if assigns and gold_labels
            button_text = $('#send_data').text()
            $('#send_data').addClass('disabled').text('Sending data..')
            @_before_create()
            @client.create(() =>
                @client.post_assigns(
                    assigns
                    () =>
                        @client.post_gold_objects(
                            gold_labels
                            () =>
                                @client.post_evaluation_objects(
                                    evaluation_labels
                                    () =>
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
                                    (p) =>
                                        @show_loading_indicator(p)
                                )
                            (p) =>
                                @show_loading_indicator(p)
                        )
                    (p) =>
                        @show_loading_indicator(p)
                )
            )
        # Assign the function to the next next click event.
        $('#send_data').one('click', @process_handler)
