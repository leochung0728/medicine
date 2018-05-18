import os
import re
import numpy as np
import pandas as pd
from pathlib import Path
from medicine.models.compound import Compound
from mlxtend.preprocessing import TransactionEncoder
from sklearn import cluster
from sklearn.externals import joblib
from medicine import config

File_Dir = config.Path['models_dir']
File_Name = 'kmeans_{}.pkl'


def create_model(transform_df, n_clusters=8):
    model = cluster.KMeans(n_clusters=n_clusters).fit(transform_df)
    return model


def get_data_from_compound():
    id_list = []
    name_list = []
    medicine_list = []
    for compound in Compound.query.all():
        id_list.append(compound.id)
        name_list.append(compound.name)

        medicines = []
        for medicine in compound.medicine:
            medicines.append(medicine.name)
        medicine_list.append(medicines)
    return id_list, name_list, medicine_list


def get_cut_list(datas):
    cut_list = []
    for data in datas:
        data = re.sub('(\s|KT)', '', data)  # 清除 KT 及 空白
        sentences = re.split('\W', data)  # 依據非字元符號split成句子

        word_list = []
        for sentence in sentences:
            word_list.extend([word for word in sentence])  # 1字
            word_list.extend([sentence[i:i + 2] for i in range(len(sentence) - 1)])  # 2字
        cut_list.append(word_list)
    return cut_list


def get_transform_df(cut_list):
    te = TransactionEncoder()
    te_ary = te.fit(cut_list).transform(cut_list)
    return pd.DataFrame(te_ary, columns=te.columns_)


class Cluster(object):
    def __init__(self, n_clusters=8):
        self.compound_df = self.get_compound_df()
        self.fit = None
        self.get_KMeans_fit(n_clusters)

    def get_compound_df(self):
        compound_df = None
        df_file_name = 'compound_df'
        df_file = Path(os.path.join(File_Dir, df_file_name))

        if df_file.is_file():
            compound_df = pd.read_pickle(df_file)
        else:
            compound_ids, compound_names, compound_medicines = get_data_from_compound()
            compound_df = pd.DataFrame(data={'id': compound_ids,
                                             'name': compound_names,
                                             'medicine': compound_medicines})
            compound_df = compound_df.set_index('id')
            compound_df.to_pickle(df_file)
        return compound_df

    def get_KMeans_fit(self, n_clusters=8):
        model_file = Path(os.path.join(File_Dir, File_Name.format(n_clusters)))
        if model_file.is_file():
            self.load_KMeans_model(model_file)
            if self.fit.n_clusters != n_clusters:
                self.fit = None
        if self.fit is None:
            compound_names = self.compound_df['name']
            cut_list = get_cut_list(compound_names)
            transform_df = get_transform_df(cut_list)
            self.fit = create_model(transform_df, n_clusters)
            self.save_KMeans_model(model_file)

    def save_KMeans_model(self, path=os.path.join(File_Dir, File_Name)):
        joblib.dump(self.fit, path)

    def load_KMeans_model(self, path=os.path.join(File_Dir, File_Name)):
        self.fit = joblib.load(path)

    def get_cluster_dict(self):
        cluster_dict = {i: np.where(self.fit.labels_ == i)[0]+1 for i in range(self.fit.n_clusters)}
        return cluster_dict


if __name__ == '__main__':
    c = Cluster()
    print(c.fit)
