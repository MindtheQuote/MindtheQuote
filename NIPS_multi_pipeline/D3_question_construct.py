import json
import re
from itertools import combinations
import random
import copy
import argparse
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
        reference_keys = [key for key in data.keys() if key.startswith("Reference")]
        answer_keys = [key for key in data.keys() if key.startswith("Answer")]

        # Ensure ReferenceN and AnswerN are one-to-one and valid
        if not (len(reference_keys) == len(answer_keys) >= 3 and
                all(int(key.split("Reference")[1]) == i + 1 for i, key in enumerate(reference_keys)) and
                all(int(key.split("Answer")[1]) == i + 1 for i, key in enumerate(answer_keys))):
            continue  # Discard this data if conditions are not met

        # Generate multiple-choice questions
        for i, (ref_key, ans_key) in enumerate(zip(reference_keys, answer_keys)):
            new_dict = {}

            # Add basic information to new_dict
            new_dict["conversation"] = data.get("conversation", "")
            new_dict["Question"] = data["Question"]
            new_dict["Reference"] = data[ref_key]  # ReferenceN becomes Reference

            Reference_text = []
            for item in new_dict["Reference"]:
                Reference_text.append(data[item])
            new_dict["Reference_text"] = copy.deepcopy(Reference_text)

            new_dict["gt_label"] = data[ans_key]  # Correct answer

            # Select distractors (randomly choose two other answers)
            other_answers = [data[ak] for ak in answer_keys if ak != ans_key]
            distractors = random.sample(other_answers, 2)
            new_dict["distractor1"], new_dict["distractor2"] = distractors

            # Add remaining keys
            new_dict["id"] = data["id"]
            new_dict["attributes"] = data.get("attributes", {})

            # Step 3: Check if Reference is sorted correctly
            reference_quotations = new_dict["Reference"]
            quotation_numbers_in_reference = [int(re.search(r'quotation(\d+)', q).group(1)) for q in reference_quotations]
            if quotation_numbers_in_reference != sorted(quotation_numbers_in_reference):
                continue  # Discard this new_dict if Reference is not sorted

            # Reorder keys
            ordered_keys = ["conversation", "Question", "Reference", "Reference_text", "gt_label", "distractor1", "distractor2", "id", "attributes"]
            new_dict = {key: new_dict[key] for key in ordered_keys}
            complement = list(set(quotation_keys) - set(new_dict["Reference"]))
            complement = [x for x in quotation_keys if x not in set(new_dict["Reference"])]
            new_dict["Ignore"] = copy.deepcopy(complement)

            Ignore_text = []
            for item in new_dict["Ignore"]:
                Ignore_text.append(data[item])
            new_dict["Ignore_text"] = copy.deepcopy(Ignore_text)

            # Append the new_dict to the list
            new_data_list.append(new_dict)

    # Save the processed data to a new JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_data_list, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")

    parser.add_argument("--input_json", type=str, help="")
    parser.add_argument("--output_json", type=str, help="")

    args = parser.parse_args()
    input_file = args.input_json
    output_file = args.output_json

    process_cleaned_data(input_file, output_file)