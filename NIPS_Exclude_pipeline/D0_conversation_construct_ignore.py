import time
import openai
import json
import random
import requests

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from topic import conversation_topic_list

from filelock import FileLock

def save_incrementally(data, file_path):
    lock_path = file_path + ".lock" 
    lock = FileLock(lock_path)
    try:
        with lock:  # 加锁
            with open(file_path, "a", encoding="utf-8") as f:
                for entry in data:
                    json.dump(entry, f, ensure_ascii=False)
                    f.write("\n")
    except Exception as e:
        print(f"Error saving data: {e}")


client = Get()
model = ''
temperature = 1

conversation_rounds_list = [3, 4, 5]
conversation_style_list = ["Formal", "Casual", "Persuasive", "Analytical", "Creative", "Narrative", "Enthusiastic"]
quotation_length_list = ["sentence", "paragraph"]
target_ability_list = ["Negative/Ignore Quoting Ability (Omitting or Hiding Selected Regions)"]
base_mission_type_list = [
    "Summarize After Ignoring Selected Passages: The user designates one or more passages to be "ignored." The task is to summarize only the remaining, non-ignored content. The answer must exclude or skip any information from the ignored portions.",
    "Sensitive Information Hiding: The user selects private or confidential text or daat to be hidden. The final output must not reveal the ignored data. The user wants only the non-sensitive parts to be disclosed.",
    "Partial Anonymization or Redaction: The user specifically wants certain fields or details (like names, addresses, IDs) to be redacted. The task is to remove or mask those sensitive elements while preserving the rest of the information.",
    "Summarize Unignored Sections: The user designates one or more passages to be ignored. The model must produce a concise summary only of the content not in those ignored passages. The ignored content should not influence or appear in the summary.",
    "Sort or Rank Unignored Data/Number: After ignoring specific segments, the user asks the model to sort or rank remaining items based on a certain criterion (e.g., numerical values, alphabetical order, etc.). Only the leftover textual details (not ignored) should be used to perform the sorting or ranking.",
    "Extract Keywords from Non-Ignored Content: The user designates some passages to be ignored and then requests keyword extraction. The model must parse only the remaining (unignored) text to identify relevant or significant keywords without referencing any ignored sections.",
    "Named Entity or Concept Extraction (Non-Ignored Only): The user designates specific passages to ignore. The model must identify named entities (people, locations, organizations, etc.) or key concepts only from the remaining text. Any details found in ignored content should be excluded.",
    "Non-Ignored Outline Generation: The user instructs the model to create an outline (e.g., bullet points or a structured plan) of the leftover information after certain portions are ignored. The resulting outline must reflect only the visible (unignored) details.",
    "Compare Remaining data/number After Ignoring: The user designates certain passages to be omitted. The question is then to compare the data/number in only the remaining information. The solution should not incorporate any data from the ignored content.",
]

