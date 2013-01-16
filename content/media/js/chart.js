ValueType = Backbone.Model.extend({
	defaults: {checked: true, name: null}
});

ValueTypes = Backbone.Collection.extend({
	model:ValueType
});

// Views
ValueTypeView = Backbone.View.extend({
	tagName: "li",
	events: {
		"click input": "change"
	},
	change: function(){
		this.model.set("checked", !this.model.get("checked"));
	},
	render: function (eventName) {
		if (this.model.get('checked'))
			$(this.el).html("<input type='checkbox' value='" + this.model.get("name") + "' checked=''/>" + this.model.get("name"));
		else
			$(this.el).html("<input type='checkbox' value='" + this.model.get("name") + "'/>" + this.model.get("name"));
        return this;
    }
});

ValueTypeListView = Backbone.View.extend({
    tagName:'ul',
    initialize:function () {
        this.collection.bind("reset", this.render, this);
    },
    render:function (eventName) {
    	_.each(this.collection.models, function (vt) {
            $(this.el).append(new ValueTypeView({model:vt}).render().el);
            vt.bind("change", this.render_chart, this);
        }, this);
        return this;
    },
    render_chart: function(){
    	add_multiline_chart(
    			this.place, 
    			this.datafile,
    			this.dataset_name,
    			this.y_axis_txt, 
    			_.map(_.filter(this.collection.models, function(m) {return m.get('checked')}), function(v) { return v.get("name")}));
    }
});

var add_multiline_chart = function(place, datafile, dataset_name, y_axis_txt, to_view){ 
	var margin = {top: 5, right: 120, bottom: 100, left: 50};
	var width = 700 - margin.left - margin.right;
	var height = 400 - margin.top - margin.bottom;

	var color = d3.scale.category10();

	var x = d3.scale.ordinal()
    	.rangePoints([0, width], .1);

	var y = d3.scale.linear()
	    .range([height, 0]);

	var xAxis = d3.svg.axis()
	    .scale(x)
	    .orient("bottom");

	var yAxis = d3.svg.axis()
	    .scale(y)
	    .orient("left");
	
	var line = d3.svg.line()
		.x(function(d) { return x(d.date) + x.rangeBand()/2 ; })
		.y(function(d) { return y(d.value); });

	d3.select(place).html("");
	var svg = d3.select(place).append("svg")
	    .attr("width", width + margin.left + margin.right)
	    .attr("height", height + margin.top + margin.bottom)
	  .append("g")
	    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	d3.tsv(datafile, function(error, data) {
		color.domain(d3.keys(data[0]).filter(function(key) { return key !== "date"; }));
		
		var values = color.domain().map(function(name) {
			return {
				name: name,
				values: data.map(function(d) {
					return {date: d.date, value: +d[name]};
				})};
		});
		
		values = _.filter(values, function(v){
			return _.contains(to_view, v.name);
		});
		
		x.domain(data.map(function(d) { return d.date; }));
		y.domain([0, d3.max(values, function(c) { return d3.max(c.values, function(v) { return v.value; }); })]);

		svg.append("g")
			.attr("class", "x axis")
			.attr("transform", "translate(0," + height + ")")
			.call(xAxis)
		.selectAll("text")  
            .style("text-anchor", "end")
            .attr("dx", "-.8em")
            .attr("dy", ".15em")
            .attr("transform", function(d) {
                return "rotate(-55)" 
                });

		svg.append("g")
	      	.attr("class", "y axis")
	      	.call(yAxis)
	   	.append("text")
	   		.attr("transform", "rotate(-90)")
	   		.attr("y", 6)
	   		.attr("dy", ".71em")
	   		.style("text-anchor", "end")
	   		.text(y_axis_txt);

		var value_type = svg.selectAll(".city")
			.data(values)
			.enter().append("g")
			.attr("class", "city");
		value_type.append("path")
	      	.attr("class", "line")
	      	.attr("d", function(d) { return line(d.values); })
	      	.style("stroke", function(d) { return color(d.name); });
	
		value_type.append("text")
	      	.datum(function(d) { return {name: d.name, value: d.values[d.values.length - 1]}; })
	      	.attr("transform", function(d) { return "translate(" + x(d.value.date) + "," + y(d.value.value) + ")"; })
	      	.attr("x", 3)
	      	.attr("dy", ".35em")
	      	.text(function(d) { return d.name; });
	});
}

var datasets =['small', 'medium', 'big']; 
var chart_settings = {
	"data_cost": {
		"metrics" : ["Estm_DS_ExpectedCost", "Estm_DS_MinCost", "Estm_DS_MaxLikelihood", 
		             "Estm_MV_ExpectedCost", "Estm_MV_MinCost", "Estm_MV_MaxLikelihood", 
		             "Estm_NoVote_ExpectedCost", "Estm_NoVote_MinCost", "Estm_NoVote_MaxLikelihood", 
		             "Eval_DS_MaxLikelihood", "Eval_DS_MinCost", "Eval_DS_Soft", 
		             "Eval_MV_MaxLikelihood", "Eval_MV_MinCost", "Eval_MV_Soft"],
		"txt": "Average data cost"
	}, 
	"data_quality": {
		"metrics" : ["Estm_DS_ExpectedCost", "Estm_DS_MinCost", "Estm_DS_MaxLikelihood", 
		             "Estm_MV_ExpectedCost", "Estm_MV_MinCost", "Estm_MV_MaxLikelihood", 
		             "Eval_DS_MaxLikelihood", "Eval_DS_MinCost", "Eval_DS_Soft",
		             "Eval_MV_MaxLikelihood", "Eval_MV_MinCost", "Eval_MV_Soft"],
		"txt": "Average data quality"
	},
	"worker_quality": {
		"metrics" : ["Estm_DS_ExpectedCost", "Estm_DS_MinCost", "Estm_DS_MaxLikelihood",
		             "Eval_DS_ExpectedCost", "Eval_DS_MinCost", "Eval_DS_MaxLikelihood"],
		"txt": "Average workers quality"
	}
}
_.each(_.keys(chart_settings), function(chart_type){
	for (var t in datasets){
		var uberplace = "#" + chart_type;
		var place_id = chart_type + "_" + datasets[t];
		var place = "#" + place_id;
		var cb_place_id = place_id + "_mode";
		var cb_place = "#" + cb_place_id;
		var datafile = "/media/csv/" + chart_type + "_"+datasets[t]+".csv";
		var dataset_name = datasets[t];
		var y_axis_txt = chart_settings[chart_type]["txt"];
		
		d3.select(uberplace).append("div").attr("id", place_id).attr("class", "span7");
		d3.select(place).append("h4").text(datasets[t] + " data set");
		add_multiline_chart(
			place, 
			datafile,
			datasets[t], 
			y_axis_txt, 
			chart_settings[chart_type]["metrics"]
		);
		d3.select(uberplace).append("div").attr("id", cb_place_id).attr("class", "span3");
		
		var vts = new ValueTypes();
		var vtsv = new ValueTypeListView({collection: vts});
		vtsv.dataset_name = dataset_name;
		vtsv.place = place;
		vtsv.datafile = datafile;
		vtsv.y_axis_txt = y_axis_txt;
		values = [];
		_.each(chart_settings[chart_type]["metrics"], function(v){
			values.push({"name": v, "checked": true});
		});
		vts.add(values);
		$(cb_place).html(vtsv.render().el);
	}
});
