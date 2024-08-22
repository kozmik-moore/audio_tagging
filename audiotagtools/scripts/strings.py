import logging
import sys
from os import PathLike, scandir
from os.path import isfile

import click
import eyed3
import pyperclip


UPPER_CASE = [
    'aor',
    'awolnation'
]


def get_logger(usefile: bool = True,
               usestream: bool = True,
               filename: str = None,
               streamformat: str = '%(message)s',
               fileformat: str = '%(asctime)s - %(name)s - %(message)s'):
    """
    Creates an informational logger for use with "strings" module
    :param usefile:
    :param usestream:
    :param filename:
    :param streamformat:
    :param fileformat:
    :return:
    """
    logger = logging.Logger(__name__, logging.INFO)
    if usestream:
        streamhandler = logging.StreamHandler()
        streamhandler.setLevel(logging.INFO)
        streamformatter = logging.Formatter(streamformat)
        streamhandler.setFormatter(streamformatter)
        logger.addHandler(streamhandler)
    if usefile:
        if not filename:
            filename = 'edit.log'
        filehandler = logging.FileHandler(filename)
        fileformatter = logging.Formatter(fileformat)
        filehandler.setFormatter(fileformatter)
        logger.addHandler(filehandler)
    return logger


# TODO create solution for special cases (e.g. "AOR", "AWOLNATION"), possibly a list-backed dict
def format_string(string: str, old: str = ',', new: str = '|', case: str | None = 'title'):
    """
    Splits a string along a delimiter, removes whitespace from the sides of each element in the split,
    converts characters to title case, and rejoins the string using a new delimiter.
    :param string:
    :param old:
    :param new:
    :param case:
    :return:
    """
    def check_case(s: list[str], c: str):
        """
        Handles special cases (e.g. all upper case, all lower case...)
        :param s:
        :param c:
        :return:
        """
        s = [getattr(x, c)() for x in s]
        for sc, ct in [(UPPER_CASE, 'upper')]:  # add more special cases at they are found
            s = [getattr(x, ct)() if x.lower() in sc else x for x in s]
        return s

    str_list = string.split(old)
    str_list = [x.strip() for x in str_list]
    if case:
        str_list = check_case(str_list, case)
    return new.join(str_list)


@click.command()
@click.option('-o', '--old', default=',', help='Original delimiter (for input).')
@click.option('-n', '--new', default='|', help='New delimiter (for output).')
@click.option('-c',
              '--case',
              type=click.STRING,
              default='title',
              help='Choose case to convert strings to. Options are "capitalize", "title", "upper", and "lower".')
@click.option('-s', '--stdout', is_flag=True, help='Output to stdout instead of clipboard.')
@click.argument('string')
def format_tagstring(string: str, old: str = ',', new: str = '|', case: str = 'title', stdout: bool = False):
    """
    Formats a string of tags by splitting them, removing excess whitespace,
    converting the case of all characters, and rejoining them with the provided delimiter.
    Sends the output to the clipboard.
    """
    new_string = format_string(string, old, new, case)

    if stdout:
        click.echo(new_string)
    else:
        pyperclip.copy(new_string)


def format_multipart_tags(path: PathLike | str,
                          tag: str = 'genre',
                          old: str = '/',
                          new: str = '|',
                          case: str = 'title',
                          verbose: bool = False,
                          logger: logging.Logger = None,
                          eyed3_warn: bool = False):
    """
    Searches a directory for MP3 files and formats them.
    Replaces the delimiters between values in the specfied tag.
    Sets case for the "genre" tag.
    :param path:
    :param tag:
    :param old:
    :param new:
    :param case:
    :param verbose:
    :param logger:
    :param eyed3_warn:
    :return:
    """
    # Create logger, if necessary
    if not logger:
        logger = get_logger(usefile=False)

    # Suppress eyed3 log warnings
    if not eyed3_warn:
        eyed3.log.setLevel(logging.ERROR)

    # Validate delimiters
    message = None
    if tag in ['artist', 'composer'] and any([x.strip() == ',' for x in [old, new]]):
        message = '"," is an invalid delimiter for "artist" tag. Process terminated.'
    if message:
        logger.warning(message)
        sys.exit()

    # Get files as directory entries
    entries = [x for x in scandir(path) if isfile(x) and x.name.endswith('.mp3')]
    entries = sorted(entries, key=lambda e: e.name)

    # Process all MP3 files at once, if found
    if entries:
        path_tags = [{'path': x.path, 'tag_obj': eyed3.load(x.path).tag} for x in entries]
        for d in path_tags:
            if verbose:
                logger.info(f'Processing "{d["path"]}"...')
            tag_obj = d['tag_obj']
            if tag_obj:
                tagvalue = getattr(tag_obj, tag)
                if tagvalue:
                    newvalue = format_string(str(tagvalue), old, new, case=case)
                    setattr(tag_obj, tag, newvalue)
        if verbose:
            logger.info('Saving changes...')
        # Save all changes at once
        for d in path_tags:
            d['tag_obj'].save()
    else:
        logger.info(f'No MP3 files found in "{path}".')


