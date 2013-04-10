class GAL_Application extends App.Application
    _client_type: App.NominalClient

    gold_objects_validation_message: "Only 2 words per line allowed."

    gold_objects_validator: (line) ->
        line.length != 2

    _before_create: () ->
        categories = @_categories_from_assigns(@parse_assigns())
        @client.creation_data['categories'] = categories
        @client.creation_data['categoryPriors'] =
            [{'categoryName': c, 'value': 1.0 / categories.length} for c in categories][0]
        @client.creation_data['costMatrix'] = @_parse_cost_matrix(categories)
        @client.creation_data['algorithm'] = $('#id_algorithm_choose :selected').val()

    _categories_from_assigns: (assigns) ->
        _.uniq(a[2] for a in assigns)

    _parse_cost_matrix: (categories) ->
        data = []
        k = 0
        l = categories.length
        for input in $('#cost_matrix input')
            data.push({
                "from": categories[Math.floor(k / l)],
                "to": categories[k % l],
                "value": parseFloat($(input).prop('value'))})
            k += 1
        return data

    on_tab_change: (e) ->
        if e.target.getAttribute('href') == '#matrix'
            @_create_cost_matrix(@parse_assigns())

    _post_populate_results_table: () ->
        #make confusion matrices clickable
        clickedAway = false
        isVisible = false
        $("a[rel=popover]").popover({html: true, title: "Confusion matrix", placement: "left", trigger: "manual"}).click((e) ->
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
        @_create_cost_matrix(@parse_assigns())

    _post_loading_results: () ->
        #select used algorithm
        @client.get_job((response) ->
            result = $.parseJSON(response.responseText)['result']
            $('#id_algorithm_choose').val(result['Initialization data']['algorithm'])
        )

    _create_cost_matrix: (assigns) ->
        $('#cost_matrix').empty()
        row = []
        cell = []
        categories = @_categories_from_assigns(assigns)

        tab = document.createElement('table')
        tbo = document.createElement('tbody')

        #header
        row = document.createElement('tr')
        row.appendChild(document.createElement('td'))
        for cat in categories
            cell = document.createElement('td')
            cont = document.createTextNode(cat)
            cell.appendChild(cont)
            row.appendChild(cell)
        tbo.appendChild(row)

        #body
        for cat1 in categories
            row = document.createElement('tr')
            cell= document.createElement('td')
            cont = document.createTextNode(cat1)
            cell.appendChild(cont)
            row.appendChild(cell)

            for cat2 in categories
                cell = document.createElement('td')
                cont = document.createElement('input')
                $(cont).css('width', 'auto')
                $(cont).prop('value', if cat1 == cat2 then 0 else 1.0 / (categories.length - 1))
                cell.appendChild(cont)
                row.appendChild(cell)
            tbo.appendChild(row)
        tab.appendChild(tbo)
        $('#cost_matrix')[0].appendChild(tab)
        $('#cost_matrix input').numeric({ negative : false })


a = new GAL_Application()
