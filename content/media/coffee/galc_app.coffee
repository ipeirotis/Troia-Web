class GALC_Application extends App.Application
    _client_type: App.ContinuousClient

    objects_validation_message: "Only 3 words per line allowed."
    data_dir: "/media/txt/cjobs_data/"
    data_info_dir: "/media/txt/cjobs_data_info/"
    gold_data_dir: "/media/txt/cjobs_gold_data/"
    evaluation_data_dir: "/media/txt/cjobs_evaluation_data/"

    objects_validator: (line) ->
        line.length != 3

    populate_results_tables: () =>
        @client.get_results(
            () =>
                $("#objects").html(_.template(
                    $("#objects_template").html(),
                    {objects: @client.objects_prediction, headers: @client.objects_headers})
                )
                new List('objects_table', {valueNames: ['object_name']})
            () =>
                $("#workers").html(_.template(
                    $("#workers_template").html(),
                    {workers: @client.workers_prediction, headers: @client.workers_headers})
                )
                new List('workers_table', {valueNames: ['worker_name']})
            () =>
                $("#job_summary").html(
                    _.template($("#job_summary_template").html(),
                        {summary: @client.summary}
                    )
                )
            () =>
                $("#img-load").hide()
                $("#response").show()
                $("#summary-inner").show()
                # $("#download_zip_btn").show()
                @_post_populate_results_table()
        )
a = new GALC_Application()
