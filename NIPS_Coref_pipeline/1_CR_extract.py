import pandas as pd
import json
from transformers import AutoTokenizer
import random
from tqdm import tqdm
import re

def construct_coref_questions(parquet_file_path, output_json_path):
    data = pd.read_parquet(parquet_file_path)
    tokenizer = AutoTokenizer.from_pretrained("tokenizer")
    
    questions = []
    
    for row in tqdm(data.values, desc="处理行"):
        clauses = row[0]     
        paragraph = row[2]      
        coref_chains = row[3]  

        if len(coref_chains) < 4:
            continue
        
        context_tokens = []
        context_with_select_tokens = [] 
        token_char_spans = [] 
        current_char = 0
        
        for clause in clauses:
            for token in clause['tokens']:
                token_text = token['text']
                if context_tokens:
                    if token_text in [".", ",", "!", "?", ";", ":", "'", "\"", ")", "]", "}", "’", "'s", "'re", "'ve", "'d", "n't", "'m", "'ll"]:
                        pass
                    else:
                        context_tokens.append(" ")
                        context_with_select_tokens.append(" ")
                        current_char += 1 
                context_tokens.append(token_text)
                context_with_select_tokens.append(token_text)
                start_char = current_char
                end_char = start_char + len(token_text)
                token_char_spans.append((start_char, end_char))
                current_char = end_char
        
        paragraph_text = ''.join(context_tokens)
        context_with_select_ori = ''.join(context_with_select_tokens)
        
        tokenized = tokenizer(
            paragraph_text,
            return_offsets_mapping=True,
            truncation=True
        )

        tokenizer_tokens = tokenized.tokens()
        offset_mappings = tokenized.offset_mapping
        
        char_to_token = {}
        for idx, (start, end) in enumerate(offset_mappings):
            for char_pos in range(start, end):
                if char_pos not in char_to_token:
                    char_to_token[char_pos] = idx 
        
        for chain in coref_chains:
            if len(chain) < 3:
                continue
            
            referent_mention = chain[0]
            r_clause_idx, r_start_idx, r_end_idx = referent_mention
            
            if r_start_idx == r_end_idx:
                referent_token = clauses[r_clause_idx]['tokens'][r_start_idx]
                xpos = referent_token.get('xpos', '')
                if xpos in ['NN', 'NNS', 'NNP', 'NNPS']:
                    referent_text = referent_token['text']
                else:
                    continue
            else:
                referent_tokens = [
                    t for t in clauses[r_clause_idx]['tokens'][r_start_idx:r_end_idx + 1]
                ]
                no_NN_flag = True
                for each_token in referent_tokens: 
                    if each_token.get('xpos', '') in ['NN', 'NNS', 'NNP', 'NNPS']:
                        no_NN_flag = False
                        break
                if no_NN_flag == True:
                    continue
                referent_tokens = [
                    t['text'] for t in clauses[r_clause_idx]['tokens'][r_start_idx:r_end_idx + 1]
                ]
                referent_text = ' '.join(referent_tokens)
            
            for mention in chain[1:]:
                clause_idx, start_idx, end_idx = mention
                
                if start_idx != end_idx:
                    continue
                
                token_info = clauses[clause_idx]['tokens'][start_idx]
                xpos = token_info.get('xpos', '')
                
                if xpos not in ['PRP', 'PRP$']:
                    continue
                
                pronoun = token_info['text']

                pattern = rf'\b{re.escape(pronoun)}\b'
                count = len(re.findall(pattern, paragraph_text))
                if count < 2:
                    continue
                token_global_idx = 0
                for c_idx, clause in enumerate(clauses[:clause_idx]):
                    token_global_idx += len(clause['tokens'])
                token_global_idx += start_idx
                
                if token_global_idx >= len(token_char_spans):
                    continue 
                
                pronoun_start_char, pronoun_end_char = token_char_spans[token_global_idx]
                
                pronoun_token_indices = set()
                for char_pos in range(pronoun_start_char, pronoun_end_char):
                    token_idx = char_to_token.get(char_pos)
                    if token_idx is not None:
                        pronoun_token_indices.add(token_idx)
                
                if not pronoun_token_indices:
                    pronoun_token_index_range = None
                else:
                    pronoun_token_index_range = (min(pronoun_token_indices), max(pronoun_token_indices))
                
                select_start_pos = pronoun_start_char
                select_end_pos = pronoun_end_char
                context_with_select = context_with_select_ori[:select_start_pos] + "<emphasize>" + context_with_select_ori[select_start_pos:select_end_pos] + "</emphasize>" + context_with_select_ori[select_end_pos:]
                
                question_text = random.choice([
                    "What does this pronoun refer to in the conversation?", 
                    "What does the pronoun I selected refer to in the conversation?", 
                    "What does the pronoun I quoted refer to in the conversation?"
                ])
                
                other_referents = []
                for other_chain in coref_chains:
                    if other_chain == chain:
                        continue 
                    
                    if len(other_chain) < 1:
                        continue 
                    
                    has_same_pronoun = False
                    for other_mention in other_chain[1:]:
                        o_clause_idx_temp, o_start_idx_temp, o_end_idx_temp = other_mention
                        if o_start_idx_temp == o_end_idx_temp:
                            other_token = clauses[o_clause_idx_temp]['tokens'][o_start_idx_temp]
                            if other_token.get('xpos', '') in ['PRP', 'PRP$'] and other_token['text'] == pronoun:
                                has_same_pronoun = True
                                break
                    if not has_same_pronoun:
                        continue
                    
                    first_mention = other_chain[0]
                    o_clause_idx, o_start_idx, o_end_idx = first_mention
                    
                    if o_start_idx == o_end_idx:
                        o_token = clauses[o_clause_idx]['tokens'][o_start_idx]
                        xpos = o_token.get('xpos', '')
                        if xpos in ['NN', 'NNS', 'NNP', 'NNPS']:
                            o_text = o_token['text']
                            if o_text != referent_text and o_text not in other_referents:
                                other_referents.append(o_text)
                    else:
                        o_tokens = [
                            t for t in clauses[o_clause_idx]['tokens'][o_start_idx:o_end_idx + 1]
                        ]
                        no_NN_flag = True
                        for each_token in o_tokens: 
                            if each_token.get('xpos', '') in ['NN', 'NNS', 'NNP', 'NNPS']:
                                no_NN_flag = False
                                break
                        if no_NN_flag == True:
                            continue
                        o_tokens = [
                            t['text'] for t in clauses[o_clause_idx]['tokens'][o_start_idx:o_end_idx + 1]
                        ]
                        o_text = ' '.join(o_tokens)
                        if o_text != referent_text and o_text not in other_referents:
                            other_referents.append(o_text)
                
                if len(other_referents) >= 2:
                    incorrect_options = random.sample(other_referents, 2)
                else:
                    continue
                
                options_A_B_C = [referent_text] + incorrect_options
                random.shuffle(options_A_B_C)
                
                options = {
                    'A': options_A_B_C[0],
                    'B': options_A_B_C[1],
                    'C': options_A_B_C[2],
                    'D': "Can not be sure."
                }
                
                if referent_text in options_A_B_C[:3]:
                    correct_index = options_A_B_C[:3].index(referent_text)
                    correct_option = chr(65 + correct_index)
                else:
                    correct_option = 'D'
                
                question_dict = {
                    'context': paragraph_text,
                    'context_with_select': context_with_select,
                    'question': question_text,
                    'pronoun': pronoun,
                    'options': options,
                    'answer': correct_option,
                    'pronoun_token_range': pronoun_token_index_range
                }
                
                questions.append(question_dict)
    
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=4)
    


# 示例用法：
file_path = ""
output_path = ""
construct_coref_questions(file_path, output_path)