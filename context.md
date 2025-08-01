# Memori

The Open-Source Memory Layer for AI Agents, Multi-Agent System !

#### Philosphy of memory :
- Its flexible, connect to any database
- Its second-memory for all your llm testing without need to give context of previous work again and again, instead connect the memori to your workspace, full long-term memory support !
- 

#### Tech Stack :
- database - sqlite, sql
- 

```bash
pip install memoriai
```


##### file structure

```md
memori
----core
---__init__.py
---memory.py
---agent.py
---database.py
----database
---basic_template ( schema )
----utils
--- enums
--- schemas (pydantic or base)



```py

from memori import Memori

office_work = Memori(
    database_connect= "",   ## You can connect sqlite, sql, postgres
    template= "basic",
    mem_prompt= " Only record {python} related stuff !",  ## optional parameter
    concious_ingest= true, ## It fetches necessary data from concious_memory, rules !!!
)

office_work.enable()  ## this approach will be similar to loguru !!!

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

#### Schema Templates

## basic_template

```yml

chat_history
- chat_id
- user_input
- output
- model
- 

short_term ( limit )
- chat_id
- 

long-term_memory
- chat_id


rules
-
-

``` 

### In-context Ingestion Technique

concious_ingset !!

Fetches data from
- short_term memory
- rules memory

### Docs

- concious_ingest = " " , ## It helos model get in-context learning basic details and personalization rules of the user 
- 


### Heart of Memori 

memori_agent
- Enum-driven chat-history auto categorization
- Single agent, does everything we will use openai for this
- 



#### Inital version support for response recording 

- openai
- litellm
- agno



#### Examples for much use 


```py

from memoriai import Memori

personal_space = Memori(
    ....parameters,
)

personal_space.enable()

```

#### Workflow of how everything will work !!

user : What is function calling 
LLM : Its is a type of tool used to help LLM go beyond generating text 


memori.enable()                  -> it will work somehow similar to logging method !!


how does memori.enable works !!!!
- it gets all the chat that you are talking with the LLM, to chat_history
- it then sents it to our kernal_agent ( gibon_agent / memori_agent ), has an defined enum schema, which it follows to categories this memories !!! into our tables or database
- 


Enum-Driven Triage: To decide what to do with new information, the Kernel uses a
highly efficient, enum-based function call. Instead of "thinking" in long paragraphs, the
LLM makes a single, low-cost token decision (e.g., `STORE_AS_FACT`,
`UPDATE_PREFERENCE`, `DISCARD_TRIVIAL`). This is lightning-fast, incredibly
cheap, and 100% reliable

how does retrival works
- it would use memori_agent to detect the category and try to find the most probable keyword or by any search algo. will find that specific memory
- for retrival you need to use function calling method for that specific pkg or code to implement it 

### Workflow

user <-> llm 

gets recorded in form of logs or other method we will se which is better.

chat_history -> passed to memory_agent

Memori Agent will be powered by openai-gpt4o

memory_agent tools
- structured the chat format rephrase it properly for memory
- use ENUM driven approach to categorize it
- it have differnt tools
-   -   categorize
-   -   etc

Suppose in future you asked, 

what was my idea last week !


How will retrival work as in workflow !!


function/tool : memoridb
uses : memory_agent to easily find search understand the llm string parameters, turns NLP based string parameters in proper parameters and then pass to perfect function that is required to do this

method : agentic enum driven function call

where the functions will run the specific queries to find the results and will return them to the memori_agent which wil refine it and pass it to the main agent !!!


### Advanced Retrival both sql and vector 

 Hybrid Approach:

SQL for structured queries (facts, preferences, rules)
Vector similarity for semantic search (when needed)
Temporal scoring for memory relevance
User behavior patterns for personalization

