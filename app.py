import os
import requests
import scrapetube
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup as bs

import llm_service
import utube_service
import constants as const


def scrape_youtube(video_ids):
    infos = {
        'title': [],
        'channel': [],
        'description': [],
        'video_id': [],
        'external_link': []
    }

    # Create a progress bar
    progress_bar = st.progress(0)

    for idx, video_id in enumerate(video_ids):

        progress_bar.progress((idx + 1) / len(video_ids))

        url = f'https://www.youtube.com/watch?v={video_id}'
        response = requests.get(url)
        soup = bs(response.text, 'html.parser')
        video_details = utube_service.get_video_details(soup)

        title_str = video_details[0] if video_details[0] is not None else ''
        channel_str = video_details[1] if video_details[1] is not None else ''
        description_str = video_details[2] if video_details[2] is not None else ''
        video_id_str = video_details[3] if video_details[3] is not None else ''
        external_link_str = video_details[4] if video_details[4] is not None else []

        infos['title'].append(title_str)
        infos['channel'].append(channel_str)
        infos['description'].append(description_str)
        infos['video_id'].append(video_id_str)
        infos['external_link'].append(external_link_str)

    # Close progress bar
    progress_bar.empty()

    # create df and save it in data folder
    df = pd.DataFrame(infos)
    df['is_trans_fetched'] = False

    channel_name = create_channel_name(infos['channel'][0])
    utube_service.save_channel_data_df(df, channel_name)

    return df, channel_name

def create_trans_txt_file(title_str, channel_str, description_str, video_id_str, transcript_str):

    print("Title:", title_str)
    print("Channel:", channel_str)
    print("Description:", description_str)
    print("Video ID:", video_id_str)
    print("Transcript:", transcript_str)

    text = (
            str(title_str) + '\n' +
            str(channel_str) + '\n' +
            str(description_str) + '\n' +
            str(video_id_str) + '\n' +
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
    
    print(" {} Text file created successfully ".format(file_txt))


def create_channel_name(channel_name_input):

    channel_name = channel_name_input.replace(" ","_")
    channel_name = channel_name.lower()
    return channel_name

def fetch_transcript(utube_info_df):

    title_list = utube_info_df['title'].tolist()
    description_list = utube_info_df['description'].tolist()
    channel_list = utube_info_df['channel'].tolist()
    video_id_list = utube_info_df['video_id'].tolist()
    is_trans_fetched = utube_info_df['is_trans_fetched'].tolist()

    if 'transcript' not in utube_info_df.columns:
                utube_info_df['transcript'] = ''

    channel_name = create_channel_name(channel_list[0])

    # Create a progress bar
    progress_bar = st.progress(0)

    for idx, video_id in enumerate(video_id_list):
        progress_bar.progress((idx + 1) / len(video_id_list))

        if is_trans_fetched[idx] is False:
            transcript = utube_service.get_single_utube_transcript(video_id)
            create_trans_txt_file(title_list[idx], channel_name, description_list[idx], video_id, transcript)

            print("Initiating Knowledgebase Creation For:{} !".format(video_id))
            llm_service.create_kb(channel_name, video_id)
            print("Knowledgebase Created For:{} !".format(video_id))

            utube_info_df.loc[idx, 'transcript'] = transcript
            utube_info_df.loc[idx, 'is_trans_fetched'] = True

            utube_service.save_channel_data_df(utube_info_df, channel_name)
    
    st.write("Knowledgebase Created Successfully !")

    # Close progress bar
    progress_bar.empty()



st.set_page_config(layout="wide")

# Create a page dropdown
page = st.sidebar.radio(
    "Page Navigator",
    [
        const.YT_EXTRACT_PAGE,
        const.YT_RAG_PAGE,
    ],
)
st.header("Youtube RAG Application")

if page == const.YT_EXTRACT_PAGE:

    utube_channel_link = st.text_input("Provide Youtube Channel Link", "")
    fetch_button = st.button("Extract & Create Knowledgebase")

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
        fetch_transcript(utube_info_df)


if page == const.YT_RAG_PAGE:

    channel_list = utube_service.get_channel_list()
    channel_list.insert(0, const.SEL_CHANL)    
    selected_channel = st.sidebar.selectbox(const.SEL_CHANL, channel_list)
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
            with st.expander("Show Source Chunks & Videos"):
                count = 1
                for idx, source_doc in enumerate(source_documents):

                    st.write("Chunk:{}".format(count))
                    col1, col2 = st.columns(2)
                                
                    with col1:
                        st.write(source_doc)
                    
                    with col2:
                        youtube_url = f"https://www.youtube.com/watch?v={video_ids[idx]}"
                        st.video(youtube_url)
                    count += 1
