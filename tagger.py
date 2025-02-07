# Audio Tagger
# Cooper Olsen, Droplet Studios

import os
import sys
import importlib

for module in ['eyed3', 'requests', 'PIL']:
    """ Tries to import required external modules.

    eyed3 is used for reading and adding ID3 metadata to mp3 files
    requests is used for querying the Music Brainz database and downloading cover art
    Pillow is used to convert cover art to JPEG

    This is run automatically.
    """

    try:
        lib = importlib.import_module(module) # assign imported module to variable temporarily
    except ImportError:
        print(f'This program requires having the {module} module installed.')
        print('Exiting...')
        sys.exit()
    else:
        globals()[module] = lib # have to add imported module to global variables to be able to reference it

class Album():
    """ Album class used to store info about each selected album """

    def __init__(self):
        self.path = ''
        self.folder_name = ''
        self.songs = []
        self.title = ''
        self.artist = ''
        self.cover = ''
        self.mbid = ''

albums = [] # store albums found in initial search

# global variable to track number of albums and tracks where metadata was added to in one run
album_count = 0 
track_count = 0

def start():
    """ Presents welcome message and handles initial directory selection.

    Function is called by main() and takes no arguments. It doesn't return any values. 
    It calls the search() function and passes the directory tree of the selected folder.
    """

    os.system('cls' if os.name == 'nt' else 'clear')
    print('Welcome to Audio Tagger! \nTo get started, please enter the directory containing mp3 files to be tagged, organised into folders by albums.')
    while True:
        try:
            # path = input('> ')
            path = '/Users/cooper/Downloads/ipod'
            # remove quotes around file path when dragging folder into command line
            if path[:1] == '\'' and path[-1:] == '\'':
                path = path[1:-1] 
            directory_tree = list(os.walk(path))
            if directory_tree == []:
                raise FileNotFoundError
            break
        except FileNotFoundError:
            print('Directory not found. Please try another directory.')
    search(directory_tree)

def search(directory_tree):
    """ Searches the selected directories for folders with mp3 files in them and creates album objects for each class.
    Album properties are set to match the path of the folder and mp3 files contained in it.

    Function is called by start() and takes a single argument of a directory tree in the form of a list (returned by os.walk().
    It does not return any values. It calls process_albums() automatically.
    """

    directory_tree.sort() # sort names of albums
    for group in directory_tree:
        group[2].sort() # sort songs within the albums
    for (parent_directory, folders, files) in directory_tree: # each item in list is a tuple
        for file in files:
            # check file extension
            if os.path.splitext(file)[1] == '.mp3':
                # create album object
                albums.append(Album())
                albums[-1].path = parent_directory
                albums[-1].songs = [parent_directory + '/' + file for file in files if os.path.splitext(file)[1] == '.mp3']
                albums[-1].folder_name = parent_directory.split('/')[-1:][0] # get name of folder without rest of path
                break
    process_albums()

def has_metadata(album):
    """ Checks mp3 files in given folder for preexisting metadata.

    Function is called by process_albums() and takes a single argument of an album object.
    It returns False if any of the files in the folder doesn't have metadata for either album name or artist.
    It returns True otherwaise.
    """

    for track in album.songs:
        try:
            file = eyed3.load(track)
            if file.tag.album == None:
                return False
            elif file.tag.album_artist == None:
                return False
        except Exception as err:
            print(err)
            return False
    return True

def process_albums():
    """ Gets user input on desired actions to take with the album. 
    It provides the general framework for searching and adding metadata.

    Function is called by search() and takes no argument. It returns no value.
    It calls the has_metadata() album, as well as get-album_info() and rename_folder() functions.
    It also calls add_metadata() if the user doesn't select to skip the album.
    """

    for album in albums:
        print(f'The folder named \'{album.folder_name}\' is selected.')
        if has_metadata(album):
            print('Metadata is already detected on the tracks of this album. Skipping...')
        else:
            print('The folder name will be used to query the MusicBrainz for album info.')
            print('Options: (c)ontinue (enter), (r)ename, (s)kip')
            while True:
                response = input('> ').lower()
                if response == 'c' or response == 'continue' or response == '':
                    get_album_info(album)
                    break
                elif response == 'r' or response == 'rename':
                    rename_folder(album)
                    break
                elif response == 's' or response == 'skip':
                    break
                else:
                    print('Invalid option. Please try again.') # performs input validation
            if response != 's' and response != 'skip':
                add_metadata(album)
        
