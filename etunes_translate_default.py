import mutagen.id3 as id3

def get_id3_str(dictlike, key):
    try:
        return str(dictlike[key])
    except KeyError:
        return None

def get_id3_fraction(dictlike, key):
    try:
        frac = str(dictlike[key])
        if '/' in frac:
            pivot = frac.index('/')
            num = frac[:pivot]
            den = frac[pivot+1:]
        else:
            num = frac
            den = None
        return num, den
    except KeyError:
        return None, None

def read_basic_metadata_from_mutagen(f):
    disk, total_disks = get_id3_fraction(f, 'TPOS')
    track, total_tracks = get_id3_fraction(f, 'TRCK')
    return {
        'album-name': get_id3_str(f, 'TALB'),
        'artist': get_id3_str(f, 'TPE1'),
        'album-artist': get_id3_str(f, 'TPE2'),
        'comment': get_id3_str(f, 'COMM::eng'),
        'composer': get_id3_str(f, 'TCOM'),
        'disk': disk,
        'sort-artist': get_id3_str(f, 'TSOA'),
        'sort-title': get_id3_str(f, 'TSOT'),
        'title': get_id3_str(f, 'TIT2'),
        'total-disks': total_disks,
        'total-tracks': total_tracks,
        'track': track,
        'year': get_id3_str(f, 'TDRC'),
    }

def add_id3_tag(f, constructor, contents):
    f.add(constructor(text=metadata))

def write_basic_metadata_to_mutagen(f, metadata):
    disk_and_total = (metadata.get('disk', '') + '/' +
                      metadata.get('total-disks', ''))
    track_and_total = (metadata.get('track', '') + '/' +
                       metadata.get('total-tracks', ''))
    def add_id3_tag(constructor, key):
        try:
            f.add(constructor(text=metadata[key]))
        except KeyError:
            pass
    def add_id3_text_frame(name, key):
        try:
            f.add(id3.TextFrame(text=metadata[key]))
        except KeyError:
            pass
    add_id3_tag(id3.TALB, 'album-name')
    add_id3_tag(id3.TPE1, 'artist')
    add_id3_tag(id3.TPE2, 'album-artist')
    add_id3_tag(id3.COMM, 'comment')
    add_id3_tag(id3.TCOM, 'composer')
    if disk_and_total != '/':
        f.add(id3.TPOS(text=disk_and_total))
    add_id3_text_frame('TSOA', 'sort-artist')
    add_id3_text_frame('TSOT', 'sort-title')
    add_id3_tag(id3.TIT2, 'title')
    add_id3_tag(id3.TDRC, 'year')
    f.save()

def read_embedded_metadata(filename):
    return read_basic_metadata_from_mutagen(id3.ID3(filename))

def write_embedded_metadata(filename, metadata):
    return write_basic_metadata_to_mutagen(id3.ID3(filename), metadata)