@click.command()
@click.option('-o', '--old', type=click.STRING, default='/', help='Old delimiter.')
@click.option('-n', '--new', type=click.STRING, default='|', help='New delimiter.')
@click.option('-c',
              '--case', type=click.STRING,
              default=None,
              help='Character case to use. Options are "title", "capitalize", "upper", and "lower".')
@click.option('-v', '--verbose', is_flag=True, help='Verbose mode.')
@click.option('-w', '--eyed3_warn', is_flag=True, help='Unsuppress warnings from eyed3 module.')
@click.argument('path', type=click.Path(writable=True, file_okay=False, exists=True))
def format_artist_tag_cli(path: PathLike | str,
                          old: str = '/',
                          new: str = '|',
                          case: str = None,
                          verbose: bool = False,
                          eyed3_warn: bool = False):
    """
    Command line tool for editing the artists tag for MP3 files.
    Searches a directory for MP3 files and formats their artist tags.
    Replaces delimiters and converts case.
    """
    logger = get_logger(usefile=False)
    format_multipart_tags(path,
                          'artist',
                          old,
                          new,
                          case,
                          verbose,
                          logger,
                          eyed3_warn)


@click.command()
@click.option('-o', '--old', type=click.STRING, default='/', help='Old delimiter.')
@click.option('-n', '--new', type=click.STRING, default='|', help='New delimiter.')
@click.option('-c',
              '--case', type=click.STRING,
              default=None,
              help='Character case to use. Options are "title", "capitalize", "upper", and "lower".')
@click.option('-v', '--verbose', is_flag=True, help='Verbose mode.')
@click.option('-w', '--eyed3_warn', is_flag=True, help='Unsuppress warnings from eyed3 module.')
@click.argument('path', type=click.Path(writable=True, file_okay=False, exists=True))
def format_composer_tag_cli(path: PathLike | str,
                            old: str = '/',
                            new: str = '|',
                            case: str = None,
                            verbose: bool = False,
                            eyed3_warn: bool = False):
    """
    Command line tool for editing the composer tag for MP3 files.
    Searches a directory for MP3 files and formats their composer tags.
    Replaces delimiters and converts case.
    """
    logger = get_logger(usefile=False)
    format_multipart_tags(path, 'composer', old, new, case, verbose, logger,
                          eyed3_warn)


@click.command()
@click.option('-o', '--old', type=click.STRING, default='/', help='Old delimiter.')
@click.option('-n', '--new', type=click.STRING, default='|', help='New delimiter.')
@click.option('-c',
              '--case', type=click.STRING,
              default=None,
              help='Character case to use. Options are "title", "capitalize", "upper", and "lower".')
@click.option('-v', '--verbose', is_flag=True, help='Verbose mode.')
@click.option('-w', '--eyed3_warn', is_flag=True, help='Unsuppress warnings from eyed3 module.')
@click.argument('path', type=click.Path(writable=True, file_okay=False, exists=True))
def format_genre_tag_cli(path: PathLike | str,
                         old: str = '/',
                         new: str = '|',
                         case: str = None,
                         verbose: bool = False,
                         eyed3_warn: bool = False):
    """
    Command line tool for editing the genre tag for MP3 files.
    Searches a directory for MP3 files and formats their genre tags.
    Replaces delimiters and converts case.
    """
    logger = get_logger(usefile=False)
    format_multipart_tags(path, 'genre', old, new, case, verbose, logger,
                          eyed3_warn)


if __name__ == '__main__':
    pass