def get_album_info(album):
    """ Gets the album info for the selected album from the Music Brainz and Cover Art Archive databases.
    Metadata is added to the album object (but not to ID3 metadata, which is done in add_metadata() function).

    The function is called by process_albums() and takes an argument of the album object.
    The function calls rename_folder() or maual_input() based on the user selection of choices.
    It always calls check_info() unless the search yields no results.
    """

    print('Searching for album metadata...')
    url = 'https://musicbrainz.org/ws/2/release'
    try:
        response = requests.get(url=url,
                                params={'query': 'release:' + album.folder_name, 'fmt': 'json'}, # query in specific format
                                headers={'User-Agent': 'AudioTagger/1.0 (jellymanlvspizza@gmail.com)'}) # User Agent header (required)
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error when getting album metadata: {http_err}')
    response = response.json()
    if len(response['releases']) != 0:
        selected = check_info(response['releases']) # this saves return value of check_info as a variable
    else:
        print('No match found. Please try again with a different name.')
        selected = 'redo'
    # change actions based on results of check info
    if selected == 'redo':
        rename_folder(album)
    elif selected == 'manual':
        manual_input(album)
    else:
        # add metadata to corresponding album object
        album.title = selected['title']
        album.artist = selected['artist-credit'][0]['name']
        print('Searching for album cover art...')
        mbid = selected['id'] # MBID required to seach for album's cover art.
        # Unless alternative action selected, search for cover art
        try:
            response = requests.get(f'https://coverartarchive.org/release/{mbid}/')
            response.raise_for_status()
            response = response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f'HTTP error when searching for cover art: {http_err}')
        if len(response['images']) != 0:
            try:
                print('Downloading cover art...')
                image = requests.get(response['images'][0]['image'])
                image.raise_for_status()
                print('Saving cover art...')
                # required to read as binary becasue that is the response object is in
                with open(album.path + '/cover.jpg', 'wb') as cover_file:
                    cover_file.write(image.content)
                album.cover = album.path + '/cover.jpg'
                print(f'Cover art saved to {album.cover}')
            except requests.exceptions.HTTPError as http_err:
                print(f'HTTP error when downloading cover art: {http_err}')
        else:
            print('No album cover art found. Skipping...')
            album.cover = None
        
def rename_folder(album):
    """ Renames selected folder that album is in.

    This album takes one argument of an album object. 
    It is (optionally) called by process_albums() and/or get_album_info() and it returns no values.
    This function automatically calls get_album_info().
    """

    print('Enter a new name.')
    while True:
        new_name = input('> ')
        if '/' in new_name:
            pass
        else:
            break
        print('The name cannot include the character \'/\'.')
    # filter out backlashes that can interfere with file paths
    new_path = '/'.join(album.path.split('/')[:-1]) + '/' + new_name # create string with new path to renamed folder
    try:
        os.rename(album.path, new_path) # rename folder itselft
        album.folder_name = new_name
        album.path = new_path
    except:
        print('Unable to change folder name. Continuing...')
    get_album_info(album)