def generate_prompt():
    conversation_rounds = random.choice(conversation_rounds_list)
    conversation_rounds = str(conversation_rounds)
    conversation_topic = random.choice(conversation_topic_list)
    conversation_style = random.choice(conversation_style_list)
    target_ability = random.choice(target_ability_list)
    quotation_length = random.choice(quotation_length_list)
    mission_type = random.choice(base_mission_type_list)
    # if ("Summarize After Ignoring Selected Passages" in mission_type) or ("Summarize Unignored Section" in mission_type) or ("Extract Keywords from Non-Ignored Content" in mission_type):
    quotation_length = "paragraph"
    return {
        "conversation_rounds": conversation_rounds,
        "conversation_topic": conversation_topic,
        "target_ability": target_ability,
        "mission_type": mission_type,
        "quotation_length": quotation_length,
        "conversation_style": conversation_style,
        "prompt": f'''You are an expert conversation architect. Generate a multi-round conversation that will later be used to test specific Large Language Model abilities. Follow these instructions strictly:

Conversation Attributes:
   - This conversation is intended to assess the LLM's {target_ability} in real-world scenarios, focusing on the mission type of {mission_type}.
   - In this context, "Quotation" refers to marking specific parts of the conversation that are intended to be ignored when answering questions. Later tasks will require the model to completely ignore these designated quotation parts and answer based solely on the remaining information.
   - The conversation must contain multiple candidate quotation regions. Each candidate region must be an **exact** verbatim copy of a segment (of length {quotation_length}) from the conversation text.
   - The conversation's content should be constructed so that if the designated quotation parts are ignored, the answer to a question on the mission type {mission_type} can be derived exclusively from the remaining information. Conversely, if the ignored parts are mistakenly used, they would lead to an a different conclusion.
   - The conversation should be centered on a specific subtopic of {conversation_topic}.
   - The conversation should have at least {conversation_rounds} rounds.
   - The style of the conversation should be {conversation_style}.
   - The conversation must include at least {conversation_rounds} distinct information points (data, entities, theories, figures, etc.) across different turns, all at the **same information level** and focus on one aspect. For example, discuss the temperature in different cities on the same day, or the different view about one theory.
   - Avoid global overviews, aggregated summaries, or comparisons in conversation.
   - Each round should focus on a different aspect or detail of the same topic. "Different" doesn't imply incorrect but rather multiple facets of a single subject.
   - Fictional content is allowed, as long as it remains logically consistent and coherent.

Generation Requirements:
   - Generate a `<subtopic>` section specifying the exact subtopic within {conversation_topic}.
   - Then provide a `<Planning>` section where you outline (1) at least {conversation_rounds} distinct information points and (2) the logical flow for the conversation.
   - After `<Planning>`, produce a `<Generation>` section with the multi-round conversation. Each user turn begins with `<|user|>\n` and ends with `<|end|>\n`. Each assistant turn begins with `<|assistant|>\n` and ends with `<|end|>\n>.
   - Do **not** generate any question for the model to answer in this prompt. You are only creating the conversation and candidate quotations itself.

**Key Addition: Candidate Quotation Parts (for Ignoring)**
   - After the conversation, create several blocks starting with `<|quotationx|>\n` and ending with `<|end|>\n` that contain **exactly one** {quotation_length} segment copied verbatim from the conversation text.
   - These candidate quotation parts represent content that will later be designated to be ignored when answering questions. They must be taken exactly as they appear in the conversation.
   - Ensure that these candidate quotations include significant information so that if they are not ignored later, they could lead to a completely different answer than when they are properly omitted.

Below is the conversation template (do not introduce any other labels beyond what is specified):
<subtopic>
[Describe the specific subtopic, e.g., "various local regulations on xx technology", "Comparing the prices of different car models in various regions", "Chronology of events in the evolution of renewable energy technology." etc.]</subtopic>
<Planning>
Ensure that the characteristics of the conversation and candidate quotation parts (information richness, distinct information points, quotation length, etc.) are fully considered to meet the requirements for evaluating the negative/ignore quoting ability and mission type.
1. Define {conversation_rounds} distinct information points at the same information level, ensuring logical flow.
   - Point 1: [One piece of information]
   - Point 2: [Another piece of information]
   - ...
2. Ensure the conversation meets all above attributes, creating a scenario where ignoring a specific {quotation_length} copied segment is critical.</Planning>
<Generation>
<|user|>
[User's initial query about one specific aspect of the subtopic]<|end|>
<|assistant|>
[Assistant's response]<|end|>
[Repeat for {conversation_rounds} rounds, each round focusing on a different detail or data point]

<|quotation1|>
[Copy here the full response from the conversation text, verbatim, as one candidate quotation part]<|end|>
<|quotation2|>
[Copy here the full response from the conversation text, verbatim, as another candidate quotation part]<|end|>
[Copy more candidate quotation parts for each information points]
'''
}

responses = []
output_file = ""
batch_size = 10
for _ in range(int(1000/batch_size)):
    batch_responses = []
    print(_)
    for i in range(batch_size):
        prompt_data = generate_prompt()
        response = client.calc(
            query=[{"role": "user", "content": prompt_data["prompt"]}],
            temp=temperature,
            n=1,
            model=model
        )

        for resp in response:
            conversation_data = {
                "conversation": resp,
                "attributes": {
                    "conversation_rounds": prompt_data["conversation_rounds"],
                    "conversation_topic": prompt_data["conversation_topic"],
                    "target_ability": prompt_data["target_ability"],
                    "mission_type": prompt_data["mission_type"],
                    "quotation_length": prompt_data["quotation_length"],
                    "conversation_style": prompt_data["conversation_style"]
                }
            }
            batch_responses.append(conversation_data)

    # Incrementally save batch
    save_incrementally(batch_responses, output_file)

print(f"Responses incrementally saved to {output_file}")
#  Please begin by analyzing the question, then provide the answer in the format: 'The answer is [option].'