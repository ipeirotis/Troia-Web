window.App = {}

class App.Client
    api_url: '/api'
    download_zip_url: "/prediction/zip"
    assigns_url: "/assigns"
    compute_url: "/compute"
    gold_objects_url: "/goldObjects"
    evaluation_objects_url: "/evaluationObjects"
    objects_prediction_url: "/objects/prediction/"
    workers_prediction_url: "/workers/quality/estimated/"
    creation_data: {}

    constructor: (@id = null) ->
        @chunk_size = 500

    create: (success) ->
        settings = {contentType: 'application/json; charset=utf-8'}
        @_post(@jobs_url, @_stringify(@creation_data), true,
            (response) =>
                result = response.result.replace(/.*ID\:\s*/, ($0) -> '')
                @id = result.replace(/.*ID\:\s*/, ($0) -> '')
                success(response)
            null, null, settings
        )

    exists: (exists_cb, not_exists_cb) ->
        @_get(@_job_url(), {}, true, (response) ->
            if response["status"] == "OK"
                exists_cb()
            else
                not_exists_cb()
        , null, true)

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
        @_get(@_job_url(), {}, true,
            (response) =>
                # XXX nasty fix for bug on loading historical job.
                # Probably one can done it better.
                @summary = response['result']
                @creation_data = @summary['initializationData']
                delete @summary['initializationData']
                success(response)
            null
            true
        )

    get_example_job: (type, data_success, gold_success, evaluation_success, success) ->
        $.ajax(url: @data_dir + type)
            .done((data) =>
                data_success(data)
                $.ajax(url: @gold_data_dir + type)
                    .done((data) =>
                        gold_success(data)
                        $.ajax(url: @evaluation_data_dir + type)
                            .done((data) ->
                                evaluation_success(data)
                                success()
                                )
                        )
                )

    post_assigns: (assigns, success, partial_success) ->
        assigns = {assigns: assigns.map(@_assign_to_json)}
        settings = {contentType: 'application/json; charset=utf-8'}
        @_post_in_chunks(@_job_url() + @assigns_url, assigns, 'assigns', true,
            0, success, null, settings, @_stringify, partial_success)

    _post_objects: (objects, success, partial_success, map_func, url) ->
        objects = {objects: objects.map(map_func)}
        settings = {contentType: 'application/json; charset=utf-8'}
        @_post_in_chunks(@_job_url() + url, objects,
            'objects', true, 0, success, null, settings, @_stringify, partial_success)

    post_gold_objects: (objects, success, partial_success) ->
        @_post_objects(objects, success, partial_success, @_gold_object_to_json, @gold_objects_url)

    post_evaluation_objects: (objects, success, partial_success) ->
        @evaluationObjects = {}
        for obj in objects
            @evaluationObjects[obj[0]] = obj[1]
        @_post_objects(objects, success, partial_success, @_evaluation_object_to_json, @evaluation_objects_url)

    download_zip: () ->
        @_get(@_job_url() + @download_zip_url, {}, true,
            (response) =>
                result = response['result']
                window.location.assign(result)
            , null, true)

    get_assigns: (success) ->
        @assigns = []
        @_get(@_job_url() + @assigns_url, {}, true,
            (response) =>
                @assigns = response['result']
                success(response)
            , null, true)

    get_gold_objects: (success) ->
        @gold_objects = []
        @_get(@_job_url() + @gold_objects_url, {}, true,
            (response) =>
                @gold_objects = response['result']
                success(response)
            , null, true)

    get_evaluation_objects: (success) ->
        @evaluation_objects = []
        @_get(@_job_url() + @evaluation_objects_url, {}, true,
            (response) =>
                @evaluation_objects = response['result']
                @evaluationObjects = {}
                for l in @evaluation_objects
                    @evaluationObjects[l.name] = l.evaluationLabel
                success(response)
            , null, true)

    get_objects_prediction: (success) ->
        @objects_prediction = []
        @_get(@_job_url() + @objects_prediction_url, {}, true,
            (response) =>
                @objects_prediction = response['result']
                success(response)
            , null, true)

    get_workers_prediction: (success) ->
        @workers_prediction = []
        @_get(@_job_url() + @workers_prediction_url, {}, true,
            (response) =>
                @workers_prediction = response['result']
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

    get_summary: (success) ->

    get_results: (success_objects, success_workers, success_summary, success) ->
        @get_prediction success_objects, success_workers, (response) =>
            @get_summary (response) ->
                success_summary(response)
                success(response)

    _job_url: (id = @id) -> @jobs_url + '/' + id

    _post_in_chunks: (url, data, axis, async, offset, success, error, settings, process, partial_cb) ->
        limit = Math.min(@chunk_size, data[axis].length - offset)
        # TODO currently it sends only the axis field.
        load = {}
        load[axis] = data[axis][offset..offset+limit]
        load = if process then process(load) else load
        @_post(url, load, async,
            (res) =>
                partial_cb(Math.min(Math.floor(100*(offset+limit)/data[axis].length), 100))
                if offset + limit < data[axis].length
                    @_post_in_chunks(url, data, axis, async, offset+limit,
                        success, error, settings, process, partial_cb)
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
                    json = $.parseJSON(res.responseText.replace(/NaN/g, null))
                    if json.status is "NOT_READY"
                        setTimeout(timeout_func, 500)
                    else
                        success(json)
        setTimeout(timeout_func, 500)

    _stringify: (data) -> JSON.stringify(data)

    _ajax_error: (jqXHR, textStatus, errorThrown) ->
        console.log jqXHR, textStatus, errorThrown

