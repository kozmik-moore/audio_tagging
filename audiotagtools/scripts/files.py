import logging
import re
from os import PathLike, walk, scandir, mkdir, remove
from os.path import split, join, exists, abspath, isfile, isdir, basename
from shutil import copytree, rmtree, move

import click
from mutagen.flac import FLAC
from mutagen.id3 import APIC
from mutagen.mp3 import MP3
from pydub import AudioSegment
from pydub.utils import mediainfo
from pyperclip import copy


def find_music_dirs(path: PathLike | str, filetype: str = 'flac'):
    """
    Searches the given directory and its subdirectories to find any directory containing music files.
    Searches for FLAC files by default.
    :param filetype:
    :param path:
    :return:
    """
    dirs_list = []
    path = abspath(path)
    for root, dirs, files in walk(path):
        if (not basename(root).startswith('.') and
                any([x.endswith('.' + filetype) for x in files])):  # Ignore hidden directories
            dirs_list.append(root)
    dirs_list = sorted(dirs_list)
    return dirs_list


# TODO change "output" to print file to working directory, rather than prompt user for file location
@click.command()
@click.option('-t', '--filetype', default='flac', help='File type.')
@click.option('-c', '--clipboard', is_flag=True, help='Send to clipboard.')
@click.option('-o', '--output', help='Name of text file to send output to. Be sure to include extension.')
@click.option('-s', '--silent', is_flag=True, help='Do not print to stdout.')
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True))
def find_music_dirs_cli(path: PathLike | str,
                        clipboard: bool,
                        silent: bool,
                        output: PathLike | str,
                        filetype: str = 'flac'):
    """
    A command line tool for finding directories with music files.
    Searches the given directory and its subdirectories to find any directory containing music files.
    """
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    if exists(path) and isdir(path):
        dirs_list = find_music_dirs(path, filetype=filetype)
        dirs_text = '\n'.join(dirs_list)
        if clipboard:
            copy(dirs_text)
        if output:
            output = abspath(output)
            if exists(output):
                logging.warning(f'{output} already exists.')
            else:
                with open(output, 'w') as file:
                    file.write(dirs_text)
        if not silent:
            click.echo(dirs_text)
    elif exists(path):
        logging.warning(f'{path} is not a directory.')
    else:
        logging.warning(f'{path} does not exist.')


def find_flac_playlists(path: PathLike | str, silent: bool = False):
    """
    Searches through a directory and its subdirectories to find XML files containing the string ".flac"
    :param silent:
    :param path:
    :return:
    """
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    files_list = []
    for root, dirs, files in walk(path):
        if not silent:
            logging.info(f'Checking "{abspath(root)}" for FLAC files...')
        for file in [x for x in files if x.endswith('.xml')]:
            file_path = join(root, file)
            with open(file_path, 'r') as f:
                text = f.read()
                if '.flac' in text:
                    if not silent:
                        logging.info('FLAC files found!')
                    files_list.append(file_path)
    files_list = sorted(files_list)
    logging.info('Finished!')
    return files_list


# TODO add option for specifying log location
# TODO change "silent" flag to "verbose"
@click.command()
@click.option('-s', '--silent', is_flag=True, help='Run without logging to terminal.')
@click.option('-o',
              '--output',
              is_flag=True,
              help='File path to write results to. If file name is not specified in path, '
                   'name will be "playlists.txt"')
@click.argument('path', type=click.Path(exists=True, file_okay=False))
def find_flac_playlists_cli(path, output: bool = False, silent: bool = False):
    """
    Command line tool for finding XML playlist files containing FLAC files
    Searches through a directory and its subdirectories to find XML files containing the string ".flac".
    """
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    if silent:
        logging.info(f'Checking playlists in {path} for FLAC files...')
    files_list = find_flac_playlists(path, silent)
    if output:
        output_loc = abspath('playlists.txt')
        with open(output_loc, 'w') as f:
            f.write('\n'.join(files_list))
        logging.info(f'Log can be found at "{output_loc}".')


def flac_playlist_to_mp3(path: PathLike | str, verbose: bool = False, inplace: bool = False):
    """
    Searches through a directory and its subdirectories to find XML files and replace ".flac" with ".mp3"
    :param inplace:
    :param verbose:
    :param path:
    :return:
    """
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    path = abspath(path)
    if not inplace:
        root, name = split(path)
        output = str(join(root, name + ' (edited)'))
        if verbose:
            logging.info(f'Copying directory tree to "{output}"...')
        copytree(path, output)
    else:
        output = path
    for root, dirs, files in walk(output):
        for file in [x for x in files if x.endswith('.xml')]:
            file_path = join(root, file)
            with open(file_path, 'r') as f:
                text = f.read()
                f.close()
            if '.flac' in text:
                if verbose:
                    logging.info(f'Editing XML file "{file_path}"...')
                text = re.sub(r'.flac', '.mp3', text)
                with open(file_path, 'w') as f:
                    f.write(text)
    logging.info(f'Finished! New files located at "{output}".')


