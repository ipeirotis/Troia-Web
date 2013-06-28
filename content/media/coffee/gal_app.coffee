class GAL_Application extends App.Application
    _client_type: App.NominalClient

    objects_validation_message: "Only 2 words per line allowed."
    data_dir: "/media/txt/jobs_data/"
    data_info_dir: "/media/txt/jobs_data_info/"
    gold_data_dir: "/media/txt/jobs_gold_data/"
    evaluation_data_dir: "/media/txt/jobs_evaluation_data/"

    objects_validator: (line) ->
        line.length != 2

    _before_create: () ->
        @categories = @_categories_from_assigns(@parse_assigns())
        @client.creation_data['categories'] = @categories
        @client.creation_data['categoryPriors'] = @_parse_category_priors()
        @client.creation_data['costMatrix'] = @_parse_cost_matrix()
        @client.creation_data['algorithm'] = $('#id_algorithm_choose :selected').val()

    _categories_from_assigns: (assigns) ->
        _.uniq(a[2] for a in assigns)

    _parse_cost_matrix: () ->
        data = []
        k = 0
        l = @categories.length
        for input in $('#cost_matrix input')
            data.push({
                "from": @categories[Math.floor(k / l)],
                "to": @categories[k % l],
                "value": parseFloat($(input).prop('value'))})
            k += 1
        return data

    _parse_category_priors: () ->
        data = []
        k = 0
        for input in $("#category_priors input")
            data.push({
                'categoryName': @categories[k],
                'value': $(input).prop('value')
                })
            k += 1
        return data

    on_tab_change: (e) ->
        if e.target.getAttribute('href') == '#matrix'
            categories = @_categories_from_assigns(@parse_assigns())
            if (!_.isEmpty(categories) and !_.isEqual(categories.sort(), @categories.sort()))
                @_post_loading_test_data()

    _post_populate_results_table: () ->
        @client.get_workers_confusion_matrices()
        @client.get_workers_details()
        @client.get_workers_payment()
        @client.get_workers_cost()
        @client.get_job((response) =>
            $(".spammer_cost").text(response['result']['strategicSpammerCost']))
        #make confusion matrices clickable
        clickedAway = false
        isVisible = false
        $("a[rel=popover]").popover({
            html: true,
            title: "Confusion matrix",
            placement: "right",
            trigger: "manual",
            content: () ->
                $("#" + @.id + "_info").html() }).click((e) ->
            $("a[rel=popover]").not(@).popover('hide')
            $(@).popover('show')
            clickedAway = false
            isVisible = true
            e.preventDefault()
            $('.popover').bind('click',() ->
                clickedAway = false
            )
        )
        $(document).click((e) ->
            if isVisible && clickedAway
                $("a[rel=popover]").popover('hide')
                isVisible = clickedAway = false
            else
                clickedAway = true
        )

    _post_loading_test_data: () ->
        @categories = @_categories_from_assigns(@parse_assigns())
        @_create_cost_matrix()
        @_create_category_priors()

    _post_loading_results: () ->
        @client.get_job((response) =>
            #select used algorithm
            init_data = response['result']['initializationData']
            $('#id_algorithm_choose').val(init_data['algorithm'])
            #create cost matrix and category priors table
            @categories = init_data['categories']
            @_create_cost_matrix(init_data['costMatrix'])
            @_create_category_priors(init_data['categoryPriors'])
        )

    _create_category_priors: (data = null) ->
        if data == null
            data = []
            for c in @categories
                data.push({'categoryName': c, 'value': 1.0/@categories.length})
        $("#category_priors").html(_.template($("#category_priors_template").html(), {
                            categories: @categories,
                            data: data}))

    _create_cost_matrix: (data = null) ->
        if data == null
            data = []
            for c1 in @categories
                for c2 in @categories
                    data.push({'from': c1, 'to': c2, 'value': if c1 == c2 then 0.0 else 1.0})
        $('#cost_matrix').html(_.template($("#cost_matrix_template").html(), {
                            categories: @categories,
                            data: data}))


a = new GAL_Application()
