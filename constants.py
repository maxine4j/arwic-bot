import os

LEVEL_DEV = 5
LEVEL_OWNER = 4
LEVEL_ADMIN = 3
LEVEL_MOD = 2
LEVEL_USER = 1
LEVEL_EVERYONE = 0

COLOR_YOUTUBE_RED = 0xcd201f
ICON_YOUTUBE = "https://www.youtube.com/yts/img/favicon_144-vflWmzoXw.png"

DOWNLOAD_DIR = "/tmp/arwicbot/"
if not os.path.isdir(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

DATA_DIR = "data/"
DATA_EXT = ".db"
if not os.path.isdir(DATA_DIR):
    os.makedirs(DATA_DIR)

LOG_DIR = "logs/"
LOG_EXT = ".log"
if not os.path.isdir(LOG_DIR):
    os.makedirs(LOG_DIR)
