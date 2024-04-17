import os
import tempfile
from qdrant_client import QdrantClient
from langchain_openai import ChatOpenAI

from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.document_loaders.text import TextLoader
from langchain_community.llms import Ollama

import utube_service

# Set OpenAI API key environment variable (not used here but might be needed elsewhere)
os.environ['OPENAI_API_KEY'] = "not_needed"
llm = Ollama(model="gemma:2b")

# Qdrant setup
qdrant_url = "http://localhost:6333"
client = QdrantClient(url=qdrant_url, prefer_grpc=False)
embeddings = SentenceTransformerEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Template for the prompt
prompt_template = """
Use the following pieces of information to answer the user's question.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context: {context}
Question: {question}

Only return the helpful answer. Answer must be detailed and well explained.

"""

# Create a prompt template
prompt = PromptTemplate(template=prompt_template, input_variables=['context', 'question'])


def create_kb(channel_name):
    print("inside create_kb")
    global qdrant_url, embeddings

    data_path = utube_service.get_data_path()
    channel_folder = os.path.join(data_path, channel_name)

    # create text file feed code here
    files = os.listdir(channel_folder)
    txt_files = [file for file in files if file.endswith('.txt')]

    for txt in txt_files:
        txt_file_name = os.path.join(channel_folder, txt)
        loader = TextLoader(txt_file_name, encoding="utf-8")
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, 
                                                    chunk_overlap=100)
        chunks = text_splitter.split_documents(documents)

        # Create vector database
        Qdrant.from_documents(
            chunks,
            embeddings,
            url=qdrant_url,
            prefer_grpc=False,
            collection_name=channel_name
        )


def get_response(query, COLLECTION_NAME):
    print("inside get_response |  query:{} collection name:{}".format(query, COLLECTION_NAME))
    db = Qdrant(client=client, embeddings=embeddings, collection_name=COLLECTION_NAME)
    retriever = db.as_retriever(search_kwargs={"k": 5}, search_type="mmr")
        
    # Initialize QA chain
    chain_type_kwargs = {"prompt": prompt}
    qa = RetrievalQA.from_chain_type(llm=llm, 
                                     chain_type="stuff", 
                                     retriever=retriever, 
                                     return_source_documents=True, 
                                     chain_type_kwargs=chain_type_kwargs, 
                                     verbose=True)
    
    # Get response
    response = qa(query)
    answer = response['result']

    video_ids = []
    source_documents = []

    for source_doc in response['source_documents']:
        
        source_text = source_doc.page_content
        source_file = source_doc.metadata['source']
        video_id = utube_service.fetch_videoid(source_file, COLLECTION_NAME)

        video_ids.append(video_id)
        source_documents.append(source_text)

    return answer, source_documents, video_ids

