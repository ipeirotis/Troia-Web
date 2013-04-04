App.set_textarea_maxrows = (max_rows) ->
    handler = (e) ->
        if @value.split('\n').length > max_rows
            @value = @value.split('\n')[0...max_rows].join('\n')
            $(".alert p").text('Only ' + max_rows + ' lines allowed.')
            $(".alert").show()
        else
            $(".alert").hide()
    $('#eval_data_input').keyup(handler)
    $('#gold_data_input').keyup(handler)

App.get_url_parameter = `function(name) {
    return decodeURIComponent((new RegExp('[?|&]' + name + '=' + '([^&;]+)').exec(location.search) || [,""])[1].replace(/\+/g, '%20')) || null;
}`

App.get_base_url = () ->
    url = document.URL
    base_url = url.replace(/\?.*/g, ($0) -> '')
    base_url = base_url.replace(/\#.*/g, ($0) -> '')
    return base_url

App.get_job_url = (id) ->
    base_url = App.get_base_url()
    return base_url + '?id=' + id
