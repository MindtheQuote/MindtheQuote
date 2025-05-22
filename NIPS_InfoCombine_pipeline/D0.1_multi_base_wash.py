import re
from typing import Optional, Dict
import json
import argparse
def read_jsonl_file(file_path: str) -> list:
    data_list = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data_list.append(json.loads(line))
    return data_list

def write_list_to_json(data_list: list, file_path: str) -> None:
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data_list, f, ensure_ascii=False, indent=4)

def process_string(input_dict) -> Optional[Dict[str, str]]:
    input_str = input_dict["conversation"]
    new_dict = {}

    subtopic_matches = re.findall(r'<subtopic>(.*?)</subtopic>', input_str, re.DOTALL)
    if len(subtopic_matches) != 1:
        print("subtopic_matches")
        return None
    subtopic_text = subtopic_matches[0].strip(" \n")
    new_dict["subtopic"] = subtopic_text

    gen_index = input_str.find("<Generation>")
    if gen_index == -1:
        print("未找到<Generation>")
        return None
    input_str = input_str[gen_index + len("<Generation>"):]
    input_str = input_str.strip(" \n")

    input_str = input_str.replace("**", "")

    input_str = re.sub(r'[ \n]*(<\|[^<>|]+\|>)[ \n]*', r'\1', input_str)

    input_str = re.sub(r'[ \n]+', ' ', input_str)

    input_str = re.sub(r'(<\|[^<>|]+\|>)', r'\1\n', input_str)

    illegal_patterns = [
        r'<[^<>|]+\|>',  # <xxx|>
        r'<\|[^<>|]+>',  # <|xxx>
        r'<(?!\|(?:user|end|assistant|quotation\d+)\|>)[^<>|]+>'  # <xxx>
    ]
    
    for pattern in illegal_patterns:
        if re.search(pattern, input_str):
            print("illegal_patterns")
            return None

    quotation_blocks = list(re.finditer(r'<\|quotation\d+\|>\n.*?<\|end\|>\n', input_str, re.DOTALL))
    if quotation_blocks:
        last_quotation_end = quotation_blocks[-1].end()
        input_str = input_str[:last_quotation_end] 

    conversation_pattern = r'(?:<\|user\|>\n.*?<\|end\|>\n<\|assistant\|>\n.*?<\|end\|>\n){1,}'
    quotation_pattern = r'(?:<\|quotation\d+\|>\n.*?<\|end\|>\n){3,}'
    full_pattern = r'^' + conversation_pattern + quotation_pattern + r'$'
    if not re.fullmatch(full_pattern, input_str, re.DOTALL):
        print("fullmatch")
        return None

    quotation_start = re.search(r'<\|quotation\d+\|>', input_str)
    if not quotation_start:
        print("quotation_start")
        return None
    conversation_part = input_str[:quotation_start.start()]
    new_dict["conversation"] = conversation_part

    quotation_iter = re.finditer(r'<\|quotation(\d+)\|>\n(.*?)<\|end\|>\n', input_str, re.DOTALL)
    quotations = {}
    prev_num = 0
    for m in quotation_iter:
        num = int(m.group(1)) 
        if num != prev_num + 1:
            return None
        prev_num = num
        content = m.group(2)
        quotations[f"quotation{num}"] = content

    if prev_num < 3:
        print("prev_num < 3")
        return None

    if len(quotations) != len(set(quotations.values())):
        return None

    for key, content in quotations.items():
        if content not in conversation_part:
            print("content not in conversation_part")
            return None
        new_dict[key] = content

    new_dict["attributes"] = input_dict["attributes"]
    return new_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")

    parser.add_argument("--input_jsonl", type=str, help="")
    parser.add_argument("--output_json", type=str, help="")

    args = parser.parse_args()
    file_path = args.input_jsonl
    save_path = args.output_json

    all_data = read_jsonl_file(file_path)
    save_all_data = []
    i=0
    for each_data in all_data:
        # print(i)
        output_data = process_string(each_data)
        if output_data:
            i+=1
            save_all_data.append(output_data)
        else:
            i+=1
            continue

    write_list_to_json(save_all_data, save_path)