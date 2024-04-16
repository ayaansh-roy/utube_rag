import scrapetube
import streamlit as st

import llm_service
import utube_service


st.header("Youtube RAG Application")

utube_channel_link = st.text_input("Provide Youtube Channel Link", "")
fetch_button = st.button("Fetch")

if fetch_button and utube_channel_link is not None:
    
    video_ids = scrapetube.get_channel(utube_channel_link)
    video_id_list = []
    for video in video_ids:
        video_id_list.append(video['videoId'])
    
    num_videos = len(video_id_list)
    utube_info_df = utube_service.scrape_youtube(video_id_list)
    st.write("There are {} videos!".format(num_videos))
    st.dataframe(utube_info_df)