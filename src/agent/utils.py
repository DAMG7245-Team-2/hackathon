import asyncio
from pinecone.data.index import Index
from tavily import AsyncTavilyClient
from langchain_huggingface import HuggingFaceEmbeddings

from agent.state import Section

async def async_search(query_list: list[str], max_depth: int) -> str:
    """Perform a web search using the given query list and return the results."""
    tavily = AsyncTavilyClient()
    searches = []
    for query in query_list:
        searches.append(
            tavily.search(
                query, max_results=max_depth, include_raw_content=True, topic="general"
            )
        )
    search_results = await asyncio.gather(*searches)
    return unique_formatted_sources(search_results)


def unique_formatted_sources(
    search_results, max_tokens_per_source: int = 4000
) -> str:
    """Format the search results into a unique string."""
    sources = []
    for result in search_results:
        sources.extend(result["results"])

    unique_url_sources = {source["url"]: source for source in sources}
    formatted_text = "Content from sources:\n"
    for i, source in enumerate(unique_url_sources.values(), 1):
        formatted_text += f"{'='*80}\n"  # Clear section separator
        formatted_text += f"Source: {source['title']}\n"
        formatted_text += f"{'-'*80}\n"  # Subsection separator
        formatted_text += f"URL: {source['url']}\n===\n"
        formatted_text += (
            f"Most relevant content from source: {source['content']}\n===\n"
        )

        char_limit = max_tokens_per_source * 4
        # Handle None raw_content
        raw_content = source.get("raw_content", "")
        if raw_content is None:
            raw_content = ""
            print(f"Warning: No raw_content found for source {source['url']}")
        if len(raw_content) > char_limit:
            raw_content = raw_content[:char_limit] + "... [truncated]"
        formatted_text += f"Full source content limited to {max_tokens_per_source} tokens: {raw_content}\n\n"
        formatted_text += f"{'='*80}\n\n"  # End section separator

    return formatted_text.strip()

def format_sections(sections: list[Section]) -> str:
    """ Format a list of sections into a string """
    formatted_str = ""
    for idx, section in enumerate(sections, 1):
        formatted_str += f"""
{'='*60}
Section {idx}: {section.name}
{'='*60}
Description:
{section.description}
Requires Research: 
{section.research}

Content:
{section.content if section.content else '[Not yet written]'}

"""
    return formatted_str


def format_rag_contexts(matches: list) -> str:
    """Formats Pinecone results into a readable string."""
    contexts = []
    for x in matches:
        text = (
            f"Text: {x['metadata']['text']}\n"
            f"Title: {x['metadata'].get('title', 'N/A')}\n"
            f"Author: {x['metadata'].get('author', 'N/A')}\n"
        )
        contexts.append(text)
    return "\n---\n".join(contexts)

def search_pinecone(index: Index, embeddings: HuggingFaceEmbeddings, query_list: list[str], top_k: int = 5) -> str:
    responses = []
    for query in query_list:
        query_emb = embeddings.embed_query(query)

        response = index.query(
            vector=query_emb,
            top_k=top_k,
            include_metadata=True
        )
        responses.append(format_rag_contexts(response.get(["matches"], [])))
    return "\n---\n".join(responses)