@click.command()
@click.option('-v', '--verbose', is_flag=True, help='Verbose mode.')
@click.option('-i', '--inplace', is_flag=True, help='Replace original files, rather than creating edited copies.')
@click.argument('path', type=click.Path(writable=True, file_okay=False))
def flac_playlist_to_mp3_cli(path: PathLike | str, verbose: bool = False, inplace: bool = False):
    """
    Command line tool for converting FLAC references in XML files to MP3 references.
    Searches through a directory and its subdirectories to find XML files and replace ".flac" with ".mp3"
    """
    flac_playlist_to_mp3(path, verbose, inplace)


# TODO add option to print out steps and files which would be affected (maybe not)
def flac_to_mp3(path: PathLike | str,
                bitrate: int = 256,
                verbose: bool = False,
                inplace: bool = False,
                delete: bool = False):
    """
    For a given directory, creates a folder of MP3 copies of all FLAC files
    """
    if delete:
        inplace = True
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info('Starting process...' if not verbose else 'Processing...')
    if verbose:
        logging.info('Checking for FLAC files...')
    path = abspath(path)

    # Check for directory entries ending in ".flac"
    entries = [x for x in scandir(path) if isfile(x) and x.name.endswith('.flac')]
    entries = sorted(entries, key=lambda x: x.name)
    if entries:
        root, name = split(path)  # Get directory name and path to parent
        output = str(join(root, name + ' (MP3)'))  # Overwrite files in directory, if it exists
        if not exists(output):
            if verbose:
                logging.info(f'Creating directory: "{output}"...')
            mkdir(output)
        bitrate_str = f'{bitrate}k' if bitrate in [128, 160, 192, 256, 320] else '256k'
        if verbose:
            logging.info(f'Bitrate set to {bitrate_str}.')
        zipped = zip(entries, [AudioSegment.from_file(x.path) for x in entries])
        if verbose:
            logging.info('Copying and converting audio files...')
        for entry, segment in zipped:
            flac_name = entry.name
            mp3_name = re.sub(r'flac$', 'mp3', flac_name)  # Replace extension in name
            tags = mediainfo(entry.path)['TAG']  # Extract non-picture metadata
            if 'comment' in tags and tags['comment'] == 'Cover (front)':
                del tags['comment']
            export_path = join(output, mp3_name)  # Create export path for new MP3 file
            if verbose:
                logging.info(f'Processing "{flac_name}"...')
            segment.export(export_path, format='mp3', bitrate=bitrate_str, tags=tags)
            mp3 = MP3(export_path)  # Create MP3 object to add picture metadata (album art)
            flac = FLAC(entry.path)  # Create FLAC object to extract picture data
            if flac.pictures:
                picture = flac.pictures[0]
                mp3.tags.add(
                    APIC(
                        encoding=0,
                        mime=picture.mime,
                        type=picture.type,
                        data=picture.data
                    )
                )
                mp3.save(v2_version=3)  # Save as ID3v2.3

        # Replace the original folder with the new
        if inplace:
            if delete:
                # Delete FLAC files in original directory
                if verbose:
                    logging.info(f'Deleting FLAC files...')
                for entry in entries:
                    remove(entry.path)
            else:
                # Search for a replacement handle for the FLAC directory and move FLAC files
                flac_dir_name = '.' + str(name.lstrip('.'))
                instance = 2
                if exists(join(root, flac_dir_name)):
                    flac_dir_name += f' ({instance})'
                while exists(join(root, flac_dir_name)):
                    instance += 1
                    flac_dir_name = re.sub(r'\(.\)$', f'({instance})', flac_dir_name)
                flac_dir = str(join(root, flac_dir_name))
                mkdir(flac_dir)
                if verbose:
                    logging.info(f'Moving FLAC files to "{flac_dir}"...')
                for entry in entries:
                    move(entry.path, join(flac_dir, entry.name))
            # Move MP3 files into original directory
            if verbose:
                logging.info(f'Moving all content in MP3 directory to {path}...')
            for entry in scandir(output):
                move(entry.path, path)
            rmtree(output)
            logging.info(f'Finished! New files can be found in "{path}".')
        else:
            logging.info(f'Finished! New files can be found in "{abspath(output)}".')
    else:
        logging.warning('No FLAC files found. Operation finished.')


@click.command()
@click.option('-b', '--bitrate', default=256, help='Bitrate of the outputted files. default: 256')
@click.option('-v', '--verbose', is_flag=True, help='Verbose mode.')
@click.option('-i',
              '--inplace',
              is_flag=True,
              help='Replace old files with new files. If old files are not deleted, they are placed in a folder with '
                   'the same name preceeded by a ".". Automatically set by --delete.'
              )
@click.option('-d', '--delete', is_flag=True, help='Delete old FLAC files. Automatically sets --inplace.')
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True))
def flac_to_mp3_cli(path: PathLike | str,
                    bitrate: int = 256,
                    verbose: bool = False,
                    inplace: bool = False,
                    delete: bool = False):
    """
    A command line tool for converting FLAC files to MP3.
    For a given directory, creates a folder of MP3 copies of all FLAC files
    """
    flac_to_mp3(path, bitrate, verbose, inplace, delete)


if __name__ == '__main__':
    pass