def check_info(query, index=0):
    """ Display album and artist information that will be added to mp3 files.
    Handles user input to decide next action in program.

    This function takes an argument of the album object, as well as an index keeping track of where in list the selected album is.
    It is called by get_album_info(). It returns the album info that has been selected out of the search results.
    It calls the check_info() function (itself) recursively, increasing or decreasing the index to traverse through results.
    """

    print('The following match has been found:')
    print(f'Album title: {query[index]['title']}')
    print(f'Artist: {query[index]['artist-credit'][0]['name']}')
    print('Options: (s)elect (enter), (n)ext, (p)revious, (r)edo search, (m)anual metadata input')
    while True:
        response = input('> ').lower()
        if response == 's' or response == 'select' or response == '':
            return query[index]
        elif (response == 'n' or response == 'next') and index < len(query) - 1:
            return check_info(query, index+1)
        elif (response == 'p' or response == 'previous') and index > 0:
            return check_info(query, index-1)
        elif response == 'r' or response == 'redo search':
            return 'redo'
        elif response == 'm' or response == 'manual metadata input':
            return 'manual'
        else:
            print('Invalid option. Please try again.')

def manual_input(album):
    """ Handles manual entry of metadata and input validation (including cover image selection).
    Metadata is added to the album object (but not to ID3 metadata, which is done in add_metadata() function).

    Function takes argument of album object. It is (optionally) called by process_albums(). It returns no values. 
    """

    while True:
        title = input('Enter the title of the album:\n> ')
        if title.replace(' ', '') != '': # check for empty string
            album.title = title
            break
    while True:
        artist = input('Enter the artist of the album:\n> ')
        if artist.replace(' ', '') != '':
            album.artist = artist
            break
    while True:
        image_path = input('Enter the path to the album cover image:\n> ')
        # remove apostrophes from file path when dragging into terminal
        if image_path[:1] == '\'' and image_path[-1:] == '\'':
                image_path = image_path[1:-1]
        # check if image can be opened (to check if file path is valid, and if corrected filetype selected)
        try:
            image = PIL.Image.open(image_path)
            break
        except OSError as err:
            print('The image path is invalid.')
            print(err)
    path, ext = os.path.splitext(image_path) # check extension on cover image file
    # convert file to JPEG if necessary
    if ext != '.jpg' and ext != '.jpeg':
        print('Converting file to JPEG...')
        try:
            image = image.convert('RGB') # image must convert to RGB before converting to JPEG
            image.save(album.path + '/cover.jpg', 'JPEG')
        except OSError:
            print('The image could not be converted to JPEG.')
    else:
        shutil.copy(image_path, album.path + '/cover.jpg') # copy image file into selected album directory
    album.cover = album.path + '/cover.jpg'

def add_metadata(album):
    """ Adds ID3 metadata from album object to mp3 tracks in album.

    This function takes one argument of the album object, and returns no values.
    It is called in the final part of the process_albums() function (unless the album is skipped altogether).
    """

    # global variables for counts (state accessible from any function)
    global album_count
    global track_count
    print('Adding metadata to album tracks...')
    track_num = 0 # this counter is reset each album in one program runs
    for track in album.songs:
        track_num += 1
        try:
            file = eyed3.load(track)
            file.tag.album = album.title
            file.tag.album_artist = album.artist
            file.tag.track_num = track_num
            if album.cover != None:
                file.tag.images.set(3, open(album.cover, 'rb').read(), 'image/jpeg') # open image as binary to add it as cover art
            file.tag.save()
        except Exception as err:
            print(f'Unable to save metadata on the track \'{track}\': {err}')
    print(f'Album metadata was written to the tracks in the album \'{album.title}\'. To edit metadata further, please use another program such as iTunes. Press enter to continue.')
    input()
    # these values are changed globally
    album_count += 1
    track_count += track_num

def finish():
    """ Displays closing message before program exit.

    This function is called in the main() function.
    """

    print(f'Thank you for using Audio Tagger. Metadata has been added to {track_count} tracks in {album_count} albums.')

def main():
    """ Starts and finishes the program by calling start() and finish(). Handles quitting program with Ctrl + C. """

    try:
        start()
    except KeyboardInterrupt:
        print('')
        finish()
        print('Exiting...')
        sys.exit()
    else:
        finish()

if __name__ == '__main__':
    main()