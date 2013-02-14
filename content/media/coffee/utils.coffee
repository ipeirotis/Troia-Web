App.set_textarea_maxrows = (max_rows) ->
    handler = (e) ->
        if @value.split('\n').length > max_rows
            @value = @value.split('\n')[0...max_rows].join('\n')
            $(".alert p").text('Only ' + max_rows + ' lines allowed.')
            $(".alert").show()
        else
            $(".alert").hide()
    $('#id_data').keyup(handler)
    $('#id_gold_data').keyup(handler)

App.parse_input = (input_el, control_el, text_el, tab_el, condition, error_msg) ->
    control_el.removeClass('error')
    text_el.text('')
    data = []
    for line, ind in input_el.val().split(/\n/)
        parsed_line = line.split(/[\t]/)
        if condition(parsed_line)
            control_el.addClass('error')
            text_el.text(error_msg + ' Check your ' + (ind+1).toString() + ' line.')
            tab_el.tab('show')
            return false
        data.push(parsed_line)

    return data
