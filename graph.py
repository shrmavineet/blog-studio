from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

from state import BlogState
from agents import get_llm, researcher_agent, writer_agent,editor_agent
from typing import Literal

MAX_REVISION = 3

# Node_Edges
## Defining the nodes

def researcher_node(state:BlogState):
    llm = get_llm()
    researcher_data = researcher_agent(
        llm = llm,
        topic=state.topic,
        audience=state.audience,
        feedback=state.research_feedback
    )
    state.research = researcher_data
    state.research_feedback = ""

    return state

def human_review_research_node(state:BlogState):
    """Pause and ask the human to approve the research or send the feedback"""
    decision = interrupt({
        "stage": "researcher_review",
        "research": state.research,
        "instructions":(
            "Reply with 'approve' to continue to writing"
        )
    })
    if isinstance(decision,dict):
        action = decision.get("action","approve")
        feedback = decision.get("feedback","")

    else:
        text = str(decision)
        action = "approve" if text.lower() in ["approve","approved","ok","yes","process",""] else "revise"

        feedback = "" if action=="approve" else text

    state.research_feedback = feedback
    return state

def writer_node(state: BlogState):
    """
    Write Agent produce the full draft blog(or revise it)
    """
    if state.draft_feedback:
        state.revision_count += 1
    llm =get_llm()
    draft_data = writer_agent(
        llm=llm,
        topic=state.topic,
        audience=state.audience,
        research=state.research,
        feedback=state.draft_feedback
        )
    state.draft = draft_data
    state.draft_feedback = ""

    return state

def human_review_draft_node(state:BlogState):
    """Pause and ask the human to approve the draft or send the feedback"""
    decision = interrupt({
        "stage": "draft_review",
        "draft": state.draft,
        "instructions":(
            "Reply with 'approve' to continue to send the editor or describe what change to send it back to the writer."
        )
    })
    if isinstance(decision,dict):
        action = decision.get("action","approve")
        feedback = decision.get("feedback","")

    else:
        text = str(decision)
        action = "approve" if text.lower() in ["approve","approved","ok","yes","process",""] else "revise"

        feedback = "" if action=="approve" else text

    state.draft_feedback = feedback
    return state

def editor_node(state:BlogState):
    llm = get_llm()
    final = editor_agent(
        llm= llm,
        topic = state.topic,
        draft = state.draft
    )
    state.final_blog = final
    return state




########### Conditional Edges

def route_after_research_review(state:BlogState) -> Literal["research","writer"]:
    if state.research_feedback:
        return "research"
    else:
        return "writer"

def route_after_draft_review(state:BlogState) -> Literal["edit","writer"]:
    if state.draft_feedback and state.revision_count <MAX_REVISION:
        return "writer"
    else:
        return "edit"


#### Build and compile the graph

def build_blog_graph():
    builder = StateGraph(BlogState)


    ###add nodes
    builder.add_node("research", researcher_node)
    builder.add_node("review_research", human_review_research_node)
    builder.add_node("writer",writer_node)
    builder.add_node("revies_draft", human_review_draft_node)
    builder.add_node("edit", editor_node)



    ### add edges
    builder.add_edge(START, "research")
    builder.add_edge("research","review_research")
    builder.add_conditional_edges("review_research",
                                  route_after_research_review,
                                  {"research": "research", "writer":"writer"}
                                  )
    builder.add_edge("writer", "revies_draft")
    builder.add_conditional_edges("revies_draft",
                                  route_after_draft_review,
                                  {"writer":"writer","edit":"edit"}
                                  )
    builder.add_edge("edit", END)
    GRAPH = builder.compile(checkpointer=InMemorySaver())
    return GRAPH