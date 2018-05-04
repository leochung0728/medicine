from medicine.flask_app import app
from flask import render_template, request, url_for
import json


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/ajax/apriori', methods=['GET', 'POST'])
def apriori():
    from medicine.analysis.association_rule import Apriori
    apriori = Apriori()

    if request.method == 'POST':
        sup_count = request.form['support']
        conf = request.form['confidence']
        len = request.form['len']
        # print(len(apriori.basket))
        # sup = float(sup_count) / len(list(apriori.basket))
        sup = sup_count
        apriori.generate_rules(min_support=float(sup), min_threshold=float(conf), max_len=int(len))
    else:
        apriori.generate_rules(min_support=0.01, min_threshold=0.7, max_len=2)
    return apriori.rules.to_json(orient='records', force_ascii=False)
