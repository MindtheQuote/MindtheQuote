import json
import re
from itertools import combinations
import random
import copy
def process_cleaned_data(input_file, output_file):
    # Step 1: Read the cleaned data from the JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        cleaned_data_list = json.load(f)

    new_data_list = []
    id_counter = 0  # Initialize ID counter

    for data in cleaned_data_list:
        # Extract all quotation keys and check their validity
        quotation_keys = [key for key in data.keys() if key.startswith("quotation")]
        quotation_numbers = sorted([int(re.search(r'quotation(\d+)', key).group(1)) for key in quotation_keys])

        # Check if quotation numbers start from 1 and are consecutive
        if not (quotation_numbers == list(range(1, len(quotation_numbers) + 1)) and len(quotation_numbers) >= 3):
            continue  # Discard this data if conditions are not met

        # Add an "id" key to the data
        data["id"] = id_counter
        id_counter += 1

        # Step 2: Construct multiple-choice questions
        ignore_keys = [key for key in data.keys() if key.startswith("Ignore")]
        answer_keys = [key for key in data.keys() if key.startswith("Answer")]

        # Ensure IgnoreN and AnswerN are one-to-one and valid
        if not (len(ignore_keys) == len(answer_keys) >= 3 and
                all(int(key.split("Ignore")[1]) == i + 1 for i, key in enumerate(ignore_keys)) and
                all(int(key.split("Answer")[1]) == i + 1 for i, key in enumerate(answer_keys))):
            continue  # Discard this data if conditions are not met

        # Generate multiple-choice questions
        for i, (ref_key, ans_key) in enumerate(zip(ignore_keys, answer_keys)):
            new_dict = {}

            # Add basic information to new_dict
            new_dict["conversation"] = data.get("conversation", "")
            new_dict["Question"] = data["Question"]
            new_dict["Ignore"] = data[ref_key]  # IgnoreN becomes Ignore

            Ignore_text = []
            for item in new_dict["Ignore"]:
                Ignore_text.append(data[item])
            new_dict["Ignore_text"] = copy.deepcopy(Ignore_text)

            new_dict["gt_label"] = data[ans_key]  # Correct answer

            # Select distractors (randomly choose two other answers)
            other_answers = [data[ak] for ak in answer_keys if ak != ans_key]
            distractors = random.sample(other_answers, 2)
            new_dict["distractor1"], new_dict["distractor2"] = distractors

            # Add remaining keys
            new_dict["id"] = data["id"]
            new_dict["attributes"] = data.get("attributes", {})

            # Step 3: Check if Ignore is sorted correctly
            ignore_quotations = new_dict["Ignore"]
            quotation_numbers_in_ignore = [int(re.search(r'quotation(\d+)', q).group(1)) for q in ignore_quotations]
            if quotation_numbers_in_ignore != sorted(quotation_numbers_in_ignore):
                continue  # Discard this new_dict if Ignore is not sorted

            # Reorder keys
            ordered_keys = ["conversation", "Question", "Ignore", "Ignore_text", "gt_label", "distractor1", "distractor2", "id", "attributes"]
            new_dict = {key: new_dict[key] for key in ordered_keys}

            # Append the new_dict to the list
            new_data_list.append(new_dict)

    # Save the processed data to a new JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_data_list, f, ensure_ascii=False, indent=4)

# Example usage
input_file = ""
output_file = ""
process_cleaned_data(input_file, output_file)