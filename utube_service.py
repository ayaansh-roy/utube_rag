import re
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
from youtube_transcript_api import YouTubeTranscriptApi


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
    return pd.DataFrame(infos)


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
    
    
    
