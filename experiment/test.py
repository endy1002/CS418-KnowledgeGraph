import jiwer
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
truth_file = [f for f in os.listdir(base_dir) if f.lower().endswith('.txt') and f.lower().__contains__("ground-truth")]
ground_truth = ''
if truth_file:
    ground_truth = ''
    with open(base_dir+"\\"+truth_file[0], "r", encoding='utf-8') as file:
        ground_truth = file.read()
else:
    print(f"ground-truth.txt not found.")
test_file = [f for f in os.listdir(base_dir) if f.lower().endswith('.txt') and not f.lower().__contains__("ground-truth")]
for file in test_file:
    predicted_text = ''
    with open(base_dir+"\\"+file, "r", encoding='utf-8') as file:
        predicted_text = file.read()
    # Compute CER
    cer = jiwer.cer(ground_truth, predicted_text)
    # Compute WER
    wer = jiwer.wer(ground_truth, predicted_text)

    print(f"\nCharacter Error Rate (CER) of {file.name}: {cer:.4f}")
    print(f"Word Error Rate (WER) of {file.name}: {wer:.4f}")