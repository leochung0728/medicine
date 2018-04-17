import os
from medicine import db
from medicine.models.medicine import Medicine
from medicine.models.alias import Alias
from medicine import config

File_Dir = config.Path['data_dir']
File_Name = '本草纲目(簡體).txt'


class DataProcess(object):
    def __init__(self, file_dir=File_Dir, file_name=File_Name):
        self.file_dir = file_dir
        self.file_name = file_name
        self.content = ''

    def read_file(self):
        self.content = ''
        with open(os.path.join(self.file_dir, self.file_name), 'r', encoding='utf8') as file:
            for line in file:
                self.content += line

    def process_data(self):
        import re
        import pandas as pd

        pattern = re.compile('<目录>(.*?)<篇名>(.*?)内容：(.*?)(?=<目录>|(?<=.$))', re.S)
        results = pattern.findall(self.content)
        data_df = pd.DataFrame(columns=['directory', 'title', 'content'])
        for index in range(len(results)):
            data_df.loc[index] = [re.sub('\n', '', text) for text in results[index]]

        for index, row in data_df.iterrows():
            if pd.isnull(row['directory']):
                continue

            if re.search(r'\w+[部|目]第\w+卷\\\w{1,2}之\w+', row['directory']):
                row['content']= re.sub(r'【 【主治】', '【主治】', row['content'])
                row['content'] = re.sub(r'主治 【附方', '主治】 【附方', row['content'])
                row['content'] = re.sub(r'附方 吐血', '附方】 吐血', row['content'])
                row['content'] = re.sub(r'【别名】', '【释名】', row['content'])
                row['content'] = re.sub(r'【主冶】', '【主治】', row['content'])

        for index, row in data_df.iterrows():
            if pd.isnull(row['directory']):
                continue

            if not re.search(r'\w+[部|目]第\w+卷\\\w{1,2}之\w+', row['directory']):
                continue

            medicine = Medicine.get(row['title'])
            if re.match(r'(.*)[部|目]', row['directory']):
                medicine.radical = re.match(r'(.*)[部|目]', row['directory']).group(1)
            db.session.add(medicine)
            db.session.commit()

            alias_content = ''
            if re.search(r'【释名】(.*?)(?=【|(?<=.$))', row['content'], re.S):
                alias_content = re.search(r'【释名】(.*?)(?=【|(?<=.$))', row['content'], re.S).group(1)

            # 別名沒有內容，跳過
            if pd.isnull(alias_content):
                continue

            if re.match(r'(.*?。)', alias_content):
                alias_content = re.match(r'(.*?。)', alias_content).group(1)

            # 開頭為「某某曰」，例如 {' 曰', '宁源曰', '弘景曰', '恭曰', '时珍曰', '藏器曰', '赤黍曰', '颂曰'}
            if re.match(r'^([^\W]{1,4}曰|[^\w]{1,3}曰).*', alias_content):
                continue

            # 某某曰前沒有「。」，例如 {'、 宗 曰', '、 弘景曰', '、颠勒 禹锡曰'}
            match = re.search(r'、\w{0,3}[\s]([^。]{1,3}[\s]?曰).*', alias_content)
            if match:
                alias_content = re.sub(match.group(1), '。' + match.group(1), alias_content)
                if re.match(r'(.*?。)', alias_content):
                    alias_content = re.match(r'(.*?。)', alias_content).group(1)

            eles = None
            match = re.match(r'(?:([^，∶；]*?)[。、])', alias_content)
            if match:
                eles = re.findall(r'([^∶，；（《》）]*?)(?:[（《].*?[》）]?)?[、。]', alias_content, re.S)
                eles = [e.replace(' ', '') for e in eles if not e.strip() == '']

            if eles:
                for ele in eles:
                    alias = Alias.get(ele, medicine.id)
                    # alias.medicine = medicine
                    db.session.add(alias)
            db.session.commit()


