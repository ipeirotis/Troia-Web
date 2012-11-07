function initialize() {

	var apiUrl = '/api/';
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
    	workerSummary(id);
    	majorityVotes(id);
    }
    else {
    	//disable results tab
    	$("#menuTab li:nth-child(2) a").attr("data-toggle", "").css("cursor",  "not-allowed");
    	//when we provide id but it doesnt exist - show error
    	if (id) {
    		$(".alert p").text("Sorry, id=" + id + " hasn't been found.");
			$(".alert").show();
    	}
    	$('#response').hide();
    	loadTestData();
    	setTextareaMaxrows(20000);
    	
    	//loading data on select change
    	$('#id_data_choose').change(function(){
    		loadTestData($('#id_data_choose :selected').val());
    	});
    	
    	$('#send_data').click(function() {
    		$(".alert").hide();
    		hasErrors = false;
    		// Validate input.
    		var workerLabels = parseWorkerAssignedLabels();
            var goldLabels = parseGoldLabels();
            var costMatrix = parseCostMatrix(categoryList);
    		if (!hasErrors && ping())
    		{
    			id = "troia-web-test-" + new Date().getTime().toString() + "-" + parseInt(Math.random()*1000000000000);
    			//if job exists, reset it
    	        if(exists(id))
    	        	reset(id);
    			// Change button.
    			$(this).addClass('disabled');
    			var buttonText = $(this).text();
    			$(this).text('Sending data..');
    			
    			var that = this;
    	        // Upload data.
    			loadCostMatrix(id, costMatrix, function() {
    				loadWorkerAssignedLabels(id, workerLabels, function() {
    					loadGoldLabels(id, goldLabels, function() {
    						// Compute and get answer.
    						$('#classes').text("");
    						$('#workers').text("");
    						$('#response').show();
    						timeoutFunc = function()
    						{
    							isComputed(id, function(res2){
    								json = $.parseJSON(res2.responseText);
    								if(!json.result)
    									setTimeout(timeoutFunc, 500);
    								else
    								{
    							    	workerSummary(id);
    							    	majorityVotes(id);
										$(that).removeClass('disabled');
										$(that).text(buttonText);
										$("#overlay").fadeOut();
										$("#url").fadeIn();
										$("#url pre").text(document.URL + "?id=" + id);
    								}
    							})
    						};
    						
    						setTimeout(function() {
    							$('#menuTab li:nth-child(2) a').attr("data-toggle", "tab").tab('show');
    							compute(id, numIterations, timeoutFunc);
    						}, 4000);
    					});
    				});
    			});
    		}
    	});
    }
    

	
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
        return decodeURIComponent((new RegExp('[?|&]' + name + '=' + '([^&;]+?)(&|#|;|$)').exec(location.search)||[,""])[1].replace(/\+/g, '%20'))||null;
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
	        complete: success,
	        error: function(jqXHR, textStatus, errorThrown) {
				$(".alert p").text("Troia server error (" + errorThrown.toString() + ").");
				$(".alert").show();
			}
        });
	};
	
    /** Performs a POST request. Sends data in chunks but only along specified
     * axis (field). */
    function postInAxisChunks(url, data, axis, async, offset, success) {
        	var newData = jQuery.extend({}, data);
            var limit = Math.min(chunkSize, data[axis].length - offset);
            newData[axis] = newData[axis].slice(offset, offset + limit);
            post(url, newData, async, function(res){
            	var p = Math.min(Math.floor(100*(offset+limit)/data[axis].length), 100);
            	$('#send_data').text("Sending " + axis + " (" + p.toString() + "%)...");
            	if (offset+limit < data[axis].length)
            		postInAxisChunks(url, data, axis, async, offset+limit, success);
            	else
            		success();
            });
    }

	function get(url, data, async, complete, error) {
		if (!complete) {
			complete = function(res){
                console.debug('GET request complete');
            };
        }
		if (!error) {
			error = function(jqXHR, textStatus, errorThrown) {
				$(".alert p").text("Troia server error (" + errorThrown.toString() + ").");
				$(".alert").show();
			};
		}
		$.ajax({
	        url: apiUrl + url,
	        type: 'get',
	        async: async,
	        data: jsonify(data),
	        complete: complete,
	        error: error
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

	function loadWorkerAssignedLabels(id, labels, success) {
		postInAxisChunks('loadWorkerAssignedLabels', {
            'id': id,
            'labels': labels
        }, "labels", true, 0, success);
	};
	
	function loadGoldLabels(id, labels, success) {
		if (labels)
			postInAxisChunks('loadGoldLabels', {
				'id': id,
                'labels': labels
			}, "labels", true, 0, success);
	};
	
	function loadCostMatrix(id, costMatrix, success) {
		post('loadCategories', {
			'id': id,
			'categories': costMatrix
		}, true, success);
	};
	
	function compute(id, numIterations, func) {
		get('computeNotBlocking', {
			'id': id,
			'iterations': numIterations
		}, true, func);
	}

	function isComputed(id, func) {
		get('isComputed', {
			'id': id
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
	
	function ping() {
		ret = false;
		get('ping', {}, false, function() {
			ret = true;
		}, function(jqXHR, textStatus, errorThrown) {
			ret = false;
			$(".alert p").text("Troia server error (" + errorThrown.toString() + ").");
			$(".alert").show();
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
		var labels = [];
		_.each(data.match(regex), function(m) {
			res = regexc.exec(m);
			matrix_res = [];
			_.each(res[7].match(matrix_regex), function(m) {
				matrix_res.push(matrix_regexc.exec(m));
			});
			if (!_.size(categoryList)) {
				_.each(matrix_res, function (el){
					labels.push(el[1]);
				});
				categoryList = _.uniq(labels);
			}
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
		$('#cost_matrix input').numeric({ negative : false });
	}
}

$(document).ready(function() {
	initialize();
});
