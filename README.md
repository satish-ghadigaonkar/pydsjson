# pydsjson
## Description

The main purpose of *pydsjson* is to provide utilities for seamless conversion between Dataset-JSON and other data
formats such as SAS XPORT, CSV etc.

You can also use `pydsjson` module as command-line tool.

## Installation

This project requires Python v3.8+. Currently, the under development version can be installed from GitHub.

```Shell
python -m pip install https://github.com/satish-ghadigaonkar/pydsjson
``` 

## Covert from Dataset-JSON to other data formats

````Python
import pydsjson.dsjson

ds = pydsjson.dsjson.ReadDatasetJason(filepath=r".\examples\source\adlbc.json",
                                      item_group_prefix="")

# Covert to Pandas dataframe
df = ds.to_df(ds_name="ADLBC")

# Convert to XPT
ds.to_xpt(dest=r".\examples\output", ds_name="ADLBC",
          define=pydsjson.dsjson.ParseDefine(r".\examples\source\define.xml"))

# Convert to CSV
ds.to_csv(dest=r".\examples\output", ds_name="ADLBC")

````

### Command-line Usage

````PowerShell
# Get help on command-line usage
dsjson --help

# Covert to XPT
dsjson --config ".\examples\source\prefixes.cfg" --define ".\examples\source\define.xml" json-to-xpt ".\examples\source\ad*.json" ".\examples\output"

# Covert to CSV
dsjson --config ".\examples ".\examples\source\define.xml" json-to-csv ".\examples\source\adlbc.json" ".\examples\output"

````

## Covert from XPT to Dataset-JSON
````Python
import pydsjson.dsjson

pdefine = pydsjson.dsjson.ParseDefine(r".\examples\source\define.xml")

pydsjson.dsjson.write_dataset_json(xptpath=r".\examples\source\adlbc.xpt", study_oid=pdefine.study_oid,
                                   metadata_version_oid=pdefine.metadata_version_oid,
                                   output_folder=r".\examples\output", item_group_prefix="", item_prefix="IT")

````
### Command-line Usage
````PowerShell
dsjson --config ".\examples\source\prefixes.cfg" --define ".\examples\source\define.xml" xpt-to-json ".\examples\source\ad*.xpt" ".\examples\output"
````

## Coming Soon
- Convert Dataset-JSON to R dataframe
- Covert CSV to Dataset-JSON
- Convert R dataframe to Dataset-JSON

## Contribution

Contribution is very welcome. When you contribute to this repository you are doing so under the below licenses. Please
checkout [Contribution](CONTRIBUTING.md) for additional information. All contributions must adhere to the
following [Code of Conduct](CODE_OF_CONDUCT.md).

## License

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg) ![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-blue.svg)

### Code & Scripts

This project is using the [MIT](http://www.opensource.org/licenses/MIT "The MIT License | Open Source Initiative")
license (see [`LICENSE`](LICENSE)) for code and scripts.

### Content

The content files like documentation and minutes are released
under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/). This does not include trademark permissions.

## Re-use

When you re-use the source, keep or copy the license information also in the source code files. When you re-use the
source in proprietary software or distribute binaries (derived or underived), copy additionally the license text to a
third-party-licenses file or similar.

When you want to re-use and refer to the content, please do so like the following:

> Content based on [Project XY (GitHub)](https://github.com/xy/xy) used under
> the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) license.