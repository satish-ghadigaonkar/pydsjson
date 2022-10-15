import pathlib

import click
import configparser
import warnings
import logging
from .dsjson import ReadDatasetJason, ParseDefine, write_dataset_json

for name, logger in logging.root.manager.loggerDict.items():
    logger.disabled = True


def get_files(infiles, file_types='*.json'):
    files = list()
    for infile in infiles:
        if infile.is_dir():
            files.extend(infile.glob(file_types))
        elif infile.is_file():
            files.append(infile)

    return files


@click.group()
@click.option('--config', type=click.Path(exists=True))
@click.option('--define', type=click.Path(exists=True))
@click.pass_context
def dataset_json(ctx, config=None, define=None):
    pdefine = ParseDefine(define) if define is not None else None

    if config is not None:
        config_parser = configparser.ConfigParser(allow_no_value=True)
        config_parser.read(config)
        item_group_prefix = config_parser.get('prefixes', 'ITEM_GROUP_PREFIX', fallback="")
        item_prefix = config_parser.get('prefixes', 'ITEM_PREFIX', fallback="IT")
        study_oid = config_parser.get('oids', 'STUDY_OID', fallback="")
        metadata_version_oid = config_parser.get('oids', 'METADATA_VERSION_OID', fallback="")
    else:
        item_group_prefix = ""
        item_prefix = "IT"
        study_oid = ""
        metadata_version_oid = ""


    ctx.ensure_object(dict)
    ctx.obj['item_group_prefix'] = item_group_prefix
    ctx.obj['item_prefix'] = item_prefix
    ctx.obj['study_oid'] = study_oid
    ctx.obj['metadata_version_oid'] = metadata_version_oid
    ctx.obj['define'] = pdefine



@dataset_json.command()
@click.argument('infiles', type=click.Path(exists=True))
@click.argument('output_folder', type=click.Path(exists=True))
@click.pass_context
def to_csv(ctx, infiles, output_folder):
    for f in get_files(infiles):
        click.echo(f'Processing {f}')
        dsjson = ReadDatasetJason(f, ctx.obj['item_group_prefix'])
        dsnames = dsjson.get_dataset_names()

        for dsname in dsnames:
            dsjson.to_csv(output_folder, dsname)


@dataset_json.command()
@click.argument('infiles', nargs=-1, type=click.Path(exists=True, path_type=pathlib.Path))
@click.argument('output_folder', type=click.Path(exists=True))
@click.pass_context
def to_xpt(ctx, infiles, output_folder):
    for f in get_files(infiles):
        click.echo(f'Processing {f}')
        dsjson = ReadDatasetJason(f, ctx.obj['item_group_prefix'])
        dsnames = dsjson.get_dataset_names()

        warnings.filterwarnings('ignore')
        for dsname in dsnames:
            dsjson.to_xpt(output_folder, dsname, ctx.obj['define'])


@dataset_json.command()
@click.argument('infiles', nargs=-1, type=click.Path(exists=True, path_type=pathlib.Path))
@click.argument('output_folder', type=click.Path(exists=True))
@click.pass_context
def to_json(ctx, infiles, output_folder):
    for f in get_files(infiles):
        click.echo(f'Processing {f}')
        define = ctx.obj['define']
        write_dataset_json(f, define.study_oid if define else ctx.obj['study_oid'],
                           define.metadata_version_oid if define else ctx.obj['metadata_version_oid'], output_folder,
                           item_group_prefix=ctx.obj['item_group_prefix'], item_prefix=ctx.obj['item_prefix'],
                           define=ctx.obj['define'])
