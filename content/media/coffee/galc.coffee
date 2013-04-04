class App.ContinuousClient extends App.Client
    jobs_url: "/cjobs"
    data_dir: "/media/txt/cjobs_data/"
    gold_data_dir: "/media/txt/cjobs_gold_data/"

    _assign_to_json: (a) -> {worker: a[0], object: a[1], label: {value: a[2]}}

    _assign_to_text: (a) -> [a.worker, a.object, a.label.value].join('\t')

    _gold_object_to_json: (o) -> {name: o[0], goldLabel: {value: o[1], zeta: o[2]}}

    _gold_object_to_text: (o) -> [o.name, o.goldLabel.value, o.goldLabel.zeta].join('\t')

