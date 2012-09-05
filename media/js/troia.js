function initialize() {
	var api_url = "/server/";
	var id = '2227';
	var max_iters = 10;
	var iters = 1;
	var category_list = [];
	
	$('#send_data').click(function(){
		var data = parse_worker_assigned_labels();
		load_categories();
		load_worker_assigned_labels(data);
		load_gold_labels();
		//majority_votes();
		for(i=0; i<max_iters; i+=iters)
			compute(iters, function(res){
				worker_summary(function(res){
					$('#response').html(res.responseText.replace(/\n/gi, '<br/>'));
				});
			});
	});
    $('a[data-toggle="tab"]').on('shown', function (e) {
    	if (e.target.getAttribute('href') === '#matrix')
    	{
    		parse_worker_assigned_labels();
    		create_table(category_list);
    	}
    })
    
    function jsonify(data)
    {
    	var post_data = {};
		for (var key in data) {
			post_data[key] = JSON.stringify(data[key]);
		};
		return post_data;
    }
	
	function do_post(url, data)
	{
		$.ajax({
	        url: api_url + url,
	        type: "POST",
	        async: false,
	        data: jsonify(data),
	        success: function(data, textStatus, jqXHR)
	        {
	        	console.log('success')
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
		_.each($("#id_gold_data").val().split(/\n/), function(line){
			var parsed_line = _.compact(line.split(/[\t ]/));
			data.push({
				'objectName': parsed_line[0],
				'correctCategory': parsed_line[1]
			});
		});
		return data;
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
		do_post('loadGoldLabels', {
			'id': id,
			'data': parse_gold_labels()
		});
	};
	
	function load_categories()
	{
		do_post('loadCategories', {
			'id': id,
			'categories': categories(category_list)
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
		do_get('majorityVotes', {
			'id': id
		});
	}
	
	function worker_summary(fun)
	{
		do_get('printWorkerSummary', {
			'id': id,
			'verbose': false
		}, fun);
	}
///////////////end of post requests

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
				cont.setAttribute('value', category['misclassification_cost'][labels[k]]);
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

