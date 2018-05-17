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


class Cluster(object):

    def __init__(self, n_clusters=8):
        self.compounds = Compound.query.all()
        self.compound_names = [c.name for c in self.compounds]
        self.compound_medicines = self.get_compound_medicines()
        self.cut_list = self.get_cut_list_by_name()
        self.df_name_medicine = pd.DataFrame({'medicines': self.compound_medicines,
                                              'name_cut': self.cut_list},
                                             index=self.compound_names)
        self.transform_df = self.get_transform_df()
        self.dict_id_name = dict(zip(self.transform_df.index, self.compound_names))
        self.fit = self.get_KMeans_fit(n_clusters)

    def get_compound_medicines(self):
        compound_list = []
        for compound in self.compounds:
            medicine_list = [medicine.name for medicine in compound.medicine]
            compound_list.append(medicine_list)
        return compound_list

    def get_cut_list_by_name(self):
        cut_list = []
        for name in self.compound_names:
            name = re.sub('(\s|KT)', '', name)  # 清除 KT 及 空白
            sentences = re.split('\W', name)  # 依據非字元符號split成句子

            word_list = []
            for sentence in sentences:
                word_list.extend([word for word in sentence])  # 1字
                word_list.extend([sentence[i:i + 2] for i in range(len(sentence) - 1)])  # 2字
            cut_list.append(word_list)
        return cut_list

    def get_transform_df(self):
        te = TransactionEncoder()
        te_ary = te.fit(self.cut_list).transform(self.cut_list)
        return pd.DataFrame(te_ary, columns=te.columns_)

    def get_KMeans_fit(self, n_clusters=8):
        model = None
        model_file = Path(os.path.join(File_Dir, File_Name.format(n_clusters)))
        if model_file.is_file():
            model = self.load_KMeans_model(model_file)
            if model.n_clusters != n_clusters:
                model = None
        if model is None:
            model = self.KMeansCluster(n_clusters)
            self.save_KMeans_model(model, model_file)
        return model

    def KMeansCluster(self, n_clusters=8):
        KMeans = cluster.KMeans(n_clusters=n_clusters)
        return KMeans.fit(self.transform_df)

    def save_KMeans_model(self, model=None, path=os.path.join(File_Dir, File_Name)):
        if model is None:
            model = self.fit
        joblib.dump(model, path)

    def load_KMeans_model(self, path=os.path.join(File_Dir, File_Name)):
        return joblib.load(path)

    def get_cluster_dict(self):
        cluster_dict = {i: np.where(self.fit.labels_ == i)[0] for i in range(self.fit.n_clusters)}
        return cluster_dict


if __name__ == '__main__':
    c = Cluster()
