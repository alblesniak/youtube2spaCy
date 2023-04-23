import argparse
import yt_dlp
import logging
from tqdm import tqdm
import pandas as pd
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_videos(channel_url=None, keyword=None, playlist_url=None):
    """
    Extracts video URLs from the provided YouTube channel, playlist, and keyword.

    :param channel_url: The URL of the YouTube channel.
    :param keyword: The keyword to filter video titles.
    :param playlist_url: The URL of the YouTube playlist.
    :return: A list of extracted video URLs.
    """
    ydl_opts = {
        'extract_flat': 'in_playlist',
        'ignoreerrors': True,
    }

    video_urls = []

    # Both keyword and playlist are provided
    if playlist_url and keyword:
        ydl_opts['playlist_items'] = 'all'
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            for video in tqdm(info['entries'], desc="Extracting videos with keyword from playlist"):
                if keyword.lower() in video['title'].lower():
                    video_urls.append(video['webpage_url'])

    # Only playlist is provided
    elif playlist_url and not keyword:
        ydl_opts['playlist_items'] = 'all'
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            for video in tqdm(info['entries'], desc="Extracting videos from playlist"):
                video_urls.append(video['webpage_url'])

    # Only channel_url and keyword are provided
    elif channel_url and keyword:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            for video in tqdm(info['entries'], desc="Extracting videos with keyword from channel"):
                if keyword.lower() in video['title'].lower():
                    video_urls.append(video['webpage_url'])

    return video_urls


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Extract video URLs from YouTube using yt-dlp')
    parser.add_argument('-c', '--channel_url', type=str,
                        help='The URL of the YouTube channel')
    parser.add_argument('-k', '--keyword', type=str,
                        help='Keyword to filter video titles')
    parser.add_argument('-p', '--playlist_url', type=str,
                        help='The URL of the YouTube playlist')

    args = parser.parse_args()

    logger.info("Extracting video URLs...")
    video_urls = extract_videos(
        args.channel_url, args.keyword, args.playlist_url)

    if args.channel_url:
        with yt_dlp.YoutubeDL({'ignoreerrors': True}) as ydl:
            channel_info = ydl.extract_info(args.channel_url, download=False)
            channel_name = channel_info['title']

        playlist_name = None
        if args.playlist_url:
            with yt_dlp.YoutubeDL({'ignoreerrors': True}) as ydl:
                playlist_info = ydl.extract_info(
                    args.playlist_url, download=False)
                playlist_name = playlist_info['title']

        metadata = []
        for url in tqdm(video_urls, desc="Extracting metadata"):
            with yt_dlp.YoutubeDL({'ignoreerrors': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                metadata.append({
                    'title': info['title'],
                    'url': info['webpage_url'],
                    'duration': info['duration'],
                    'upload_date': info['upload_date'],
                    'view_count': info['view_count'],
                    'like_count': info['like_count'],
                    'dislike_count': info['dislike_count'],
                    'comment_count': info['comment_count'],
                    'playlist_name': playlist_name,
                })

        df = pd.DataFrame(metadata)
        data_folder_path = f"data/{channel_name}"
        os.makedirs(data_folder_path, exist_ok=True)
        df.to_excel(f"{data_folder_path}/metadata.xlsx", index=False)

        logger.info(f"Saved metadata to {data_folder_path}/metadata.xlsx")

        # Download audio files
        audio_folder_path = f"{data_folder_path}/audio"
        os.makedirs(audio_folder_path, exist_ok=True)

        ydl_options = {
            'format': 'bestaudio/best',
            'outtmpl': f'{audio_folder_path}/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'merge_output_format': 'mp3',  # Ensure the output file is in mp3 format
            'retries': 10,  # Number of times to retry the download in case of errors
            'fragment_retries': 10,  # Number of times to retry a fragment in case of errors
            'ignoreerrors': True,  # Continue downloading the next video in case of errors
        }

        with yt_dlp.YoutubeDL(ydl_options) as ydl:
            for url in tqdm(video_urls, desc="Downloading audio"):
                ydl.download([url])

        logger.info(f"Downloaded audio files to {audio_folder_path}")

    else:
        print("No channel URL provided. Please provide a channel URL.")
