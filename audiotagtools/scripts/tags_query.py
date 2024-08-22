import logging

import musicbrainzngs

musicbrainzngs.set_useragent('audiotagtools', '0.5.6', 'koz.moore@gmail.com')

RELEASEGROUP_FIELDS = ('alias, arid, artist, artistname, comment, creditname, primarytype, reid, release, '
                       'releasegroup, releasegroupaccent, releases, rgid, secondarytype, status, tag, type').split(', ')


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
            filename = 'tagging.log'
        filehandler = logging.FileHandler(filename)
        fileformatter = logging.Formatter(fileformat)
        filehandler.setFormatter(fileformatter)
        logger.addHandler(filehandler)
    return logger


def get_artist(artist: str, strict: bool = True, **kwargs):
    key1 = 'artist-list'
    try:
        results = musicbrainzngs.search_artists(query=artist, strict=strict, **kwargs)
    except musicbrainzngs.WebServiceError as err:
        print(f'Request error: {err}')
    else:
        print(f'Number of results: {len(results[key1])}')
        for result in results[key1]:
            for k, v in result.items():
                print(f'{k}: {v}')


def get_release(album: str = '', **kwargs):
    try:
        results = musicbrainzngs.search_releases(query=album, **kwargs)
    except musicbrainzngs.WebServiceError as err:
        print(f'Request error: {err}')
    else:
        print(f'Number of results: {len(results["release-list"])}')
        for result in results['release-list']:
            for k, v in result.items():
                print(f'{k}: {v}')


def get_recording(recording: str = '', **kwargs):
    try:
        results = musicbrainzngs.search_recordings(query=recording, **kwargs)
    except musicbrainzngs.WebServiceError as err:
        print(f'Request error: {err}')
    else:
        key1 = 'recording-list'
        results = [x for x in results[key1] if x['ext:score'] == '100']
        print(f'Number of results: {len(results)}')
        for result in results:
            for k, v in result.items():
                print(f'{k}: {v}')


def get_release_group(**kwargs):
    key = 'release-group-list'
    try:
        results = musicbrainzngs.search_release_groups(**kwargs)
    except musicbrainzngs.WebServiceError as err:
        print(f'Request error: {err}')
    else:
        print(f'Number of results: {len(results[key])}')
        for result in results[key]:
            for k, v in result.items():
                print(f'{k}: {v}')


def get_artist_id(artist: str = '',
                  strict: bool = True,
                  logger: logging.Logger = None,
                  **kwargs):
    """
    Searches MusicBrainz releases for an artist ID.
    :param artist:
    :param strict:
    :param logger:
    :param kwargs:
    :return:
    """
    # Get logger
    if not logger:
        logger = get_logger(usefile=False)

    # Keys for searching results
    key1 = 'artist-list'
    key2 = 'id'

    try:
        logger.info('Searching MusicBrainz artists...')
        results = musicbrainzngs.search_artists(query=artist, strict=strict, **kwargs)
    except musicbrainzngs.WebServiceError as err:
        msg = f'Request error: {err}'
        logger.warning(msg)
    else:  # Process results
        artist_id: str | None = ''
        results = list([x for x in results[key1] if x['ext:score'] == '100'])
        if len(results) > 0:
            artist_id = results[0][key2]
            logger.info(f'Artist ID found: {artist_id}')
        else:
            logger.warning('No matching artist ID found')
        return artist_id


def get_release_id(album: str = '',
                   strict: bool = True,
                   logger: logging.Logger = None,
                   **kwargs):
    """
    Searches MusicBrainz releases for a release ID.
    :param album:
    :param strict:
    :param logger:
    :param kwargs:
    :return:
    """
    # Get logger
    if not logger:
        logger = get_logger(usefile=False)

    # Keys for searching results
    key1 = 'release-list'
    key2 = 'id'

    try:
        logger.info('Searching MusicBrainz releases...')
        results = musicbrainzngs.search_releases(query=album, strict=strict, **kwargs)
    except musicbrainzngs.WebServiceError as err:
        msg = f'Request error: {err}'
        logger.warning(msg)
    else:  # Process results
        release_id: str | None = ''
        results = list([x for x in results[key1] if x['ext:score'] == '100'])
        if len(results) > 0:
            release_id = results[0][key2]
            logger.info(f'Release ID found: {release_id}')
        else:
            logger.warning('No matching release ID found')
        return release_id


