import pathlib
import click
import configparser
import warnings
import logging
from .dsjson import ReadDatasetJason, ParseDefine, write_dataset_json

for name, logger in logging.root.manager.loggerDict.items():
    logger.disabled = True


def get_files(infiles: tuple[pathlib.Path], file_types='*.json'):
    files = list()
    for infile in infiles:
        if infile.is_dir():
            files.extend(infile.expanduser().glob(file_types))
        elif infile.is_file():
            files.append(infile.expanduser())

    return files


@click.group()
@click.option('--config', type=click.Path(exists=True),
              help="Path for configuration file specifying item group prefix and item prefix")
@click.option('--define', type=click.Path(exists=True), help="Path for Define xml file")
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
@click.argument('infiles', nargs=-1, type=click.Path(exists=True, path_type=pathlib.Path))
@click.argument('output_folder', type=click.Path(exists=True, path_type=pathlib.Path, file_okay=False, writable=True))
@click.pass_context
def json_to_csv(ctx, infiles, output_folder):
    """Converts Dataset JSON to CSV

    \b
    infiles       : Path for Dataset JSON files. These can be multiple files.
    output_folder : Output folder for converted CSV files
    """
    for f in get_files(infiles):
        click.echo(f'Processing {f}')
        dsjson = ReadDatasetJason(f, ctx.obj['item_group_prefix'])
        dsnames = dsjson.get_dataset_names()

        for dsname in dsnames:
            dsjson.to_csv(output_folder, dsname)


@dataset_json.command()
@click.argument('infiles', nargs=-1, type=click.Path(exists=True, path_type=pathlib.Path))
@click.argument('output_folder', type=click.Path(exists=True, dir_okay=True, writable=True))
@click.pass_context
def json_to_xpt(ctx, infiles, output_folder):
    for f in get_files(infiles):
        click.echo(f'Processing {f}')
        dsjson = ReadDatasetJason(f, ctx.obj['item_group_prefix'])
        dsnames = dsjson.get_dataset_names()

        warnings.filterwarnings('ignore')
        for dsname in dsnames:
            dsjson.to_xpt(output_folder, dsname, ctx.obj['define'])


@dataset_json.command()
@click.argument('infiles', nargs=-1, type=click.Path(exists=True, path_type=pathlib.Path))
@click.argument('output_folder', type=click.Path(exists=True, dir_okay=True, writable=True))
@click.pass_context
def xpt_to_json(ctx, infiles, output_folder):
    for f in get_files(infiles):
        click.echo(f'Processing {f}')
        define = ctx.obj['define']
        write_dataset_json(f, define.study_oid if define else ctx.obj['study_oid'],
                           define.metadata_version_oid if define else ctx.obj['metadata_version_oid'], output_folder,
                           item_group_prefix=ctx.obj['item_group_prefix'], item_prefix=ctx.obj['item_prefix'],
                           define=ctx.obj['define'])
