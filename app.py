import os
import requests
import scrapetube
import pandas as pd
import streamlit as st
from stqdm import stqdm
from bs4 import BeautifulSoup as bs

import llm_service
import utube_service
import constants as const

#st.set_page_config(layout="wide")

# Create a page dropdown
page = st.sidebar.radio(
    "Page Navigator",
    [
        const.YT_FETCH_PAGE,
        const.YT_AGENT_PAGE,
    ],
)


def scrape_youtube(video_ids):
    infos = {
        'title': [],
        'channel': [],
        'description': [],
        'video_id': [],
        'external_link': [],
        'transcript':[]
    }

    # Create a progress bar
    progress_bar = st.progress(0)

    for idx, video_id in enumerate(video_ids):

        progress_bar.progress((idx + 1) / len(video_ids))
        transcript = utube_service.get_single_utube_transcript(video_id)

        url = f'https://www.youtube.com/watch?v={video_id}'
        response = requests.get(url)
        soup = bs(response.text, 'html.parser')
        video_details = utube_service.get_video_details(soup)

        title_str = video_details[0] if video_details[0] is not None else ''
        channel_str = video_details[1] if video_details[1] is not None else ''
        description_str = video_details[2] if video_details[2] is not None else ''
        video_id_str = video_details[3] if video_details[3] is not None else ''
        external_link_str = video_details[4] if video_details[4] is not None else []
        transcript_str = transcript if transcript is not None else ''

        infos['title'].append(title_str)
        infos['channel'].append(channel_str)
        infos['description'].append(description_str)
        infos['video_id'].append(video_id_str)
        infos['external_link'].append(external_link_str)
        infos['transcript'].append(transcript_str)

        text = (
            str(title_str) + '\n' +
            str(channel_str) + '\n' +
            str(description_str) + '\n' +
            str(video_id_str) + '\n' +
            str(external_link_str) + '\n' +
            str(transcript_str)
        )

        print(text)


        channel_str = create_channel_name(channel_str)
        data_path = utube_service.get_data_path()
        channel_path = os.path.join(data_path, channel_str)

        channel_path_encoded = channel_path.encode('utf-8')
        os.makedirs(channel_path_encoded, exist_ok=True)

        file_txt =  video_id_str + ".txt"
        file_name = os.path.join(channel_path, file_txt)
        print("File Name:{}".format(file_name))

        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(text)

    # Close progress bar
    progress_bar.empty()

    # create df and save it in data folder
    df = pd.DataFrame(infos)
    channel_name = create_channel_name(infos['channel'][0])
    utube_service.save_channel_data_df(df, channel_name)

    return df, channel_name



def create_channel_name(channel_name_input):


    channel_name = channel_name_input.replace(" ","_")
    channel_name = channel_name.lower()
    return channel_name


st.header("Youtube RAG Application")

if page == const.YT_FETCH_PAGE:

    utube_channel_link = st.text_input("Provide Youtube Channel Link", "")
    fetch_button = st.button("Fetch")
    kb_button = st.button("Create Knowledge Base")

    if fetch_button and len(utube_channel_link)>5:
        
        utube_icon_link, utube_channel_id = utube_service.scrape_channel_id_and_icon(utube_channel_link)
        video_ids = scrapetube.get_channel(utube_channel_id)
        video_id_list = []
        for video in video_ids:
            video_id_list.append(video['videoId'])
        
        print("Fetched video list:{}".format(video_id_list))
        
        num_videos = len(video_id_list)
        utube_info_df, channel_name = scrape_youtube(video_id_list)
        st.write("There are {} videos!".format(num_videos))
        st.dataframe(utube_info_df)
        llm_service.create_kb(channel_name)
        st.write("Knowledgebase Created Successfully!")



if page == const.YT_AGENT_PAGE:

    channel_list = utube_service.get_channel_list()
    channel_list.insert(0, const.SEL_CHANL)    
    selected_channel = st.selectbox(const.SEL_CHANL, channel_list)
    user_query = st.text_input("Ask Anything", "")

    if selected_channel and selected_channel != const.SEL_CHANL:
        channel_df = utube_service.get_channel_data_df(selected_channel)
        if not channel_df.empty:
            with st.expander("Show Youtube Video Metadata"):
                st.dataframe(channel_df)


    if len(user_query)>10 and selected_channel != const.SEL_CHANL:
        answer, source_documents, video_ids = llm_service.get_response(user_query, selected_channel)
        st.write(answer)

        if len(source_documents) > 0:
            with st.expander("Show Source Chunks"):
                count = 1
                for idx, source_doc in enumerate(source_documents):

                    st.write("Chunk:{}".format(count))
                    st.write(source_doc)

                    youtube_url = const.YT_URL_PRFX + video_ids[idx]
                    st.video(youtube_url)
                    st.write(youtube_url)
                    count += 1
