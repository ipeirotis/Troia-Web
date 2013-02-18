window.App = {}

class Client
    constructor: (@id = @generate_id(), @api_url = 'api') ->
        @job_url = "#{@api_url}/#{@id}"
        @chunk_size = 10

    set_id: (@id) ->

    generate_id: ->
        @id = "troia-web-test-" + new Date().getTime().toString() + "-" + parseInt(Math.random()*1000000000000)

    exists: ->
        ret = false
        @_get(@jobs_cb + @id, {}, false,
            () -> ret = true,
            () -> ret = false,
            false)
        return ret

    ping: ->
        ret = false
        @_get('status', {}, false,
            () -> ret = true,
            () -> ret = false,
            false)
        return ret

    compute: (success, iterations = 20) ->
        @_post("#{@jobs_cb}/#{@id}#{@compute_cb}", {'iterations': iterations},
            true, success, true)

    get_test_data: (type, data_cb, gold_data_cb) ->
        $.ajax(
            url: @data_folder + type)
            .done(data_cb)
        $.ajax(
            url: @gold_data_folder + type)
            .done(gold_data_cb)

    _post_in_chunks: (url, data, axis, async, offset, success) ->
        limit = Math.min(@chunk_size, data[axis].length - offset)
        @_post(url, data[axis][offset..offset+limit], async,
            (res) ->
                if offset + limit < data[axis].length
                    @_post_in_chunks(url, data, axis, async, offset+limit, success, id)
                else
                    success()
            ,true)

    _ajax: (url, type, data, async, success, error = null, redirect = null,
            settings = {}) ->
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
        console.log(set)
        $.ajax(set)

    _post: (url, data, async, success, error = null, redirect = null,
            settings = {}) ->
        @_ajax(url, 'post', data, async, success, error, redirect, settings)

    _get: (url, data, async, success, error = null, redirect = null,
            settings = {}) ->
        @_ajax(url, 'get', data, async, success, error, redirect, settings)

    _redirect_func: (response, success) ->
        timeout_func = () =>
            $.ajax
                url: @api_url + "/" + response.redirect
                type: "get"
                complete: (res) ->
                    if res.statusText is "OK"
                        success(res)
                    else
                        setTimeout(timeout_func, 500)
        setTimeout(timeout_func, 500)

    _jsonify: (data) ->
        result = {}
        for k, v of data
            result[k] = if k isnt "id" then JSON.stringify(v) else v
        return result

    _ajax_error: (jqXHR, textStatus, errorThrown) ->
        console.log jqXHR, textStatus, errorThrown


class App.NominalClient extends Client
    jobs_cb: "/jobs"
    assigns_cb: "/assignedLabels"
    compute_cb: "/compute"
    gold_labels_cb: "/goldData"
    data_prediction_cb: "/prediction/data"
    data_folder: "/media/txt/jobs_data/"
    gold_data_folder: "/media/txt/jobs_gold_data/"

    create: (categories, success) ->
        @_post(@jobs_cb, {'id': id, 'categories': categories},
            true, success, false)

    post_assigns: (assigns, success) ->
        @_post_in_chunks("#{@jobs_cb}/#{@id}/#{@assigns_cb}", {'labels': assigns},
            "labels", true, 0, success)

    post_gold_labels: (labels, success) ->
        if labels
            @_post_in_chunks(@jobs_cb + @id + @gold_labels_cb, {'labels':
                labels}, "labels", true, 0, success)

    collect_predicted_labels: (success) ->
        @predicted_labels = []
        algorithms = ["DS", "MV"]
        label_choosing_functions = ["MaxLikelihood", "MinCost"]
        for alg in algorithms
            for choose_func in label_choosing_functions
                @get_predicted_labels(
                    alg,
                    choose_func,
                    () =>
                        @predicted_labels.length == algorithms.length * label_choosing_functions.length
                    , success)

    get_predicted_labels: (alg, label_choosing_func, success_cond, success) ->
        @_get(@jobs_cb + @id + @data_prediction_cb, {
            'algorithm': alg,
            'labelChoosing': label_choosing_func
            }, true,
            (res) =>
                json = $.parseJSON(res.responseText)
                @predicted_labels.push(json)
                if success_cond()
                    success()
            ,null, true)


class App.ContinuousClient extends Client
    jobs_cb: "/cjobs"
    assigns_cb: "/assigns"
    compute_cb: "/compute"
    gold_objects_cb: "/goldObjects"
    data_prediction_cb: "/prediction/objects/"
    worker_prediction_cb: "/prediction/workers/"
    data_folder: "/media/txt/cjobs_data/"
    gold_data_folder: "/media/txt/cjobs_gold_data/"

    _post_as_json: (url, data, async, success, redirect) ->
        $.ajax
            url: @api_url + url
            type: 'post'
            dataType: 'json'
            contentType: "application/json; charset=utf-8"
            async: async
            data: JSON.stringify(data)
            success: (response) =>
                if redirect
                    @_redirect_func(response, success)
                else
                    success(response)
            error: @ajax_error

    create: (success) ->
        console.log("asd")
        @_post(@jobs_cb, {'id': @id}, true, success)
        console.log("asd")

    post_assigns: (assigns, success) ->
        url = "#{@jobs_cb}/#{@id}#{@assigns_cb}"
        json = JSON.stringify({
            assigns: {worker: a[0], object: a[1], label: a[2]} for a in assigns})
        console.log json
        settings = {contentType: 'application/json; charset=utf-8'}
        @_post(url, json, true, success, null, null, settings)

    post_gold_objects: (objects, success) ->
        url = "#{@jobs_cb}/#{@id}#{@gold_objects_cb}"
        objects = {'object': o[0], 'label': o[1]} for o in objects
        json = JSON.stringify({objects: objects})
        settings = {contentType: 'application/json; charset=utf-8'}
        @_post(url, json, true, success, null, null, settings)

    collect_predicted_labels: (success) ->
        @predicted_labels = []
        @_get(@jobs_cb + @id + @data_prediction_cb, {}, true,
            (res) =>
                @predicted_labels = $.parseJSON(res.responseText)['result']
                success()
            , null, true)

    collect_workers_statistics: (success) ->
        @worker_stats = []
        @_get(@jobs_cb + @id + @worker_prediction_cb, {}, true,
            (res) =>
                @worker_stats = $.parseJSON(res.responseText)['result']
                success()
            , null, true)
