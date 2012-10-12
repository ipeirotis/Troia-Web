function initialize() {
	var api_url = "/api/";
	var iters = 1;
	var id = 123;
	$('#jobid').prop('value', id);
	var category_list = []; //lista klas
	var old_category_list = [];
	var data_error = false;
	var gold_error = false;
//	var table_created = false;
	$('#response').hide();
	load_test_data();
	set_textarea_maxrows(50);
	
	$('#send_data').click(function(){
		//validate
		var data = parse_worker_assigned_labels();
		parse_gold_labels();
		if (gold_error)
		{
			$('#myTab li:nth-child(2) a').tab('show');
			return;
		}
		if (data_error)
		{
			$('#myTab li:nth-child(1) a').tab('show');
			return;
		}
		//btn change
		var btn_text =$(this).text();
		$(this).addClass('disabled');
		
		//posting data
		reset();
		id = parseInt($('#jobid').prop('value'));
		$(this).text('Sending data..');
		load_cost_matrix();
		load_worker_assigned_labels(data);
		load_gold_labels();
		
		//compute and get answer
		$('#response').show();
		i = 0;
		var that = this;
		interval_func = setInterval(function(){
			i += 1;
			if (i>$('#iternumber').val())
			{
				clearInterval(interval_func);
				$(that).removeClass('disabled');
				$(that).text(btn_text);
				return;
			}
			$(that).text('Iteration ' + i + '..');
			compute(iters, function(res){
//				$('#workers').html(worker_summary().replace(/\n/gi, '<br/>'));
				$('#workers').html(create_workers_table(worker_summary()));
				$('#classes').html(create_classes_table(majority_votes()));
			});
		}, 1500);
	});
	
    $('a[data-toggle="tab"]').on('shown', function (e) {
    	if (e.target.getAttribute('href') === '#matrix') // && !table_created)
    	{
//    		table_created = true;
    		parse_worker_assigned_labels();
    		if (!_.isEqual(old_category_list, category_list))
    			create_table(category_list);
    		$('#mytable input').numeric({ negative : false });
    	}
    });
    

    function set_textarea_maxrows(rows)
    {
    	function handler(e)
    	{
    		if(this.value.split('\n').length > rows)
                this.value = this.value.split('\n').slice(0, rows).join('\n');
    	}
    	$('#id_data').keyup(handler);
    	$('#id_gold_data').keyup(handler);
    }

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
		old_category_list = category_list;
		category_list = [];
		data_error = false;
		_.each($("#id_data").val().split(/\n/), function(line){
			var parsed_line = _.compact(line.split(/[\t ]/));
			if (parsed_line.length !== 3)
			{
				$('#data .control-group').addClass('error');
				$('#data span').text('Only 3 words per line.');
				data_error = true;
			}
			data.push({
				'workerName': parsed_line[0],
				'objectName': parsed_line[1],
				'categoryName': parsed_line[2]
			});
			if (parsed_line[2])
				category_list.push(parsed_line[2]);
		});
		if (!data_error)
		{
			$('#data .control-group').removeClass('error');
			$('#data span').text('');
		}
		
		category_list = _.uniq(category_list);
		
		return data;
	};
	
	function parse_gold_labels()
	{
		var data = [];
		gold_error = false;
		if ($("#id_gold_data").val())
		{
			_.each($("#id_gold_data").val().split(/\n/), function(line){
				var parsed_line = _.compact(line.split(/[\t ]/));
				if (parsed_line.length !== 2)
				{
					$('#gold .control-group').addClass('error');
					$('#gold span').text('Only 2 words per line.');
					gold_error = true;
				}
				data.push({
					'objectName': parsed_line[0],
					'correctCategory': parsed_line[1]
				});
			});
			if (!gold_error)
			{
				$('#gold .control-group').removeClass('error');
				$('#gold span').text('');
			}
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
            'labels': data
		});
	};
	
	function load_gold_labels()
	{
		var data = parse_gold_labels()
		if (data.length)
			do_post('loadGoldLabels', {
				'id': id,
                'labels': data
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
            json = $.parseJSON(response.responseText);
            res = json.result;
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
            json = $.parseJSON(response.responseText);
            res = json.result;
		});
		return res;
	}
	
	function reset()
	{
		do_get('reset', {
			'id': id
		});
	}
///////////////end of post requests
	
	function create_classes_table(data) {
		return _.template($("#classes_template").html(), {data: data});
	};
	
	function create_workers_table(data) {
		var regex = /Worker: ([0-9a-zA-Z]+)\nError Rate: (\d+.\d*%)\nQuality \(Expected\): (---|\d+.\d*%)\nQuality \(Optimized\): (\-\-\-|\d+.\d*%)\nNumber of Annotations: (\d+)\nNumber of Gold Tests: (\d+)\nConfusion Matrix: \n(^(.)+\n)*/mg;
		var regexc = /Worker: ([0-9a-zA-Z]+)\nError Rate: (\d+.\d*%)\nQuality \(Expected\): (---|\d+.\d*%)\nQuality \(Optimized\): (\-\-\-|\d+.\d*%)\nNumber of Annotations: (\d+)\nNumber of Gold Tests: (\d+)\nConfusion Matrix: \n((.|\n)*)/m;
		var ret = []
		_.each(data.match(regex), function(m){
			ret.push(regexc.exec(m));
		});		
		return _.template($("#workers_template").html(), {data: ret} );
	}

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
				$(cont).css('width', 'auto');
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
