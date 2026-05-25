import json
from pathlib import Path

import torch
from torch.utils.data import Dataset
from sklearn.model_selection import train_test_split

from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    DataCollatorForSeq2Seq,
)

from calendar_schema import build_prompt, to_compact_json


MODEL_NAME = "google/mt5-small"
DATA_PATH = "train_data_calendar_3000.txt"
OUTPUT_DIR = "./calendar_json_model"

# 빠른 학습용
MAX_INPUT_LEN = 512
MAX_TARGET_LEN = 192


def load_jsonl(path: str):
    records = []

    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{line_no}번째 줄 JSON 파싱 실패: {e}")

            if "input" not in obj or "output" not in obj:
                raise ValueError(f"{line_no}번째 줄에 input 또는 output이 없습니다.")

            target = to_compact_json(obj["output"])

            records.append(
                {
                    "input": obj["input"],
                    "target": target,
                }
            )

    return records


class CalendarDataset(Dataset):
    """
    속도 개선 핵심:
    __getitem__에서 매번 tokenizer를 돌리지 않고,
    Dataset 생성 시 한 번만 tokenize합니다.
    """

    def __init__(self, records, tokenizer):
        source_texts = [build_prompt(item["input"]) for item in records]
        target_texts = [item["target"] for item in records]

        model_inputs = tokenizer(
            source_texts,
            max_length=MAX_INPUT_LEN,
            truncation=True,
            padding=False,
        )

        labels = tokenizer(
            text_target=target_texts,
            max_length=MAX_TARGET_LEN,
            truncation=True,
            padding=False,
        )

        self.features = []

        for i in range(len(records)):
            self.features.append(
                {
                    "input_ids": model_inputs["input_ids"][i],
                    "attention_mask": model_inputs["attention_mask"][i],
                    "labels": labels["input_ids"][i],
                }
            )

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        return self.features[idx]


def main():
    print("start")
    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    if not Path(DATA_PATH).exists():
        raise FileNotFoundError(f"학습 데이터 파일을 찾지 못했습니다: {DATA_PATH}")

    print("데이터 로딩 중...")
    records = load_jsonl(DATA_PATH)
    print(f"전체 데이터 수: {len(records)}")

    train_records, valid_records = train_test_split(
        records,
        test_size=0.05,
        random_state=42,
        shuffle=True,
    )

    print(f"학습 데이터 수: {len(train_records)}")
    print(f"검증 데이터 수: {len(valid_records)}")

    print("tokenizer 로딩 중...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=False)

    print("model 로딩 중...")
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"사용 device: {device}")

    if torch.cuda.is_available():
        print(f"GPU 이름: {torch.cuda.get_device_name(0)}")
        print(f"CUDA 버전: {torch.version.cuda}")

    model = model.to(device)
    print(f"모델 위치: {next(model.parameters()).device}")

    print("Dataset tokenization 중...")
    train_dataset = CalendarDataset(train_records, tokenizer)
    valid_dataset = CalendarDataset(valid_records, tokenizer)

    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
    )

    training_args = Seq2SeqTrainingArguments(
        output_dir=OUTPUT_DIR,

        # 속도 우선: 학습 중 평가/체크포인트 저장 끔
        eval_strategy="no",
        save_strategy="no",
        load_best_model_at_end=False,

        learning_rate=3e-5,

        # GPU 메모리 부족하면 4 → 2로 낮추십시오.
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,

        # effective batch size = 4 * 2 = 8
        gradient_accumulation_steps=2,

        num_train_epochs=3,

        # 학습 중 생성 평가 끔
        predict_with_generate=False,
        generation_max_length=MAX_TARGET_LEN,

        logging_steps=10,

        fp16=False,
        bf16=False,
        report_to="none",

        # Windows에서는 일단 0이 안정적입니다.
        dataloader_num_workers=0,
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=valid_dataset,
        processing_class=tokenizer,
        data_collator=data_collator,
    )

    print("학습 시작...")
    trainer.train()

    print("최종 모델 저장 중...")
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    print(f"학습 완료: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()