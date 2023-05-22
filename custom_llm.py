from llama_cpp import Llama
from llama_index import download_loader, SimpleDirectoryReader, ServiceContext, LLMPredictor, GPTVectorStoreIndex, PromptHelper, StorageContext, load_index_from_storage
from pathlib import Path
import os
import streamlit as st
from streamlit_chat import message
from langchain.llms.base import LLM
from llama_index import SimpleDirectoryReader, LangchainEmbedding, GPTListIndex, PromptHelper
from llama_index import LLMPredictor, ServiceContext
from typing import Optional, List, Mapping, Any
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from llama_index import LangchainEmbedding, ServiceContext

# load in HF embedding model from langchain
embed_model = LangchainEmbedding(HuggingFaceEmbeddings())

# define prompt helper
# set maximum input size
max_input_size = 2048
# set number of output tokens
num_output = 256
# set maximum chunk overlap
max_chunk_overlap = 20
prompt_helper = PromptHelper(max_input_size, num_output, max_chunk_overlap)


class CustomLLM(LLM):
    
    model_name = "./GPT4All-13B-snoozy.ggml.q4_0.bin"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        prompt_length = len(prompt) + 5
        llm = Llama(model_path="./GPT4All-13B-snoozy.ggml.q4_0.bin", n_threads=12)
        
        # output 3;30;38=44.73 llm("Q: Name the planets in the solar system? A: ", max_tokens=32, stop=["Q:", "\n"], echo=True)
        print(prompt)
        output = llm(f"Q: {prompt} A: ", max_tokens=256, stop=['A: '], echo=True)['choices'][0]['text'].replace('A: ', '').strip()
        print('OUTPUT: ' + str(output))

        # only return newly generated tokens
        return output[prompt_length:]

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {"name_of_model": self.model_name}

    @property
    def _llm_type(self) -> str:
        return "custom"

# define our LLM
llm_predictor = LLMPredictor(llm=CustomLLM())
service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor, prompt_helper=prompt_helper, embed_model=embed_model)

PATH_TO_PDFS = 'C:/'
PATH_TO_INDEXES = 'GPT_INDEXES'
if not os.path.exists(PATH_TO_INDEXES):
        os.makedirs(PATH_TO_INDEXES)

#build index from PDF
def pdf_to_index(pdf_path, save_path):
    PDFReader = download_loader('PDFReader')
    loader = PDFReader()
    documents = loader.load_data(file=Path(pdf_path))
    index = GPTVectorStoreIndex.from_documents(documents, service_context=service_context)
    # deprecated
    # index.save_to_disk(save_path)
    index.storage_context.persist(persist_dir=save_path)
    print('saved to disk')


#query index using GPT
def query_index(query_u):
    # deprecated
    # index = GPTVectorStoreIndex.load_from_disk(index_path, service_context=service_context)
    pdf_to_use = get_manual()
    storage_context = StorageContext.from_defaults(persist_dir=f"{PATH_TO_INDEXES}/{pdf_to_use}")
    index = load_index_from_storage(storage_context, service_context=service_context)
    query_engine = index.as_query_engine()
    response = query_engine.query(query_u)
    # deprecated
    # response=index.query(query_u)
    st.session_state.past.append(query_u)
    st.session_state.generated.append(response.response)   


def clear_convo():
    st.session_state['past'] = []
    st.session_state['generated'] = []

def save_pdf(file):
    if not os.path.exists(PATH_TO_INDEXES):
        os.makedirs(PATH_TO_INDEXES)
        pdf_to_index(pdf_path=f'{PATH_TO_PDFS}/{file}', save_path=f'{PATH_TO_INDEXES}/{file}')
        print('saving index')
    else:
        pdf_to_index(pdf_path=f'{PATH_TO_PDFS}/{file}', save_path=f'{PATH_TO_INDEXES}/{file}')
        print('saving index')


def get_manual():
    manual = st.session_state['manual']
    print(manual)
    return manual

def init():
    st.set_page_config(page_title='PDF ChatBot', page_icon=':robot_face: ') 
    st.sidebar.title('Available PDF')



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

    with st.form(key='my_form', clear_on_submit=True):
        user_input= st.text_area("You:", key="input", height=75) 
        submit_button =st.form_submit_button(label="Submit")

    if user_input and submit_button:
        query_index(query_u=user_input)

    if st.session_state['generated']:
        for i in range(len(st.session_state['generated'])-1, -1, -1): 
            message(st.session_state['generated'][i], key=str(i))
            message(st.session_state['past'][i], is_user=True, key=str(i) + "user")
    
    manual_names = os.listdir(PATH_TO_INDEXES)
    manual = st.sidebar. radio("Choose a manual:", manual_names, key='init')
    st.session_state['manual'] = manual
    file = st.file_uploader("Choose a PDF file to index...")
    clicked = st.button('Upload File', key='Upload')
    if file and clicked:
        save_pdf(file.name)