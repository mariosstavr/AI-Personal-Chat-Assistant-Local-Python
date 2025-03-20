from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

# Load and split PDFs
loader = PyPDFLoader("documents/manual.pdf")
pages = loader.load()

# Split text into chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
texts = text_splitter.split_documents(pages)

# Create embeddings and store in ChromaDB
embeddings = OpenAIEmbeddings(openai_api_key="API KEY")
db = Chroma.from_documents(texts, embeddings, persist_directory="chroma_db")
db.persist()