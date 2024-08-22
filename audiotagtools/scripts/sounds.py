import logging
from os import scandir, DirEntry, mkdir
from os.path import join, abspath, exists, isdir, split
from typing import List, TypedDict

import click
from pydub import AudioSegment
from pydub.utils import mediainfo

SegmentDict = TypedDict('SegmentDict', {'direntry': DirEntry, 'segment': AudioSegment})
"""
A TypedDict that keeps the original audio file information tethered to the AudioSegment it generates
"""


def create_segments(files: List[DirEntry]):
    """
    Creates a list of SegmentDict objects
    :param files:
    :return:
    """
    segments = []
    for de in files:
        segment_dict = SegmentDict(direntry=de, segment=AudioSegment.from_mp3(de.path))
        segments.append(segment_dict)
    return segments


def adjust_volume_level(segments: List[SegmentDict], adjustment: int = 10):
    """
    Adjusts the volume of each AudioSegment up or down
    :param segments:
    :param adjustment:
    :return:
    """
    for i in range(len(segments)):
        segments[i]['segment'] += adjustment
    return segments


def adjust_volume(path, levelchange=10, inplace=False, verbose=False):
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    msg = []
    if not verbose:
        logging.info('Starting volume adjustment...')
    working = abspath(path)
    if not exists(working):
        msg.append(f'Directory "{working}" does not exist.')
    elif not isdir(working):
        msg.append(f'"{working}" is not a directory.')
    else:
        if not inplace:
            components = split(working)
            output = join(components[0], components[1] + " (edited)" if components[1] else "edited")
        else:
            output = working
        if verbose:
            logging.info(f'Scanning directory: "{working}"')
        dir_objs = scandir(working)
        audio_files = list([x for x in dir_objs if x.is_file() and x.name[-4:].lower() == '.mp3'])
        if audio_files:
            if verbose:
                logging.info(f'{len(audio_files)} MP3 files found. Proceeding...')
            if not exists(output):
                if verbose:
                    info = f'Creating directory: "{output}"'
                    logging.info(info)
                mkdir(output)
            elif verbose:
                info = f'Editing files in "{output}".' if inplace else (f'"{output}" already exists. Copying over any '
                                                                        f'existing files.')
                logging.info(info)
            seg_objs = create_segments(audio_files)
            if verbose:
                info = ''
                if not levelchange:
                    info = 'No volume adjustment.'
                else:
                    info += (f'{"Increasing" if levelchange > 0 else "Decreasing"} volume of all files by '
                             f'{abs(levelchange)} dB.')
                logging.info(info)
            for seg_dict in seg_objs:
                t = seg_dict['direntry'].name
                m = mediainfo(seg_dict['direntry'].path)['TAG']
                if verbose:
                    logging.info(f'Processing "{t}" ...')
                seg_dict['segment'] += levelchange
                seg_dict['segment'].export(join(output, t), tags=m)

            # Create a description text file
            if verbose:
                logging.info('Creating "description.txt" ...')
            file_msg = f'Volume adjusted for {len(audio_files)} files.'
            if levelchange == 0:
                file_msg += ' No volume edits.'
            elif levelchange > 0:
                file_msg += f' Volume increased by {levelchange} dB.'
            else:
                file_msg += f' Volume decreased by {abs(levelchange)} dB.'
            with open(join(output, 'description.txt'), 'w') as f:
                f.write(file_msg)
            if verbose:
                info = f' New files can be found in "{output}".' if not inplace else ''
                logging.info(f'Finished!{info}')
            else:
                logging.info('Finished!')
        else:
            msg.append('No MP3 files found.')
    if msg:
        for m in msg:
            logging.warning(m)
        logging.warning('Aborted.')


@click.command()
@click.option('-i', '--inplace', default=False, is_flag=True, help='Directly edit files in directory.')
@click.option('-l', '--levelchange', default=10, help='Number of dB to increase volume by.')
@click.option('-v', '--verbose', default=False, is_flag=True, help='Verbose mode.')
@click.argument('path')
def increase_volume(path, levelchange, inplace, verbose):
    """
    Increases the volume of all mp3 files in a directory.
    """
    adjust_volume(path, levelchange, inplace, verbose)


@click.command()
@click.option('-i', '--inplace', default=False, is_flag=True, help='Directly edit files in directory.')
@click.option('-l', '--levelchange', default=10, help='Number of dB to decrease volume by.')
@click.option('-v', '--verbose', default=False, is_flag=True, help='Verbose mode.')
@click.argument('path')
def decrease_volume(path, levelchange, inplace, verbose):
    """
    Decreases the volume of all mp3 files in a directory.
    """
    adjust_volume(path, -1 * levelchange, inplace, verbose)


if __name__ == '__main__':
    pass
