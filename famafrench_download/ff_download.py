import requests
from lxml.html import document_fromstring
import tempfile
from zipfile import ZipFile
import re
import pandas as pd
import polars as pl
from io import StringIO
import numpy as np


base_url = 'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french'

def list_datasets():
    url = f'{base_url}/data_library.html'
    response = requests.get(url)
    source = document_fromstring(response.content)
    search_pattern = ".//a[starts-with(@href, 'ftp/') and substring(@href, string-length(@href) - 7) = '_CSV.zip']/@href"
    datasets = [i[4:-8] for i in source.xpath(search_pattern)]
    return datasets

def list_archives(factor_model):
    if factor_model == 'ff3':
        url = f'{base_url}/Data_Library/f-f_factors_archive.html'
    if factor_model == 'ff5':
        url = f'{base_url}/Data_Library/f-f_5_factors_2x3_archive.html'

    response = requests.get(url)
    source = document_fromstring(response.content)
    search_pattern = ".//a[starts-with(@href, 'Historical_Archives/')]/@href"
    datasets = [
        f'archive {factor_model} {re.search(r'\d\d \d\d\d\d', i)[0]}'
        for i in source.xpath(search_pattern)]
    # Remove duplicates
    datasets = sorted(
        list(set(datasets)), key=lambda x: x.split()[-1], reverse=True)
    return datasets

def _read_zipfile(file_url):
    file_source = requests.get(file_url).content
    with tempfile.TemporaryFile() as temp:
        temp.write(file_source)
        with ZipFile(temp) as tempzip:
            for i in tempzip.namelist():
                if not i.endswith('/'):
                    data = tempzip.open(i).read().decode()

    return data

def _extract_sections(fname):
    if 'archive' in fname:
        fname_split = fname.split(' ')
        model = fname_split[1]
        month = fname_split[2]
        year = fname_split[3]
        base_url_archive = f'{base_url}/Data_Library/Historical_Archives/{month}%20{year}%20Update/ftp'
        if model == 'ff3':
            url = f'{base_url_archive}/F-F_Research_Data_Factors_TXT.zip'
            try:
                raw = _read_zipfile(url)
            except:
                url = f'{base_url_archive}/F-F_Research_Data_Factors_CSV.zip'
                raw = _read_zipfile(url)
        if model == 'ff5':
            url = f'{base_url_archive}/F-F_Research_Data_5_Factors_2x3_TXT.zip'
            try:
                raw = _read_zipfile(url)
            except:
                url = f'{base_url_archive}/F-F_Research_Data_5_Factors_2x3_CSV.zip'
                raw = _read_zipfile(url)
    else:
        url = f'{base_url}/ftp/{fname}_CSV.zip'
        raw = _read_zipfile(url)

    if 'TXT.zip' in url:
        file_type = 'txt'
    if 'CSV.zip' in url:
        file_type = 'csv'

    # Split data if multiple sections and remove top notes
    section_split = raw.split('\r\n\r\n')
    # Handle notes at the beginning and the end of file
    sections = []
    for i in section_split:
        if len(i) > 500:
            sections.append(i)

    return sections, file_type

def port_dl(fname):
    sections, file_type = _extract_sections(fname)
    data = {}
    for i in sections:
        # Section start position
        if file_type == 'txt':
            section_start = re.search(r'^\s\s+', i, re.M).start()
            df = pd.read_fwf(StringIO(i[section_start:]))
        if file_type == 'csv':
            section_start = re.search(r'^\s*,', i, re.M).start()
            df = pd.read_csv(StringIO(i[section_start:]))

        df.columns = df.columns.str.lower().str.replace('-', '')
        col_name = list(df.columns)
        col_name[0] = 'date'
        df.columns = col_name
        # Deal with missing values (i.e. -99.99, -999)
        df = df.replace([-99.99, -999], np.nan)
        # Get data frequency
        info = i[:section_start].replace('Factors', '').split(':')[0].strip()
        # Fill data frequency if missing
        if len(info) == 0:
            if re.search('weekly|daily', fname):
                info = fname.split('_')[-1].title()
            else:
                info = 'Monthly'

        data[info] = pl.from_pandas(df)

    return data

