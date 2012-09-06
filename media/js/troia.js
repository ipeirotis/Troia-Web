function initialize() {
	var api_url = "/api/";
	var iters = 1;
	var id = 123;
	$('#jobid').prop('value', id);
	var category_list = []; //lista klas
//	var table_created = false;
	$('#response').hide();
	load_test_data();
	
	
	$('#send_data').click(function(){
		var data = parse_worker_assigned_labels();
		id = parseInt($('#jobid').prop('value'));
		load_cost_matrix();
		load_worker_assigned_labels(data);
		load_gold_labels();
		$('#response').show();
		for(i=0; i<$('#iternumber').val(); i+=iters)
			compute(iters, function(res){
				$('#workers').html(worker_summary().replace(/\n/gi, '<br/>'));
				$('#classes').html(create_classes_table(majority_votes()));
			});
	});
    $('a[data-toggle="tab"]').on('shown', function (e) {
    	if (e.target.getAttribute('href') === '#matrix') // && !table_created)
    	{
//    		table_created = true;
    		parse_worker_assigned_labels();
    		create_table(category_list);
    	}
    })
    
    function load_test_data()
    {
    	$('#id_data').val("worker1 http://sunnyfun.com    porn\nworker1 http://sex-mission.com porn\nworker1 http://google.com      porn\nworker1 http://youporn.com     porn\nworker1 http://yahoo.com       porn\nworker2 http://sunnyfun.com    notporn\nworker2 http://sex-mission.com porn\nworker2 http://google.com      notporn\nworker2 http://youporn.com     porn\nworker2 http://yahoo.com       porn\nworker3 http://sunnyfun.com    notporn\nworker3 http://sex-mission.com porn\nworker3 http://google.com      notporn\nworker3 http://youporn.com     porn\nworker3 http://yahoo.com       notporn\nworker4 http://sunnyfun.com    notporn\nworker4 http://sex-mission.com porn\nworker4 http://google.com      notporn\nworker4 http://youporn.com     porn\nworker4 http://yahoo.com       notporn\nworker5 http://sunnyfun.com    porn\nworker5 http://sex-mission.com notporn\nworker5 http://google.com      porn\nworker5 http://youporn.com     notporn	\nworker5 http://yahoo.com       porn");
    	$('#id_gold_data').val("http://google.com      notporn");
    	parse_worker_assigned_labels();
		create_table(category_list);
    };
    
    function jsonify(data)
    {
    	var post_data = {};
		for (var key in data) {
			post_data[key] = JSON.stringify(data[key]);
		};
		return post_data;
    };
	
	function do_post(url, data)
	{
		$.ajax({
	        url: api_url + url,
	        type: "POST",
	        async: false,
	        data: jsonify(data),
	        success: function(data, textStatus, jqXHR)
	        {
//	        	console.log('success')
	        }
	    });
	};
	
	function do_get(url, data, complete_fun)
	{
		if (! complete_fun)
			complete_fun = function(res){};
		$.ajax({
	        url: api_url + url,
	        type: "GET",
	        async: false,
	        data: jsonify(data),
	        complete: complete_fun
	    });
	};
	
	function misclassification_cost(labels, label)
	//returns {'a': 1.0, 'b': 1.0, 'c': 0, 'd': 1.0} for labels=[a, b, c, d], label=c
	{
		var ret = {};
		var avg = 1.0/(labels.length-1.0);
		_.each(labels, function(l){
			if (l !== label)
				ret[l] = avg;
		});
		ret[label] = 0;
		return ret;
	};
	
	function categories(labels){
		var ret = [];
		_.each(labels, function(l){
			ret.push({
				'prior': 1.0,
				'name': l,
				'misclassification_cost': misclassification_cost(labels, l)
			});
		});
		return ret;
	};
	
	function parse_worker_assigned_labels()
	{
		var data = [];
		category_list = [];
		_.each($("#id_data").val().split(/\n/), function(line){
			var parsed_line = _.compact(line.split(/[\t ]/));
			data.push({
				'workerName': parsed_line[0],
				'objectName': parsed_line[1],
				'categoryName': parsed_line[2]
			});
			if (parsed_line[2])
				category_list.push(parsed_line[2]);
		});
		category_list = _.uniq(category_list);
		return data;
	};
	
	function parse_gold_labels()
	{
		var data = [];
		if ($("#id_gold_data").val())
		{
			_.each($("#id_gold_data").val().split(/\n/), function(line){
				var parsed_line = _.compact(line.split(/[\t ]/));
				data.push({
					'objectName': parsed_line[0],
					'correctCategory': parsed_line[1]
				});
			});
		}
		return data;
	};
	
	function parse_cost_matrix(labels)
	{
		var ret = [];
		var k = 0;
		var l = labels.length;
		_.each($('#mytable input'), function(i){
			if (k%l == 0){
				d = {};
				ret.push({
					'prior': 1.0,
					'name': labels[k/l],
					'misclassification_cost': d
				});
			}
			d[labels[k%l]] = parseFloat($(i).prop('value'));
			k += 1;
		});
		return ret;
	};
	
//////////////post requests
	function load_worker_assigned_labels(data)
	{
		do_post('loadWorkerAssignedLabels',{
			'id': id,
			'data': data
		});
	};
	
	function load_gold_labels()
	{
		var data = parse_gold_labels()
		if (data.length)
			do_post('loadGoldLabels', {
				'id': id,
				'data': data
			});
	};
	
	function load_cost_matrix()
	{
		
		do_post('loadCategories', {
			'id': id,
			'categories': parse_cost_matrix(category_list)
		});
	};
	
	function compute(it, fun)
	{
		do_get('computeBlocking', {
			'id': id,
			'iterations': it
		}, fun);
	}
	
	function majority_votes()
	{
		var res;
		do_get('majorityVotes', {
			'id': id
		}, function(response){
			res = response.responseText;
		});
		return res;
	}
	
	function worker_summary()
	{
		var res;
		do_get('printWorkerSummary', {
			'id': id,
			'verbose': false
		}, function(response){
			res = response.responseText;
		});
		return res;
	}
///////////////end of post requests
	
	function create_classes_table(data) {
		return _.template($("#classes_template").html(), {data: JSON.parse(data)} );
	};
	
//	function create_workers_table(data) {
//		return _.template($("#workes_template").html(), {data: JSON.parse(data)} );
//	}

	function create_table(labels) {
		$('#mytable').empty();
		row=new Array();
		cell=new Array();
		cat = categories(labels);
	
		row_num=labels.length;
		cell_num=labels.length;
		
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
				$(cont).css('width', 100);
				$(cont).prop('value', category['misclassification_cost'][labels[k]]);
				cell[k].appendChild(cont);
				row[c].appendChild(cell[k]);
			}
			tbo.appendChild(row[c]);
		}
		tab.appendChild(tbo);
		$('#mytable')[0].appendChild(tab);
	};	
}

$(document).ready(function() {
	initialize();
});
