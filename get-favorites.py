import os
import json
from hashlib import sha1
import re
import pprint
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "windows_user", help="Windows Username. Used to build necessary paths"
)
args = parser.parse_args()


# My paths assume you are using WSL -- change accordingly if running on Windows Host
PLAYER_DAT = f"/mnt/c/Users/{args.windows_user}/AppData/LocalLow/Hyperbolic Magnetism/Beat Saber/PlayerData.dat"
SONG_DIR = "/mnt/c/Program Files (x86)/Steam/steamapps/common/Beat Saber/Beat Saber_Data/CustomLevels"


def get_song_hashes():

    song_hashes = {}
    for dirpath, dirnames, filenames in os.walk(SONG_DIR):
        _, song_name = os.path.split(dirpath)

        # Skip the top-level-directory
        if dirpath == SONG_DIR:
            continue

        # Read info.date from song and collect the _beatmapFileName entries
        beatMapFileNames = []
        with open(os.path.join(dirpath, "info.dat"), "r") as f:
            info = f.read()
            info_json = json.loads(info)

            for beatmap_set in info_json["_difficultyBeatmapSets"]:
                for difficulty_beatmap in beatmap_set["_difficultyBeatmaps"]:
                    beatMapFileNames.append(difficulty_beatmap["_beatmapFilename"])

        # Hash info.dat...
        m = sha1()
        with open(os.path.join(dirpath, "info.dat"), "rb") as f:
            m.update(f.read())

        # and then the corresponding beatmap files
        for bmap_file in beatMapFileNames:
            with open(os.path.join(dirpath, bmap_file), "rb") as f:
                m.update(f.read())

        digest = m.hexdigest()
        song_hashes[digest.upper()] = song_name

    return song_hashes


def get_favorite_songs():

    # Parse Player Data
    player_data = ""
    with open(PLAYER_DAT, "r") as f:
        player_data = f.read()

    player_data = json.loads(player_data)
    return player_data["localPlayers"][0]["favoritesLevelIds"]


def replace_missing_titles(favorite_songs, song_hashes):

    # Create lists of missing and not-missing info songs
    info_missing = re.compile("custom_level_[A-F\d]+$")
    missing_info = []
    has_info = []
    for song in favorite_songs:
        if info_missing.match(song):
            missing_info.append(song)
        else:
            has_info.append(song)

    # Using song_hashes get the info for missing-info songs
    missing_songs = []
    for song in missing_info:
        song_hash = song.split("_")[2]
        missing_songs.append(song_hashes[song_hash])

    return has_info + missing_songs


if __name__ == "__main__":
    song_hashes = get_song_hashes()
    favorite_songs = get_favorite_songs()
    song_list = replace_missing_titles(favorite_songs, song_hashes)

    print(*song_list, sep=os.linesep)
