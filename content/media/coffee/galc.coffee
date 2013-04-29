class App.ContinuousClient extends App.Client
    jobs_url: "/jobs"
    data_dir: "/media/txt/cjobs_data/"
    gold_data_dir: "/media/txt/cjobs_gold_data/"
    evaluation_data_dir: "/media/txt/cjobs_evaluation_data/"
    creation_data: {'algorithm': 'GALC'}

    _assign_to_json: (a) -> {worker: a[0], object: a[1], label: {value: a[2]}}

    _assign_to_text: (a) -> [a.worker, a.object, a.label.value].join('\t')

    _gold_object_to_json: (o) -> {name: o[0], goldLabel: {value: o[1], zeta: o[2]}}

    _gold_object_to_text: (o) -> [o.name, o.goldLabel.value, o.goldLabel.zeta].join('\t')

    _evaluation_object_to_json: (o) -> {name: o[0], evaluationLabel: {value: o[1], zeta: o[2]}}

    _evaluation_object_to_text: (o) -> [o.name, o.evaluationLabel.value, o.evaluationLabel.zeta].join('\t')

    get_summary: (success) ->
        if (not _.has(this, 'creation_data'))
            @get_job (response) ->
                success(response)
        else
            success(response)

