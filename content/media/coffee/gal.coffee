class App.NominalClient extends App.Client
    jobs_url: "/jobs"
    objects_summary_url: "/objects/quality/summary"
    workers_summary_url: "/workers/quality/summary"
    data_dir: "/media/txt/jobs_data/"
    gold_data_dir: "/media/txt/jobs_gold_data/"
    evaluation_data_dir: "/media/txt/jobs_evaluation_data/"
    workers_confustion_matrix: "/workers/quality/matrix"
    workers_payment: "/workers/quality/payment"


    _assign_to_json: (a) -> {worker: a[0], object: a[1], label: a[2]}

    _assign_to_text: (a) -> [a.worker, a.object, a.label].join('\t')

    _gold_object_to_json: (o) -> {name: o[0], goldLabel: o[1]}

    _gold_object_to_text: (o) -> [o.name, o.goldLabel].join('\t')

    _evaluation_object_to_json: (o) -> {name: o[0], evaluationLabel: o[1]}

    _evaluation_object_to_text: (o) -> [o.name, o.evaluationLabel].join('\t')

    get_objects_prediction: (success) ->
        @objects_prediction = []
        @objects_headers = ["MinCost"]#TROIA-368["MaxLikelihood", "MinCost"]
        @_get_objects_prediction_rec(success, @objects_headers)

    _get_objects_prediction_rec: (success, label_choosing_functions) ->
        choose_func = label_choosing_functions[0]
        @_get(@_job_url() + @objects_prediction_url, {'labelChoosing': choose_func}, true,
            (response) =>
                result = $.parseJSON(response.responseText)['result']
                result['name'] = choose_func
                @objects_prediction.push(result)
                if (label_choosing_functions.length > 1)
                    @_get_objects_prediction_rec(success, label_choosing_functions[1..])
                else
                    @objects_prediction = @transpose_objects(
                        @objects_prediction,
                        "objectName",
                        "categoryName")
                    success()
            , null, true)

    get_workers_prediction: (success) ->
        @workers_prediction = []
        @workers_headers = ["ExpectedCost", "MinCost"]#TROIA-368["ExpectedCost", "MinCost", "MaxLikelihood"]
        @_get_workers_prediction_rec(() =>
            @_get(@_job_url() + @workers_confustion_matrix, {}, true,
                (response) =>
                    for r in $.parseJSON(response.responseText)['result']
                        @workers_prediction[r.workerName]["matrix"] =
                            _.template($("#confusion_matrix_template").html(), {
                                categories: @creation_data.categories,
                                data: r.value})
                    @_get(@_job_url() + @workers_payment, {}, true,
                        (response) =>
                            for r in $.parseJSON(response.responseText)['result']
                                @workers_prediction[r.workerName]["payment"] = r.value
                            success()
                        , null, true)
                , null, true)
        , @workers_headers)

    _get_workers_prediction_rec: (success, cost_algorithms) ->
        cost_algorithm = cost_algorithms[0]
        @_get(@_job_url() + @workers_prediction_url, {'costAlgorithm': cost_algorithm}, true,
            (response) =>
                result = $.parseJSON(response.responseText)['result']
                result["name"] = cost_algorithm
                @workers_prediction.push(result)
                if (cost_algorithms.length > 1)
                    @_get_workers_prediction_rec(success, cost_algorithms[1..])
                else
                    @workers_prediction = @transpose_objects(
                        @workers_prediction,
                        "workerName",
                        "value")
                    success()
            , null, true)

    get_objects_summary: (success) ->
        @_get(@_job_url() + @objects_summary_url, {}, true
            (response) =>
                result = _.omit($.parseJSON(response.responseText)['result'], "MaxLikelihood")
                @objects_summary = result
                success(response)
            null, true)

    get_workers_summary: (success) ->
        @_get(@_job_url() + @workers_summary_url, {}, true
            (response) =>
                result = _.omit($.parseJSON(response.responseText)['result'], "MaxLikelihood")
                @workers_summary = result
                success(response)
            null, true)

    get_summary: (success) ->
        @get_objects_summary (response) =>
            @get_workers_summary (response) =>
                if (not _.has(this, 'creation_data'))
                    @get_job (response) ->
                        success(response)
                else
                    success(response)

    # for input [{key: 'aaa', value: 'bbb'}, {key: 'ccc', value: 'ddd'}, name="EEE"]
    # returns {'aaa': {"EEE": 'bbb'}, 'ccc': {"EEE": 'ddd'}}
    transpose_objects: (arg, key, value) ->
        ret = {}
        for a in arg[0]
            ret[a[key]] = {}
        for res in arg
            for a in res
                ret[a[key]][res.name] =  if typeof a[value] == "number" then Math.round(a[value]*100)/100 else a[value]
        return ret
