function initialize() {


    var apiUrl = 'http://localhost:8080/troia-server-0.0.1/';
    var id = getURLParameter("id");
    var categoryList = [];
    var oldCategoryList = [];
    var chunkSize = 500;
    var numIterations = 10;
    var hasErrors = false;
    var loading = false;

    $('#url').hide();
    $(".alert").hide();

    if (id && exists(id)) {
        //switch to results tab
        $('#menuTab li:nth-child(2) a').tab('show');
        //disable inputs tab
        $("#menuTab li:nth-child(1) a").attr("data-toggle", "").css("cursor",  "not-allowed");
        //print results
        majorityVotes(id); //calls workerSummary
    }
    else {
        //disable results tab
        $("#menuTab li:nth-child(2) a").attr("data-toggle", "").css("cursor",  "not-allowed");
        //when we provide id but it doesnt exist - show error
        if (id) {
            $(".alert p").text("Sorry, id=" + id + " hasn't been found.");
            $(".alert").show();
        }
        loadTestData();
        setTextareaMaxrows(20000);

        //loading data on select change
        $('#id_data_choose').change(function(){
            loadTestData($('#id_data_choose :selected').val());
        });

        var clickHandler = function() {
            $(".alert").hide();
            hasErrors = false;
            // Validate input.
            var workerLabels = parseWorkerAssignedLabels();
            var goldLabels = parseGoldLabels();
            var categories = parseCostMatrix(categoryList);
            if (!hasErrors && ping()) {
                id = "troia-web-test-" + new Date().getTime().toString() + "-" + parseInt(Math.random()*1000000000000);
                // Change button.
                var buttonText = $(this).text();
                $(this).addClass('disabled').text('Sending data..');
                var that = this;
                // Upload data.
                createJob(id, function(){
                    loadCategories(id, categories, function() {
                        loadWorkerAssignedLabels(id, workerLabels, function() {
                            loadGoldLabels(id, goldLabels, function() {
                                // Compute and get answer.
                                $("#img-load").show();
                                $("#response").hide();
                                $(that).text('Computing..');
                                $('#menuTab li:nth-child(2) a').attr("data-toggle", "tab").tab('show');

                                compute(id,  numIterations, function() {
                                    $(that).removeClass('disabled').text(buttonText);
                                    $(that).one('click', clickHandler);
                                    $("#url pre").text(document.URL + "?id=" + id);
                                    majorityVotes(id);
                                });
                            });
                        });
                    });
                });
            } else {
                $(this).one('click', clickHandler);
            }
        };
        $('#send_data').one('click', clickHandler);
    }

    $(document).keydown(function(e){
        if (e.keyCode === 27)
            $("a[rel=popover]").popover('hide');
    });

    $('a[data-toggle="tab"]').on('shown', function (e) {
        $(".alert").hide();
        if (e.target.getAttribute('href') === '#matrix')
        {
            parseWorkerAssignedLabels();
            if (!_.isEqual(oldCategoryList, categoryList))
            createCostMatrix(categoryList);
        }
    });

    function getURLParameter(name) {
        return decodeURIComponent((new RegExp('[?|&]' + name + '=' + '([^&;]+)').exec(location.search)||[,""])[1].replace(/\+/g, '%20'))||null;
    }

    function setTextareaMaxrows(maxRows) {
        function handler(e) {
            if (this.value.split('\n').length > maxRows){
                this.value = this.value.split('\n').slice(0, maxRows).join('\n');
                $(".alert p").text('Only ' + maxRows.toString() + ' lines allowed.');
                $(".alert").show();
            }
            else
                $(".alert").hide();
        }
        $('#id_data').keyup(handler);
        $('#id_gold_data').keyup(handler);
    }

    function loadTestData(type) {
        invalidateCostMatrix = function() {
            parseWorkerAssignedLabels();
            createCostMatrix(categoryList);
        }
        if (type)
        {
            $.ajax({
                url: "/media/txt/data" + type,
            }).done(function(data) { 
                $('#id_data').val(data);
                invalidateCostMatrix();
            });
            $.ajax({
                url: "/media/txt/gold" + type,
            }).done(function(data) { 
                $('#id_gold_labels').val(data);
                invalidateCostMatrix();
            });
        }
        else
        {
            $('#id_data').val("worker1 http://sunnyfun.com    porn\nworker1 http://sex-mission.com porn\nworker1 http://google.com      porn\nworker1 http://youporn.com     porn\nworker1 http://yahoo.com       porn\nworker2 http://sunnyfun.com    notporn\nworker2 http://sex-mission.com porn\nworker2 http://google.com      notporn\nworker2 http://youporn.com     porn\nworker2 http://yahoo.com       porn\nworker3 http://sunnyfun.com    notporn\nworker3 http://sex-mission.com porn\nworker3 http://google.com      notporn\nworker3 http://youporn.com     porn\nworker3 http://yahoo.com       notporn\nworker4 http://sunnyfun.com    notporn\nworker4 http://sex-mission.com porn\nworker4 http://google.com      notporn\nworker4 http://youporn.com     porn\nworker4 http://yahoo.com       notporn\nworker5 http://sunnyfun.com    porn\nworker5 http://sex-mission.com notporn\nworker5 http://google.com      porn\nworker5 http://youporn.com     notporn	\nworker5 http://yahoo.com       porn");
            $('#id_gold_labels').val("http://google.com      notporn");
            invalidateCostMatrix();
        }
    };

    function jsonify(data) {
        var result = {};
        for (var key in data) {
        	if (key !== 'id')
        		result[key] = JSON.stringify(data[key]);
        	else
        		result[key] = data[key];
        };
        return result;
    };

    function ajax_error(jqXHR, textStatus, errorThrown){
        $(".alert p").text("Troia server error (" + errorThrown.toString() + ").");
        $(".alert").show();
    }

    /** Performs a POST request. */
    function post(url, data, async, success, redirect, id) {
        if (!success) {
            success = function(data, textStatus, jqXHR) {
                console.debug('POST request complete');
            }
        }
        $.ajax({
            url: apiUrl + url,
            type: 'post',
            async: async,
            data: jsonify(data),
            complete: function(res) {
                if(redirect){
                    redirect_func(id, res, success);
                }
                else
                    success(res);
            },
            error: ajax_error
        });
    };

    /** Performs a POST request. Sends data in chunks but only along specified
     * axis (field). */
    function postInAxisChunks(url, data, axis, async, offset, success, id) {
        var newData = jQuery.extend({}, data);
        var limit = Math.min(chunkSize, data[axis].length - offset);
        newData[axis] = newData[axis].slice(offset, offset + limit);
        post(url, newData, async, function(res){
            var p = Math.min(Math.floor(100*(offset+limit)/data[axis].length), 100);
            $('#send_data').text("Sending " + axis + " (" + p.toString() + "%)...");
            if (offset+limit < data[axis].length)
                postInAxisChunks(url, data, axis, async, offset+limit, success, id);
            else
                success();
        }, true, id);
    }

    function get(url, data, async, complete, error, redirect, id) {
        if (!complete) {
            complete = function(res){
                console.debug('GET request complete');
            };
        }
        $.ajax({
            url: apiUrl + url,
            type: 'get',
            async: async,
            data: jsonify(data),
            complete: function(res) {
                if(redirect){
                    redirect_func(id, res, complete);
                }
                else
                    complete(res);
            },
            error: error ? error : ajax_error
        });
    };

    function redirect_func(id, res, success) {
        timeoutf = function(){
            json = $.parseJSON(res.responseText);
            $.ajax({
                url: apiUrl + 'jobs/' + id + "/status/" + json.redirect,
                type: 'get',
                complete: function(res) {
                    if (res.statusText === "OK")
                        success(res);
                    else
                        setTimeout(timeoutf, 500);

                },
                error: ajax_error
            });
        }
        setTimeout(timeoutf, 500);
    };

    function misclassificationCost(labels, label) {
        //returns {'a': 0.33, 'b': 0.33, 'c': 0, 'd': 0.33} for labels=[a, b, c, d], label=c
        var result = {};
        var avg = 1.0 / (labels.length - 1.0);
        _.each(labels, function(l) {
            if (l !== label)
            result[l] = avg;
        });
        result[label] = 0;
        return result;
    };

    function categories(labels){
        var result = [];
        _.each(labels, function(l) {
            result.push({
                'prior': 1.0,
                'name': l,
                'misclassificationCost': misclassificationCost(labels, l)
            });
        });
        return result;
    };

    /** Parses labels input. */
    function parseWorkerAssignedLabels() {
        var data = [];
        oldCategoryList = categoryList;
        categoryList = [];
        var dataError = false;
        _.each($("#id_data").val().split(/\n/), function(line, ind){
            var parsedLine = _.compact(line.split(/[\t ]/));
            if (parsedLine.length !== 3) {
                $('#data .control-group').addClass('error');
                $('#data span').text('Only 3 words per line allowed. Check your ' + (ind+1).toString() + ' line.');
                dataError = true;
            }
            data.push({
                'workerName': parsedLine[0],
                'objectName': parsedLine[1],
                'categoryName': parsedLine[2]
            });
            if (parsedLine[2]) {
                categoryList.push(parsedLine[2]);
            }
        });
        if (dataError) {
            hasErrors = true;
            $('#dataTab li:nth-child(1) a').tab('show');
        } else {
            $('#data .control-group').removeClass('error');
            $('#data span').text('');
        }
        categoryList = _.uniq(categoryList);
        return data;
    };

    /** Parses gold labels input. */
    function parseGoldLabels() {
        var data = [];
        var dataError = false;
        if ($("#id_gold_labels").val()) {
            _.each($("#id_gold_labels").val().split(/\n/), function(line, ind){
                var parsedLine = _.compact(line.split(/[\t ]/));
                if (parsedLine.length !== 2) {
                    $('#gold .control-group').addClass('error');
                    $('#gold span').text('Only 2 words per line allowed. Check your ' + (ind+1).toString() + ' line.');
                    dataError = true;
                }
                data.push({
                    'objectName': parsedLine[0],
                    'correctCategory': parsedLine[1]
                });
            });
            if (dataError) {
                hasErrors = true;
                $('#dataTab li:nth-child(2) a').tab('show');
                data = undefined;
            } else {
                $('#gold .control-group').removeClass('error');
                $('#gold span').text('');
            }
        }
        return data;
    };

    /** Parses cost matrix input. */
    function parseCostMatrix(labels) {
        var data = [];
        var k = 0;
        var l = labels.length;
        _.each($('#cost_matrix input'), function(i) {
            if (k % l === 0){
                d = {};
                data.push({
                    'prior': 1.0,
                    'name': labels[k / l],
                    'misclassification_cost': d
                });
            }
            d[labels[k % l]] = parseFloat($(i).prop('value'));
            k += 1;
        });
        return data;
    };

    function createJob(id, success) {
        post('jobs', {
            'id': id
        }, true, success, false);
    };

    function loadWorkerAssignedLabels(id, labels, success) {
        postInAxisChunks('jobs/' + id + '/assignedLabels', {
            'labels': labels
        }, "labels", true, 0, success, id);
    };

    function loadGoldLabels(id, labels, success) {
        if (labels)
            postInAxisChunks('jobs/' + id + "/goldData", {
                'labels': labels
            }, "labels", true, 0, success, id);
    };

    function loadCategories(id, categories, success) {
        post('jobs/' + id + '/categories', {
            'categories': categories
        }, true, success, true, id);
    };

    function compute(id, numIterations, success) {
        post('jobs/' + id + '/compute', {
            'iterations': numIterations
        }, true, success, true, id);
    }

    function exists(id) {
        $.ajax({
            url: apiUrl + 'jobs/' + id,
            type: 'get',
            async: false,
            complete: function (res){
                ret = true;
            },
            error: function(jqXHR, textStatus, errorThrown) {
                ret = false;
            }
        });
        return ret;
    }

    function ping() {
        ret = null;
        get('status/ping', {}, false, function() {
            if (ret === null) {
                ret = true;
            }
        }, function(jqXHR, textStatus, errorThrown) {
            ret = false;
            $(".alert p").text("Troia server error (" + errorThrown.toString() + ").");
            $(".alert").show();
        }, false);
        return ret;
    }

    function majorityVotes(id) {
        get('jobs/' + id + '/prediction/MV/data', {}, true, function(response){
            json = $.parseJSON(response.responseText);
            $('#classes').html(createClassesTable(json.result));
            workerSummary(id);
        }, ajax_error, true, id);
    }

    function workerSummary(id)
    {
        get('jobs/' + id + '/prediction/workers', {}, true, function(response) {
            json = $.parseJSON(response.responseText);
            $("#img-load").fadeOut(200, function() {
                $('#workers').html(createWorkersTable(json.result));
                $("a[rel=popover]").popover({html: true, title: "Confusion matrix", placement: "left"}).click(function(e) {
                    $("a[rel=popover]").not(this).popover('hide');
                    e.preventDefault();
                });
                $("#response").fadeIn(200);
                if (!$("#url pre").text()) {
                    $("#url pre").text(document.URL);
                }
                $("#url").fadeIn(200);
            });
        }, ajax_error, true, id);
    }

    function createClassesTable(classes) {
        return _.template($("#classes_template").html(), {
            classes: classes 
        });
    };

    function createWorkersTable(data) {
        if (categoryList.length === 0){
            categories = [];
            _.each(data[0]['Confusion Matrix'], function(el){
                categories.push(el['from']);
            });
            categoryList = _.uniq(categories);
        }
        categoryList = _.sortBy(categoryList);
        _.each(data, function(d){
            d['cm'] = _.template($("#confusion_matrix_template").html(), {categories: categoryList, data: d['Confusion Matrix']} );
        });
        return _.template($("#workers_template").html(), {workers: data} );
    }

    function createCostMatrix(labels) {
        $('#cost_matrix').empty();
        row = new Array();
        cell = new Array();
        cat= categories(labels);
        row_num = labels.length;
        cell_num = labels.length;

        tab=document.createElement('table');
        tbo=document.createElement('tbody');

        //header
        row = document.createElement('tr');
        row.appendChild(document.createElement('td'))
            for(k=0;k<cell_num;k++) {
                cell=document.createElement('td');
                cont = document.createTextNode(labels[k])
                    cell.appendChild(cont);
                row.appendChild(cell);
            }
        tbo.appendChild(row);

        //body
        for(c=0;c<row_num;c++){
            row[c]=document.createElement('tr');
            cell=document.createElement('td');
            cont = document.createTextNode(labels[c]);
            cell.appendChild(cont);
            row[c].appendChild(cell);

            var category = _.find(cat, function(ca){
                return ca['name'] === labels[c];
            });

            for(k=0;k<cell_num;k++) {
                cell[k]=document.createElement('td');
                cont=document.createElement('input');
                $(cont).css('width', 'auto');
                $(cont).prop('value', category['misclassificationCost'][labels[k]]);
                cell[k].appendChild(cont);
                row[c].appendChild(cell[k]);
            }
            tbo.appendChild(row[c]);
        }
        tab.appendChild(tbo);
        $('#cost_matrix')[0].appendChild(tab);
        $('#cost_matrix input').numeric({ negative : false });
    }
}

(function ($) {
    $.fn.rotateTableCellContent = function (options) {

        var cssClass = ((options) ? options.className : false) || "vertical";

        var cellsToRotate = $('.' + cssClass, this);

        var betterCells = [];
        cellsToRotate.each(function () {
            var cell = $(this)
            , newText = cell.text()
            , height = cell.height()
            , width = cell.width()
            , newDiv = $('<div>', { height: width, width: height }), newInnerDiv = $('<div>', { text: newText, 'class': 'rotated' });

        newDiv.append(newInnerDiv);

        betterCells.push(newDiv);
        });

        cellsToRotate.each(function (i) {
            $(this).html(betterCells[i]);
        });
    };
})(jQuery);

$(document).ready(function() {
    initialize();
    //$("#workers .table th").each(function(){$(this).height($(this).width())});
    //Basic usage
    $('#workers .table').rotateTableCellContent();

    //specify class name of cell you want to rotate
    $('#workers .table')
    .rotateTableCellContent({className: 'whatever'});

$("#workers .table").createScrollableTable({
    width: '586px',
    height: '600px'
});

});
