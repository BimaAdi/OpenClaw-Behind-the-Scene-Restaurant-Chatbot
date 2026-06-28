# OpenClaw Behind The Scene

Have you ever wonder how LLM access your file system, accessing social media or do a websearch? does it
even possible? let's see the architecture of LLM model. Based on the paper that start it all [attention is all you need](https://arxiv.org/pdf/1706.03762) LLM used technique called Attention layer. 
![Attention Layer](./img/attention.png)

Attention layer doesn't stated the input and the output must be an text, image or audio. As long as the data can be transform in to a number (aka embeddings in reseach term) it can be feed in to LLM. You can see the visualization of attention layer from this website [https://poloclub.github.io/transformer-explainer/](https://poloclub.github.io/transformer-explainer/) (shoot out for poloclub that create this amazing visualizer).


Ok we found that it's not limited to text, image or audio. So what training data do popular LLM (GPT, Gemini, Claude) used.

| LLM Provider | Data | Source |
|--|--|--|
| Open AI (GPT) | public internet data + RLHF | https://openai.com/index/gpt-4-research/ |
| Anthropic (Claude) | public internet data with constitution | https://www.anthropic.com/transparency |
| Google (Gemini) | public internet data + RLHF | https://gemini.google/overview/ |

As we know most of data on public internet are text, image or audio. And most embbeding tools (data to number) converted text, image or audio to number and vice versa. So I highly sure that they use text, image and audio as training data (DISCLAIMER CMIIW I can be wrong about it since I don't have access to their training data).


The question is can tools like web search, social media chat or file system embedded in to number so it can be used as training data? Currently there is no embbeding algorithm to convert those tools in to number. Even if we can embbed those tools It will be economically inefficient. You have to retrain the model every time there is new tools. It will cost high amount of money and time.


So how Openclaw, Claude Code, Github Copilot and other AI agent access those tools? Before I revealing their secret we must know how chat on LLM works. Let's say I have LLM chat like these:

```
You: Can you generate 5 random number?
LLM: Sure 4, 5, 2, 1, 9
You: Remove number 2 from that list
LLM: Ok 4, 5, 1, 9
You: Choose 1 number from that list
LLM: I choose number 5
```
Maybe you think behind the scene the code is like this
```mermaid
sequenceDiagram
  App->>LLM: Can you generate 5 random number?
  LLM->>App: Sure 4, 5, 2, 1, 9
  App->>LLM: Remove number 2 from that list
  LLM->>App: Ok 4, 5, 1, 9
  App->>LLM: Choose 1 number from that list
  LLM->>App: I choose number 5
```
This not how the code work behind the scene. You must include the previous chat as well
```mermaid
sequenceDiagram
  App->>LLM: You: Can you generate 5 random number? <br>
  LLM->>App: Sure 4, 5, 2, 1, 9
  App->>LLM: You: Can you generate 5 random number? <br> LLM: Sure 4, 5, 2, 1, 9 <br> You: Remove number 2 from that list <br>
  LLM->>App: Ok 4, 5, 1, 9
  App->>LLM: You: Can you generate 5 random number? <br> LLM: Sure 4, 5, 2, 1, 9 <br> You: Remove number 2 from that list <br> LLM: Ok 4, 5, 1, 9 <br> You: Choose 1 number from that list <br>
  LLM->>App: I choose number 5
```
Let's continue. Let's say we want to create chatbot for our restaurant. First we separated chat into 3 actor:
1. User (Client): is chat that inputed by client who use the app
2. LLM: is the chat that ouput by LLM
3. User (System): is chat that inputed by application. it's considered as User by LLM. hidden from Client.

First we have to tell the LLM to act as a restaurant assitant. We will act as User (System) in order to tell the AI (this is called system prompt).

```mermaid
sequenceDiagram
  participant User (Client)
  participant User (System)
  participant LLM
  User (System)->>LLM: User (System): You are a friendly restaurant assistant. Our restaurant named mcdonalds. It's restaurant address is on 15 Central Park Washington US.
  LLM->>User (System): Ok
```
then let user use the chat.
```mermaid
sequenceDiagram
  participant User (Client)
  participant User (System)
  participant LLM
  User (System)->>LLM: User (System): You are a friendly restaurant assistant. Our restaurant named mcdonalds. It's restaurant address is on 15 Central Park Washington US.
  LLM->>User (System): Ok
  User (Client)->>User (System): What restaurant it is?
  User (System)->>LLM: User (System): You are a friendly restaurant assistant. Our restaurant named mcdonalds. <br> LLM: Ok <br> User (Client): User (Client): What restaurant it is?
  LLM->>User (System): Our restaurant named mcdonalds
  User (System)->>User (Client): User: What restaurant it is? <br> LLM: Our restaurant named mcdonalds
  User (Client)->>User (System): where the restaurant is?
  User (System)->>LLM: User (System): You are a friendly restaurant assistant. Our restaurant named mcdonalds. <br> LLM: Ok <br> User (Client): User (Client): What restaurant it is? <br> LLM: Our restaurant named mcdonalds <br> User (Client): where the restaurant is?
  LLM->>User (System): Our restaurant is on 15 Central Park Washington US
  User (System)->>User (Client): User: What restaurant it is? <br> LLM: Our restaurant named mcdonalds <br> User: Our restaurant is on 15 Central Park Washington US
```
Ok but there is no tools on the example. Let's add tools on the example. Let's say I have tools (python function) like these:
```python
def list_menu() -> list[tuple[str, int]]:
    """return list of menu and it's priced"""
    ...

def search_menu(keyword: str) -> list[tuple[str, int]]:
    """search menu by name"""
    ...
```
The trick is to use some specific text that LLM must use in order to call the tools. Here's the system prompt
```
You are a helpful and friendly restaurant assistant.

You can ask for tools using these exact strings:
- TOOL_CALL: list_menu()
- TOOL_CALL: search_menu("keyword")
```
Before using tools the flow it's like this
```mermaid
flowchart TD
  System_Prompt-->|1|LLM_Output
  LLM_Output-->|2|System
  System-->|3|User_Input
  User_Input-->|4|System
  System-->|5|LLM_Output
```
Then we will change how we response based on the text outputed by LLM. 
```mermaid
flowchart TD
  System_Prompt-->|1|LLM_Output
  LLM_Output-->|2|System
  System-->|4a. no tools call|User_Input
  System-->|4b. text contains tools call|Tools
  Tools-->System
  User_Input-->|5|System
  System-->|6|LLM_Output
```
here's chat example using tools call
```mermaid
sequenceDiagram
  participant User (Client)
  participant User (System)
  participant LLM
  participant Tools
  User (System)->>LLM: User (Sytem): system prompt bla-bla...
  LLM->>User (System): Ok
  User (Client)->>User (System): Can I get list of menu please?
  User (System)->>LLM: User (Sytem): system prompt bla-bla... <br> LLM: Ok <br> User (Client): Can I get list of menu please?
  LLM->>User (System): TOOL_CALL: list_menu()
  User (System)->>Tools: `list_menu()`
  Tools->>User (System): Hamburger 10.000, Steak 20.000, Milkshake 5.000
  User (System)->>LLM: User (Sytem): system prompt bla-bla... <br> LLM: Ok <br> User (Client): Can I get list of menu please? <br> LLM: TOOL_CALL: list_menu() <br> User (Sytem): Hamburger 10.000, Steak 20.000, Milkshake 5.000
  LLM->>User (System): Here are the menu
  User (System)->>User (Client): User: Can I get list of menu please? <br> LLM: TOOL_CALL: list_menu() <br> Hamburger 10.000, Steak 20.000, Milkshake 5.000 <br> Here are the menu
  User (Client)->>User (System): I want 1 Steak and 1 Milkshake please
  User (System)->>LLM: User (Sytem): system prompt bla-bla... <br> LLM: Ok <br> User (Client): Can I get list of menu please? <br> LLM: TOOL_CALL: list_menu() <br> User (Sytem): Hamburger 10.000, Steak 20.000, Milkshake 5.000 <br> User (Client): I want 1 Steak and 1 Milkshake please
  LLM->>User (System): Ok that's will be 25.000
  User (System)->>User (Client): User: Can I get list of menu please? <br> LLM: TOOL_CALL: list_menu() <br> Hamburger 10.000, Steak 20.000, Milkshake 5.000 <br> Here are the menu <br> User: I want 1 Steak and 1 Milkshake please <br> LLM: Ok that's will be 25.000
```

Using text parsing to call tools right now is considered bad practice. You must use tools call provide by your sdk.
| SDK Provider | docs |
|--|--|
| OpenAI | https://developers.openai.com/api/docs/guides/tools?tool-type=function-calling |
| Antrophic | - https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools <br> - https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls | 
| Google | https://ai.google.dev/gemini-api/docs/generate-content/function-calling |
| Ollama | https://docs.ollama.com/capabilities/tool-calling |
| Open Router | https://openrouter.ai/docs/guides/features/tool-calling |

I still show the example using text parsing because that's what happening under the hood.


Using tools call function had a disadvantage It not reusable. If I want to using the tools using other SDK I have to code again. And the most hard part is how about if I want to connect my tools to existing agent provider such as OpenClaw, Hermes, Cursor or Copilot.


Luckily there is a protocol called [MCP](https://modelcontextprotocol.io/docs/getting-started/intro). TLDR MCP is a standard for LLM Tooling. So every tools that use MCP protocol can integrated easily with agent that support MCP. MCP has three mode:
1. stdio (execute script directly, can't be connected remotely)
2. sse (will be depreceated, can be connected remotely)
3. streamable-http (sse replacement, can be connected remotely)
 
You can see mcp tools in [restauran_tools.py](./restaurant_tools.py) and how to connect using copilot on [copilot doc](https://code.visualstudio.com/docs/agent-customization/mcp-servers).


That's all guys. I hope this blog can help you to create your first AI Agent. Happy Coding :) :tada:
