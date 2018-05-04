import pandas as pd
from medicine.models.compound import Compound


class Apriori(object):
    freq_items = None
    rules = None

    def __init__(self):
        self.basket = self.get_basket()
        self.binaryMatrix = self.transfer_to_matrix()

    def get_basket(self):
        compound_list = []
        for compound in Compound.query.all():
            medicine_list = [medicine.name for medicine in compound.medicine]
            compound_list.append(medicine_list)
        return compound_list

    def transfer_to_matrix(self):
        from mlxtend.preprocessing import TransactionEncoder
        te = TransactionEncoder()
        return pd.DataFrame(te.fit(self.basket).transform(self.basket),
                            columns=te.columns_)

    def generate_freq_items(self, min_support=0.01, use_colnames=True, max_len=2):
        from mlxtend.frequent_patterns import apriori
        self.freq_items = apriori(self.binaryMatrix,
                                  min_support=min_support,
                                  max_len=max_len,
                                  use_colnames=use_colnames)

    def generate_rules(self, min_support=0.01, use_colnames=True, max_len=2,
                       metric='confidence', min_threshold=0.7):
        from mlxtend.frequent_patterns import association_rules
        if self.freq_items is None:
            self.generate_freq_items(min_support, use_colnames, max_len)
        self.rules = association_rules(self.freq_items, metric, min_threshold)


if __name__ == '__main__':
    apriori = Apriori()
    print(len(apriori.basket))
    # apriori.generate_rules()
    # print(apriori.rules.to_json(lines=True, orient='records'))
