import os
import re
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
from youtube_transcript_api import YouTubeTranscriptApi

def scrape_channel_id_and_icon(utube_url_with_channel_name):

    youtube_icon_link = None
    youtube_channel_id = None

    response = requests.get(utube_url_with_channel_name)
    soup = bs(response.text, 'html.parser')

    # Find all anchor tags
    for link in soup.find_all('link', href=True):
        href = link['href']
        if href.startswith('https://yt3.googleusercontent.com'):
            youtube_icon_link = href
        elif href.startswith('https://www.youtube.com/channel'):
            youtube_channel_id = href.replace("https://www.youtube.com/channel/","")

    return youtube_icon_link, youtube_channel_id


def get_video_details(soup):
    title = channel = description = video_id = external_links = None
    data = re.search(r'var ytInitialPlayerResponse = (\{.*?\});', soup.prettify())
    if data:
        data = json.loads(data.group(1))
        video_details = data.get('videoDetails', {})
        title = video_details.get('title')
        channel = video_details.get('author')
        description = video_details.get('shortDescription')
        video_id = video_details.get('videoId')
        external_links = re.findall(r'(https?://\S+)', description)
    return title, channel, description, video_id, external_links


def scrape_youtube(video_ids):
    infos = {
        'title': [],
        'channel': [],
        'description': [],
        'video_id': [],
        'external_link': [],
        'transcript':[]
    }
    for video_id in video_ids:

        transcript = get_single_utube_transcript(video_id)

        url = f'https://www.youtube.com/watch?v={video_id}'
        response = requests.get(url)
        soup = bs(response.text, 'html.parser')
        video_details = get_video_details(soup)
        infos['title'].append(video_details[0] if video_details[0] is not None else '')
        infos['channel'].append(video_details[1] if video_details[1] is not None else '')
        infos['description'].append(video_details[2] if video_details[2] is not None else '')
        infos['video_id'].append(video_details[3] if video_details[3] is not None else '')
        infos['external_link'].append(video_details[4] if video_details[4] is not None else [])
        infos['transcript'].append(transcript if transcript is not None else '')

    df = pd.DataFrame(infos)
    save_channel_data_df(df)
    return df


def get_bulk_utube_transcript(video_ids):

    transcript_dict = {}
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_ids)

    for idx, transcript in enumerate(transcript_list):
        transcript_en = transcript.translate('en').fetch()
        transcript_en_txt = transcript_en[0]["text"]
        transcript_dict[video_ids[idx]] = transcript_en_txt
    
    return transcript_dict

def get_single_utube_transcript(video_id):

    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

    for transcript in transcript_list:
        transcript_en = transcript.translate('en').fetch()
        transcript_en_txt = transcript_en[0]["text"]
        return transcript_en_txt

    return None
    
def save_channel_data_df(df, channel_name):
    print("Inside save_channel_data_df channel name:{}".format(channel_name))
    folder_name = "data"
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    channel_dir = os.path.join(cur_dir, folder_name, channel_name)
    file_name = channel_name + ".csv"
    file_path = os.path.join(channel_dir, file_name)

    os.makedirs(channel_dir, exist_ok=True)

    # Save the DataFrame to a CSV file
    df.to_csv(file_path, index=False)
    

def get_channel_list():
    print("inside get_channel_list")
    data_dir = get_data_path()
    folders = os.listdir(data_dir)
    return folders


def get_channel_data_df(channel_name):
    print("inside get_channel_data_df channel name:{}".format(channel_name))
    data_dir = get_data_path()
    channel_dir = os.path.join(data_dir, channel_name)
    channel_name = channel_name + ".csv"
    file_name = os.path.join(channel_dir, channel_name)
    df = pd.read_csv(file_name)
    return df


def get_data_path():

    folder_name = "data"
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cur_dir, folder_name)


def fetch_videoid(path, channel_name):

    data_path = get_data_path()
    channel_path = os.path.join(data_path, channel_name)
    source_file = path.replace(channel_path, "")
    video_id = source_file.split('.')[0][1:]
    return video_id
