function initialize() {

	var apiUrl = '/api/';
	var id = 1;
	var categoryList = [];
	var oldCategoryList = [];
    var chunkSize = 100;

	$('#response').hide();
	loadTestData();
	
	$('#send_data').click(function() {
		id = parseInt(Math.random()*1000000000000);
		// Validate input.
		var workerLabels = parseWorkerAssignedLabels();
        var goldLabels = parseGoldLabels();
        var costMatrix = parseCostMatrix(categoryList);
		// Change button.
		$(this).addClass('disabled');
		var buttonText = $(this).text();
		$(this).text('Sending data..');
        // Upload data.
		if(exists(id))
			reset(id);
		loadCostMatrix(id, costMatrix);
		loadWorkerAssignedLabels(id, workerLabels);
		loadGoldLabels(id, goldLabels);
		// Compute and get answer.
		$('#classes').text("");
		$('#workers').text("");
		$('#response').show();
		var i = 1;
        var numIterations = 1;
		var that = this;
		func = function(res) {
			$(that).text('Iteration ' + i + '..');
	    	workerSummary(id);
	    	majorityVotes(id);
	    	if (i < $('#id_num_iterations').val())
	    	{
	    		setTimeout(function() {
	    			compute(id, numIterations, func);
	    		}, 1500);
	    	}
	    	else
	    	{
				clearInterval(func);
				$(that).removeClass('disabled');
				$(that).text(buttonText);
	    	}
	    	i++;
        }
		compute(id, numIterations, func);
	});
	
    $('a[data-toggle="tab"]').on('shown', function (e) {
    	if (e.target.getAttribute('href') === '#matrix')
    	{
    		parseWorkerAssignedLabels();
    		if (!_.isEqual(oldCategoryList, categoryList))
    			createCostMatrix(categoryList);
    		$('#cost_matrix input').numeric({ negative : false });
    	}
    });
    
    function loadTestData() {
    	$('#id_data').val("worker1 http://sunnyfun.com    porn\nworker1 http://sex-mission.com porn\nworker1 http://google.com      porn\nworker1 http://youporn.com     porn\nworker1 http://yahoo.com       porn\nworker2 http://sunnyfun.com    notporn\nworker2 http://sex-mission.com porn\nworker2 http://google.com      notporn\nworker2 http://youporn.com     porn\nworker2 http://yahoo.com       porn\nworker3 http://sunnyfun.com    notporn\nworker3 http://sex-mission.com porn\nworker3 http://google.com      notporn\nworker3 http://youporn.com     porn\nworker3 http://yahoo.com       notporn\nworker4 http://sunnyfun.com    notporn\nworker4 http://sex-mission.com porn\nworker4 http://google.com      notporn\nworker4 http://youporn.com     porn\nworker4 http://yahoo.com       notporn\nworker5 http://sunnyfun.com    porn\nworker5 http://sex-mission.com notporn\nworker5 http://google.com      porn\nworker5 http://youporn.com     notporn	\nworker5 http://yahoo.com       porn");
    	$('#id_gold_labels').val("http://google.com      notporn");
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
	
    /** Performs a POST request. Sends data in chunks but only along specified
     * axis (field). */
    function postInAxisChunks(url, data, axis, async, success) {
        if (false) { //TODO
            console.warn('Attempt to post in chunks non-array object');
        }
        var offset = 0;
        var reminder = undefined;
        var limit = 0;
        do {
        	var newData = jQuery.extend({}, data);
            limit = Math.min(chunkSize, data[axis].length - offset);
            newData[axis] = newData[axis].slice(offset, offset + limit);
            post(url, newData, async, function(res){
            	var p = Math.floor(100*offset/data[axis].length);
            	$('#send_data').text("Sending " + axis + " (" + p.toString() + "%)...");
            });
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
		if ($("#id_gold_labels").val()) {
			_.each($("#id_gold_labels").val().split(/\n/), function(line){
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
            if (dataError) {
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

	function loadWorkerAssignedLabels(id, labels) {
		postInAxisChunks('loadWorkerAssignedLabels', {
            'id': id,
            'labels': labels
        }, "labels", false);
	};
	
	function loadGoldLabels(id, labels) {
		if (labels)
			post('loadGoldLabels', {
				'id': id,
                'labels': labels
			}, true);
	};
	
	function loadCostMatrix(id, costMatrix) {
		post('loadCategories', {
			'id': id,
			'categories': costMatrix
		}, true);
	};
	
	function compute(id, numIterations, func) {
		get('computeBlocking', {
			'id': id,
			'iterations': numIterations
		}, true, func);
	}
	
	function exists(id) {
		ret = false;
		get('exists', {
			'id': id
		}, false, function (res){
			json = $.parseJSON(res.responseText);
            ret = json.result;
		});
		return ret;
	}
	
	function majorityVotes(id) {
		get('majorityVotes', {
			'id': id
		}, true, function(response){
            json = $.parseJSON(response.responseText);
            $('#classes').html(createClassesTable(json.result));
		});
	}
	
	function workerSummary(id)
	{
		get('printWorkerSummary', {
            'id': id,
            'verbose': false
        }, true, function(response) {
            json = $.parseJSON(response.responseText);
    	    $('#workers').html(createWorkersTable(json.result));
        });
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
		var matrix_regex = /P\[([0-9a-zA-Z]+)\->([0-9a-zA-Z]+)\]=(\d+.\d*%)/mg;
		var matrix_regexc = /P\[([0-9a-zA-Z]+)\->([0-9a-zA-Z]+)\]=(\d+.\d*%)/m;
		_.each(data.match(regex), function(m) {
			res = regexc.exec(m);
			matrix_res = [];
			_.each(res[7].match(matrix_regex), function(m) {
				matrix_res.push(matrix_regexc.exec(m));
			});
			res[7] = createConfusionMatrix(categoryList, matrix_res);
			result.push(res);
		});		
		return _.template($("#workers_template").html(), {workers: result} );
	}
	
	function createConfusionMatrix(labels, matrix_res) {
		row = new Array();
		cell = new Array();
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
		 
			for(k=0;k<cell_num;k++) {
				cell[k]=document.createElement('td');
//				var val = 0;
//				for (x=0; x<cell_num*cell_num; x++)
//					if (matrix_res[x][1] === labels[c] && matrix_res[x][2] === labels[k])
//					{
//						val = matrix_res[x][3];
//						break;
//					}
				cont=document.createTextNode(matrix_res[c*cell_num + k][3]);
				cell[k].appendChild(cont);
				row[c].appendChild(cell[k]);
			}
			tbo.appendChild(row[c]);
		}
		tab.appendChild(tbo);
		
		var tmp = document.createElement("div");
		tmp.appendChild(tab);
		return tmp.innerHTML;
	};	

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
	}
}

$(document).ready(function() {
	initialize();
});
