import argparse
from os.path import abspath, exists, isdir

from audiotagtools.scripts import find_music_dirs, get_logger, format_multipart_tags


def format_all_multipart_tags(path: str, old: str = '/', new: str = '|', verbose: bool = False):
    """
    Edits the tags of MP3 files in a directory and its subdirectories.
    :param verbose:
    :param path:
    :param old:
    :param new:
    :return:
    """
    # Create logger
    logger = get_logger(filename='tagsedit.log')

    # Check path
    if not path:
        path = input('Please provide a directory: ')
    path = abspath(path)
    if exists(path) and isdir(path):
        logger.info(f'Searching for MP3 files in "{path}"...')
        mp3_dirs = find_music_dirs(path, filetype='mp3')
        for d in mp3_dirs:
            logger.info(f'Formatting tags in "{d}"...')
            for tag, case in ('artist', None), ('composer', None), ('genre', 'title'):
                logger.info(f'Formatting "{tag}" tag...')
                try:
                    format_multipart_tags(d, tag, old, new, case, verbose, logger)
                except Exception as e:
                    logger.info(f'Exception {e.__class__}: {e}.\nSkipping this directory.')
        logger.info('Finished!')
    elif exists(path):
        logger.warning(f'"{path}" is not a directory.')
    else:
        logger.warning(f'"{path}" does not exist.')


def run():
    parser = argparse.ArgumentParser(
        description='Edits the tags of MP3 files in a directory and its subdirectories.'
    )

    # Commands
    parser.add_argument('path', help='The root directory to start searching in.')
    parser.add_argument('-o', '--old', default='/', help='The original delimiter for the tags.')
    parser.add_argument('-n', '--new', default='|', help='The new delimiter for the tags.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose mode.')

    args = parser.parse_args()
    if args:
        format_all_multipart_tags(args.path, args.old, args.new, args.verbose)


if __name__ == '__main__':
    run()
