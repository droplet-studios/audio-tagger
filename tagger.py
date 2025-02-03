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
        self.title = ''
        self.artist = ''
        self.cover = None

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
    target_folders = []

    directory_tree.sort() # sort names of albums
    for group in directory_tree:
        group[2].sort() # sort songs within the albums

    for (parent_directory, folders, files) in directory_tree:
        for file in files:
            if os.path.splitext(file)[1] == '.mp3':
                if parent_directory not in target_folders:
                    target_folders.append(parent_directory)
    process_albums(target_folders)

def process_albums(target_folders):
    folder_names = [folder.split('/')[-1:][0] for folder in target_folders] # get name of folder without rest of path

    folders = list(zip(target_folders, folder_names)) # make tuple with the full file path and the folder name itself 

    index = 0
    for folder in folders:
        print(f'The folder named \'{folder[1]}\' is selected.')
        print('Options: (c)ontinue (enter), (r)ename, (s)kip')
        while True:
            response = input('process> ').lower()
            if response == 'c' or response == 'continue' or response == '':
                get_album_info(folder[1])
                break
            elif response == 'r' or response == 'rename':
                new_name = rename_folder(folder)
                folders[index] = new_name
                get_album_info(folder[1])
                break
            elif response == 's' or response == 'skip':
                break
            else:
                print('Invalid option. Please try again.')
        index += 1

def get_album_info(name):
    print('Searching for album metadata...')

    url = 'https://musicbrainz.org/ws/2/release'
    try:
        response = requests.get(url=url,
                                params={'query': 'release:' + name, 'fmt': 'json'},
                                headers={'User-Agent': 'AudioTagger/1.0 (jellymanlvspizza@gmail.com)'})
        
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        print(http_err)
    except Exception as err:
        print(err)
    print(response.url)
    response = response.json()
    selected = check_info(response['releases'])
    
    if selected:
        print('Searching for album cover art...')
        mbid = selected['id']
        try:
            response = requests.get(f'https://coverartarchive.org/release/{mbid}/')
            response.raise_for_status()

            image = requests.get(response['images'][0]['image'])
            image.raise_for_status()

        except requests.exceptions.HTTPError as http_err:
            print(http_err)
        except Exception as err:
            print(err)

        album = Album()
        album.title = selected['title']
        album.artist = selected['artist-credit'][0]['name']
        album.cover = image
        
def rename_folder(folder):
    print('Enter a new name.')
    while True:
        new_name = input('> ')
        if '/' in new_name:
            pass
        else:
            break
        print('The name cannot include the character \'/\'.')

    new_path = '/'.join(folder[0].split('/')[:-1]) + '/' + new_name # create string with new path to renamed folder

    try:
        os.rename(folder[0], new_path)
        return (new_path, new_name)
    except:
        print('Unable to change folder name. Continuing...')
        return folder

def check_info(albums, index=0):
    print(albums)
    print(index)
    print('The following match has been found:')
    print(f'Album title: {albums[index]['title']}')
    print(f'Artist: {albums[index]['artist-credit'][0]['name']}')
    print('Options: (s)elect (enter), (n)ext, (p)revious, (m)anual metadata input')
    while True:
        response = input('check> ').lower()
        if response == 's' or response == 'select' or response == '':
            selection = albums[index]
            break
        elif (response == 'n' or response == 'next') and index < len(albums) - 1:
            check_info(albums, index+1)
        elif (response == 'p' or response == 'previous') and index > 0:
            check_info(albums, index-1)
        elif response == 'm' or response == 'manual metadata input':
            selection = None
            break
        else:
            print('Invalid option. Please try again.')
    return selection

def check_metadata():
    pass

start()