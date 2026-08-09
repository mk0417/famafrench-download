# Download Fama-French data

A simple Python library for downloading Fama-French datasets from Ken French's Data Library.

## Installation

I do not want to manage a PyPI package. Therefore, you can install `famafrench_download` directly from the GitHub repository using `pip`:

```bash
pip install git+https://github.com/mk0417/famafrench-download.git
```

## Usage

### 1. List Available Datasets

To view all available dataset names from Ken French's Data Library:

```python
import famafrench_download as ffd

# List dataset identifiers
datasets = ffd.list_datasets()
print(datasets[:5])
```

### 2. List Historical Archives

To view available historical archive dataset names for 3-factor (`ff3`) or 5-factor (`ff5`) models:

```python
# List 3-factor archives
archives_ff3 = ffd.list_archives('ff3')
print(archives_ff3)

# List 5-factor archives
archives_ff5 = ffd.list_archives('ff5')
print(archives_ff5)
```

### 3. Download Datasets

Use `port_dl` with a dataset name to download, and return a dictionary of Polars DataFrames keyed by data frequency (e.g., `Monthly`, `Annual`, `Daily`):

```python
# Download Fama-French 3 Factors dataset
data = ffd.port_dl('F-F_Research_Data_Factors')

# The original file contains both monthly and annual factor returns
data['Monthly']

data['Annual']
```

