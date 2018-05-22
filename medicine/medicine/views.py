from medicine.flask_app import app
from flask import render_template, request, url_for


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


@app.route('/analysis/kmeans', methods=['GET', 'POST'])
def kmeans():
    return render_template('kmeans.html')


@app.route('/analysis/kmeans/ajax', methods=['GET', 'POST'])
def kmeans_ajax():
    import json
    from collections import Counter
    from medicine.analysis.cluster import Cluster

    k_group = int(request.form.get('k', 8))
    g_group = int(request.form.get('g', 0))

    c = Cluster(k_group)
    compound_df = c.compound_df
    compound_df = compound_df[['name', 'medicine']]
    cluster_dict = c.get_cluster_dict()

    group_df = compound_df.loc[cluster_dict[g_group], ]
    group_df['group'] = g_group
    table_data = group_df.to_json(orient='values', force_ascii=False)

    objs = []
    for ms in group_df['medicine']:
        objs.extend(ms)
    chart_data = sorted(list(Counter(objs).items()), key=lambda tup: tup[1], reverse=True)

    result = {'table_data': table_data,
              'chart_data': chart_data}
    return json.dumps(result, ensure_ascii=False)


@app.route('/analysis/lda', methods=['GET', 'POST'])
def lda():
    return render_template('lda.html')


@app.route('/analysis/lda/ajax', methods=['GET', 'POST'])
def lda_ajax():
    import json
    from collections import Counter
    from medicine.analysis.cluster1 import Cluster

    k_group = int(request.form.get('k', 8))
    g_group = int(request.form.get('g', 0))

    c = Cluster(k_group)
    compound_df = c.compound_df
    compound_df = compound_df[['name', 'medicine']]
    cluster_dict = c.get_cluster_dict()

    group_df = compound_df.loc[cluster_dict[g_group], ]
    group_df['group'] = g_group
    table_data = group_df.to_json(orient='values', force_ascii=False)

    objs = []
    for ms in group_df['medicine']:
        objs.extend(ms)
    chart_data = sorted(list(Counter(objs).items()), key=lambda tup: tup[1], reverse=True)

    topics = [c.transform_df.columns[index] for index in c.fit.components_[g_group].argsort()[: -10-1: -1]]

    result = {'table_data': table_data,
              'chart_data': chart_data,
              'topic_data': topics}
    return json.dumps(result, ensure_ascii=False)
