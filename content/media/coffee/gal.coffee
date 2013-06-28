class App.NominalClient extends App.Client
    jobs_url: "/jobs"
    estimated_objects_quality_summary_url: "/objects/quality/estimated/summary"
    evaluated_objects_quality_summary_url: "/objects/quality/evaluated/summary"
    estimated_objects_cost_summary_url: "/objects/cost/estimated/summary"
    estimated_workers_quality_summary_url: "/workers/quality/estimated/summary"
    evaluated_workers_quality_summary_url: "/workers/quality/evaluated/summary"
    data_dir: "/media/txt/jobs_data/"
    gold_data_dir: "/media/txt/jobs_gold_data/"
    evaluation_data_dir: "/media/txt/jobs_evaluation_data/"
    workers_confusion_matrix: "/workers/quality/matrix"
    workers_payment: "/workers/quality/payment"
    workers_details: "/workers/"
    workers_cost: "/workers/cost/estimated"
    worker_payment: (wid) -> "/workers/" + wid + "/quality/payment"

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
                result = response['result']
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
        @workers_headers = ["MinCost"]#TROIA-368["ExpectedCost", "MinCost", "MaxLikelihood"]
        @_get_workers_prediction_rec(success, @workers_headers)

    _get_workers_prediction_rec: (success, cost_algorithms) ->
        cost_algorithm = cost_algorithms[0]
        @_get(@_job_url() + @workers_prediction_url, {'costAlgorithm': cost_algorithm}, true,
            (response) =>
                result = response['result']
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

    get_workers_payment: () ->
        for wp in _.keys(@workers_prediction)
            @_get(@_job_url() + @worker_payment(wp), {}, true,
                (response) =>
                    result = response['result']
                    if result?
                        $("#" + result.workerName + "_payment").text(@_round(result.value, 2))
                , null, true)

    get_workers_confusion_matrices: () ->
        @_get(@_job_url() + @workers_confusion_matrix, {}, true,
            (response) =>
                for r in response['result']
                    $("#" + r.workerName + "_confusion_matrix").html(
                        _.template($("#confusion_matrix_template").html(), {
                                categories: @creation_data.categories,
                                data: r.value}))
            , null, true)

    get_workers_details: () ->
        @_get(@_job_url() + @workers_details, {}, true,
            (response) =>
                for r in response['result']
                    $("#" + r.workerName + "_details").html(
                        _.template($("#worker_details_template").html(), {
                                assigns: r.value.assigns,
                                gold_tests: r.value.goldTests,
                                correct_gold_tests: r.value.correctGoldTests}))
            , null, true)

    get_workers_cost: () ->
        @_get(@_job_url() + @workers_cost, {}, true,
            (response) =>
                for r in response['result']
                    $("#" + r.workerName + "_cost").text(@_round(r.value, 2))
            , null, true)

    get_objects_summary: (success) ->
        @_many_async_get_calls([
            {
                url: @estimated_objects_quality_summary_url,
                data: {},
                success: (response) =>
                    @estimated_objects_quality_summary = {}
                    for func, val of response['result']
                        @estimated_objects_quality_summary[func] = @_round(val, 2)

            },
            {
                url: @estimated_objects_cost_summary_url,
                data: {},
                success: (response) =>
                    @estimated_objects_cost_summary = {}
                    for func, val of response['result']
                        @estimated_objects_cost_summary[func] = @_round(val, 2)
            },
            {
                url: @evaluated_objects_quality_summary_url,
                data: {},
                success: (response) =>
                    @evaluated_objects_quality_summary = {}
                    for func, val of response['result']
                        @evaluated_objects_quality_summary[func] = @_round(val, 2)
            }],
            success)

    get_workers_summary: (success) ->
        @_many_async_get_calls([{
            url: @estimated_workers_quality_summary_url,
            data: {},
            success: (response) =>
                @estimated_workers_summary = {}
                for func, val of response['result']
                    @estimated_workers_summary[func] = @_round(val, 2)
        },
        {
            url: @evaluated_workers_quality_summary_url,
            data: {},
            success: (response) =>
                @evaluated_workers_summary = {}
                for func, val of response['result']
                    @evaluated_workers_summary[func] = @_round(val, 2)
        }],
        success)

    get_summary: (success) ->
        @get_objects_summary (response) =>
            @get_workers_summary (response) =>
                @get_job (response) ->
                    success(response)

    # for input [{key: 'aaa', value: 'bbb'}, {key: 'ccc', value: 'ddd'}, name="EEE"]
    # returns {'aaa': {"EEE": 'bbb'}, 'ccc': {"EEE": 'ddd'}}
    transpose_objects: (arg, key, value) ->
        ret = {}
        for a in arg[0]
            ret[a[key]] = {}
        for res in arg
            for a in res
                ret[a[key]][res.name] =  if typeof a[value] == "number" then @_round(a[value], 2) else a[value]
        return ret

    _round: (value, digits) ->
        Math.round(value*Math.pow(10, digits))/Math.pow(10, digits)
