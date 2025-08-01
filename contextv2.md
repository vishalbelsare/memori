#### Future implementation of vector database support to memori 


- [] Future implementation MCP for memori 

```py
vector_db="", # the url for connecting to vector db
vector_api_key="", # the api key for connecting to the vector db
```

### how will the vector_db will work with memoriai

As per memori strucutre, memori will create structured collections in the vector_database itself,

when you give your, vector_db ="url" and vector_api_key="key", we have hooks with some of the popular databases, where we create the speific collections and other things for proper usage of memori with vector database !

we will be implemneting hooks for each vector database, with an schema that will be applied on vector_db when connected, by default for now we will be supporting openai embeddings model will add support to more in future.

so the new workflow will be, 

user <-> llm

chat_history ( saved in db ) -> vector_db ( conntected -> memory_configs applied ) -> structred_data from chat_history -> embeddings_model -> (specific) vector_db collection 



and when the vector db is enabled, there is another condtion for our memory and retrival agents, 
That is an

Hydrid Search Protocal
- if the search requires in depth search, then it would use semantic search by vector db
    - otherwise it would use the normal sql queries method  
- This will be decided by the memori agent itself


But, database_connect=" ",   # it isn't optional, you still need to give the data, where whole data will be structured properly in hte database itself
further the strcutured data will be properly passed to embeddings model and to the proper collection in the vector database we are using !



```py

from memori import Memori

personal = Memori(
    database_connect= "",   ## You can connect sqlite, sql, postgres
    template= "basic",
    mem_prompt= " Only record {python} related stuff !",  ## optional parameter
    concious_ingest= true, ## It fetches necessary data from concious_memory, rules !!!
    vector_db="", ## we support direct endpoints of various vector db, 
    vector_api_key="",
)

personal.enable()  ## this approach will be similar to loguru !!!

from litellm import completion
from dotenv import load_dotenv
import json

load_dotenv()

response =  completion(
    model="gpt-4.1",
    messages=[
        {
            "role": "user",
            "content": "Write an essay on AI !"
        }
    ]
)

# or we could , try to somehow record the output through the response format !!

print(response)
```