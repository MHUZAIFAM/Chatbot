import streamlit as st
import requests

# =================================
#            API CONFIG
# =================================
# Endpoint where the FastAPI chatbot server is running

API_URL = "http://127.0.0.1:8001/chat"


# =================================
#        STREAMLIT PAGE SETUP
# =================================
# Configure page appearance

st.set_page_config(
    page_title="Isentia Bot",
    page_icon="🧠",
    layout="centered"
)

st.title("Isentia Bot")
st.caption("Ask questions about the dataset")


# =================================
#           RESET CHAT
# =================================
# Clears chat history and reloads the interface

if st.button("Reset Chat"):
    st.session_state.messages = []
    st.rerun()


# =================================
#       RESPONSE FORMATTER
# =================================
# Converts structured API responses into
# human-readable markdown displayed in Streamlit

def format_response(answer):


    # =================================
    #             SCHEMA
    # =================================
    # Handles queries asking about dataset structure
    # Example:
    # "What sections exist in the dataset?"

    if answer["type"] == "schema":

        sections = answer["data"]["Sections"]

        text = "### Sections in dataset\n"

        for s in sections:
            readable = s.replace("_", " ").title()
            text += f"- {readable}\n"

        return text


    # =================================
    #          SCHEMA COUNT
    # =================================
    # Handles queries like:
    # "How many sections are there?"

    elif answer["type"] == "schema_count":

        total = answer["data"]["Total_Sections"]

        return f"### Total Sections\n{total}"

    # =================================
    #          SECTION COUNT
    # =================================
    elif answer["type"] == "section_count":

        data = answer["data"]

        section = data["Section"].replace("_", " ").title()

        return f"""
    ### Items in {section}

    {data['Count']}
    """


    # =================================
    #         ITEM PLACEMENT
    # =================================
    # Shows which section an item belongs to

    elif answer["type"] == "item_section":

        item = answer["data"]

        section = item["Section"].replace("_", " ").title()

        return f"""

### Item Placement

**Item ID:** `{item['Item ID']}`

**Section:** {section}

"""


    # =================================
    #          ITEM DETAILS
    # =================================
    # Shows complete item information including:
    # - section
    # - rank
    # - media outlet
    # - relevant article text
    elif answer["type"] == "item_details":

        data = answer["data"]

        section_raw = data.get("Section")
        section = section_raw.replace("_", " ").title() if section_raw else "Unselected"

        text = data.get("Relevant Text")

        if not text:
            clean_text = "No article text available for this item."
        else:
            clean_text = str(text)
            clean_text = clean_text.replace('" "', '\n\n')
            clean_text = clean_text.replace('..."', '...\n\n')
            clean_text = clean_text.replace('."', '.\n\n')

        return f"""

### Item Details

**Item ID:** `{data['Item ID']}`

**Section:** {section}

**Rank:** {data['Rank']}

**Media Outlet:** *{data['Media Outlet']}*

---

### Full Article

{clean_text}

"""


    # =================================
    #        ITEM EXPLANATION
    # =================================
    # Explains why an item was placed in a section

    elif answer["type"] == "item_explanation":

        item = answer["data"]

        section = item.get("Section", "Unknown")

        if section != "Unknown":
            section = section.replace("_", " ").title()

        reason = item.get("Reason", "No explanation available.")

        return f"""

### Item Explanation

**Item ID:** `{item['Item ID']}`

**Section:** {section}

---

{reason}

"""


    # =================================
    #            RANKING
    # =================================
    # Displays highest / lowest ranked items

    elif answer["type"] == "ranking":

        data = answer["data"]

        text = "### Ranking Results\n"

        for r in data:
            sec = r["Section"].replace("_", " ").title()
            text += f"- **{sec}** → Item `{r['Item ID']}` (Rank {r['Rank']})\n"

        return text
    # =================================
    #          ITEM  RANK
    # =================================
    elif answer["type"] == "item_rank":

        data = answer["data"]

        return f"""

    ### Item Rank

    **Item ID:** `{data['Item ID']}`

    **Rank:** {data['Rank']}

    """

    # =================================
    #        RANK EXPLANATION
    # =================================

    elif answer["type"] == "rank_explanation":

        data = answer["data"]

        return f"""
    ### Rank Explanation

    **Item ID:** `{data['Item ID']}`

    **Rank:** {data['Rank']}

    **Explanation:**
    {data['Explanation']}
    """

    # =================================
    #          INVALID SECTION
    # =================================
    elif answer["type"] == "invalid_section_query":

        data = answer["data"]

        section = data["Actual Section"].replace("_", " ").title()

        return f"""

    ### Section Clarification

    **Item ID:** `{data['Item ID']}`

    This item was placed in **{section}**.

    However, the section mentioned in your question **does not exist in the dataset**.

    """

    # =================================
    #        SECTION NEGATION
    # =================================

    elif answer["type"] == "section_negation":

        data = answer["data"]

        actual = data["Actual Section"].replace("_", " ").title()

        not_section = data["Not Section"].replace("_", " ").title()

        actual_reason = data.get("Actual Reason", "No explanation available.")

        not_reason = data.get("Not Reason", "No explanation available.")

        return f"""

    ### Section Clarification


    **Item ID:** `{data['Item ID']}`


    This item belongs to **{actual}**.


    **Reason:**

    {actual_reason}


    ---


    It does **not belong to {not_section}**.


    **Reason:**

    {not_reason}

    """
    # =================================
    #          ITEM LIST
    # =================================

    elif answer["type"] == "section_item_list":

        data = answer["data"]

        section = data["Section"].replace("_", " ").title()
        count = data["Count"]
        items = data["Items"]

        text = f"### Items in {section}\n\n"
        text += f"**Number of items:** {count}\n\n"
        text += "**Item IDs:**\n"

        for item in items:
            text += f"- {item}\n"

        return text

    # =================================
    #          ITEM UNSELECTED
    # =================================
    elif answer["type"] == "unselected_reasoning":

        data = answer.get("data", {})

        text = "### Unselected Item Explanation\n\n"
        text += f"**Item ID:** `{data.get('Item ID', 'Unknown')}`\n\n"

        section_reasons = data.get("Section_Reasons") or []

        for sec in section_reasons:
            section_raw = sec.get("Section")
            reason_raw = sec.get("Reason")

            section = str(section_raw).replace("_", " ").title() if section_raw else "Unknown Section"
            reason = reason_raw if reason_raw else "No reason available."

            text += f"**{section}**\n"
            text += f"Reason for not selecting:\n{reason}\n\n"

        text += "**Conclusion:** The item does not meet the criteria for any section, therefore it was placed in **Unselected**."

        return text


    # =================================
    #          AGGREGATION
    # =================================
    # Shows number of items in each section

    elif answer["type"] == "aggregation":

        text = "### Items per Section\n"

        for sec, count in answer["data"].items():
            readable = sec.replace("_", " ").title()

            text += f"- {readable}: {count}\n"

        return text


    # =================================
    #         SECTION COUNTS
    # =================================
    # Alternative output for section distribution

    elif answer["type"] == "section_counts":

        text = "### Items per Section\n"

        for sec, count in answer["data"].items():
            readable = sec.replace("_", " ").title()

            text += f"- {readable}: {count}\n"

        return text


    # =================================
    #         BASIC ITEM INFO
    # =================================
    # Simple fallback item information

    elif answer["type"] == "item":

        item = answer["data"]

        return f"""
### Item Information

**Item ID:** {item['Item ID']}

**Headline:**  
{item['Headline']}
"""


    # =================================
    #         ITEM LOCATION
    # =================================
    # Returns section location for an item

    elif answer["type"] == "item_location":

        data = answer["data"]

        section = data["Section"].replace("_", " ").title()

        return f"""

### Item Location

**Item ID:** `{data['Item ID']}`

**Section:** {section}

"""


    # =================================
    #           SENTIMENT
    # =================================
    # Displays sentiment analysis results
    elif answer["type"] == "sentiment":

        data = answer["data"]

        return f"""
    ### Sentiment Analysis

    **Item ID:** {data['Item ID']}

    **Sentiment:** {data['Sentiment']}

    **Explanation:**
    {data['Explanation']}
    """

    # =================================
    #              ERROR
    # =================================
    # Displays errors returned by API

    elif answer["type"] == "error":

        return f"⚠️ {answer['data']}"


    return str(answer)


# =================================
#           CHAT HISTORY
# =================================
# Stores conversation history in session state

if "messages" not in st.session_state:
    st.session_state.messages = []


# =================================
#        DISPLAY CHAT HISTORY
# =================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.write(message["content"])


# =================================
#           USER INPUT
# =================================
# Chat input box for asking questions

prompt = st.chat_input("Ask something about the dataset...")


# =================================
#        PROCESS USER QUERY
# =================================

if prompt:

    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.write(prompt)


    # Generate assistant response
    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            try:

                response = requests.post(
                    API_URL,
                    json={"question": prompt},
                    timeout=30
                )

                if response.status_code == 200:

                    result = response.json()["answer"]

                    formatted = format_response(result)

                else:

                    formatted = f"API Error: {response.status_code}"

                st.write(formatted)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": formatted
                })

            except requests.exceptions.Timeout:
                st.error("API request timed out.")

            except Exception as e:
                st.error(f"Could not connect to API: {e}")