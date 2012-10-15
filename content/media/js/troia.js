function initialize() {

	var apiUrl = '/api/';
    var id = 123;
	var categoryList = [];
	var oldCategoryList = [];
    var chunkSize = 2;

//	var table_created = false;

	$('#response').hide();
	loadTestData();
	setTextareaMaxrows(50);
	
	$('#send_data').click(function() {
		// Validate input.
		var workerLabels = parseWorkerAssignedLabels();
        var goldLabels = parseGoldLabels();
        var costMatrix = parseCostMatrix(workerLabels);
		// Change button.
		$(this).addClass('disabled');
		var buttonText = $(this).text();
		$(this).text('Sending data..');
        // Upload data.
		reset(id);
		loadWorkerAssignedLabels(id, workerLabels);
		loadGoldLabels(id, goldLabels);
		loadCostMatrix(id, costMatrix);
		// Compute and get answer.
		$('#response').show();
		var i = 0;
        var numIterations = 1;
		var that = this;
		func = setInterval(function() {
			i += 1;
			if (i > $('#num_iterations').val()) {
				clearInterval(func);
				$(that).removeClass('disabled');
				$(that).text(buttonText);
			} else {
			    $(that).text('Iteration ' + i + '..');
			    compute(numIterations, function(res) {
//				$('#workers').html(worker_summary().replace(/\n/gi, '<br/>'));
				    $('#workers').html(create_workers_table(worker_summary()));
				    $('#classes').html(create_classes_table(majority_votes()));
                });
            }
		}, 1500);
	});
	
    $('a[data-toggle="tab"]').on('shown', function (e) {
    	if (e.target.getAttribute('href') === '#matrix') // && !table_created)
    	{
//    		table_created = true;
    		parse_worker_assigned_labels();
    		if (!_.isEqual(old_category_list, category_list))
    			createCostMatrix(categoryList);
    		$('#cost_matrix input').numeric({ negative : false });
    	}
    });
    

    function setTextareaMaxrows(maxRows) {
    	function handler(e) {
    		if (this.value.split('\n').length > maxRows)
                this.value = this.value.split('\n').slice(0, maxRows).join('\n');
    	}
    	$('#id_data').keyup(handler);
    	$('#id_gold_data').keyup(handler);
    }

    function loadTestData() {
    	$('#id_data').val("worker1 http://sunnyfun.com    porn\nworker1 http://sex-mission.com porn\nworker1 http://google.com      porn\nworker1 http://youporn.com     porn\nworker1 http://yahoo.com       porn\nworker2 http://sunnyfun.com    notporn\nworker2 http://sex-mission.com porn\nworker2 http://google.com      notporn\nworker2 http://youporn.com     porn\nworker2 http://yahoo.com       porn\nworker3 http://sunnyfun.com    notporn\nworker3 http://sex-mission.com porn\nworker3 http://google.com      notporn\nworker3 http://youporn.com     porn\nworker3 http://yahoo.com       notporn\nworker4 http://sunnyfun.com    notporn\nworker4 http://sex-mission.com porn\nworker4 http://google.com      notporn\nworker4 http://youporn.com     porn\nworker4 http://yahoo.com       notporn\nworker5 http://sunnyfun.com    porn\nworker5 http://sex-mission.com notporn\nworker5 http://google.com      porn\nworker5 http://youporn.com     notporn	\nworker5 http://yahoo.com       porn");
    	$('#id_gold_data').val("http://google.com      notporn");
    	parseWorkerAssignedLabels();
		createCostMatrix(categoryList);
    };
    
    function jsonify(data) {
    	var result = {};
		for (var key in data) {
			result[key] = JSON.stringify(data[key]);
		};
		return result;
    };
	
    /** Performs a POST request. */
	function post(url, data, async, success) {
        if (!success) {
            success == function(data, textStatus, jqXHR) {
                console.debug('POST request complete');
            }
        }
		$.ajax({
	        url: apiUrl + url,
	        type: 'post',
	        async: async,
	        data: jsonify(data),
	        success: success
        });
	};

    /** Performs a POST request. Sends data in chunks. */
    function postInChunks(url, data, async, success) {
        if (false) { //TODO
            console.warn('Attempt to post in chunks non-array object');
        }
        var chunk = undefined;
        var offset = 0;
        var reminder = undefined;
        do {
            limit = Math.min(chunkSize, data.length - offset);
            chunk = data.slice(offset, offset + limit);
            post(url, chunk, async, success);
            offset += limit;
        } while (offset < data.length);
    }
	
    /** Performs a POST request. Sends data in chunks but only along specified
     * axis (field). */
    function postInAxisChunks(url, data, axis, async, success) {
        if (false) { //TODO
            console.warn('Attempt to post in chunks non-array object');
        }
        var chunk = undefined;
        var offset = 0;
        var reminder = undefined;
        newData = data;
        do {
            limit = Math.min(chunkSize, data[axis].length - offset);
            chunk = data[axis].slice(offset, offset + limit);
            newData[axis] = chunk;
            post(url, newData, async, success);
            offset += limit;
        } while (offset < data[axis].length);
    }

	function get(url, data, async, complete) {
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
	        complete: complete
	    });
	};
	
	function misclassificationCost(labels, label) {
	//returns {'a': 1.0, 'b': 1.0, 'c': 0, 'd': 1.0} for labels=[a, b, c, d], label=c
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
		_.each($("#id_data").val().split(/\n/), function(line){
			var parsedLine = _.compact(line.split(/[\t ]/));
			if (parsedLine.length !== 3) {
				$('#data .control-group').addClass('error');
				$('#data span').text('Only 3 words per line allowed.');
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
			$('#myTab li:nth-child(1) a').tab('show');
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
		if ($("#id_gold_data").val()) {
			_.each($("#id_gold_data").val().split(/\n/), function(line){
				var parsedLine = _.compact(line.split(/[\t ]/));
				if (parsedLine.length !== 2) {
					$('#gold .control-group').addClass('error');
					$('#gold span').text('Only 2 words per line allowed.');
					dataError = true;
				}
				data.push({
					'objectName': parsedLine[0],
					'correctCategory': parsedLine[1]
				});
			});
            if (goldError) {
                $('#myTab li:nth-child(2) a').tab('show');
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
		_.each($('#cost_matrix_inner input'), function(i) {
			if (k % l === 0){
				d = {};
				data.push({
					'prior': 1.0,
					'name': labels[k / l],
					'misclassificationCost': d
				});
			}
			d[labels[k % l]] = parseFloat($(i).prop('value'));
			k += 1;
		});
		return data;
	};

	function loadWorkerAssignedLabels(id, labels) {
		postInAxisChunks('loadWorkerAssignedLabels', {
            'id': id,
            'labels': labels
        }, 'labels');
	};
	
	function loadGoldLabels(id, labels) {
		if (labels)
			post('loadGoldLabels', {
				'id': id,
                'labels': parseGoldLabels()
			});
	};
	
	function loadCostMatrix(id, costMatrix) {
		post('loadCategories', {
			'id': id,
			'categories': costMatrix
		});
	};
	
	function compute(id, numIterations, func) {
		get('computeBlocking', {
			'id': id,
			'iterations': numIterations
		}, func);
	}
	
	function majorityVotes(id) {
		var result = undefined;
		get('majorityVotes', {
			'id': id
		}, function(response){
            json = $.parseJSON(response.responseText);
            result = json.result;
		});
		return result;
	}
	
	function workerSummary(id)
	{
		var result = undefined;
        var success = function(response) {
            json = $.parseJSON(response.responseText);
            result = json.result;
        };
		get('printWorkerSummary', {
            'id': id,
            'verbose': false
        }, success);
		return result;
	}
	
	function reset(id)
	{
		get('reset', {
            'id': id
        });
	}
	
	function createClassesTable(classes) {
		return _.template($("#classes_template").html(), {
            classes: classes 
        });
	};
	
	function createWorkersTable(data) {
		var regex = /Worker: ([0-9a-zA-Z]+)\nError Rate: (\d+.\d*%)\nQuality \(Expected\): (---|\d+.\d*%)\nQuality \(Optimized\): (\-\-\-|\d+.\d*%)\nNumber of Annotations: (\d+)\nNumber of Gold Tests: (\d+)\nConfusion Matrix: \n(^(.)+\n)*/mg;
		var regexc = /Worker: ([0-9a-zA-Z]+)\nError Rate: (\d+.\d*%)\nQuality \(Expected\): (---|\d+.\d*%)\nQuality \(Optimized\): (\-\-\-|\d+.\d*%)\nNumber of Annotations: (\d+)\nNumber of Gold Tests: (\d+)\nConfusion Matrix: \n((.|\n)*)/m;
		var result = [];
		_.each(data.match(regex), function(m) {
			result.push(regexc.exec(m));
		});		
		return _.template($("#workers_template").html(), {workers: result} );
	}

	function createCostMatrix(labels) {
		$('#cost_matrix_inner').empty();
		row = new Array();
		cell = new Array();
		cat= categories(labels);
		row_num = labels.length;
		cell_num = labels.length;
		
		tab=document.createElement('table');
		tab.setAttribute('id','newtable');
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
	};	
}

$(document).ready(function() {
	initialize();
});
