import json
import random
import argparse
def read_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data_list, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, ensure_ascii=False, indent=4)

def extract_quotation_numbers(cleaned_data):
    all_quotations = set()
    for data in cleaned_data:
        for key, value in data.items():
            if key.startswith("Reference") or key.startswith("Background"):
                all_quotations.update(value)
    quotation_numbers = sorted(int(q.split("quotation")[1]) for q in all_quotations)
    expected_numbers = list(range(1, len(quotation_numbers) + 1))
    return quotation_numbers == expected_numbers and len(quotation_numbers) >= 3

def extract_all_quotations(data):
    all_quotations = set()
    for key, value in data.items():
        if key.startswith("Reference") or key.startswith("Background"):
            all_quotations.update(value)
    return all_quotations


def generate_new_dicts(cleaned_data):
    new_dicts = []
    id_counter = 0

    for data in cleaned_data:
        try:
            reference_keys = sorted([k for k in data.keys() if k.startswith("Reference")], key=lambda x: int(x[9:]))
            background_keys = sorted([k for k in data.keys() if k.startswith("Background")], key=lambda x: int(x[10:]))
            answer_keys = sorted([k for k in data.keys() if k.startswith("Answer")], key=lambda x: int(x[6:]))
            if not (len(reference_keys) == len(background_keys) == len(answer_keys) >= 2):
                print("len(reference_keys) == len(background_keys) == len(answer_keys) < 2")
                continue
            if [int(k[9:]) for k in reference_keys] != list(range(1, len(reference_keys) + 1)):
                print("int(k[9:]) for k in reference_keys] != list(range(1, len(reference_keys) + 1)")
                continue

            all_quotations = extract_all_quotations(data)

            for i in range(len(reference_keys)):
                ref_key = reference_keys[i]
                bg_key = background_keys[i]
                ans_key = answer_keys[i]

                new_dict = {
                    "Reference": data[ref_key],
                    "Background": data[bg_key],
                    "gt_label": data[ans_key],
                    "distractor1": None,
                    "distractor2": None,
                    "conversation": data.get("conversation", ""),
                    "Question": data["Question"],
                    "id": id_counter,
                    "attributes": data.get("attributes", {})
                }

                other_answers = [data[k] for k in answer_keys if k != ans_key]
                distractors = random.sample(other_answers, 1)
                new_dict["distractor1"] = distractors
                new_dict["distractor2"] = ""
                if set(data[ref_key]) & set(data[bg_key]):
                    continue

                ref_numbers = [int(q.split("quotation")[1]) for q in data[ref_key]]
                if ref_numbers != sorted(ref_numbers):
                    data[ref_key] = [f"quotation{num}" for num in sorted(ref_numbers)]
                    new_dict["Reference"] = data[ref_key]
                
                for key, value in data.items():
                    if key.startswith("quotation"):
                        new_dict[key] = value

                new_dicts.append(new_dict)
            id_counter += 1
        

        except Exception as e:
            continue

    return new_dicts

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")

    parser.add_argument("--input_json", type=str, default='', help="")
    parser.add_argument("--output_json", type=str, default='', help="")

    args = parser.parse_args()
    input_file = args.input_json
    output_file = args.output_json

    cleaned_data = read_json(input_file)

    new_dicts = generate_new_dicts(cleaned_data)

    save_json(new_dicts, output_file)