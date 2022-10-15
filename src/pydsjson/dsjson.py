import json
import pandas as pd
import numpy as np
import xport.v56
import os
from lxml import etree as et


class Column:
    __slots__ = ('oid', 'name', 'label', 'type', 'length', 'format')

    def __init__(self, col_oid: str, col_name: str, col_type: str, col_label: str | None = None,
                 col_length: int | None = None, col_format: str | None = None):
        self.oid = col_oid
        self.name = col_name
        self.label = col_label
        self.type = col_type
        self.length = col_length
        self.format = col_format

    def __repr__(self):
        return f'({self.name}, {self.label})'


class Dataset:
    __slots__ = ('oid', 'name', 'label', 'columns')

    def __init__(self, ds_oid: str, ds_name: str, ds_label: str | None = None, ds_columns: list[Column] | None = None):
        self.oid = ds_oid
        self.name = ds_name
        self.label = ds_label
        self.columns = ds_columns if ds_columns is not None else dict()

    def append_columns(self, columns):
        self.columns.update(columns)

    def get_column(self, col_name):
        return self.columns.get(col_name)

    def get_column_names(self):
        return list(self.columns.keys())

    def __repr__(self):
        return f'({self.name}, {self.label})'


class ReadDatasetJason:
    __slots__ = ('filepath', 'data', 'datasets', 'item_group_prefix')

    def __init__(self, filepath, item_group_prefix=""):
        self.filepath = filepath
        self.item_group_prefix = item_group_prefix
        self.data = self.load_data(filepath)
        self.datasets = self.create_datasets()

    @staticmethod
    def load_data(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)

    @staticmethod
    def create_dataset(ds_oid: str, ds_name: str, ds_label: str | None = None):
        return Dataset(ds_oid, ds_name, ds_label)

    def create_datasets(self):
        datasets = []

        for item_group, value in self.data.get("clinicalData").get("itemGroupData").items():
            dataset = self.create_dataset(item_group, value.get("name"), value.get("label"))
            dataset.append_columns(self.create_columns(dataset))
            datasets.append(dataset)

        return tuple(datasets)

    @staticmethod
    def create_column(col_oid: str, col_name: str, col_type: str, col_label: str | None = None,
                      col_length: int | None = None):
        return Column(col_oid, col_name, col_type, col_label, col_length)

    def create_columns(self, dataset: Dataset):
        return {
            item.get("name"): self.create_column(item.get("OID"), item.get("name"), item.get("type"), item.get("label"),
                                                 item.get("length")) for item in
            self.data.get("clinicalData").get("itemGroupData").get(
                '.'.join(filter(None, [self.item_group_prefix, dataset.name]))).get(
                "items")}

    def get_dataset(self, ds_name):
        for dataset in self.datasets:
            if dataset.name == ds_name:
                return dataset

    def get_dataset_names(self):
        return [dataset.name for dataset in self.datasets]

    def get_column(self, ds_name, col_name):
        return self.get_dataset(ds_name).get_column(col_name)

    def get_column_names(self, ds_name):
        return self.get_dataset(ds_name).get_column_names()

    def get_dataset_records(self, ds_name: str):
        return self.data.get("clinicalData").get("itemGroupData").get(
            '.'.join(filter(None, [self.item_group_prefix, ds_name]))).get("itemData")

    def to_df(self, ds_name):
        return pd.DataFrame(self.get_dataset_records(ds_name), columns=self.get_column_names(ds_name)).set_index(
            'ITEMGROUPDATASEQ')

    def to_xpt(self, dest, ds_name, define=None):
        df = self.to_df(ds_name)
        dataset = self.get_dataset(ds_name)

        ds = xport.Dataset(df, name=dataset.name, label=dataset.label)
        for (k, v) in ds.items():
            v.label = dataset.get_column(k).label

            if define is not None:
                fmt = define.get_column(dataset.name, k).format
                if fmt is not None:
                    v.format = define.get_column(dataset.name, k).format

        with open(os.path.join(dest, dataset.name.lower() + '.xpt'), 'wb') as f:
            xport.v56.dump(ds, f)

    def to_csv(self, dest, ds_name):
        self.to_df(ds_name).to_csv(os.path.join(dest, ds_name.lower() + '.csv'))


