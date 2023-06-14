from llama_index import download_loader, ServiceContext, LLMPredictor, GPTVectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.callbacks import CallbackManager, LlamaDebugHandler
from pathlib import Path
import os
import streamlit as st
from streamlit_chat import message
from langchain.chat_models import ChatOpenAI
import openai
from dotenv import load_dotenv
from usp.tree import sitemap_tree_for_homepage

load_dotenv()

key = os.getenv('OPENAI_API_KEY')
os.environ['OPENAI_API_KEY'] = key
openai.api_key = key

llama_debug = LlamaDebugHandler(print_trace_on_end=True)
callback_manager = CallbackManager([llama_debug])

llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
llm_predictor = LLMPredictor(llm=llm)
service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor, chunk_size=512, callback_manager=callback_manager)

PATH_TO_INDEX = r'C:\Users\Alexandru Raduca\Proiecte\chatpdf\gpt_chatwithPDF\index'
PATH_TO_FILES = r'C:\Users\Alexandru Raduca\Proiecte\chatpdf\gpt_chatwithPDF\files'

if not os.path.exists(PATH_TO_INDEX):
    os.makedirs(PATH_TO_INDEX)

storage_context = StorageContext.from_defaults(persist_dir=PATH_TO_INDEX)
index = load_index_from_storage(storage_context, service_context=service_context)


# build index from docx
def index_file(file): 
    extension = file.name[-4:]
        
    match extension:
        case 'docx':
            reader = download_loader("DocxReader")
            print(file.name)
        case '.pdf':
            reader = download_loader("PDFReader")
    loader = reader()
    file_path = f'{PATH_TO_FILES}/{file.name}'
    documents = loader.load_data(file=Path(file_path))
    
    for document in documents:
        index.insert(document)
    index.storage_context.persist(persist_dir=PATH_TO_INDEX)


# build index from website
def website_to_index(url):

    BeautifulSoupWebReader = download_loader("BeautifulSoupWebReader")
    loader = BeautifulSoupWebReader()
    try:
        tree = sitemap_tree_for_homepage(url)
        pages = tree.all_pages()
        count = sum(1 for _ in pages)
        print(f"Found {count} pages")
        urls = []
        for page in tree.all_pages():
            # print(page)
            urls.append(page.url)
        print(f"{len(urls)} urls")

        documents = loader.load_data(urls=urls)
        print(f"{len(documents)} documents")
        for document in documents:
            index.insert(document)
        index.storage_context.persist(persist_dir=PATH_TO_INDEX)
    except Exception as ex:
        print(ex)
        st.write(ex)


# query index using GPT
def query_index(query_u):
    storage_context = StorageContext.from_defaults(persist_dir=PATH_TO_INDEX)
    index = load_index_from_storage(storage_context, service_context=service_context)
    query_engine = index.as_query_engine()
    response = query_engine.query(query_u)
    
    st.session_state.past.append(query_u)
    st.session_state.generated.append(response.response)


def clear_convo():
    st.session_state['past'] = []
    st.session_state['generated'] = []


def init():
    st.set_page_config(page_title='KnowHub ChatBot', page_icon=':robot_face: ') 
    st.title("KnowHub ChatBot")


if __name__ == '__main__':
    init()

    clear_button = st.sidebar.button("Clear Conversation", key="clear") 
    if clear_button:
        clear_convo()

    if 'generated' not in st.session_state:
        st.session_state['generated'] = []

    if 'past' not in st.session_state:
        st.session_state['past'] = []

    if 'manual' not in st.session_state:
        st.session_state['manual'] = []

    with st.form(key='chat', clear_on_submit=True):
        user_input = st.text_area("You:", key="input", height=75) 
        submit_button = st.form_submit_button(label="Submit")

    if user_input and submit_button:
        query_index(query_u=user_input)

    if st.session_state['generated']:
        for i in range(len(st.session_state['generated'])-1, -1, -1): 
            message(st.session_state['generated'][i], key=str(i))
            message(st.session_state['past'][i], is_user=True, key=str(i) + "user")

    file = st.file_uploader("Choose a PDF file to index...")
    clicked = st.button('Index File', key='Upload')
    if file and clicked:
        with st.spinner(text='Indexing file...'):
            index_file(file)
        st.success('File indexed successfully!')
    
    website = st.text_input("Enter website URL:")
    clicked = st.button("Index Website")

    if website and clicked:
        with st.spinner(text='Indexing website...'):
            website_to_index(website)
        st.success('Website indexed successfully!')