window.App = {}

class Client
    api_url: '/api'
    download_zip_url: "/prediction/zip"
    assigns_url: "/assigns"
    compute_url: "/compute"
    gold_objects_url: "/goldObjects"
    objects_prediction_url: "/objects/prediction/"
    workers_prediction_url: "/workers/quality/estimated/"
    _creation_data: {}

    constructor: (@id = null) ->
        @chunk_size = 100

    create: (success) ->
        @_post(@jobs_url, @_creation_data, true,
            (response) =>
                result = response.result.replace(/.*ID\:\s*/, ($0) -> '')
                @id = result.replace(/.*ID\:\s*/, ($0) -> '')
                success(response)
        )

    exists: () ->
        ret = false
        @_get(@jobs_url + @id, {}, false,
            () -> ret = true,
            () -> ret = false
        )
        return ret

    ping: () ->
        ret = false
        @_get('/status', {}, false
            () -> ret = true
            (jqXHR, textStatus, errorThrown) =>
                @_ajax_error(jqXHR, textStatus, errorThrown)
                ret = false
        )
        return ret

    compute: (success) ->
        @_post(@_job_url() + @compute_url, {}, true, success, null, true)


    get_job: (success) ->
        @_get(@_job_url(), {}, true, success, null, true)

    get_example_job: (type, data_success, gold_success) ->
        $.ajax(
            url: @data_dir + type)
            .done(data_success)
        $.ajax(
            url: @gold_data_dir + type)
            .done(gold_success)

    post_assigns: (assigns, success) ->
        assigns = {assigns: assigns.map(@_assign_to_json)}
        settings = {contentType: 'application/json; charset=utf-8'}
        @_post_in_chunks(@_job_url() + @assigns_url, assigns, 'assigns', true,
            0, success, null, settings, @_stringify)

    post_gold_objects: (objects, success) ->
        objects = {objects: objects.map(@_gold_object_to_json)}
        settings = {contentType: 'application/json; charset=utf-8'}
        @_post_in_chunks(@_job_url() + @gold_objects_url, objects,
            'objects', true, 0, success, null, settings, @_stringify)

    download_zip: () ->
        @_get(@_job_url() + @download_zip_url, {}, true,
            (response) =>
                result = $.parseJSON(response.responseText)['result']
                window.location.assign(result)
            , null, true)

    get_assigns: (success) ->
        @assigns = []
        @_get(@_job_url() + @assigns_url, {}, true,
            (response) =>
                @assigns = $.parseJSON(response.responseText)['result']
                success(response)
            , null, true)

    get_gold_objects: (success) ->
        @gold_objects = []
        @_get(@_job_url() + @gold_objects_url, {}, true,
            (response) =>
                @gold_objects = $.parseJSON(response.responseText)['result']
                success(response)
            , null, true)

    get_objects_prediction: (success) ->
        @objects_prediction = []
        @_get(@_job_url() + @objects_prediction_url, {}, true,
            (response) =>
                @objects_prediction = $.parseJSON(response.responseText)['result']
                success(response)
            , null, true)

    get_workers_prediction: (success) ->
        @workers_prediction = []
        @_get(@_job_url() + @workers_prediction_url, {}, true,
            (response) =>
                @workers_prediction = $.parseJSON(response.responseText)['result']
                success(response)
            , null, true)

    get_prediction: (success_objects, success_workers, success) ->
        @get_objects_prediction((response) =>
                success_objects(response)
                @get_workers_prediction((response) ->
                    success_workers(response)
                    success(response)
                )
        )

    _job_url: (id = @id) -> @jobs_url + '/' + id

    _post_in_chunks: (url, data, axis, async, offset, success, error, settings, process) ->
        limit = Math.min(@chunk_size, data[axis].length - offset)
        # TODO currently it sends only the axis field.
        load = {}
        load[axis] = data[axis][offset..offset+limit]
        load = if process then process(load) else load
        @_post(url, load, async,
            (res) =>
                if offset + limit < data[axis].length
                    @_post_in_chunks(url, data, axis, async, offset+limit,
                        success, error, settings, process)
                else
                    success()
            , error, true, settings)

    _ajax: (url, type, data, async, success, error = null, redirect = null, settings = {}) ->
        set = $.extend(settings, {
            url: @api_url + url
            type: type
            data: data
            async: async
            success: (response) =>
                if redirect
                    @_redirect_func(response, success)
                else
                    success(response)
            error:
                if error then error else @_ajax_error
        })
        $.ajax(set)

    _post: (url, data, async, success, error = null, redirect = null, settings = {}) ->
        @_ajax(url, 'post', data, async, success, error, redirect, settings)

    _get: (url, data, async, success, error = null, redirect = null, settings = {}) ->
        @_ajax(url, 'get', data, async, success, error, redirect, settings)

    _redirect_func: (response, success) ->
        timeout_func = () =>
            $.ajax
                url: @api_url + "/" + response.redirect
                type: "get"
                complete: (res) ->
                    json = $.parseJSON(res.responseText)
                    if json.status is "OK"
                        success(res)
                    else
                        setTimeout(timeout_func, 500)
        setTimeout(timeout_func, 500)

    _jsonify: (data) ->
        result = {}
        for k, v of data
            result[k] = if k isnt "id" then JSON.stringify(v) else v
        return result

    _stringify: (data) -> JSON.stringify(data)

    _ajax_error: (jqXHR, textStatus, errorThrown) ->
        console.log jqXHR, textStatus, errorThrown


class App.NominalClient extends Client
    jobs_url: "/jobs"
    data_dir: "/media/txt/jobs_data/"
    gold_data_dir: "/media/txt/jobs_gold_data/"

    _assign_to_json: (a) -> {worker: a[0], object: a[1], label: a[2]}

    _assign_to_text: (a) -> [a.worker, a.object, a.label].join('\t')

    _gold_object_to_json: (o) -> {name: o[0], goldLabel: o[1]}

    _gold_object_to_text: (o) -> [o.name, o.goldLabel].join('\t')

    # collect_predicted_labels: (success) ->
    #     @predicted_labels = []
    #     algorithms = ["DS", "MV"]
    #     label_choosing_functions = ["MaxLikelihood", "MinCost"]
    #     for alg in algorithms
    #         for choose_func in label_choosing_functions
    #             @get_predicted_labels(
    #                 alg,
    #                 choose_func,
    #                 () =>
    #                     @predicted_labels.length == algorithms.length * label_choosing_functions.length
    #                 , success)

    # get_predicted_labels: (alg, label_choosing_func, success_cond, success) ->
    #     @_get(@jobs_cb + @id + @data_prediction_cb, {
    #         'algorithm': alg,
    #         'labelChoosing': label_choosing_func
    #         }, true,
    #         (res) =>
    #             json = $.parseJSON(res.responseText)
    #             @predicted_labels.push(json)
    #             if success_cond()
    #                 success()
    #         ,null, true)


class App.ContinuousClient extends Client
    jobs_url: "/cjobs"
    data_dir: "/media/txt/cjobs_data/"
    gold_data_dir: "/media/txt/cjobs_gold_data/"

    _assign_to_json: (a) -> {worker: a[0], object: a[1], label: {value: a[2]}}

    _assign_to_text: (a) -> [a.worker, a.object, a.label.value].join('\t')

    _gold_object_to_json: (o) -> {name: o[0], goldLabel: {value: o[1], zeta: o[2]}}

    _gold_object_to_text: (o) -> [o.name, o.goldLabel.value, o.goldLabel.zeta].join('\t')

