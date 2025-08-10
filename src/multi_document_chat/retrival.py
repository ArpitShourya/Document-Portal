import sys,os
from typing import List, Optional
from dotenv import load_dotenv
from operator import itemgetter

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.vectorstores import FAISS


from utils.model_loader import ModelLoader
from model.models import PromptType
from prompt.prompt_library import PROMPT_REGISTRY
from exception.custom_exception import DocumentPortalException
from logger.custom_logger import CustomLogger

class ConversationalRAG:
    def __init__(self,session_id:str, retriver=None):
        try:
            self.log=CustomLogger().get_logger(__name__)
            self.session_id=session_id
            self.llm=self._load_llm()
            self.contextualize_prompt:ChatPromptTemplate=PROMPT_REGISTRY[PromptType.CONTEXTUALIZE_QUESTION.value]
            self.qa_prompt: ChatPromptTemplate=PROMPT_REGISTRY[PromptType.CONTEXT_QA.value]
            if retriver is None:
                raise ValueError("retriver cannot be None")
            self.retriver=retriver
            self._build_lcel_chain()
            self.log.info("ConversationalRAG initialized",session_id=self.session_id)



        except Exception as e:
            self.log.error("Error initializing Conversational RAG")
            raise DocumentPortalException("Error initializing Conversational RAG")
        
    def load_retriver_from_faiss(self, index_path:str):
        """
            Load A FAISS vectorstore from disk and convert to retriver.
        """
        try:
            embeddings=ModelLoader().load_embeddings()
            if not os.path.isdir(index_path):
                raise FileNotFoundError(f"FAISS index directory not found: {index_path}")
            vectorstore=FAISS.load_local(
                index_path,
                embeddings,
                allow_dangerous_deserialization=True
            )

            self.retriver=vectorstore.as_retriever(search_type="similarity", search_kwargs={"k":5})
            self.log.info("FAISS retriver loaded successfully", index_path=index_path)
            return self.retriver

        except Exception as e:
            self.log.error("Error loading retriver")
            raise DocumentPortalException("Error loading retriver")
        
    def invoke(self,user_input:str,chat_history:Optional[List[BaseMessage]]=None)->str:
        """_summary_

        Args:
            user_input (str): _description_
            chat_history (Optional[List[BaseMessage]], optional): _description_. Defaults to None.

        Raises:
            DocumentPortalException: _description_

        Returns:
            str: _description_
        """
        try:
            chat_history= chat_history or []
            payload={"input":user_input, "chat_history":chat_history}
            
            answer=self.chain.invoke(payload)
            if not answer:
                self.log.warning("No answer generated",user_input=user_input,session_id=self.session_id)
                return "no answer generated."
            
            self.log.info("Chain invoked successfully",
                          session_id=self.session_id,
                          user_input=user_input,
                          answer_preview=answer[:150]
                          )
            return answer
        except Exception as e:
            self.log.error("Error in invoke")
            raise DocumentPortalException("Error in invoke")

    def _load_llm(self):
        try:
            llm=ModelLoader().load_llm()
            if not llm:
                raise ValueError("LLM could not be loaded")
            self.log.info("LLM loaded successfully", session_id=self.session_id)
            return llm
        except Exception as e:
            self.log.error("Error loading llm",error=str(e))
            raise DocumentPortalException("Error laoding llm")
        
    @staticmethod
    def _format_docs(docs):
        return "\n\n".join(d.page_content for d in docs)

    def _build_lcel_chain(self):
        try:
            
            question_rewriter=(
                {
                    "input": itemgetter("input"),
                    "chat_history":itemgetter("chat_history")
                }
                |self.contextualize_prompt
                |self.llm
                |StrOutputParser()
            )
            retrive_docs=question_rewriter|self.retriver |self._format_docs

            self.chain=(
                {
                    "context": retrive_docs,
                    "input": itemgetter("input"),
                    "chat_history": itemgetter("chat_history")
                }
                |self.qa_prompt
                |self.llm
                |StrOutputParser()
            )

            self.log.info("LCEL chain created", session_id=self.session_id)
        except Exception as e:
            self.log.error("Error building lcel chain",error=str(e))
            raise DocumentPortalException("Error nuilding lcel chain")
