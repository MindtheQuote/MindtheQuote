import time
import openai
import json
import random
import requests
import argparse
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from topic import conversation_topic_list

def save_incrementally(data, file_path):
    with open(file_path, "a", encoding="utf-8") as f:
        for entry in data:
            json.dump(entry, f, ensure_ascii=False)
            f.write("\n")

client = Get()
temperature = 7

conversation_rounds_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
information_points_list = [3, 4, 5, 6]
conversation_style_list = ["Formal", "Casual", "Persuasive", "Analytical", "Creative", "Narrative", "Enthusiastic"]
quotation_length_list = ["full sentence", "full paragraph", "full paragraph", "full paragraph"]
target_ability_list = ["Reference and Contextual Response"]
base_mission_type_list = [
    ["Price Comparison Based on Quoted Reference: When the reference quotation specifies a particular item (e.g., "Item B: 8 dollar") and background quotations list prices of other items (e.g., "Item A: 10 dollar" and "Item C: 5 dollar"), the model must compare these figures. The answer should identify which background item is more expensive than the referenced one, strictly based on the provided numerical data.", "The conversation is designed to present pricing information in a balanced manner across multiple turns. Each pricing detail is stated with equal authority, ensuring that one candidate quotation serves as the reference item and others as background data. The dialogue must provide multiple, identical-level descriptions of item prices so that, when only candidate quotations are used, the model can unambiguously compare the reference price with the background prices."],
    ["Temporal Sequence Reasoning with Context: With a reference quotation indicating an event with a specific date (e.g., "Event Y occurred on March 5th") and background quotations listing other events with their dates (e.g., "Event X occurred on March 1st" and "Event Z occurred on February 28th"), the model must determine the chronological relationship. The answer should identify which event happened before or after the reference event, solely using the provided dates.", "The conversation must include multiple, equally weighted descriptions of event dates and their chronological order. One or more candidate quotations must serve as the reference event(s) while others offer background temporal details. The dialogue is constructed so that the same event is described redundantly, enabling the model to later extract candidate quotations that unambiguously support the determination of the sequence solely from the provided quotations."],
    ["Attribute Comparison Across Context and Reference: When the reference quotation provides a measurable attribute of an item (e.g., "Product Y has a rating of 4.0 stars") and background quotations offer similar attributes for other items (e.g., "Product X: 4.5 stars" and "Product Z: 4.8 stars"), the model must perform a direct comparison. The answer should specify which products have higher (or lower) values than the referenced product.", "The conversation is structured to offer multiple, same-level descriptions of specific attribute values for various items. One candidate quotation must clearly define the reference attribute value, while others provide background information for comparison. The dialogue ensures that all items are described with equal prominence, so that if only candidate quotations are selected, the model can accurately compare the reference attribute with the background attributes."],
    ["Contextual Cause-Effect Linkage: Given a reference quotation that states an effect or recommendation (e.g., "You should replace the cooling fan immediately") and a background quotation that provides a cause (e.g., "The device overheated due to prolonged usage"), the model must link the effect to its cause. The answer should clearly state that the recommendation is based on the background cause.", "The conversation must deliver equal-level, redundant descriptions of an effect (or recommendation) and its underlying cause. One candidate quotation is designated as the reference effect, while one or more provide background causal information. The dialogue is organized so that both the reference and the background are described without hierarchical bias, enabling the model to deduce the causal linkage exclusively from the candidate quotations."],
    ["Contextual Selection Based on Criteria: Provided a reference quotation that highlights a particular preference or criterion (e.g., selecting an item with a specific price point) along with background quotations listing various items and their attributes, the model must select the items from the background that meet the criterion specified by the reference. The answer should list only those items that conform to the given requirement.", "The conversation is designed to offer multiple, parallel descriptions of filtering criteria and corresponding item details. The reference candidate quotation must state the filtering standard, while background candidate quotations list items with their attributes. The dialogue ensures that all relevant details are presented at the same level, so that if only candidate quotations are used, the model can filter the items accurately based solely on the provided text."],
    ["Direct Comparison with Context Integration: With a reference quotation that specifies a particular detail (e.g., "Item B costs 7.3 dollar") and background quotations that offer comparable details for other items (e.g., "Item A costs 20 dollar" and "Item C costs 2 dollar"), the model must directly compare these details. The answer should indicate which background item stands out relative to the reference.", "The conversation is arranged to include redundant, same-level statements of numerical data. One candidate quotation presents a specific numerical value as the reference, while background candidate quotations offer other numerical values for direct comparison. The dialogue must ensure that every numerical detail is provided uniformly, allowing the model to perform an unambiguous comparison using only the candidate quotations."],
    ["Integrated Inference from Reference and Context: The model receives a reference quotation that implies a decision or inference (e.g., "You should leave earlier tomorrow") alongside background quotations that supply supporting context (e.g., "Traffic is usually heavy during rush hour"). The answer should integrate both to deduce the rationale behind the reference statement.", "The conversation must incorporate multiple, equally weighted descriptions of a decision or inference scenario. One candidate quotation delivers the reference statement, while the background candidate quotations offer complementary information needed for synthesis. The dialogue is structured so that all relevant pieces of information are described redundantly, ensuring that if only candidate quotations are available, the model can integrate them to derive the intended inference."],
    ["Contextual Elaboration of a Reference Statement: Given a reference quotation that provides a brief statement (e.g., "It would be wise to update the software") and a background quotation that offers additional detail (e.g., "The system has been experiencing bugs due to outdated software"), the model must elaborate on the reference. The answer should explain that the recommendation is based on the issues mentioned in the background.", "The conversation is crafted to provide succinct reference statements alongside detailed background descriptions, both given at the same level of authority. Candidate quotations are generated for the reference and the background without hierarchy, ensuring that if only these quotations are extracted, the model can expand the reference content accurately based solely on the available background information."],
    ["Quantitative Comparison with Contextual Data: When a reference quotation contains a quantitative figure (e.g., "Service B costs 20 dollars") and background quotations list similar figures for other services (e.g., "Service A costs 25 dollars" and "Service C costs 15 dollars"), the model must perform a quantitative comparison. The answer should specify which background figure exceeds or falls below the reference figure.", "The conversation must present quantitative data in a uniform manner across multiple turns. One candidate quotation must clearly state the reference numerical value, while background candidate quotations include additional quantitative details. The dialogue is constructed so that all numbers are described with equal prominence, ensuring that if only candidate quotations are used, the model can perform an accurate quantitative comparison."],
    ["Relative Ranking Determination: With a reference quotation providing a metric for an item (e.g., "Model Y has a battery life of 8 hours") and background quotations offering comparable metrics for other models (e.g., "Model X: 10 hours" and "Model Z: 7 hours"), the model must rank the items. The answer should clearly state which models rank higher or lower than the referenced one based on the provided metrics.", "The conversation is designed to include multiple same-level descriptions of items’ evaluation metrics or rankings. One candidate quotation provides the reference metric, while background candidate quotations offer corresponding metrics for other items. The dialogue ensures that every description is of equal weight, so that if only candidate quotations are extracted, the model can unambiguously determine the relative ranking of the items."],
    ["Conditional Outcome Reasoning: Provided a reference quotation that states a conditional suggestion (e.g., "If you experience overheating, turn off the device immediately") along with background quotations that supply the condition (e.g., "The device’s temperature has been rising steadily"), the model must deduce the correct outcome. The answer should confirm the conditional recommendation based solely on the provided background.", "The conversation must deliver redundant, equally weighted descriptions of conditional statements and the relevant conditions. A candidate quotation must state the reference condition or suggestion, while background candidate quotations provide the necessary supporting context. The dialogue is organized such that if only candidate quotations are used, the model can deduce the correct outcome solely from the provided conditions."],
    ["Multiple Criteria Filtering: When a reference quotation emphasizes a specific criterion (e.g., "I prefer an affordable product") and background quotations list several items with various attributes (e.g., price, quality), the model must filter the background to identify only those items meeting the reference criterion. The answer should list the items that match the affordability requirement as provided in the background.", "The conversation is structured to include multiple, parallel descriptions of a set of filtering criteria and corresponding item attributes. The reference candidate quotation articulates the filtering standards, while background candidate quotations list the items’ attributes in equal detail. The dialogue ensures that every criterion and item is described uniformly, enabling the model to filter the items based solely on the candidate quotations."],
    ]