class ParseDefine:
    __slots__ = ('filepath', 'root', 'namespace', 'datasets', 'study_oid', 'metadata_version_oid')

    def __init__(self, filepath):
        self.filepath = filepath
        self.root = self.get_root(filepath)
        self.namespace = self.get_namespace()
        self.datasets = self.create_datasets()
        self.study_oid = self.root.find('default:Study', self.namespace).get('OID')
        self.metadata_version_oid = self.root.find('default:Study/default:MetaDataVersion', self.namespace).get('OID')

    @staticmethod
    def get_root(filepath):
        parser = et.XMLParser(ns_clean=True)
        root = et.parse(filepath, parser).getroot()
        return root

    def get_namespace(self):
        return {k if k is not None else 'default': v for k, v in self.root.nsmap.items()}

    @staticmethod
    def create_dataset(ds_oid: str, ds_name: str, ds_label: str | None = None):
        return Dataset(ds_oid, ds_name, ds_label)

    def create_datasets(self):
        datasets = []

        for item_group_def in self.root.findall('default:Study/default:MetaDataVersion/default:ItemGroupDef',
                                                self.namespace):
            oid = item_group_def.get('OID')
            name = item_group_def.get('Name')
            label = item_group_def.find('default:Description/default:TranslatedText', self.namespace).text
            dataset = self.create_dataset(oid, name, label)
            dataset.append_columns(self.create_columns(item_group_def))
            datasets.append(dataset)

        return tuple(datasets)

    @staticmethod
    def create_column(col_oid, col_name: str, col_type: str, col_label: str | None = None,
                      col_length: int | None = None,
                      col_format: str | None = None):
        return Column(col_oid, col_name, col_type, col_label, col_length, col_format)

    def create_columns(self, item_group_def):
        col_dict = dict()
        for item_ref in item_group_def.findall('default:ItemRef', self.namespace):
            item_def = self.root.find(
                "default:Study/default:MetaDataVersion/default:ItemDef[@OID='" + item_ref.get('ItemOID') + "']",
                self.namespace)
            col_dict[item_def.get('Name')] = self.create_column(item_def.get("OID"), item_def.get("Name"),
                                                                item_def.get("DataType"), item_def.find(
                    'default:Description/default:TranslatedText', self.namespace).text, item_def.get("Length"),
                                                                item_def.get(
                                                                    '{' + self.namespace.get('def') + '}DisplayFormat'))

        return col_dict

    def get_dataset(self, ds_name):
        for dataset in self.datasets:
            if dataset.name == ds_name:
                return dataset

    def get_dataset_names(self):
        return [dataset.name for dataset in self.datasets]

    def get_column(self, ds_name, col_name):
        return self.get_dataset(ds_name).get_column(col_name)

    def get_column_names(self, ds_name):
        return self.get_dataset(ds_name).get_column_names()


def write_dataset_json(xptpath, study_oid: str, metadata_version_oid: str, output_folder, item_group_prefix="",
                       item_prefix='IT', define=None):
    with open(xptpath, 'rb') as f:
        library = xport.v56.load(f)

        for ds in library.values():
            jsondict = {'clinicalData': {'studyOID': study_oid, 'metaDataVersionOID': metadata_version_oid,
                                         'itemGroupData': dict()}}
            dsdict = dict()
            dsdict['records'] = ds.shape[0]
            dsdict['name'] = ds.name.upper()
            dsdict['label'] = ds.dataset_label if len(ds.dataset_label) else ds.name.upper()
            dsdict['items'] = list()
            dsdict['itemData'] = list()

            if len(ds.columns):
                items = [
                    {'OID': 'ITEMGROUPDATASEQ', 'name': 'ITEMGROUPDATASEQ', 'label': 'Record identifier',
                     'type': 'integer'}]
                for k, v in ds.items():
                    item_name = k.upper()
                    item_oid = '.'.join(filter(None, [item_prefix, item_name]))
                    item_label = v.label if len(v.label) else item_name
                    item_width = define.get_column(ds.name.upper(), item_name).length if define else v.width

                    if v.vtype.name == 'CHARACTER':
                        item_type = 'string'
                    else:
                        item_type = define.get_column(ds.name.upper(), item_name).type if define else 'float'

                    items.append(
                        {'OID': item_oid, 'name': item_name, 'label': item_label, 'type': item_type,
                         'length': item_width})

                dsdict['items'] = items
                ds.replace({np.nan: None}, inplace=True)
                dsdict['itemData'] = [[index] + obs for index, obs in enumerate(ds.values.tolist(), start=1)]

            jsondict['clinicalData']['itemGroupData'].update(
                {'.'.join(filter(None, [item_group_prefix, ds.name.upper()])): dsdict})

            with open(os.path.join(output_folder, ds.name.lower() + '.json'), 'w') as outfile:
                json.dump(jsondict, outfile)
