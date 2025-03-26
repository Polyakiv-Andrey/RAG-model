import csv
import glob
import os
import tempfile

from langchain_community.document_loaders import TextLoader, PyPDFLoader, UnstructuredWordDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

class RAGModel:
    def __init__(
            self,
            model_name='gemma3',
            embedding_model='nomic-ai/nomic-embed-text-v1',
            persist_dir='chroma_db'
    ):
        self.model_name = model_name
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={"trust_remote_code": True}
        )
        self.persist_dir = persist_dir
        self.vectorstore = None
        self.qa_chain = None
        print("[Init] Initialized RAG with Gemma 3 + HuggingFace Embeddings")

    def load_and_index_documents(self, folder_path='data'):
        print("[Load] Reading documents...")

        loaders = []

        txt_files = glob.glob(f"{folder_path}/**/*.txt", recursive=True)
        for file in txt_files:
            loaders.append(TextLoader(file))

        pdf_files = glob.glob(f"{folder_path}/**/*.pdf", recursive=True)
        for file in pdf_files:
            loaders.append(PyPDFLoader(file))

        docx_files = glob.glob(f"{folder_path}/**/*.docx", recursive=True)
        for file in docx_files:
            loaders.append(UnstructuredWordDocumentLoader(file))

        csv_files = glob.glob(f"{folder_path}/**/*.csv", recursive=True)
        for file in csv_files:
            if os.path.exists(file):
                with open(file, newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    rows = list(reader)

                    text = "\n".join([", ".join(row) for row in rows])

                    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as tmpfile:
                        tmpfile.write(text)
                        tmpfile_path = tmpfile.name

                    loaders.append(TextLoader(tmpfile_path))

            else:
                raise FileNotFoundError(f"CSV file not found: {file}")
        if not loaders:
            raise ValueError("No supported documents found.")

        raw_docs = []
        for loader in loaders:
            raw_docs.extend(loader.load())

        print(f"[Docs] Loaded {len(raw_docs)} raw documents")

        print("[Split] Splitting documents...")
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = splitter.split_documents(raw_docs)

        if not docs:
            raise ValueError("No text chunks found after splitting.")

        print(f"[Embed] Embedding {len(docs)} chunks...")
        self.vectorstore = Chroma.from_documents(
            documents=docs,
            embedding=self.embedding_model,
            persist_directory=self.persist_dir
        )
        self.vectorstore.persist()
        print("[Persist] Vectorstore saved to disk.")

    def load_vectorstore(self):
        print("[Load] Loading vectorstore from disk...")
        self.vectorstore = Chroma(
            embedding_function=self.embedding_model,
            persist_directory=self.persist_dir
        )

    def setup_qa_chain(self, prompt: PromptTemplate):
        if not self.vectorstore:
            raise ValueError("Vectorstore is not initialized.")

        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        llm = Ollama(model=self.model_name)
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            chain_type="stuff",
            chain_type_kwargs={"prompt": prompt}
        )
        print("[Chain] QA Chain ready.")

    def ask(self, question: str) -> str:
        if not self.qa_chain:
            raise ValueError("QA chain not initialized.")
        print(f"[Ask] {question}")
        return self.qa_chain.run(question)


custom_prompt = PromptTemplate.from_template("""
{context}
Question: {question}
Answer:
""")
