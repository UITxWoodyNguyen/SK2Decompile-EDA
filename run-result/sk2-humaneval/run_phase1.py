import json
from vllm import LLM, SamplingParams

HE_PATH = "/kaggle/input/datasets/wood1enqxyn/sk2decompile-autodecomp-repos/LLM4Decompile/sk2decompile/evaluation/data/humaneval_normsrcpseudo.json"
OUT_P1 = "/kaggle/working/he_phase1.jsonl"
MODEL_P1 = "LLM4Binary/sk2decompile-struct-6.7b"

MAX_MODEL_LEN = 8192
MAX_NEW_TOKENS = 1536
MAX_PROMPT_TOKENS = MAX_MODEL_LEN - MAX_NEW_TOKENS

with open(HE_PATH, "r", encoding="utf-8") as f:
    samples = [d for d in json.load(f) if d.get("language") == "c"]

llm = LLM(
    model=MODEL_P1,
    tensor_parallel_size=2,
    dtype="half",
    max_model_len=MAX_MODEL_LEN,
    gpu_memory_utilization=0.85,
    trust_remote_code=True,
)
tokenizer = llm.get_tokenizer()

before = "# This is the assembly code:\n"
after = "\n# What is the source code?\n"
prompts = []
truncated_cnt = 0
for s in samples:
    code_ids = tokenizer.encode(s["ida_pseudo_norm"].strip(), add_special_tokens=False)
    if len(code_ids) > MAX_PROMPT_TOKENS - 64:
        code_ids = code_ids[: MAX_PROMPT_TOKENS - 64]
        truncated_cnt += 1
    code_str = tokenizer.decode(code_ids, skip_special_tokens=True)
    prompts.append(before + code_str + after)

print(f"Đã chuẩn bị {len(prompts)} prompts (số mẫu bị cắt bớt do quá dài: {truncated_cnt})")

params = SamplingParams(
    temperature=0.0,
    max_tokens=MAX_NEW_TOKENS,
    stop=[tokenizer.eos_token] if tokenizer.eos_token else None,
)

outputs = llm.generate(prompts, params)

with open(OUT_P1, "w", encoding="utf-8") as f_out:
    for s, out in zip(samples, outputs):
        raw_p1 = out.outputs[0].text
        clean_p1 = raw_p1.replace("Ġ", " ").replace("Ċ", "\n").replace("ĉ", "\t").strip()
        s["phase1_ir"] = clean_p1
        f_out.write(json.dumps(s, ensure_ascii=False) + "\n")

print(f"Hoàn tất Pha 1: {len(samples)} mẫu -> {OUT_P1}")
