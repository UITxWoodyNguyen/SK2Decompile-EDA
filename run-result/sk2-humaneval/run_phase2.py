import json
from vllm import LLM, SamplingParams

IN_P1 = "/kaggle/working/he_phase1.jsonl"
OUT_P2 = "/kaggle/working/sk2_humaneval_recovered.jsonl"
MODEL_P2 = "LLM4Binary/sk2decompile-ident-6.7b"

MAX_MODEL_LEN = 8192
MAX_NEW_TOKENS = 1536
MAX_PROMPT_TOKENS = MAX_MODEL_LEN - MAX_NEW_TOKENS

with open(IN_P1, "r", encoding="utf-8") as f:
    samples = [json.loads(line) for line in f if line.strip()]

llm = LLM(
    model=MODEL_P2,
    tensor_parallel_size=2,
    dtype="half",
    max_model_len=MAX_MODEL_LEN,
    gpu_memory_utilization=0.85,
    trust_remote_code=True,
)
tokenizer = llm.get_tokenizer()

before_rec = "# This is the normalized code:\n"
after_rec = "\n# What is the source code?\n"
prompts = []
truncated_cnt = 0
for s in samples:
    code_ids = tokenizer.encode(s["phase1_ir"].strip(), add_special_tokens=False)
    if len(code_ids) > MAX_PROMPT_TOKENS - 64:
        code_ids = code_ids[: MAX_PROMPT_TOKENS - 64]
        truncated_cnt += 1
    code_str = tokenizer.decode(code_ids, skip_special_tokens=True)
    prompts.append(before_rec + code_str + after_rec)

print(f"Đã chuẩn bị {len(prompts)} prompts (số mẫu bị cắt bớt: {truncated_cnt})")

params = SamplingParams(
    temperature=0.0,
    max_tokens=MAX_NEW_TOKENS,
    stop=[tokenizer.eos_token] if tokenizer.eos_token else None,
)

outputs = llm.generate(prompts, params)

with open(OUT_P2, "w", encoding="utf-8") as f_out:
    for s, out in zip(samples, outputs):
        raw_p2 = out.outputs[0].text
        clean_p2 = raw_p2.replace("Ġ", " ").replace("Ċ", "\n").replace("ĉ", "\t").strip()
        s["recovered_code"] = clean_p2
        f_out.write(json.dumps(s, ensure_ascii=False) + "\n")

print(f"Hoàn tất Pha 2: {len(samples)} mẫu -> {OUT_P2}")
