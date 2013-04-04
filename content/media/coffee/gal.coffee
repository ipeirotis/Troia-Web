class App.NominalClient extends App.Client
    jobs_url: "/jobs"
    data_dir: "/media/txt/jobs_data/"
    gold_data_dir: "/media/txt/jobs_gold_data/"

    _assign_to_json: (a) -> {worker: a[0], object: a[1], label: a[2]}

    _assign_to_text: (a) -> [a.worker, a.object, a.label].join('\t')

    _gold_object_to_json: (o) -> {name: o[0], goldLabel: o[1]}

    _gold_object_to_text: (o) -> [o.name, o.goldLabel].join('\t')

    get_objects_prediction: (success) ->
        @objects_prediction = []
        label_choosing_functions = ["MaxLikelihood", "MinCost"]
        for choose_func in label_choosing_functions
            @_get(@_job_url() + @objects_prediction_url, {'labelChoosing': choose_func}, true,
                (response) =>
                    console.log(response)
                    result = $.parseJSON(response.responseText)['result']
                    result['name'] = choose_func
                    @objects_prediction.push(result)
                    if @objects_prediction.length == label_choosing_functions.length
                        console.log @objects_prediction
                        console.log @transpose_objects(@objects_prediction)
                        success(response)
                , null, true)

    transpose_objects: (arg) ->
        ret = [];
        _.each(_.keys(arg[0]), (obj) ->
            if (obj != "name")
                ret.push({'name': obj});
        )
        # console.log ret
        _.each(arg, (a) ->
            _.each(ret, (obj) ->
                obj[a.name] = typeof a[obj.name] == "number" ? Math.round(a[obj.name]*100)/100 : a[obj.name];
            )
        )
        return ret;
