from llama_index import download_loader, ServiceContext, LLMPredictor, GPTVectorStoreIndex, StorageContext, load_index_from_storage
from pathlib import Path
import os
import streamlit as st
from streamlit_chat import message
from langchain.chat_models import ChatOpenAI
import openai

openai.api_key = "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"
# os.environ['OPENAI_API_KEY'] = "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"
llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo"))
service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor)

PATH_TO_DOCS = r'C:\Users\Alexandru Raduca\Proiecte\chatpdf\gpt_chatwithPDF\docs'
PATH_TO_PDFS = r'C:\Users\Alexandru Raduca\Proiecte\chatpdf\gpt_chatwithPDF\pdfs'
PATH_TO_INDEXES = r'C:\Users\Alexandru Raduca\Proiecte\chatpdf\gpt_chatwithPDF\indexes'
if not os.path.exists(PATH_TO_INDEXES):
    os.makedirs(PATH_TO_INDEXES)


# build index from PDF
def pdf_to_index(file):
    if not os.path.exists(PATH_TO_INDEXES):
        os.makedirs(PATH_TO_INDEXES)

        pdf_path = f'{PATH_TO_PDFS}/{file}'
        save_path = f'{PATH_TO_INDEXES}/{file}'
    else:
        pdf_path = f'{PATH_TO_PDFS}/{file}'
        save_path = f'{PATH_TO_INDEXES}/{file}'

    PDFReader = download_loader('PDFReader')
    loader = PDFReader()
    documents = loader.load_data(file=Path(pdf_path))
    index = GPTVectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir=save_path)


# build index from docx
def docx_to_index(file): 
    if not os.path.exists(PATH_TO_INDEXES):
        os.makedirs(PATH_TO_INDEXES)
        docx_path = f'{PATH_TO_DOCS}/{file}'
        save_path = f'{PATH_TO_INDEXES}/{file}'
    else:
        docx_path = f'{PATH_TO_DOCS}/{file}'
        save_path = f'{PATH_TO_INDEXES}/{file}' 

    DocxReader = download_loader("DocxReader")
    loader = DocxReader()
    documents = loader.load_data(file=Path(docx_path))
    index = GPTVectorStoreIndex.from_documents(documents) 
    index.storage_context.persist(persist_dir=save_path) 


# build index from website
def website_to_index(url):
    BeautifulSoupWebReader = download_loader("BeautifulSoupWebReader")
    loader = BeautifulSoupWebReader()
    documents = loader.load_data(urls=[url])
    print(documents[0])
    # Create a new index for the website content
    website_index = GPTVectorStoreIndex.from_documents(documents)

    title = documents[0].extra_info["URL"].replace("https://", "").replace("http://", "").replace("/", "")
    # Save the index to the storage
    website_index.storage_context.persist(persist_dir=f'{PATH_TO_INDEXES}/{title}')


# query index using GPT
def query_index(query_u):
    index_to_use = get_manual()
    storage_context = StorageContext.from_defaults(persist_dir=f"{PATH_TO_INDEXES}/{index_to_use}")
    index = load_index_from_storage(storage_context, service_context=service_context)
    query_engine = index.as_query_engine()
    response = query_engine.query(query_u)
    
    st.session_state.past.append(query_u)
    st.session_state.generated.append(response.response)   


def clear_convo():
    st.session_state['past'] = []
    st.session_state['generated'] = []


def get_manual():
    manual = st.session_state['manual']
    print(manual)
    return manual


def init():
    st.set_page_config(page_title='KnowHub ChatBot', page_icon=':robot_face: ') 
    st.sidebar.title('Available resources')


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
    
    manual_names = os.listdir(PATH_TO_INDEXES)
    manual = st.sidebar. radio("Choose a resource:", manual_names, key='init')
    st.session_state['manual'] = manual
    
    file = st.file_uploader("Choose a PDF file to index...")
    clicked = st.button('Index File', key='Upload')
    if file and clicked:
        extension = file.name[-4:]
        
        match extension:
            case 'docx':
                docx_to_index(file.name)
                print(file.name)
            case '.pdf':
                pdf_to_index(file.name)
    
    website_input = st.text_input("Enter website URL:")
    index_website_button = st.button("Index Website")

    if website_input and index_website_button:
        website_to_index(website_input)

