window.App = {}

class Client
    constructor: (@id = @generate_id(), @api_url = 'http://localhost:8080/troia-server-0.8/') ->
        @chunk_size = 10

    set_id: (@id) ->

    generate_id: ->
        "troia-web-test-" + new Date().getTime().toString() + "-" + parseInt(Math.random()*1000000000000)

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

    compute: (iterations = 20) ->
        @_post(@jobs_cb + @id + @compute_cb, {'iterations': iterations}, 
            true, success, true)

    get_test_data: (type, data_cb, gold_data_cb) ->
        $.ajax(
            url: @data_folder + type)
            .done((data) ->
                data_cb())
        $.ajax(
            url: @gold_data_folder + type)
            .done((data) ->
                gold_data_cb())


    _post_in_chunks: (url, data, axis, async, offset, success) ->
        limit = Math.min(@chunk_size, data[axis].length - offset)
        @_post(url, data[axis][offset..offset+limit], async, 
            (res) ->
                if offset + limit < data[axis].length
                    @_post_in_chunks(url, data, axis, async, offset+limit, success, id)
                else
                    success()
            ,true)

    _post: (url, data, async, success, redirect) ->
        $.ajax
            url: @api_url + url
            type: "post"
            async: async
            data: @_jsonify(data)
            success: (response) ->
                if redirect
                    @_redirect_func(response, success)
                else
                    success(response)
            error: @_ajax_error

    _get: (url, data, async, success, error, redirect) ->
        $.ajax
            url: @api_url + url
            type: "get"
            async: async
            data: data
            success: (response) =>
                if redirect
                    @_redirect_func(response, success)
                else
                    success(response)
            error: if error then error else @_ajax_error

    _redirect_func: (response, success) ->
        timeout_func = () =>
            $.ajax
                url: @api_url + response.redirect
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
    'jobs_cb': "jobs/"
    'assigns_cb': "/assignedLabels"
    'compute_cb': "/compute"
    'gold_labels_cb': "/goldData"
    'data_prediction_cb': "/prediction/data"
    'data_folder': "/media/txt/jobs_data/"
    'gold_data_folder': "/media/txt/jobs_gold_data/"

    create: (categories, success) ->
        @_post(@jobs_cb, {'id': id, 'categories': categories},
            true, success, false)

    post_assigns: (assigns, success) ->
        @_post_in_chunks(@jobs_cb + @id + @assigns_cb, {'labels': assigns},
            "labels", true, 0, success)

    post_gold_labels: (labels, success) ->
        if labels
            @_post_in_chunks(@jobs_cb + @id + @gold_labels_cb, {'labels': 
                labels}, "labels", true, 0, success)

    collect_predicted_labels: (success) ->
        @predicted_labels = []
        algorithms = ["DS", "MV"]
        label_choosing_functions = ["MaxLikelihood", "MinCost"];
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
    'jobs_cb': "cjobs/"
    'assigns_cb': "/assigns"
    'compute_cb': "/compute"
    'gold_labels_cb': "/goldObjects"
    'data_prediction_cb': "/prediction/objects/"
    'worker_prediction_cb': "/prediction/workers/"
    'data_folder': "/media/txt/cjobs_data/"
    'gold_data_folder': "/media/txt/cjobs_gold_data/"

    create: (success) ->
        @_post(@jobs_cb, {'id': @id}, true, success, false)

    post_assigns: (assigns, success) ->
        for assign in assigns
            @_post(@jobs_cb + @id + @assigns_cb, {
                'object': assign[0],
                'worker': assign[1],
                'label': assign[2]}, 
                false, #in the future we will post in chunks and use async = true
                () -> console.log "todo"
                , true)
        success()

    post_gold_labels: (labels, success) ->
        for label in labels
            @_post(@jobs_cb + @id + @gold_labels_cb, {
                'objectId': label[0],
                'label': label[1],
                'zeta': label[2]}, 
                false, #in the future we will post in chunks and use async = true
                () -> console.log "todo"
                , true)
        success()

    collect_predicted_labels: (success) ->
        @predicted_labels = []
        @_get(@jobs_cb + @id + @data_prediction_cb, {}, true, 
            (res) =>
                @predicted_labels.push($parseJSON(res.responseText))
            , null, true)

    collect_workers_statistics: (success) ->
        @worker_stats = []
        @_get(@jobs_cb + @id + @worker_prediction_cb, {}, true,
            (res) =>
                @worker_stats.push($parseJSON(res.responseText))
            , null, true)
