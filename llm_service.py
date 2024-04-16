import os
import tempfile
from qdrant_client import QdrantClient
from langchain_openai import ChatOpenAI

from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.document_loaders import UnstructuredFileLoader as FileLoader

# Set OpenAI API key environment variable (not used here but might be needed elsewhere)
os.environ['OPENAI_API_KEY'] = "not_needed"

# Initialize ChatOpenAI instance (using LM Studio inference server)
llm = ChatOpenAI(base_url="http://localhost:1234/v1")

COLLECTION_NAME = "giskard_db"

# Qdrant setup
qdrant_url = "http://localhost:6333"
client = QdrantClient(url=qdrant_url, prefer_grpc=False)
embeddings = SentenceTransformerEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db = Qdrant(client=client, embeddings=embeddings, collection_name=COLLECTION_NAME)


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

def load_pdf(uploaded_pdf):
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(uploaded_pdf.read())
        temp_file_path = temp_file.name

        loader = FileLoader(temp_file_path)
        documents = loader.load()

    return documents


def create_kb(documents):
    global qdrant_url, embeddings

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, 
                                                   chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)

    # Create vector database
    Qdrant.from_documents(
        chunks,
        embeddings,
        url=qdrant_url,
        prefer_grpc=False,
        collection_name=COLLECTION_NAME
    )


def get_response(query):

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

    source_documents = []
    for source_doc in response['source_documents']:
        source_documents.append(source_doc.page_content)

    return answer, source_documents