def get_release_group_id(album: str = '',
                         artist: str = None,
                         strict: bool = True,
                         country: str = 'US',
                         date: int | str = None,
                         tracks: int = None,
                         logger: logging.Logger = None,
                         **kwargs):
    """
    Searches MusicBrainz releases for a release group id.
    :param album:
    :param artist:
    :param strict:
    :param country:
    :param date:
    :param tracks:
    :param logger:
    :param kwargs:
    :return:
    """
    # Get logger
    if not logger:
        logger = get_logger(usefile=False)

    # Keys for searching results
    key1 = 'release-list'
    key2 = 'release-group'
    key3 = 'id'

    try:
        logger.info('Searching MusicBrainz releases...')
        results = musicbrainzngs.search_releases(query=album, artist=artist, strict=strict, country=country,
                                                 date=date, tracks=tracks, **kwargs)
    except musicbrainzngs.WebServiceError as err:
        msg = f'Request error: {err}'
        logger.warning(msg)
    else:  # Process results
        releasegroup_id: str | None = ''
        results = list([x for x in results[key1] if x['ext:score'] == '100'])
        if len(results) > 0:
            releasegroup_id = results[0][key2][key3]
            logger.info(f'Release group ID found: {releasegroup_id}')
        else:
            logger.warning('No matching release group ID found')
        return releasegroup_id


def get_recording_id(title: str = '',
                     strict: bool = True,
                     logger: logging.Logger = None,
                     **kwargs):
    """
    Searches MusicBrainz releases for a release ID.
    :param title:
    :param strict:
    :param logger:
    :param kwargs:
    :return:
    """
    # Get logger
    if not logger:
        logger = get_logger(usefile=False)

    # Keys for searching results
    key1 = 'recording-list'
    key2 = 'id'

    try:
        logger.info('Searching MusicBrainz recordings...')
        results = musicbrainzngs.search_recordings(query=title, strict=strict, **kwargs)
    except musicbrainzngs.WebServiceError as err:
        msg = f'Request error: {err}'
        logger.warning(msg)
    else:  # Process results
        recording_id: str | None = ''
        results = list([x for x in results[key1] if x['ext:score'] == '100'])
        if len(results) > 0:
            recording_id = results[0][key2]
            logger.info(f'Recording ID found: {recording_id}')
        else:
            logger.warning('No matching recording ID found')
        return recording_id


def get_release_group_genres(releasegroupid: str, logger: logging.Logger = None, **kwargs):
    """
    Given a release group id, searches MusicBrainz for the genre tags associated with a release group
    :param releasegroupid:
    :param logger:
    :param kwargs:
    :return:
    """
    # Get logger, if necessary
    if not logger:
        logger = get_logger(usefile=False)

    # Keys for searching results
    key1 = 'release-group'
    key2 = 'tag-list'
    key3 = 'name'
    try:
        logger.info('Searching MusicBrainz release group IDs...')
        results = musicbrainzngs.get_release_group_by_id(id=releasegroupid, includes=['tags'], **kwargs)
    except musicbrainzngs.WebServiceError as err:
        msg = f'Request error: {err}.'
        logger.warning(msg)
    else:  # Process results
        genres = results[key1][key2]
        genre_list = [x[key3] for x in genres]
        return genre_list


def get_album_data(album: str = '',
                   artist: str = None,
                   tracks: int = None,
                   strict: bool = True,
                   logger: logging.Logger = None,
                   **kwargs):
    """
    Given an artist name, album name, and number of tracks, searches MusicBrainz releases for album data
    :param album:
    :param artist:
    :param tracks:
    :param strict:
    :param logger:
    :param kwargs: 
    :return: 
    """
    # Get logger, if necessary
    if not logger:
        logger = get_logger(usefile=False)

    try:
        results = musicbrainzngs.search_releases(query=album, artist=artist, tracks=tracks, strict=strict, **kwargs)
    except musicbrainzngs.WebServiceError as err:
        msg = f'Request error: {err}.'
        logger.info(msg)
    else:  # Process results
        # Keys
        key1 = 'release-list'

        release_data = {}
        release_id: str | None = ''
        results = list([x for x in results[key1] if x['ext:score'] == '100'])
        if len(results) > 0:
            release_id = results[0]
            logger.info(f'Release found: {release_id}')
        else:
            logger.warning('No matching release group ID found')
        return release_id


if __name__ == '__main__':
    # re_id = get_release_id('Steal This Album', artist='System Of A Down', country='US',)
    # r_id = get_recording_id('More', release='Boston', artist='Boston', reid=re_id, date='1976', tracks=8, country='US')
    # get_recording(reid=re_id, strict=True)
    get_artist('System of a Down')
