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
File_Name = '本草綱目.txt'


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
        # 本草綱目.csv [將 本草綱目.txt 結構化]
        content = self.read_txt_file()
        pattern = re.compile(r'    \n(?:(^\S.*)(?:\n    \n))?(^\S.*)\n((?:    .*\n?)+)(?=    \n?)', re.M)
        finds = pattern.findall(content)
        df = pd.DataFrame(columns=['目錄', '標題', '內文'])
        for find in finds:
            df_row = dict((key, '') for key in df.columns)
            df_row['目錄'] = '\n'.join([t.strip() for t in find[0].strip().split('\n')])
            df_row['標題'] = '\n'.join([t.strip() for t in find[1].strip().split('\n')])
            df_row['內文'] = '\n'.join([t.strip() for t in find[2].strip().split('\n')])
            df = df.append(df_row, ignore_index=True)
        df.to_csv(os.path.join(config.Path['data_dir'], '本草綱目.csv'), encoding='utf-8-sig')

        # 本草纲目(簡體)_Ver1.csv [修正 本草纲目(簡體).csv 括號不完整等問題]
        for index, row in df.iterrows():
            if pd.isnull(row['目錄']):
                continue
            if re.search(r'\w+[部|目]第\w+卷 \w{1,2}之\w+', row['目錄']):
                row['內文'] = re.sub(r'【 【主治】', '【主治】', row['內文'])
                row['內文'] = re.sub(r'主治 【附方', '主治】 【附方', row['內文'])
                row['內文'] = re.sub(r'附方 吐血', '附方】 吐血', row['內文'])
                row['內文'] = re.sub(r'【别名】', '【釋名】', row['內文'])
                row['內文'] = re.sub(r'【主冶】', '【主治】', row['內文'])
        df.to_csv(os.path.join(config.Path['data_dir'], '本草綱目_Ver1.csv'), encoding='utf-8-sig')

        # 本草綱目_Ver2.csv [本草綱目_Ver1.csv]
        new_df = pd.DataFrame(columns=['目錄', '標題', '釋名', '內文', '部位', '部位內文', '主治', '氣味', '附方'])
        for index, row in df.iterrows():
            if pd.isnull(row['目錄']):
                continue
            if not re.search(r'\w+[部|目]第\w+卷 \w{1,2}之\w+', row['目錄']):
                continue
            data_row = dict((k, '') for k in new_df.columns)
            data_row['目錄'] = row['目錄']
            data_row['標題'] = row['標題']
            data_row['內文'] = row['內文']
            if re.search(r'【釋名】(.*?)(?=【|(?<=.$))', data_row['內文'], re.S):
                data_row['釋名'] = re.search(r'【釋名】(.*?)(?=【|(?<=.$))', data_row['內文'], re.S).group(1)
            newContent = re.sub(r'(?:(\w{1,10})  (【(?:.*)))', r'\\x\1\\x\n\2', data_row['內文'], re.M)
            sites = re.findall(r'(\\x.+?\\x.*?)(?=\\x|(?<=.$))', newContent, re.S)
            sites = sites if sites else [data_row['內文']]
            for s_content in sites:
                data_row['部位內容'] = s_content
                if re.search(r'\\x(.+?)\\x', s_content, re.S):
                    data_row['部位'] = re.search(r'\\x(.+?)\\x', s_content, re.S).group(1)
                if re.search(r'【主治】(.*?)(?=【|(?<=.$))', s_content, re.S):
                    data_row['主治'] = re.search(r'【主治】(.*?)(?=【|(?<=.$))', s_content, re.S).group(1)
                if re.search(r'【氣味】(.*?)(?=【|(?<=.$))', s_content, re.S):
                    data_row['氣味'] = re.search(r'【氣味】(.*?)(?=【|(?<=.$))', s_content, re.S).group(1)
                if re.search(r'【附方】(.*?)(?=【|(?<=.$))', s_content, re.S):
                    data_row['附方'] = re.search(r'【附方】(.*?)(?=【|(?<=.$))', s_content, re.S).group(1)
                new_df = new_df.append(data_row, ignore_index=True)
        new_df.to_csv(os.path.join(config.Path['data_dir'], '本草綱目_Ver2.csv'), encoding='utf-8-sig')

        # 本草綱目_Ver3.csv [結構化 附方 與 附方內容]
        df = new_df
        new_df = pd.DataFrame(columns=['標題', '附方', '內文', '完整內文'])
        previous_title = None
        pattern = r'[。）》\n][\w ]*?( ?\w+[\w ，、]{1,10})∶(.*?)(?=(?:[。）》\n][\w ]*?(?: ?\w+[\w ，、]{1,10})∶)|(?<=.$))'
        for index, row in df.iterrows():
            title = row['標題']
            compound_content = row['附方']
            if title == previous_title or pd.isnull(compound_content):
                continue
            else:
                previous_title = title
            finds = re.findall(pattern, compound_content, re.M)
            if not finds:
                continue
            for find in finds:
                df_row = dict((k, '') for k in new_df.columns)
                df_row['標題'] = title
                df_row['附方'] = find[0]
                df_row['內文'] = find[1]
                df_row['完整內文'] = compound_content
                new_df = new_df.append(df_row, ignore_index=True)
        file_path = os.path.join(config.Path['data_dir'], '本草綱目_Ver3.csv')
        new_df.to_csv(file_path, encoding='utf-8-sig')

        # 本草綱目_Ver4.csv [結構化 附方 與 附方內容]
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
        # df = new_df
        # new_df = pd.DataFrame(columns=['標題', '附方', '完整內文', '內文', '藥材組合'])
        # for index, row in df.iterrows():
        #     if pd.isnull(row['內文']):
        #         continue
        #     content = re.sub('\s', '', row['內文'])
        #     match = re.search('（\w{0,3}《?\w{2,8}》?）|《\w{2,8}》', content)
        #     if match:
        #         content = re.sub('（\w{0,3}《?\w{2,8}》?）|《\w{2,8}》', '', content)
        #     mFinds = re.findall('(' + join_mName + ')', content)
        #     aFinds = re.findall('(' + join_aName + ')', content)
        #     finds = list()
        #     medicine = Medicine.get(name=re.sub('\s', '', row['標題']))
        #     finds.append(medicine.name)
        #     finds.extend(mFinds)
        #     for aFind in aFinds:
        #         alias = Alias.get(name=aFind)
        #         medicine = Medicine.query.get(alias.medicine_id)
        #         # finds.append(medicine.name)
        #     # print(set(finds))
        #     df_row = dict((k, '') for k in df.columns)
        #     df_row['標題'] = re.sub('\s', '', row['標題'])
        #     df_row['附方'] = row['附方']
        #     df_row['完整內文'] = re.sub('\s', '', row['完整內文'])
        #     df_row['內文'] = row['內文']
        #     df_row['藥材組合'] = '、'.join(set(finds))
        #     df = df.append(df_row, ignore_index=True)
        # file_path = os.path.join(config.Path['data_dir'], '本草綱目_Ver4.csv')
        # df.to_csv(file_path, encoding='utf-8-sig')

    def process_data(self):
        self.process_data_by_medicine_and_alias()
        self.process_data_by_property()
        self.process_data_by_compound()

    @staticmethod
    def process_data_by_medicine_and_alias():
        file_path = os.path.join(config.Path['data_dir'], '本草綱目_Ver2.csv')
        data_df = pd.read_csv(file_path, index_col=[0], engine='python', encoding='utf-8-sig')

        for index, row in data_df.iterrows():
            if pd.isnull(row['目錄']):
                continue

            if not re.search(r'\w+[部|目]第\w+卷 \w{1,2}之\w+', row['目錄']):
                continue

            medicine = Medicine.get(re.sub('\s', '', row['標題']))
            if re.match(r'(.*)[部|目]', row['目錄']):
                medicine.radical = re.match(r'(.*)[部|目]', row['目錄']).group(1)
            db.session.add(medicine)
            db.session.commit()

            alias_content = ''
            if re.search(r'【釋名】(.*?)(?=【|(?<=.$))', row['內文'], re.S):
                alias_content = re.search(r'【釋名】(.*?)(?=【|(?<=.$))', row['內文'], re.S).group(1)

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
        file_path = os.path.join(config.Path['data_dir'], '本草綱目_Ver2.csv')
        data = pd.read_csv(file_path, index_col=[0], engine='python', encoding='utf-8-sig')
        pattern = '.*?[。；]|.*'
        property_keys = ['cold', 'cool', 'warm', 'hot',
                         'neutral', 'sour', 'sweet', 'bitter',
                         'salty', 'pungent', 'poison']
        medicine_dict = OrderedDict()
        medicine_temp = None
        for index, row in data.iterrows():
            property_dict = dict.fromkeys(property_keys, 0)
            title = re.sub('\s', '', row['標題'])
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

            if re.search('熱', content):
                text = re.search('(大熱)|(熟熱)|(熱)|(微熱)', content).group()
                if text == '大熱':
                    property_dict['hot'] = 3
                elif text == '熟熱' or text == '熱':
                    property_dict['hot'] = 2
                elif text == '微熱':
                    property_dict['hot'] = 1

            if re.search('溫', content):
                text = re.search('(大溫)|(溫)|(小溫)|(微溫)', content).group()
                if text == '大溫':
                    property_dict['warm'] = 3
                elif text == '溫':
                    property_dict['warm'] = 2
                elif text == '小溫' or text == '微溫':
                    property_dict['warm'] = 1

            if re.search('冷|涼', content):
                text = re.search('(冷利)|(至冷)|(冷)|(小冷)|(涼)', content).group()
                if text == '冷利' or text == '至冷':
                    property_dict['cool'] = 3
                elif text == '冷' or text == '涼':
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

            if re.search('鹹', content):
                text = re.search('(鹹)|(微鹹)', content).group()
                if text == '鹹':
                    property_dict['salty'] = 2
                elif text == '微鹹':
                    property_dict['salty'] = 1

            if re.search('辛', content):
                text = re.search('(辛美)|(辛)|(微辛)', content).group()
                if text == '辛美' or text == '辛':
                    property_dict['pungent'] = 2
                elif text == '微辛':
                    property_dict['pungent'] = 1

            if re.search('毒', content):
                text = re.search('(大毒)|(大有毒)|(有毒)|(微毒)|(小毒)|(無毒)', content).group()
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
        file_path = os.path.join(config.Path['data_dir'], '本草綱目_Ver3.csv')
        data = pd.read_csv(file_path, index_col=[0], engine='python', encoding='utf-8-sig')
        # (columns=['標題', '附方', '內文', '完整內文'])
        medicine_all = Medicine.query.all()
        alias_all = Alias.query.all()

        medicine_names = set([medicine.name for medicine in medicine_all if len(medicine.name) > 1])
        alias_names = set([alias.name for alias in alias_all if len(alias.name) > 1])
        join_mName = '|'.join(medicine_names)
        join_aName = '|'.join(alias_names)
        last_compound = None
        medicine_temp = None
        for index, row in data.iterrows():
            if pd.isnull(row['內文']):
                continue
            if medicine_temp != row['標題']:
                medicine_temp = row['標題']
                last_compound = None
            content = re.sub('\s', '', row['內文'])
            # Match（夏子益《奇疾方》）、（《千金方》）、（陈巽方）... and Clean
            match = re.search('（\w{0,3}《?\w{2,8}》?）|《\w{2,8}》', content)
            if match:
                content = re.sub('（\w{0,3}《?\w{2,8}》?）|《\w{2,8}》', '', content)
            mFinds = re.findall('(' + join_mName + ')', content)
            aFinds = re.findall('(' + join_aName + ')', content)
            find_medicines = list()
            medicine = Medicine.get(name=re.sub('\s', '', row['標題']))
            find_medicines.append(medicine)
            find_medicines.extend([Medicine.get(name=m) for m in mFinds])
            for aFind in aFinds:
                alias = Alias.get(name=aFind)
                medicine = Medicine.query.get(alias.medicine_id)
                find_medicines.append(medicine)
            if re.search('(又法)|(又一法)|(又方)|(又散)|(一法)|(一方)', row['附方']):
                if last_compound is not None:
                    row['附方'] = last_compound
            else:
                last_compound = row['附方']

            compound = Compound(name=row['附方'], description=row['內文'], source=medicine.name)
            compound.medicine.extend(set(find_medicines))
            db.session.add(compound)
        db.session.commit()


if __name__ == '__main__':
    dp = DataProcess()
    # dp.create_datas()  # 將資料進行結構化 (僅第一次需要執行)
    dp.process_data()
