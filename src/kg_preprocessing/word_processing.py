from underthesea import sent_tokenize, text_normalize, word_tokenize
import re

def fix_token_errors(tokenized_text):
    # Pattern: Look for "tác_giả_" glued to a Capitalized word (The Name)
    # \w+ matches "Liêu", "Nguyễn", etc.
    pattern = r"(tác_giả)_([A-ZĐÀ-Ỹ][a-zđà-ỹ]+)"
    
    # Replace with: "tác_giả" [SPACE] "Name"
    fixed_text = re.sub(pattern, r"\1 \2", tokenized_text)
    
    return fixed_text

paragraph = "Những phần chủ yếu của một bài thuốc Một bài thuốc Đông y gồm có 3 phần chính:"
sentences = sent_tokenize(paragraph)
for sentence in sentences:
    normalized_sentence = text_normalize(sentence)
    tokens = word_tokenize(normalized_sentence, format="text")
    fixed_tokens = fix_token_errors(tokens)
    print(fixed_tokens)