def generate_prompt():
    conversation_rounds = random.choice(conversation_rounds_list)
    if conversation_rounds==1 or conversation_rounds==2:
        information_points = random.choice(information_points_list)
    else:
        information_points = conversation_rounds

    conversation_topic = random.choice(conversation_topic_list)
    conversation_style = random.choice(conversation_style_list)
    target_ability = random.choice(target_ability_list)
    quotation_length = random.choice(quotation_length_list)
    selected_mission_type_list = random.choice(base_mission_type_list)
    mission_type = selected_mission_type_list[1]
    return {
        "conversation_rounds": conversation_rounds,
        "information_points": information_points,
        "conversation_topic": conversation_topic,
        "selected_mission_type_list": selected_mission_type_list,
        "target_ability": target_ability,
        "mission_type": mission_type,
        "quotation_length": quotation_length,
        "conversation_style": conversation_style,
        "prompt": f'''Generate a multi-round conversation that will later be used to test the LLM’s {target_ability} in real-world scenarios. **{mission_type}**.
Instructions:
	1.	The conversation must be centered on a specific subtopic of {conversation_topic} and include at least {conversation_rounds} rounds. The conversation style should be {conversation_style}.
	2.	The conversation must introduce at least {information_points} distinct information points (e.g., specific data, figures, dates, or viewpoints regarding a single subject). All of these information points, as well as any background context, must later be included in the candidate quotation blocks.
	3.	The conversation must be constructed so that if, later on, only some of the selected candidate quotation regions (which include both the directly quoted content and the background information) are used, a question can be answered conclusively using only that information.
	4.	After the conversation, output all candidate quotation and background regions. Each candidate quotation must be a {quotation_length} exactly copied from the conversation. These {quotation_length} should come from different parts of the conversation and represent distinct information points or background context.
	5.	Fictional content is allowed, as long as it remains logically consistent and coherent.

Conversation Requirements:
   - Generate a `<subtopic>` section that describes the specific subtopic.
   - Then create a `<Planning>` section where you list at least {conversation_rounds} distinct information points. List each information point without categorizing them as "key" or "distractor"; simply include the details that will later be available for quotation selection.
   - Next, generate a `<Generation>` section containing the multi-round conversation. Use the following format:
        Each user turn begins with `<|user|>\n` and ends with `<|end|>\n`.
        Each assistant turn begins with `<|assistant|>\n` and ends with `<|end|>\n`.
   - **Do not generate any question** for the LLM to answer in this prompt; you are only creating the conversation text and the candidate quotation parts.
   - Do not include any comparisons, versus statements, global overviews, or summaries in the conversation.
   - The content intended for candidate quotation blocks (both the direct quotes and the background information) should later be a {quotation_length}.

Candidate Quotation Regions:
After the conversation, output multiple candidate quotation blocks. Each block must follow this format:
<|quotationX|>
[Exact copy of a {quotation_length}]
<|end|>
(Where X is a sequential number.)
These candidate quotations must be exact, verbatim copies of a {quotation_length}. Do not add any additional identifiers or formatting within or around the quoted area.
"Exact copy" means that every token, symbol, and letter—including their case (uppercase or lowercase)—is precisely identical to the original conversation. The connective phrases of the {quotation_length} must also be copied. Connective phrases such as 'First', 'In addition', 'Therefore', 'Additionally', 'However', and 'For example' can appear at different positions(especially the beginning) in a sentence.
For example, for the paragraph:
Yes, a trademark must not create a likelihood of confusion with existing trademarks in the same class of goods or services...
The quotation part must include the 'Yes' in front of this part as: <|quotation1|>\nYes, a trademark must not create a likelihood of confusion with existing trademarks in the same class of goods or services...<|end|>
For another example, for the sentence:
The United States imposed a 25% tariff on steel imports in March 2018, aiming to protect domestic producers and address concerns about unfair trade practices.
The quotation part must include the entire sentence, not only the part before or after the comma. So the quotation here should be: <|quotation1|>\nThe United States imposed a 25% tariff on steel imports in March 2018, aiming to protect domestic producers and address concerns about unfair trade practices.<|end|>
Each candidate quotation must be a {quotation_length} exactly copied from the conversation.
Do not include additional symbol or marker around the quotation part, like \', \" or **.

Below is the conversation template (do not introduce any additional labels):
<subtopic>
[Describe the specific subtopic, e.g., "Comparing prices of consumer electronics in different markets" or "Timeline of technological advancements in electric vehicles."]
</subtopic>
<Planning>
Outline {information_points} distinct information points.
For example:
- Information Point 1: [A specific data point, such as "Smartphone A costs $699"]
- Information Point 2: [A specific data point, such as "Smartphone B costs $799"]
- Information Point 3: [A specific data point, such as "Smartphone C costs $499"]
...
Explain the logical flow of the conversation.
</Planning>
<Generation>
<|user|>
[User's initial query about an aspect of the subtopic]
<|end|>
<|assistant|>
[Assistant's response that incorporates the above information points naturally in the conversation, ensuring that parts intended for quotation (both direct quotes and background details) are present and will later be extracted as candidate quotations.]
<|end|>
...Repeat for {conversation_rounds} rounds...
<|quotation1|>
[Exact copy of one {quotation_length} containing either a direct quoted element or background context.]
<|end|>
<|quotation2|>
[Exact copy of another {quotation_length} containing either a direct quoted element or background context.]
<|end|>
[Include all candidate quotations]
'''
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")

    parser.add_argument("--output_jsonl", type=str, help="")
    parser.add_argument("--model", type=str, help="")
    parser.add_argument("--create_num", type=str, default='200', help="")

    args = parser.parse_args()
    output_file = args.output_jsonl
    model = args.model
    create_num = int(args.create_num)

    responses = []
    batch_size = 10
    for _ in range(int(create_num/batch_size)):
        batch_responses = []
        print(_)
        for i in range(batch_size):
            print(i)
            prompt_data = generate_prompt()
            response, _ = client.calc(
                query=prompt_data["prompt"],
                temp=temperature,
                model=model
            )

            for resp in response:
                conversation_data = {
                    "conversation": resp,
                    "attributes": {
                        "conversation_rounds": prompt_data["conversation_rounds"],
                        "information_points": prompt_data["information_points"],
                        "conversation_topic": prompt_data["conversation_topic"],
                        "target_ability": prompt_data["target_ability"],
                        "selected_mission_type_list": prompt_data["selected_mission_type_list"],
                        "mission_type": prompt_data["mission_type"],
                        "quotation_length": prompt_data["quotation_length"],
                        "conversation_style": prompt_data["conversation_style"],
                        "model": model
                    }
                }
                batch_responses.append(conversation_data)

        # Incrementally save batch
        save_incrementally(batch_responses, output_file)

    print(f"Responses incrementally saved to {output_file}")
    #  Please begin by analyzing the question, then provide the answer in the format: 'The answer is [option].'