if __name__ == '__main__':
    dp = DataProcess()
    dp.read_file()
    dp.process_data()

    # me = Medicine.query.filter_by(id=4).first()
    # print(me.alias)

    # step 1
    # import re
    # import pandas as pd
    #
    # dc = DataProcess()
    # dc.read_file()
    # pattern = re.compile('<目录>(.*?)<篇名>(.*?)内容：(.*?)(?=<目录>|(?<=.$))', re.S)
    # m = pattern.findall(dc.content)
    # df = pd.DataFrame(columns=['directory', 'title', 'content'])
    # for i in range(len(m)):
    #     df.loc[i] = [re.sub('\n', '', text) for text in m[i]]
    # df.to_csv(os.path.join(config.Path['data_dir'], '本草纲目(簡體).csv'), encoding='utf-8-sig')

    # step 2
    # import re
    # import pandas as pd
    # from collections import Counter
    #
    # file_path = os.path.join(config.Path['data_dir'], '本草纲目(簡體).csv')
    # data = pd.read_csv(file_path, index_col=[0], engine='python', encoding='utf-8-sig')
    # A, B = list(), list()
    # for index, row in data.iterrows():
    #     if pd.isnull(row['directory']):
    #         continue
    #     if re.search(r'主治第', row['directory']):
    #         l = re.findall(r'【(.*?)】', row['content'])
    #         A.extend(l)
    #     elif re.search(r'\w+[部|目]第\w+卷\\\w{1,2}之\w+', row['directory']):
    #         l = re.findall(r'【(.*?)】', row['content'])
    #         B.extend(l)
    # print(set(B))
    # print(Counter(A))
    # print(Counter(B))

    # step 3
    # import re
    # import pandas as pd
    # from collections import Counter
    #
    # file_path = os.path.join(config.Path['data_dir'], '本草纲目(簡體).csv')
    # data = pd.read_csv(file_path, index_col=[0], engine='python', encoding='utf-8-sig')
    # A, B = list(), list()
    # for index, row in data.iterrows():
    #     if pd.isnull(row['directory']):
    #         continue
    #     if re.search(r'\w+[部|目]第\w+卷\\\w{1,2}之\w+', row['directory']):
    #         row['content']= re.sub(r'【 【主治】', '【主治】', row['content'])
    #         row['content'] = re.sub(r'主治 【附方', '主治】 【附方', row['content'])
    #         row['content'] = re.sub(r'附方 吐血', '附方】 吐血', row['content'])
    #         row['content'] = re.sub(r'【别名】', '【释名】', row['content'])
    #         row['content'] = re.sub(r'【主冶】', '【主治】', row['content'])
    #         l = re.findall(r'【(.*?)】', row['content'])
    #         B.extend(l)
    # print(set(B))
    # print(Counter(B))
    # data.to_csv(os.path.join(config.Path['data_dir'], '本草纲目(簡體)_Ver1.csv'), encoding='utf-8-sig')

    # step 4
    # import re
    # import pandas as pd
    #
    # file_path = os.path.join(config.Path['data_dir'], '本草纲目(簡體)_Ver1.csv')
    # data = pd.read_csv(file_path, index_col=[0], engine='python', encoding='utf-8-sig')
    # df = pd.DataFrame(columns=['目錄', '篇名', '釋名', '內容', '部位', '部位內容', '主治', '氣味', '附方'])
    # for index, row in data.iterrows():
    #     if pd.isnull(row['directory']):
    #         continue
    #     if not re.search(r'\w+[部|目]第\w+卷\\\w{1,2}之\w+', row['directory']):
    #         continue
    #     df_row = dict((k, '') for k in df.columns)
    #     df_row['目錄'] = row['directory']
    #     df_row['篇名'] = row['title']
    #     df_row['內容'] = row['content']
    #     if re.search(r'【释名】(.*?)(?=【|(?<=.$))', df_row['內容'], re.S):
    #         df_row['釋名'] = re.search(r'【释名】(.*?)(?=【|(?<=.$))', df_row['內容'], re.S).group(1)
    #     sites = re.findall(r'(\\x.+?\\x.*?)(?=\\x|<目录>|(?<=.$))', df_row['內容'], re.S)
    #     sites = sites if sites else [df_row['內容']]
    #     for s_content in sites:
    #         df_row['部位內容'] = s_content
    #         if re.search(r'\\x(.+?)\\x', s_content, re.S):
    #             df_row['部位'] = re.search(r'\\x(.+?)\\x', s_content, re.S).group(1)
    #         if re.search(r'【主治】(.*?)(?=【|(?<=.$))', s_content, re.S):
    #             df_row['主治'] = re.search(r'【主治】(.*?)(?=【|(?<=.$))', s_content, re.S).group(1)
    #         if re.search(r'【气味】(.*?)(?=【|(?<=.$))', s_content, re.S):
    #             df_row['氣味'] = re.search(r'【气味】(.*?)(?=【|(?<=.$))', s_content, re.S).group(1)
    #         if re.search(r'【附方】(.*?)(?=【|(?<=.$))', s_content, re.S):
    #             df_row['附方'] = re.search(r'【附方】(.*?)(?=【|(?<=.$))', s_content, re.S).group(1)
    #         df = df.append(df_row, ignore_index=True)
    # df.to_csv(os.path.join(config.Path['data_dir'], '本草纲目(簡體)_Ver2.csv'), encoding='utf-8-sig')

    # step 5
    # import re
    # import pandas as pd
    #
    # file_path = os.path.join(config.Path['data_dir'], '本草纲目(簡體)_Ver2.csv')
    # data = pd.read_csv(file_path, index_col=[0], engine='python', encoding='utf-8-sig')
    # alias_list = list()
    # for content in data.iloc[:, 2]:
    #     if pd.isnull(content):
    #         continue
    #
    #     alias_content = ''
    #     if re.match(r'(.*?。)', content):
    #         alias_content = re.match(r'(.*?。)', content).group(1)
    #
    #     # 開頭為「某某曰」，例如 {' 曰', '宁源曰', '弘景曰', '恭曰', '时珍曰', '藏器曰', '赤黍曰', '颂曰'}
    #     if re.match(r'^([^\W]{1,4}曰|[^\w]{1,3}曰).*', alias_content):
    #         continue
    #
    #     # 某某曰前沒有「。」，例如 {'、 宗 曰', '、 弘景曰', '、颠勒 禹锡曰'}
    #     match = re.search(r'、\w{0,3}[\s]([^。]{1,3}[\s]?曰).*', alias_content)
    #     if match:
    #         alias_content = re.sub(match.group(1), '。' + match.group(1), alias_content)
    #         if re.match(r'(.*?。)', alias_content):
    #             alias_content = re.match(r'(.*?。)', alias_content).group(1)
    #
    #     match = re.match(r'(?:([^，∶；]*?)[。、])', alias_content)
    #     if match:
    #         eles = re.findall(r'([^∶，；（《》）]*?)(?:[（《].*?[》）]?)?[、。]', alias_content, re.S)
    #         eles = [e.replace(' ', '') for e in eles if not e.strip() == '']
    #         alias_list.extend(eles)
    # # print(len(set(alias_list)))
    # # print(set(alias_list))
