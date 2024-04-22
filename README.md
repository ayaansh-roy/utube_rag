# YouTube RAG Application

Welcome to the YouTube RAG Application, where advanced Gen AI tools and techniques meet the vast world of YouTube content. Our application is designed to empower users to query data from their favorite YouTube channels and receive precise answers, complete with links to the respective videos.

## Key Features

- **Query Processing**: Ask any query related to specific topics, keywords, or trends from YouTube channel data and get accurate answers swiftly.
- **Video and Metadata Extraction**: Utilize Scrapetube and the YouTube Transcript API to extract all videos and their metadata from any YouTube channel.
- **Transcript Fetching**: Streamline your content analysis by fetching both videos and their transcripts effortlessly.
- **Knowledge Base Creation**: Leverage Qdrant Vector DB to create a comprehensive knowledge base for enhanced content understanding.
- **RAG Pipeline**: Integrate our Retriever-Augmented-Generation (RAG) pipeline with large language models like Gemma from Google for improved content recommendation.
- **Streamlit UI**: Experience a user-friendly interface built with Streamlit for efficient YouTube channel management.

## Getting Started

To get started with the YouTube RAG Application, follow these steps:

**Install Dependencies**: Begin by installing all the necessary Python packages listed in the `requirements.txt` file.
   ```bash
   pip install -r requirements.txt
   ```
**Docker Setup**: Ensure Docker is installed and running on your system. Then, execute the following command to start the Qdrant container, which is essential for our knowledge base operations.
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```
**Docker Setup**: Ollama is required to run quantized Large Language Models (LLMs) locally. Install Ollama using the provided installation script or package manager.
**Large Language Model Setup**: While our application supports various LLMs, we provide instructions for installing gemma:2b. This step is optional if you prefer to use a different LLM.
```bash
ollama install gemma:2b
ollama run gemma:2b
ollama serve
```
Replace gemma:2b with the identifier of your preferred LLM if necessary.

**License**
This project is licensed under the MIT License - see the LICENSE file for details.