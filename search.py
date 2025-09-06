import weaviate
from weaviate.classes.query import MetadataQuery
from typing import List, Dict, Any
import os
from groq import Groq
import prompt_templates
from pydantic import BaseModel
import torch
import clip
from PIL import Image
import io



class groqHandler:
    def __init__(self, api_key:str, template:str = prompt_templates.message_to_product6):
        self.api_key = api_key
        try:
            self.groq_client = Groq(api_key=self.api_key)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            print("Groq client initialized")
            
        self.template = template
        self.messages = [
            {
                "role": "system",
                "content": self.template
            }
        ]

    
    def query_to_products(self, query:str) -> str:
            
            self.messages.append(
                {
                    "role": "user",
                    "content": query
                }
            )
            chat_completion = self.groq_client.chat.completions.create(
                messages=self.messages,
                model="llama3-8b-8192"
            )
            self.messages.append(
                {
                    "role": "assistant",
                    "content": chat_completion.choices[0].message.content
                }
            )
            # print(chat_completion.choices[0].message.content)
            return chat_completion.choices[0].message.content







class WeaviateQueryService: #Databse se related sab kuch
    def __init__(self, collection:str = "CleanedProducts", groqHandler : groqHandler = None, target_vector:str = None):

        try:
            self.client = weaviate.connect_to_local()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if(self.client.is_ready()):
                print("Weaviate client initialized")
            else:
                print("Weaviate client not initialized")

        
        self.collection = self.client.collections.get(collection)
        self.groqHandler = groqHandler


        if target_vector:
            self.target_vector = target_vector
        else:
            self.target_vector = "name_master_sub_art_col_use_seas_gender"


        
#  text to poroduct (find)
    def get_results(self, query: str, limit: int = 30, groq_llama_simplfy : bool = True, print_responses_name: bool = False) -> List[Dict[str, Any]]:
        
        if groq_llama_simplfy and self.groqHandler:
            modified_query = self.groqHandler.query_to_products(query)
        else: 
            modified_query = query
        print(modified_query, type(modified_query))
        results = self.collection.query.near_text(
            # concepts=modified_query.split(','),
            query=modified_query,
            limit=limit,
            return_metadata=MetadataQuery(distance=True),
            target_vector=self.target_vector
        )

        # results = self.collection.query.near_text(
        #     query=modified_query,
        #     limit=limit,
        #     return_metadata=MetadataQuery(distance=True),
        #     target_vector=self.target_vector
        # )


        list_of_results = list()
        if print_responses_name:
            # print(results.objects)
            for o in results.objects:
                print(o.properties["productDisplayName"],  o.metadata.distance)
                list_of_results.append(o.properties)


        return list_of_results
        # return results.objects.properties
    
    def get_recommends(self) -> List[Dict[str, Any]]:
        prompt = "Recommend something based on all previous prompts"
        
        response = self.get_results(query=prompt, limit = 20, groq_llama_simplfy=True, print_responses_name=True)
        return response

