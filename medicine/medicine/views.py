from medicine.flask_app import app
from flask import render_template, request, url_for
import json


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/analysis/apriori', methods=['GET'])
def apriori():
    return render_template('apriori.html')

@app.route('/analysis/apriori/ajax', methods=['GET', 'POST'])
def apriori_ajax():
    from medicine.analysis.association_rule import Apriori
    apriori = Apriori()

    if request.method == 'POST':
        sup_count = int(request.form['support'])
        conf = float(request.form['confidence'])
        max_len = int(request.form['len'])
        sup = sup_count / len(list(apriori.basket))
        apriori.generate_rules(min_support=sup, min_threshold=conf, max_len=max_len)
    else:
        sup = 10 / len(list(apriori.basket))
        apriori.generate_rules(min_support=sup)
    return apriori.rules.to_json(orient='records', force_ascii=False)

@app.route('/analysis/cluster', methods=['GET', 'POST'])
def cluster():
    return render_template('cluster.html')

@app.route('/analysis/cluster/ajax', methods=['GET', 'POST'])
def cluster_ajax():
    import json
    import pandas as pd
    from collections import Counter
    from medicine.analysis.cluster import Cluster

    kgroup = int(request.form.get('k', 8))
    group = int(request.form.get('g', 0))
    c = Cluster(kgroup)
    cluster_dict = c.get_cluster_dict()
    ids = cluster_dict.get(group)
    names = [c.dict_id_name[i] for i in ids]
    medicines = [c.compound_medicines[i] for i in ids]
    groups = [group] * len(ids)
    group_df = pd.DataFrame(data={'name': names, 'medicine': medicines, 'group': groups},
                            columns=['name', 'medicine', 'group'])
    table_data = group_df.to_json(orient='values', force_ascii=False)

    objs = []
    for ms in medicines:
        objs.extend(ms)
    chart_data = sorted(list(Counter(objs).items()), key=lambda tup: tup[1], reverse=True)

    result = {'table_data': table_data,
              'chart_data': chart_data}
    return json.dumps(result, ensure_ascii=False)
