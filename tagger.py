# Audio Tagger
# Cooper Olsen, Droplet Studios

import os
import sys
import importlib
import urllib
import urllib.parse

# these should be removed when not testing
import eyed3
import requests

for module in ['eyed3', 'requests']:
    try:
        lib = importlib.import_module(module)
    except ImportError:
        print(f'This program requires having the {module} module installed.')
        print('Exiting...')
        sys.exit()
    else:
        globals()[module] = lib

class Album():
    def __init__(self):
        self.path = ''
        self.folder_name = ''
        self.songs = []
        self.title = ''
        self.artist = ''
        self.cover = None
        self.mbid = ''

albums = []

def start():
    os.system('cls' if os.name == 'nt' else 'clear')

    print('Welcome to Audio Tagger! \nTo get started, please enter the directory containing mp3 files to be tagged, organised into folders by albums.')

    while True:
        try:
            # path = input('> ')
            path = '/Users/cooper/Downloads/ipod'
            if path[:1] == '\'' and path[-1:] == '\'':
                path = path[1:-1] # remove quotes around file path when dragging folder into command line
            directory_tree = list(os.walk(path))
            if directory_tree == []:
                raise FileNotFoundError
            break
        except FileNotFoundError:
            print('Directory not found. Please try another directory.')

    search(directory_tree)

def search(directory_tree):
    directory_tree.sort() # sort names of albums
    for group in directory_tree:
        group[2].sort() # sort songs within the albums

    for (parent_directory, folders, files) in directory_tree:
        for file in files:
            if os.path.splitext(file)[1] == '.mp3':
                albums.append(Album())
                albums[-1].path = parent_directory
                albums[-1].songs = [file for file in files if os.path.splitext(file)[1] == '.mp3']
                albums[-1].folder_name = parent_directory.split('/')[-1:][0] # get name of folder without rest of path
                break
    
    process_albums()

def process_albums():
    for album in albums:
        print(f'The folder named \'{album.folder_name}\' is selected.')
        print('This name will be used to query the MusicBrainz for album info.')
        print('Options: (c)ontinue (enter), (r)ename, (s)kip')
        while True:
            response = input('process> ').lower()
            if response == 'c' or response == 'continue' or response == '':
                get_album_info(album)
                break
            elif response == 'r' or response == 'rename':
                rename_folder(album)
                break
            elif response == 's' or response == 'skip':
                break
            else:
                print('Invalid option. Please try again.')

def get_album_info(album):
    print('Searching for album metadata...')

    url = 'https://musicbrainz.org/ws/2/release'
    try:
        response = requests.get(url=url,
                                params={'query': 'release:' + album.folder_name, 'fmt': 'json'},
                                headers={'User-Agent': 'AudioTagger/1.0 (jellymanlvspizza@gmail.com)'})
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        print(http_err)
    except Exception as err:
        print(err)

    print(response.url)
    response = response.json()
    selected = check_info(response['releases'])
    print(selected)
    if selected == 'redo':
        rename_folder(album)
    elif selected == 'manual':
        manual_input(album)
    else:
        album.title = selected['title']
        album.artist = selected['artist-credit'][0]['name']
        print('Searching for album cover art...')
        mbid = selected['id']
        try:
            response = requests.get(f'https://coverartarchive.org/release/{mbid}/')
            response.raise_for_status()
            response = response.json()
            image = requests.get(response['images'][0]['image'])
            image.raise_for_status()
            album.cover = image
        except requests.exceptions.HTTPError as http_err:
            print(http_err)
        except Exception as err:
            print(err)
        
def rename_folder(album):
    print('Enter a new name.')
    while True:
        new_name = input('> ')
        if '/' in new_name:
            pass
        else:
            break
        print('The name cannot include the character \'/\'.')
    new_path = '/'.join(album.path.split('/')[:-1]) + '/' + new_name # create string with new path to renamed folder
    try:
        os.rename(album.path, new_path)
        album.folder_name = new_name
        album.path = new_path
    except:
        print('Unable to change folder name. Continuing...')
    get_album_info(album)

def check_info(query, index=0):
    print('The following match has been found:')
    print(f'Album title: {query[index]['title']}')
    print(f'Artist: {query[index]['artist-credit'][0]['name']}')
    print('Options: (s)elect (enter), (n)ext, (p)revious, (r)edo search, (m)anual metadata input')
    while True:
        response = input('check> ').lower()
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
    pass

def check_metadata():
    pass

start()