import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

#GET LLM
def get_llm(model_name:str='openai/gpt-oss-20b', temprature:float=0.5):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to the .env file.")

    llm = ChatGroq(model=model_name, temperature=temprature, api_key=api_key)
    return llm

#Research Agent
RESEARCHER_PROMPT = ChatPromptTemplate.from_messages([
    {
        "role": "system",
        "content": """
You are a Research Agent. Given a blog topic and target audience, produce a clear,
structured research outline.

Include:
1. 5-7 key points the blog should cover
2. Important facts, stats, or examples for each point
3. Suggested angle or hook

Be concise. Use bullet points.
DO NOT write the full blog yet.
"""
    },
    {
        "role": "user",
        "content": """
Topic: {topic}
Audience: {audience}
Revision hints: {revision_hints}

Write the research outline now.
"""
    }
])

def researcher_agent(llm:ChatGroq, topic:str, audience:str, feedback:str=""):

    if feedback:
        revision_hints = f"The human provided this feedback on your previous research-please address it {feedback}."
    else:
        revision_hints="This is your first attempt"

    chain = RESEARCHER_PROMPT | llm

    result = chain.invoke({
        "topic": topic,
        "audience": audience,
        "revision_hints": revision_hints
    })
    return result.content

# Write Agent
WRITER_PROMPT = ChatPromptTemplate.from_messages([
    {"role":"system","content":"""
"You are a Blog Writer Agent. Using the research notes provided, Write a complete,"
"engaging blog post. \n"
"Rules: \n"
"- Length: 500 -800 words \n"
"- Structure: Catchy title, intro hook, 3-5 sections with H2 headings, conclusion \n"
"- Do not add a 'word count' at the end"
"""},
{"role":"user","content":"""
Topic: {topic},
Audience: {audience},
ResearchNotes: {research},
{revision_hints}
Write the full blog post now
"""}
])


def writer_agent(llm:ChatGroq,topic:str,audience:str, research:str ="",feedback:str="")->str:
    revision_hints = f"The human provided this feedback on your previous draft and asked for these changes:{feedback}, Please apply these changes during writting the blog"

    if not feedback:
        revision_hints = "This is your first attempt"

    chain = WRITER_PROMPT | llm
    result = chain.invoke({
        "topic":topic,
        "audience": audience,
        "research": research,
        "revision_hints": revision_hints
    })
    return result.content

#Editor Agent

EDITOR_PROMPT = ChatPromptTemplate.from_messages([
    {"role":"system", "content":"""
"You are an Editor Agent-the final quality fate before publishing.\n"
"Take the draft and produce the final polished version. Specifically:\n"
"- Fix grammar, spelling and awkward phrasing\n"
"- Tighten wordy sentences \n"
"- Improve flow and transitions between section \n"
"- Make the title and intro more compelling if needed\n"
"- Keep the same structure and markdown formatting \n"
"- Blog wordings should look like human, not a AI, and don't use any special chars and complex/fancy words. \n"
"Output only the final polished blog post - no commentary"
"""},
{"role":"user", "content":"""
Topic:{topic},
Draft: {draft}

Return the published blog post
"""}
])

def editor_agent(llm:ChatGroq, topic:str, draft:str="")-> str:
    chain = EDITOR_PROMPT | llm
    result = chain.invoke({
        "topic":topic,
        "draft":draft
    })

    return result.content