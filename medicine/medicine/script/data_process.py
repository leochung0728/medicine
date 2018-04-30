import os
import re
import pandas as pd
from collections import OrderedDict
from medicine import config
from medicine.flask_app import db
from medicine.models.medicine import Medicine
from medicine.models.alias import Alias
from medicine.models.property import Property
from medicine.models.compound import Compound
from medicine.models.medicine_compound import medicine_compound

File_Dir = config.Path['data_dir']
File_Name = '本草纲目(簡體).txt'


class DataProcess(object):
    def __init__(self, file_dir=File_Dir, file_name=File_Name):
        self.file_dir = file_dir
        self.file_name = file_name

    def read_txt_file(self, file_dir=None, file_name=None):
        content = ''
        if file_dir is None: file_dir = self.file_dir
        if file_name is None: file_name = self.file_name

        with open(os.path.join(file_dir, file_name), 'r', encoding='utf8') as file:
            for line in file:
                content += line
        return content

    def create_datas(self):
        # 本草纲目(簡體).csv [將 本草纲目(簡體).txt 結構化]
        content = self.read_txt_file()
        pattern = re.compile('<目录>(.*?)<篇名>(.*?)内容：(.*?)(?=<目录>|(?<=.$))', re.S)
        m = pattern.findall(content)
        df = pd.DataFrame(columns=['directory', 'title', 'content'])
        for i in range(len(m)):
            # df.loc[i] = [re.sub('\n', '', text) for text in m[i]]
            df.loc[i] = [text for text in m[i]]  # 不取代換行，保持原始狀態以利正則表示法進行
        df.to_csv(os.path.join(config.Path['data_dir'], '本草纲目(簡體).csv'), encoding='utf-8-sig')

        # 本草纲目(簡體)_Ver1.csv [修正 本草纲目(簡體).csv 括號不完整等問題]
        for index, row in df.iterrows():
            if pd.isnull(row['directory']):
                continue
            if re.search(r'\w+[部|目]第\w+卷\\\w{1,2}之\w+', row['directory']):
                row['content'] = re.sub(r'【 【主治】', '【主治】', row['content'])
                row['content'] = re.sub(r'主治 【附方', '主治】 【附方', row['content'])
                row['content'] = re.sub(r'附方 吐血', '附方】 吐血', row['content'])
                row['content'] = re.sub(r'【别名】', '【释名】', row['content'])
                row['content'] = re.sub(r'【主冶】', '【主治】', row['content'])
        df.to_csv(os.path.join(config.Path['data_dir'], '本草纲目(簡體)_Ver1.csv'), encoding='utf-8-sig')

        # 本草纲目(簡體)_Ver2.csv [本草纲目(簡體)_Ver1.csv]
        data = pd.DataFrame(columns=['目錄', '篇名', '釋名', '內容', '部位', '部位內容', '主治', '氣味', '附方'])
        for index, row in df.iterrows():
            if pd.isnull(row['directory']):
                continue
            if not re.search(r'\w+[部|目]第\w+卷\\\w{1,2}之\w+', row['directory']):
                continue
            data_row = dict((k, '') for k in data.columns)
            data_row['目錄'] = row['directory']
            data_row['篇名'] = row['title']
            data_row['內容'] = row['content']
            if re.search(r'【释名】(.*?)(?=【|(?<=.$))', data_row['內容'], re.S):
                data_row['釋名'] = re.search(r'【释名】(.*?)(?=【|(?<=.$))', data_row['內容'], re.S).group(1)
            sites = re.findall(r'(\\x.+?\\x.*?)(?=\\x|<目录>|(?<=.$))', data_row['內容'], re.S)
            sites = sites if sites else [data_row['內容']]
            for s_content in sites:
                data_row['部位內容'] = s_content
                if re.search(r'\\x(.+?)\\x', s_content, re.S):
                    data_row['部位'] = re.search(r'\\x(.+?)\\x', s_content, re.S).group(1)
                if re.search(r'【主治】(.*?)(?=【|(?<=.$))', s_content, re.S):
                    data_row['主治'] = re.search(r'【主治】(.*?)(?=【|(?<=.$))', s_content, re.S).group(1)
                if re.search(r'【气味】(.*?)(?=【|(?<=.$))', s_content, re.S):
                    data_row['氣味'] = re.search(r'【气味】(.*?)(?=【|(?<=.$))', s_content, re.S).group(1)
                if re.search(r'【附方】(.*?)(?=【|(?<=.$))', s_content, re.S):
                    data_row['附方'] = re.search(r'【附方】(.*?)(?=【|(?<=.$))', s_content, re.S).group(1)
                data = data.append(data_row, ignore_index=True)
        data.to_csv(os.path.join(config.Path['data_dir'], '本草纲目(簡體)_Ver2.csv'), encoding='utf-8-sig')

        # 本草纲目(簡體)_Ver3.csv [結構化 附方 與 附方內容]
        # Make compound's name
        compounds = data.loc[:, '附方']
        # pattern = r'[。）》]{1,3}( ?\w{0,3} ?\n? ?\w{0,8}?[ ，、]{0,2}\w{1,11})∶'
        # pattern = r'[。）》]{1,3}( ?\w{0,3} ?\n? ?\w{0,8}?[ ，、]{0,2}\w{1,11})∶'
        # pattern = r'[。）》]{1,3}((?: ?\w{1,20}[，、]?\n?)?\
        # (?:(?:\w+[，、]?){0,2}\n?){0,3}\w{1,11})∶'
        # pattern = r'[。）》]{1,3}((?: ?\w{1,20}[ ，、]?\n?)?\
        # (?:(?:\w+[，、]){0,2} ?\n?){0,3}\w{1,11})∶'
        pattern = r'[。）》]((?: ?\w{0,10}[ ，、]?\n?){0,1}' \
                  r'(?: ?\w{0,2}[，、] \n){0,2}' \
                  r'(?:(?:\w+[，、]){1,3} ?\n?){0,3}\w{1,11})∶'

        name_list = []
        for compound in compounds:
            if pd.isnull(compound):
                continue
            finds = re.findall(pattern, compound)
            if len(finds) > 0:
                finds = [re.sub(r'\s', '', find) for find in finds]
                name_list.extend(finds)

        d_len, u_len = 2, 35  # 控制附方名稱長度
        name_list = [name for name in name_list if d_len <= len(name) <= u_len]

        compound_df = pd.DataFrame(columns=['title', 'compound', 'content', 'content_c'])
        compound_join = '|'.join(name_list)
        pattern = '(' + compound_join + ')∶' + '(.*?)' + '(?=(?=(?:' + compound_join + ')∶)|(?<=.$))'

        previous_title = None
        for index, row in data.iterrows():
            title = row['篇名']
            compound = row['附方']
            if title == previous_title or pd.isnull(compound):
                continue
            else:
                previous_title = title
            finds = re.findall(pattern, re.sub('\s', '', compound))
            if len(finds) == 0:
                continue
            for find in finds:
                df_row = dict((k, '') for k in compound_df.columns)
                df_row['title'] = title
                df_row['compound'] = find[0]
                df_row['content'] = find[1]
                df_row['content_c'] = compound
                compound_df = compound_df.append(df_row, ignore_index=True)
        file_path = os.path.join(config.Path['data_dir'], '本草纲目(簡體)_Ver3.csv')
        compound_df.to_csv(file_path, encoding='utf-8-sig')

        # 本草纲目(簡體)_Ver4.csv [結構化 附方 與 附方內容]
        from medicine.models.medicine import Medicine
        from medicine.models.alias import Alias

        medicine_all = Medicine.query.all()
        alias_all = Alias.query.all()

        medicine_names = set([medicine.name for medicine in medicine_all if len(medicine.name) > 1])
        alias_names = set([alias.name for alias in alias_all if len(alias.name) > 1])
        join_mName = '|'.join(medicine_names)
        join_aName = '|'.join(alias_names)

        df = pd.DataFrame(columns=['title', 'compound', 'content_c', 'content', 'medicines'])
        for index, row in compound_df.iterrows():
            if pd.isnull(row['content']):
                continue
            content = re.sub('\s', '', row['content'])
            # Match（夏子益《奇疾方》）、（《千金方》）、（陈巽方）... and Clean
            match = re.search('（\w{0,3}《?\w{2,8}》?）|《\w{2,8}》', content)
            if match:
                content = re.sub('（\w{0,3}《?\w{2,8}》?）|《\w{2,8}》', '', row['content'])

            mFinds = re.findall('(' + join_mName + ')', content)
            aFinds = re.findall('(' + join_aName + ')', content)
            finds = list()
            medicine = Medicine.get(name=re.sub('\s', '', row['title']))
            finds.append(medicine.name)
            finds.extend(mFinds)
            for aFind in aFinds:
                alias = Alias.get(name=aFind)
                medicine = Medicine.query.get(alias.medicine_id)
                # finds.append(medicine.name)
            # print(set(finds))
            df_row = dict((k, '') for k in df.columns)
            df_row['title'] = re.sub('\s', '', row['title'])
            df_row['compound'] = row['compound']
            df_row['content_c'] = re.sub('\s', '', row['content_c'])
            df_row['content'] = row['content']
            df_row['medicines'] = '、'.join(set(finds))
            df = df.append(df_row, ignore_index=True)
        file_path = os.path.join(config.Path['data_dir'], '本草纲目(簡體)_Ver4.csv')
        df.to_csv(file_path, encoding='utf-8-sig')

    def process_data(self):
        self.process_data_by_medicine_and_alias()
        self.process_data_by_property()
        self.process_data_by_compound()

    @staticmethod
    def process_data_by_medicine_and_alias():
        file_path = os.path.join(config.Path['data_dir'], '本草纲目(簡體)_Ver2.csv')
        data_df = pd.read_csv(file_path, index_col=[0], engine='python', encoding='utf-8-sig')

        for index, row in data_df.iterrows():
            if pd.isnull(row['目錄']):
                continue

            if not re.search(r'\w+[部|目]第\w+卷\\\w{1,2}之\w+', row['目錄']):
                continue

            medicine = Medicine.get(re.sub('\s', '', row['篇名']))
            if re.match(r'(.*)[部|目]', row['目錄']):
                medicine.radical = re.match(r'(.*)[部|目]', row['目錄']).group(1)
            db.session.add(medicine)
            db.session.commit()

            alias_content = ''
            if re.search(r'【释名】(.*?)(?=【|(?<=.$))', row['內容'], re.S):
                alias_content = re.search(r'【释名】(.*?)(?=【|(?<=.$))', row['內容'], re.S).group(1)

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
                    if alias is None:
                        alias = Alias(name=ele, medicine_id=medicine.id)
                    # alias.medicine = medicine
                    db.session.add(alias)
            db.session.commit()

    @staticmethod
    def process_data_by_property():
        file_path = os.path.join(config.Path['data_dir'], '本草纲目(簡體)_Ver2.csv')
        data = pd.read_csv(file_path, index_col=[0], engine='python', encoding='utf-8-sig')
        pattern = '.*?[。；]|.*'
        property_keys = ['cold', 'cool', 'warm', 'hot',
                         'neutral', 'sour', 'sweet', 'bitter',
                         'salty', 'pungent', 'poison']
        medicine_dict = OrderedDict()
        medicine_temp = None
        for index, row in data.iterrows():
            property_dict = dict.fromkeys(property_keys, 0)
            title = re.sub('\s', '', row['篇名'])
            position = re.sub('\s', '', row['部位']) if not pd.isnull(row['部位']) else ''
            content = re.sub('\s', '', row['氣味']) if not pd.isnull(row['氣味']) else ''

            m = Medicine.query.filter_by(name=title).first()

            if medicine_temp != m.name:
                medicine_temp = m.name
                medicine_dict = OrderedDict()

            match = re.match(pattern, content)
            if match:
                content = match.group()

            if re.search('同', content):
                something = ''
                if re.search('(?:同([^。]))|(?:(.)同)', content):
                    for search in re.search('(?:同([^。]))|(?:(.)同)', content).groups():
                        if search is not None:
                            something = search
                            break

                if something == '' and len(medicine_dict) > 0:
                    first_key = list(medicine_dict.items())[0][0]
                    medicine_dict[position] = medicine_dict[first_key]

                elif len(medicine_dict) > 0:
                    match_success = False
                    for item in medicine_dict.keys():
                        if re.search(something, item):
                            match_success = True
                            property_dict = medicine_dict[item]
                            break
                    if not match_success:
                        property_dict = list(medicine_dict.items())[len(medicine_dict) - 1][1]

            if re.search('热', content):
                text = re.search('(大热)|(熟热)|(热)|(微热)', content).group()
                if text == '大热':
                    property_dict['hot'] = 3
                elif text == '熟热' or text == '热':
                    property_dict['hot'] = 2
                elif text == '微热':
                    property_dict['hot'] = 1

            if re.search('温', content):
                text = re.search('(大温)|(温)|(小温)|(微温)', content).group()
                if text == '大温':
                    property_dict['warm'] = 3
                elif text == '温':
                    property_dict['warm'] = 2
                elif text == '小温' or text == '微温':
                    property_dict['warm'] = 1

            if re.search('冷|凉', content):
                text = re.search('(冷利)|(至冷)|(冷)|(小冷)|(凉)', content).group()
                if text == '冷利' or text == '至冷':
                    property_dict['cool'] = 3
                elif text == '冷' or text == '凉':
                    property_dict['cool'] = 2
                elif text == '小冷':
                    property_dict['cool'] = 1

            if re.search('寒', content):
                text = re.search('(大寒)|(寒)|(小寒)|(微寒)', content).group()
                if text == '大寒':
                    property_dict['cold'] = 3
                elif text == '寒':
                    property_dict['cold'] = 2
                elif text == '小寒' or text == '微寒':
                    property_dict['cold'] = 1

            if re.search('平', content):
                property_dict['neutral'] = 2

            if re.search('酸', content):
                text = re.search('(并酸)|(酸)|(微酸)', content).group()
                if text == '并酸':
                    property_dict['sour'] = 3
                elif text == '酸':
                    property_dict['sour'] = 2
                elif text == '微酸':
                    property_dict['sour'] = 1

            if re.search('甘', content):
                text = re.search('(并甘)|(甘)|(微甘)', content).group()
                if text == '并甘':
                    property_dict['sweet'] = 3
                elif text == '甘':
                    property_dict['sweet'] = 3
                elif text == '微甘':
                    property_dict['sweet'] = 3

            if re.search('苦', content):
                text = re.search('(苦)|(微苦)|(小苦)', content).group()
                if text == '苦':
                    property_dict['bitter'] = 2
                elif text == '微苦' or text == '小苦':
                    property_dict['bitter'] = 1

            if re.search('咸', content):
                text = re.search('(咸)|(微咸)', content).group()
                if text == '咸':
                    property_dict['salty'] = 2
                elif text == '微咸':
                    property_dict['salty'] = 1

            if re.search('辛', content):
                text = re.search('(辛美)|(辛)|(微辛)', content).group()
                if text == '辛美' or text == '辛':
                    property_dict['pungent'] = 2
                elif text == '微辛':
                    property_dict['pungent'] = 1

            if re.search('毒', content):
                text = re.search('(大毒)|(大有毒)|(有毒)|(微毒)|(小毒)|(无毒)', content).group()
                if text == '大毒' or text == '大有毒':
                    property_dict['poison'] = 3
                elif text == '有毒':
                    property_dict['poison'] = 2
                elif text == '微毒' or text == '小毒':
                    property_dict['poison'] = 1

            medicine_dict[position] = property_dict
            property = Property.get(position, medicine_id=m.id)
            if property is None:
                property = Property(position=position, medicine_id=m.id, **property_dict)
            db.session.add(property)
            db.session.commit()

    @staticmethod
    def process_data_by_compound():
        file_path = os.path.join(config.Path['data_dir'], '本草纲目(簡體)_Ver3.csv')
        data = pd.read_csv(file_path, index_col=[0], engine='python', encoding='utf-8-sig')

        medicine_all = Medicine.query.all()
        alias_all = Alias.query.all()

        medicine_names = set([medicine.name for medicine in medicine_all if len(medicine.name) > 1])
        alias_names = set([alias.name for alias in alias_all if len(alias.name) > 1])
        join_mName = '|'.join(medicine_names)
        join_aName = '|'.join(alias_names)
        last_compound = None
        medicine_temp = None
        for index, row in data.iterrows():
            if pd.isnull(row['content']):
                continue
            if medicine_temp != row['title']:
                medicine_temp = row['title']
                last_compound = None
            content = re.sub('\s', '', row['content'])
            # Match（夏子益《奇疾方》）、（《千金方》）、（陈巽方）... and Clean
            match = re.search('（\w{0,3}《?\w{2,8}》?）|《\w{2,8}》', content)
            if match:
                content = re.sub('（\w{0,3}《?\w{2,8}》?）|《\w{2,8}》', '', content)
            mFinds = re.findall('(' + join_mName + ')', content)
            aFinds = re.findall('(' + join_aName + ')', content)
            find_medicines = list()
            medicine = Medicine.get(name=re.sub('\s', '', row['title']))
            find_medicines.append(medicine)
            find_medicines.extend([Medicine.get(name=m) for m in mFinds])
            for aFind in aFinds:
                alias = Alias.get(name=aFind)
                medicine = Medicine.query.get(alias.medicine_id)
                find_medicines.append(medicine)
            if re.search('(又法)|(又一法)|(又方)|(又散)|(一法)|(一方)', row['compound']):
                if last_compound is not None:
                    row['compound'] = last_compound
            else:
                last_compound = row['compound']

            compound = Compound(name=row['compound'], description=row['content'])
            compound.medicine.extend(set(find_medicines))
            db.session.add(compound)
        db.session.commit()


if __name__ == '__main__':
    dp = DataProcess()
    # dp.create_datas()  # 將資料進行結構化 (僅第一次需要執行)
    dp.process_data()

    ######## [ 測試 ] ########
    # step 1 (本草纲目(簡體)_Ver1.csv)
    # import re
    # import pandas as pd
    #
    # dc = DataProcess()
    # dc.read_file()
    # pattern = re.compile('<目录>(.*?)<篇名>(.*?)内容：(.*?)(?=<目录>|(?<=.$))', re.S)
    # m = pattern.findall(dc.content)
    # df = pd.DataFrame(columns=['directory', 'title', 'content'])
    # for i in range(len(m)):
    #     # df.loc[i] = [re.sub('\n', '', text) for text in m[i]]
    #     df.loc[i] = [text for text in m[i]]
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

    # step 4 (本草纲目(簡體)_Ver2.csv)
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

    # step 5 (別名)
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

    # step 6 (本草纲目(簡體)_Ver3.csv)
    # import re
    # import pandas as pd
    #
    # file_path = os.path.join(config.Path['data_dir'], '本草纲目(簡體)_Ver2.csv')
    # data = pd.read_csv(file_path, index_col=[0], engine='python', encoding='utf-8-sig')
    #
    # # Make compound's name
    # compounds = data.loc[:, '附方']
    # # pattern = r'[。）》]{1,3}( ?\w{0,3} ?\n? ?\w{0,8}?[ ，、]{0,2}\w{1,11})∶'
    # # pattern = r'[。）》]{1,3}( ?\w{0,3} ?\n? ?\w{0,8}?[ ，、]{0,2}\w{1,11})∶'
    # # pattern = r'[。）》]{1,3}((?: ?\w{1,20}[，、]?\n?)?\
    # # (?:(?:\w+[，、]?){0,2}\n?){0,3}\w{1,11})∶'
    # # pattern = r'[。）》]{1,3}((?: ?\w{1,20}[ ，、]?\n?)?\
    # # (?:(?:\w+[，、]){0,2} ?\n?){0,3}\w{1,11})∶'
    # pattern = r'[。）》]((?: ?\w{0,10}[ ，、]?\n?){0,1}' \
    #           r'(?: ?\w{0,2}[，、] \n){0,2}' \
    #           r'(?:(?:\w+[，、]){1,3} ?\n?){0,3}\w{1,11})∶'
    #
    # name_list = []
    # for compound in compounds:
    #     if pd.isnull(compound):
    #         continue
    #     finds = re.findall(pattern, compound)
    #     if len(finds) > 0:
    #         finds = [re.sub(r'\s', '', find) for find in finds]
    #         name_list.extend(finds)
    #
    # d_len, u_len = 2, 35
    # name_list = [name for name in name_list if d_len <= len(name) <= u_len]
    #
    # compound_df = pd.DataFrame(columns=['title', 'compound', 'content', 'content_c'])
    # compound_join = '|'.join(name_list)
    # pattern = '(' + compound_join + ')∶' + '(.*?)' + '(?=(?=(?:' + compound_join + ')∶)|(?<=.$))'
    #
    # previous_title = None
    # for index, row in data.iterrows():
    #     title = row['篇名']
    #     compound = row['附方']
    #     if title == previous_title or pd.isnull(compound):
    #         continue
    #     else:
    #         previous_title = title
    #     finds = re.findall(pattern, re.sub('\s', '', compound))
    #     if len(finds) == 0:
    #         continue
    #     for find in finds:
    #         df_row = dict((k, '') for k in compound_df.columns)
    #         df_row['title'] = title
    #         df_row['compound'] = find[0]
    #         df_row['content'] = find[1]
    #         df_row['content_c'] = compound
    #         compound_df = compound_df.append(df_row, ignore_index=True)
    # file_path = os.path.join(config.Path['data_dir'], '本草纲目(簡體)_Ver3.csv')
    # compound_df.to_csv(file_path, encoding='utf-8-sig')

    # step 7 (附方)
    # import re
    # import pandas as pd
    # from medicine.models.medicine import Medicine
    # from medicine.models.alias import Alias
    #
    # medicine_all = Medicine.query.all()
    # alias_all = Alias.query.all()
    #
    # medicine_names = set([medicine.name for medicine in medicine_all if len(medicine.name) > 1])
    # alias_names = set([alias.name for alias in alias_all if len(alias.name) > 1])
    # join_mName = '|'.join(medicine_names)
    # join_aName = '|'.join(alias_names)
    #
    # file_path = os.path.join(config.Path['data_dir'], '本草纲目(簡體)_Ver3.csv')
    # compound_df = pd.read_csv(file_path, index_col=[0], engine='python', encoding='utf-8-sig')
    # new_df = pd.DataFrame(columns=['title', 'compound', 'content_c', 'content', 'medicines'])
    # for index, row in compound_df.iterrows():
    #     if pd.isnull(row['content']):
    #         continue
    #     content = re.sub('\s', '', row['content'])
    #     # Match（夏子益《奇疾方》）、（《千金方》）、（陈巽方）... and Clean
    #     match = re.search('（\w{0,3}《?\w{2,8}》?）|《\w{2,8}》', content)
    #     if match:
    #         content = re.sub('（\w{0,3}《?\w{2,8}》?）|《\w{2,8}》', '', row['content'])
    #
    #     mFinds = re.findall('(' + join_mName + ')', content)
    #     aFinds = re.findall('(' + join_aName + ')', content)
    #     finds = list()
    #     medicine = Medicine.get(name=re.sub('\s', '', row['title']))
    #     finds.append(medicine.name)
    #     finds.extend(mFinds)
    #     for aFind in aFinds:
    #         alias = Alias.get(name=aFind)
    #         medicine = Medicine.query.get(alias.medicine_id)
    #         # finds.append(medicine.name)
    #     # print(set(finds))
    #     df_row = dict((k, '') for k in new_df.columns)
    #     df_row['title'] = re.sub('\s', '', row['title'])
    #     df_row['compound'] = row['compound']
    #     df_row['content_c'] = row['content_c']
    #     df_row['content'] = row['content']
    #     df_row['medicines'] = '、'.join(set(finds))
    #     new_df = new_df.append(df_row, ignore_index=True)
    # file_path = os.path.join(config.Path['data_dir'], '本草纲目(簡體)_Ver4.csv')
    # new_df.to_csv(file_path, encoding='utf-8-sig')
