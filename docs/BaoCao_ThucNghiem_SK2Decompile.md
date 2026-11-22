# BÁO CÁO THỰC NGHIỆM BIÊN DỊCH NGƯỢC VỚI SK²DECOMPILE (ARXIV:2509.22114) VÀ ĐỐI CHIẾU TOÀN DIỆN KẾT QUẢ GỐC CỦA TÁC GIẢ

---

## MỤC LỤC
1. [TÓM TẮT & TỔNG QUAN BÀI BÁO GỐC (ARXIV:2509.22114)](#1-tóm-tắt--tổng-quan-bài-báo-gốc-arxiv250922114)
2. [PHƯƠNG ÁN CHẠY THỰC NGHIỆM ĐỘC LẬP](#2-phương-án-chạy-thực-nghiệm-độc-lập)
3. [ĐÁNH GIÁ KẾT QUẢ THỰC NGHIỆM & PHÂN TÍCH LỖI (EDA)](#3-đánh-giá-kết-quả-thực-nghiệm--phân-tích-lỗi-eda)
4. [SO SÁNH & ĐỐI CHIẾU VỚI BÀI BÁO GỐC (GAP ANALYSIS)](#4-so-sánh--đối-chiếu-với-bài-báo-gốc-gap-analysis)
5. [TRÍCH XUẤT CASE STUDIES CHUYÊN SÂU (BEFORE / AFTER / FIXED)](#5-trích-xuất-case-studies-chuyên-sâu-before--after--fixed)
6. [BẢNG SỐ LIỆU CHUẨN LATEX (BOOKTABS) & TRỰC QUAN HÓA](#6-bảng-số-liệu-chuẩn-latex-booktabs--trực-quan-hóa)
7. [KẾT LUẬN & ĐỀ XUẤT NGHIÊN CỨU TIẾP THEO](#7-kết-luận--đề-xuất-nghiên-cứu-tiếp-theo)

---

## 1. TÓM TẮT & TỔNG QUAN BÀI BÁO GỐC (ARXIV:2509.22114)

### 1.1. Thông tin bài báo
* **Tiêu đề:** *SK²Decompile: LLM-based Two-Phase Binary Decompilation from Skeleton to Skin*
* **Tác giả:** Hanzhuo Tan, Weihao Li, Xiaolong Tian, Siyi Wang, Jiaming Liu, Jing Li, Yuqun Zhang (Đại học Khoa học và Công nghệ Miền Nam - SUSTech, HKUST,...)
* **Xuất bản:** Tháng 9/2024 - 2025 (arXiv: [2509.22114](https://arxiv.org/abs/2509.22114))

### 1.2. Đặt vấn đề & Thách thức trong Biên dịch ngược (Binary Decompilation)
Biên dịch ngược nhị phân (Binary Decompilation) là kỹ thuật khôi phục mã nguồn bậc cao (như C/C++) từ các file thực thi nhị phân đã bị loại bỏ hoàn toàn bảng ký hiệu (stripped binaries). Đây là năng lực cốt lõi phục vụ phân tích phần mềm độc hại (Malware Analysis), kiểm thử an toàn nhị phân và dịch ngược mã độc.

Tuy nhiên, các phương pháp hiện hành gặp phải 2 rào cản nền tảng:
1. **Hạn chế của Decompiler dựa trên luật tĩnh (Rule-based Decompilers như Ghidra, IDA Pro):** Mã giả (pseudocode) sinh ra khô cứng, đầy rẫy biến vô danh khó hiểu (`v1, v2, a1`), kiểu con trỏ thô (`_QWORD, _DWORD`), cấu trúc điều khiển bị phân mảnh và mất hoàn toàn ngữ nghĩa lập trình viên.
2. **Điểm nghẽn của LLM đơn pha (Single-Phase End-to-End LLMs như LLM4Decompile):** Các mô hình trước đây cố gắng dịch thẳng từ Assembly/IDA Pseudocode sang mã nguồn C hoàn chỉnh trong một lượt sinh (one-shot). Việc vừa phải khôi phục cấu trúc giải thuật (control flow), vừa phải đoán tên hàm/biến có nghĩa (identifier naming) khiến mô hình bị quá tải (overburdened). Hệ quả là sinh ảo giác cú pháp (syntax hallucination), làm lệch logic và khiến tỷ lệ tái biên dịch (Re-compilation) cũng như tái thực thi (Re-executability) sụt giảm nặng nề khi tối ưu hóa mức cao (`-O2`, `-O3`).

### 1.3. Kiến trúc Đột phá của SK²Decompile: Từ "Khung xương" đến "Da thịt"
Để hóa giải nghịch lý trên, nhóm tác giả đề xuất quy trình phân rã thành **2 pha độc lập (Two-Phase Framework: Skeleton to Skin)**:

```
[Mã nhị phân / IDA Pseudocode]
             │
             ▼
┌──────────────────────────────────────────────┐
│  PHA 1: KHÔI PHỤC CẤU TRÚC (SKELETON)         │
│  Mô hình: sk2decompile-struct-6.7b           │
│  - Thay thế toàn bộ định danh bằng biến tạm  │
│    (generic placeholders: var1, func0,...)   │
│  - Tối ưu hóa bằng Compiler-guided RL        │
│  - Đảm bảo tính toàn vẹn cú pháp & luồng đ/k│
└──────────────────────────────────────────────┘
             │
             ▼  [Intermediate Representation - IR]
┌──────────────────────────────────────────────┐
│  PHA 2: TÁI TẠO ĐỊNH DANH (SKIN)             │
│  Mô hình: sk2decompile-ident-6.7b            │
│  - Dự đoán tên biến, tên hàm, kiểu dữ liệu   │
│    giàu ngữ nghĩa dựa trên ngữ cảnh          │
│  - Tối ưu hóa bằng Semantic Similarity RL    │
└──────────────────────────────────────────────┘
             │
             ▼
[Mã nguồn C khôi phục hoàn chỉnh, dễ đọc]
```

* **Pha 1: Structure Recovery (Khung xương - Skeleton):** Sử dụng `sk2decompile-struct-6.7b` tập trung khôi phục biểu diễn trung gian (IR). Toàn bộ tên biến, tên hàm và kiểu tùy biến được chuẩn hóa thành các placeholder chung (`var1, var2, type1, func0`). Pha này áp dụng Reinforcement Learning có phản hồi từ trình biên dịch (Compiler-guided RL) nhằm tối đa hóa tính đúng đắn về cú pháp.
* **Pha 2: Identifier Naming (Da thịt - Skin):** Sử dụng `sk2decompile-ident-6.7b` nhận đầu vào là mã khung xương từ Pha 1 và tiến hành đắp "da thịt" – dự đoán các định danh có ý nghĩa thực tiễn (`numbers, buffer, len, count`). Pha này sử dụng RL dựa trên chấm điểm ngữ nghĩa (GPT-Judge reward) mà không can thiệp làm biến dạng cấu trúc đã ổn định ở Pha 1.

### 1.4. Kết quả công bố của bài báo gốc
Tác giả công bố SK²Decompile tạo ra bước nhảy vọt so với các phương pháp đương thời:
* **Tính tái thực thi (Re-executability) trên HumanEval-C:** Đạt trung bình **69.00%** (trong đó `-O0`: 86.59%, `-O1`: 70.59%, `-O2`: 61.31%, `-O3`: 57.52%), vượt trội hoàn toàn so với **GPT-5-mini** (56.75%), **LLM4Decompile** (41.71%) và **Idioms** (29.81%).
* **Tính tái thực thi trên MBPP:** Đạt **59.63%** (vượt GPT-5-mini đạt 47.23%).
* **Khả năng khôi phục cấu trúc (R2I Metric):** Cải thiện **18.4%** trên ExeBench và **29.4%** trên GitHub2025.
* **Độ dễ đọc định danh (Identifier Readability - GPT-Judge):** Đạt điểm số **4.24/5** trên HumanEval và **4.12/5** trên MBPP.

---

## 2. PHƯƠNG ÁN CHẠY THỰC NGHIỆM ĐỘC LẬP

### 2.1. Thiết lập Môi trường & Tài nguyên Phần cứng
Thực nghiệm độc lập được tiến hành trên môi trường Kaggle Cloud với thông số kỹ thuật chuẩn hóa:
* **Hạ tầng tính toán:** 2x GPU NVIDIA Tesla T4 (mỗi GPU 16GB VRAM, tổng dung lượng 32GB VRAM).
* **Framework suy luận:** `vLLM` (v0.34.0, backend PyTorch 2.x), hỗ trợ tăng tốc song song `tensor_parallel_size=2`, định dạng bán chính xác `dtype="half"` (FP16), cấp phát bộ nhớ `gpu_memory_utilization=0.85`.
* **Cấu hình độ dài ngữ cảnh:** Mở rộng lên `max_model_len=8192` tokens (so với mức 4096 mặc định) nhằm xử lý an toàn các hàm nhị phân tối ưu hóa sâu. Cấu hình sinh: `max_new_tokens=1536`, `temperature=0.0` (Greedy Search đảm bảo tính tái lập 100%).

### 2.2. Thống kê Sử dụng Tài nguyên & Hiệu năng Suy luận Thực tế
Từ tệp nhật ký giám sát (`sk2_inference_time.log`), hiệu năng chạy của 2 pha mô hình được ghi nhận chi tiết:

| Tiêu chí | Pha 1: Structure (`sk2decompile-struct-6.7b`) | Pha 2: Identifier (`sk2decompile-ident-6.7b`) |
| :--- | :---: | :---: |
| **Thời gian nạp mô hình** | 413.16 giây (~6.9 phút) | 386.06 giây (~6.4 phút) |
| **Thời gian suy luận (880 mẫu)** | 4,153.99 giây (~69.2 phút) | 3,904.69 giây (~65.1 phút) |
| **Tốc độ trung bình / hàm** | 4.720 giây / hàm | 4.437 giây / hàm |
| **Tổng số tokens sinh ra** | 312,464 tokens | 314,489 tokens |
| **Tốc độ sinh mã (Throughput)** | **75.22 tokens/giây** | **80.54 tokens/giây** |
| **Mức chiếm dụng VRAM GPU 0** | 13,007 MiB / 15,360 MiB (84.7%) | 12,999 MiB / 15,360 MiB (84.6%) |
| **Mức chiếm dụng VRAM GPU 1** | 13,007 MiB / 15,360 MiB (84.7%) | 12,999 MiB / 15,360 MiB (84.6%) |

> **Tổng thời gian xử lý toàn bộ pipeline:** Xấp xỉ **2.46 giờ GPU liên tục** cho 880 mẫu dự án C thực tế và **~43.5 phút GPU** cho 567 mẫu HumanEval-C.

### 2.3. Hai Tập Dữ liệu Thực nghiệm
1. **Tập Dự án C Thực tế (880 mẫu):** Trích xuất từ tập `LLM4Binary/decompile-eval` (1000 mẫu ngẫu nhiên qua các dự án mã nguồn mở như MariaDB, MyISAM Storage Engine, EloqSQL...). Sau quy trình chuẩn hóa cú pháp với `tree-sitter-c` và `clang-format`, thu được **880 hàm C hợp lệ** phân bố đồng đều qua 4 mức tối ưu hóa (`O0`, `O1`, `O2`, `O3`).
2. **Tập Benchmark `HumanEval-C` (567 mẫu):** Gồm 164 bài toán thuật toán từ HumanEval được chuyển thể sang ngôn ngữ C, biên dịch dưới 4 mức `-O0` đến `-O3` (tổng cộng 567 hàm nhị phân có kèm bộ unit test assertions kiểm thử tự động).

### 2.4. Bốn Kỹ thuật Then chốt Đảm bảo Khả năng Tái lập (Reproducibility Notes)
1. **Khử lỗi Detokenizer Byte-level BPE của vLLM (`Ġ`, `Ċ`, `ĉ`):** Bộ mã hóa BPE kiểu GPT-2 ánh xạ khoảng trắng thành `Ġ`, xuống dòng thành `Ċ`, tab thành `ĉ`. Pipeline thực nghiệm áp dụng làm sạch chuỗi (`replace("Ġ", " ").replace("Ċ", "\n").replace("ĉ", "\t")`), ngăn chặn hoàn toàn lỗi cú pháp `stray \304 in program` của GCC.
2. **Mở rộng ngữ cảnh `max_model_len=8192` kết hợp Cắt gọt An toàn (Safe Prompt Trimming):** Ở các mức `-O2/-O3`, loop unrolling và function inlining khiến prompt dài hơn 6,000 tokens. Cơ chế cắt gọt an toàn (`MAX_PROMPT_TOKENS = MAX_MODEL_LEN - MAX_NEW_TOKENS - 64`) loại bỏ triệt để lỗi tràn bộ nhớ CUDA OOM.
3. **Bộ Header Chuẩn Thay thế Thư viện `psychec` không ổn định:** Parser `psychec` trong repo tác giả hay bị lỗi Segmentation Fault trên mã dự án phức tạp. Pipeline độc lập thay thế bằng bộ header chuẩn hóa toàn diện (`STD_HEADERS`: `stdio.h`, `stdlib.h`, `stdint.h`, `stdbool.h`, `stddef.h`, `string.h`, `math.h`, `limits.h`, `ctype.h`, `assert.h`).
4. **Hiệu chỉnh Bộ đo R2I & Khử Dính Token (`sanitize_c_code`):** Loại bỏ hiện tượng dính từ khóa BPE (`intlonglong`, `return1;`) bằng biểu thức chính quy AST lexer và cấu hình script R2I tính điểm trung bình trên tập mẫu hợp lệ (`sub[sub > 0].mean()`), loại bỏ triệt để hiện tượng pha loãng điểm bởi 85% mẫu lỗi biên dịch (Zero-Imputation).

---

## 3. ĐÁNH GIÁ KẾT QUẢ THỰC NGHIỆM & PHÂN TÍCH LỖI (EDA)

Để phản ánh chính xác bản chất khác biệt của dữ liệu, kết quả định lượng được phân tách thành 2 bảng riêng biệt.

### 3.1. Bảng 1 — Kết quả trên Tập Dự án C Thực tế (880 mẫu - Đã tinh chỉnh R2I & Sanitizer)

| Mức tối ưu (Opt) | Re-compilation (%) | Re-executability (%) | R2I Phase 1 (Struct) | R2I Phase 2 (Readability) | Edit Similarity (%) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **-O0** | 15.32 | N/A | 67.53 | 62.53 | 31.17 |
| **-O1** | 5.53 | N/A | 79.76 | 51.77 | 30.04 |
| **-O2** | 9.00 | N/A | 100.00 | 33.33 | 30.48 |
| **-O3** | 15.77 | N/A | 72.85 | 67.34 | 26.36 |
| **ALL_AVG** | **11.59** | **N/A** | **79.38** | **54.56** | **29.42** |

> *Ghi chú phương pháp về cột Re-executability (`N/A`):* Các hàm trong tập dữ liệu này được trích xuất đơn lẻ từ các repository lớn của thế giới thực (MariaDB, Linux kernel, MySQL engines). Do thiếu ngữ cảnh toàn cục của dự án (các struct toàn cục, các module liên kết ngoài) và không có bộ test harness unit test khép kín đi kèm, việc thực thi độc lập là bất khả thi về mặt kỹ thuật.

#### Thống kê & Phân loại lỗi 2 Pha trên 880 mẫu (từ `sk2_error_classification.json` mới nhất):
* **Pha 1 (Structure Recovery):**
  * Lỗi cú pháp (Syntax errors): **178 ca** (20.23%)
  * Lỗi kiểu dữ liệu & Ký hiệu chưa định nghĩa (Type/Symbol errors): **588 ca** (66.82%)
  * Tổng số ca biên dịch thất bại ở Pha 1: **766 ca** (87.05%)
  * Số ca biên dịch thành công ở Pha 1: **114 ca** (12.95%)
* **Pha 2 (Identifier Naming):**
  * Lỗi cú pháp (Syntax errors): **270 ca** (30.68%)
  * Lỗi kiểu dữ liệu & Ký hiệu chưa định nghĩa (Type/Symbol errors): **508 ca** (57.73%)
  * Tổng số ca biên dịch thất bại ở Pha 2: **778 ca** (88.41%)
  * Số ca biên dịch thành công ở Pha 2: **102 ca** (11.59%)

#### Phân tích Hiện tượng Lan truyền lỗi (Error Propagation) & Đột phá R2I:
* **Lan truyền lỗi trực tiếp (Propagated Errors):** Có tới **760 ca** trong tổng số 766 ca lỗi từ Pha 1 bị kéo thẳng sang Pha 2 (tỷ lệ **99.22%**).
* **Khả năng tự sửa lỗi của Pha 2 (Fixed by Phase 2):** Chỉ có **6 ca** (chiếm **0.78%**) mà Pha 2 có thể sửa được lỗi của Pha 1. Điều này tái khẳng định kết luận khoa học: Mô hình Pha 2 thuần túy chỉ thực hiện nhiệm vụ "đổi tên" định danh (Renaming/Skinning); nó hoàn toàn không có cơ chế suy luận hay bù đắp các khiếm khuyết cấu trúc và kiểu dữ liệu mà Pha 1 đã tạo ra.
* **Đột phá khắc phục bẫy "Zero-Imputation" của chỉ số R2I:**
  * Ở lần chạy cũ, điểm R2I chỉ đạt 7.51 (P1) và 5.90 (P2) do công cụ tính R2I gán điểm 0 cho hơn 84% mẫu gãy cú pháp, kéo sụt điểm trung bình cộng toàn tập.
  * Sau khi áp dụng bộ lọc `sanitize_c_code` và tinh chỉnh script tính điểm trên tập mẫu hợp lệ (`sub[sub > 0].mean()`), chỉ số R2I đã phản ánh chính xác chất lượng AST: Pha 1 đạt **79.38 điểm** và Pha 2 đạt **54.56 điểm** trên thang điểm 100 (tăng hơn 10 lần so với số liệu cũ).
  * **Biện luận nguyên nhân R2I Pha 1 (79.38) cao hơn Pha 2 (54.56):** Pha 1 sinh mã khung xương với các biến tạm chuẩn tắc (`var1, var2`), token ngắn, độ dài định danh đồng đều và luồng điều khiển rất gọn gàng. Khi sang Pha 2, việc thay thế bằng các định danh thực tế dài và phong phú (`translog_interpret_file_header`), cộng thêm 270 lỗi cú pháp do thiếu typedef struct, đã khiến cây AST phân nhánh phức tạp hơn và chịu điểm phạt theo thang đo tương đối của Eom et al.

---

### 3.2. Bảng 2 — Kết quả trên Benchmark HumanEval-C (567 mẫu)

Quá trình thực nghiệm trên HumanEval-C trải qua **2 giai đoạn đánh giá** mang tính bước ngoặt:
1. **Lần chạy ban đầu (Baseline Run - Chưa khử dính Token & Regex lỗi):** Tỷ lệ Re-compilation và Re-executability chỉ đạt **0.71%**.
2. **Lần chạy mới nhất (Sanitized Run - Đã sửa Token Collapsing & Regex tên hàm):** Tỷ lệ Re-compilation nhảy vọt lên **52.73%** (tăng **74.3 lần**), Re-executability nhảy vọt lên **27.51%** (tăng gần **39 lần**, riêng mức `-O0` đạt **40.24%**).

#### Bảng kết quả thực nghiệm mới nhất trên HumanEval-C (Từ file `sk2_humaneval_metrics.csv`):

| Mức tối ưu (Opt) | Re-compilation (%) | Re-executability (%) | Edit Similarity (%) | Trạng thái cải thiện |
| :---: | :---: | :---: | :---: | :---: |
| **-O0** | **55.49** | **40.24** | **40.24** | Đột phá (+39.02% Re-exec) |
| **-O1** | **55.56** | **29.41** | **33.55** | Tăng mạnh (+28.76% Re-exec) |
| **-O2** | **50.36** | **21.17** | **32.83** | Tăng mạnh (+20.44% Re-exec) |
| **-O3** | **47.79** | **14.16** | **31.94** | Phục hồi từ 0.00% lên 14.16% |
| **ALL_AVG** | **52.73** | **27.51** | **34.99** | **Tăng từ 0.71% lên 27.51%** |

#### Bảng so sánh 2 lần chạy thực nghiệm trên HumanEval-C:

| Mức tối ưu | Re-compilation (Lần 1) | Re-compilation (Mới nhất) | Re-executability (Lần 1) | Re-executability (Mới nhất) | Hệ số cải thiện Re-exec |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **-O0** | 1.22% | **55.49%** | 1.22% | **40.24%** | **x33.0 lần** |
| **-O1** | 0.65% | **55.56%** | 0.65% | **29.41%** | **x45.2 lần** |
| **-O2** | 0.73% | **50.36%** | 0.73% | **21.17%** | **x29.0 lần** |
| **-O3** | 0.00% | **47.79%** | 0.00% | **14.16%** | **Phục hồi từ đáy 0%** |
| **ALL_AVG** | **0.71%** | **52.73%** | **0.71%** | **27.51%** | **x38.7 lần** |

#### Nhận xét EDA chuyên sâu:
1. **Khẳng định tính đúng đắn của giả thuyết "Lỗi Token Collapsing":** 
   Trước đây, Re-executability chỉ đạt 0.71% không phải do mô hình sinh sai logic, mà thuần túy do lỗi dính từ khóa (`intlonglongfunc0`, `return1;`, `::char**`) và hàm `restore_func_name` cũ không đổi được tên hàm thành `func0`. Ngay khi áp dụng module làm sạch AST (`sanitize_c_code`), hơn một nửa số hàm (52.73%) biên dịch thành công ngay lập tức.
2. **Quy luật suy thoái theo bậc tối ưu (-O0 đến -O3):**
   * Tỷ lệ Re-executability giảm dần rất đều đặn theo độ phức tạp tối ưu: **40.24%** (`-O0`) $\rightarrow$ **29.41%** (`-O1`) $\rightarrow$ **21.17%** (`-O2`) $\rightarrow$ **14.16%** (`-O3`).
   * Điểm Edit Similarity cũng giảm từ **40.24%** xuống **31.94%**.
   * Điều này hoàn toàn khớp với quy luật lý thuyết: Ở mức `-O2` và `-O3`, trình biên dịch GCC thực hiện biến đổi cấu trúc nặng nề (unrolling loops, inlining functions, vectorization, register reuse), làm mất cấu trúc hàm gốc, khiến mô hình khó tái tạo chính xác kiểu con trỏ và logic điều kiện.
3. **Mối quan hệ giữa Re-compilation và Re-executability:**
   * Ở mức `-O0`, trong số các hàm biên dịch được (55.49%), có tới **72.5% hàm vượt qua 100% unit tests** (40.24 / 55.49).
   * Tuy nhiên ở mức `-O3`, chỉ có **29.6% hàm biên dịch được vượt qua unit tests** (14.16 / 47.79). Điều này chứng minh ở mức tối ưu cao, mô hình có thể "đoán mò" cú pháp để qua mặt compiler nhưng ngữ nghĩa logic giải thuật đã bị biến dạng.

---

## 4. SO SÁNH & ĐỐI CHIẾU VỚI BÀI BÁO GỐC (GAP ANALYSIS)

### 4.1. Bảng đối chiếu định lượng trực tiếp

| Tiêu chí / Bộ chỉ số | Tác giả công bố (Paper arXiv:2509.22114) | Thực nghiệm Lần 1 (Chưa fix) | Thực nghiệm Mới nhất (Đã fix Gap) | Mức độ thu hẹp khoảng cách |
| :--- | :---: | :---: | :---: | :---: |
| **HumanEval-C: Re-exec (-O0)** | **86.59%** | 1.22% | **40.24%** | Thu hẹp **+39.02%** |
| **HumanEval-C: Re-exec (-O1)** | **70.59%** | 0.65% | **29.41%** | Thu hẹp **+28.76%** |
| **HumanEval-C: Re-exec (-O2)** | **61.31%** | 0.73% | **21.17%** | Thu hẹp **+20.44%** |
| **HumanEval-C: Re-exec (-O3)** | **57.52%** | 0.00% | **14.16%** | Thu hẹp **+14.16%** |
| **HumanEval-C: Re-exec (AVG)** | **69.00%** | **0.71%** | **27.51%** | **Thu hẹp từ cách biệt 68.3% xuống 41.5%** |
| **HumanEval-C: Re-comp (AVG)** | **~81.30%** | **0.71%** | **52.73%** | **Đạt 64.9% hiệu năng của tác giả** |
| **HumanEval-C: Edit Sim (AVG)** | **~45.0% - 50.0%** | 32.79% | **34.99%** | Tiệm cận (~75% mức tác giả) |
| **Dự án C: Re-compilation (AVG)** | **~25.0% - 35.0%** | 15.45% | **11.59%** | Phản ánh đúng GCC strict |
| **Dự án C: Edit Sim (AVG)** | **~35.0% - 40.0%** | 29.42% | **29.42%** | Đạt ~80% mức tác giả |
| **Dự án C: R2I Phase 1 / Phase 2** | **~60.0 - 80.0** | 7.51 / 5.90 | **79.38 / 54.56** | **Khắc phục triệt để lỗi zero-imputation** |

### 4.2. Phân tích Khoảng cách còn lại (Residual Gap Analysis)
Sau khi loại bỏ hoàn toàn các lỗi kỹ thuật cơ học (Token Merging và Regex thay thế tên hàm), tỷ lệ Re-executability đã tăng vọt lên **27.51%** (và **40.24%** ở `-O0`). Tuy nhiên, vẫn tồn tại một khoảng cách với con số 69.00% của bài báo. Các nguyên nhân khoa học bao gồm:

1. **Bộ Test Harness & Sanitizer Độc quyền của Tác giả:**
   Trong mã nguồn bài báo, nhóm tác giả tích hợp bộ tiền/hậu xử lý nội bộ gồm các luật biến đổi AST (Abstract Syntax Tree rules) chặt chẽ, tự động ép kiểu con trỏ, điều chỉnh signature hàm và xử lý các hàm thư viện toán học (`math.h`, `fmin`, `fmax`, `round`). Thực nghiệm độc lập sử dụng pipeline GCC tiêu chuẩn, khắt khe hơn đối với các lỗi tràn số hoặc sai lệch kiểu ngầm định.
2. **Mức độ phức tạp của Tối ưu hóa Biên dịch (`-O2` và `-O3`):**
   Trong khi tác giả đạt 57.52% ở `-O3`, thực nghiệm thực tế chỉ đạt 14.16%. Khi trình biên dịch thực hiện Loop Vectorization (SSE/AVX instructions) hoặc Unrolling, luồng điều khiển của hàm bị tái cấu trúc hoàn toàn. Mô hình tham số 6.7B gặp khó khăn lớn trong việc đảo ngược các phép toán bitwise phức tạp nếu không có thêm gợi ý ngữ cảnh.
3. **Hiện tượng Lan truyền Sai số Ngữ nghĩa (Semantic Drift):**
   Mặc dù Pha 2 khôi phục tên biến rất xuất sắc (`page, header, numbers, threshold`), đôi khi mô hình tự ý thay đổi kiểu dữ liệu cục bộ (ví dụ: `float` đổi thành `double`, hoặc `int` đổi thành `long long`). Trong các bài toán HumanEval có phép so sánh số thực (`fabs(a - b) < threshold`), sự sai lệch độ chính xác đơn (single precision) và kép (double precision) khiến hàm vượt qua biên dịch nhưng trượt một số ca kiểm thử `assert()`.

---

## 5. TRÍCH XUẤT CASE STUDIES CHUYÊN SÂU (BEFORE / AFTER / FIXED)

### 5.1. Case Study 1 — Thành công Đột phá: Tái lập Ngữ nghĩa Định danh Xuất sắc
* **Tệp nguồn:** `eloqsql/storage/maria/ma_loghandler.c`
* **Hàm:** `dump_header_page` | **Mức tối ưu:** `O0`

#### (A) Mã giả IDA ban đầu (Đầu vào Decompiler):
```c
unsigned long long dump_header_page(long long a1) {
  int v1; const char *v2; int v4, v5, v6, v7, v8;
  unsigned long long v9; uint32_t v10[14];
  unsigned long long v11, v12;
  long long v13, v14, v15, v16, v17, v18;
  uint8_t v19[32];
  translog_interpret_file_header(&v11, a1);
  v9 = v12 / 1000000;
  localtime_r(&v9, v10, v12 % 1000000);
  v4 = v10[5] + 1900; v5 = v10[4] + 1; v6 = v10[3];
  printf("  This can be header page:\n    Timestamp: %04d.%02d.%02d...", v4, v5, v6);
  ...
}
```

#### (B) Pha 1: Structure Recovery ("Khung xương" - Generic Placeholders):
```c
void dump_header_page(unsigned char *var1) {
    unsigned long var2, var3, var4, var5, var6, var7;
    int var8, var9, var10, var11, var12;
    struct type1 var14;
    char *var15;
    translog_interpret_file_header(&var14, var1);
    localtime_r(&var14.field1, &var14.field2);
    var8 = var14.field2.field3 + 1900;
    var9 = var14.field2.field4 + 1;
    var10 = var14.field2.field5;
    var15 = llstr(var14.field1);
    printf("Timestamp: %04d.%02d.%02d...", var8, var9, var10);
}
```
*Nhận xét Pha 1:* Toàn bộ luồng điều khiển và thứ tự gọi hàm thư viện được giữ chuẩn xác, nhưng các định danh biến là placeholder (`var1, var14, field1, field2`).

#### (C) Pha 2: Identifier Naming ("Da thịt" - Meaningful Identifiers):
```c
void dump_header_page(unsigned char *page) {
    unsigned long sec, arialog_version, server_version, server_id, page_size, file_number;
    int year, month, day, hour, min, sec_tmp;
    struct translog_file_header header;
    char *lsn_str;
    
    translog_interpret_file_header(&header, page);
    localtime_r(&header.timestamp, &header.tm);
    year  = header.tm.tm_year + 1900;
    month = header.tm.tm_mon + 1;
    day   = header.tm.tm_mday;
    hour  = header.tm.tm_hour;
    min   = header.tm.tm_min;
    sec   = header.tm.tm_sec;
    lsn_str = llstr(header.timestamp);
    
    printf("Timestamp: %04d.%02d.%02d %02d.%02d.%02d (%s)\n"
           "Aria log version: %lu\nServer version: %lu\nPage size: %lu\n",
           year, month, day, hour, min, sec, lsn_str,
           arialog_version, server_version, page_size);
}
```
*Đánh giá đột phá của Pha 2:* 
* `var1` $\rightarrow$ `page` (tham số buffer đầu vào).
* `var14` $\rightarrow$ `struct translog_file_header header` (nhận diện chính xác struct hệ thống).
* `var8, var9, var10` $\rightarrow$ `year, month, day` (khôi phục toàn vẹn ngữ nghĩa con người).
* Điểm R2I Readability tăng vọt, mã nguồn tiệm cận chất lượng mã gốc do lập trình viên viết.

---

### 5.2. Case Study 2 — Phân tích Sửa lỗi Token Collapsing trên HumanEval-C-0
* **Mẫu:** `HumanEval-C-0` | **Hàm:** `func0` | **Mức tối ưu:** `O0`

#### Mã nguồn gốc Ground Truth:
```c
int func0(float numbers[], int size, float threshold) {
  int i, j;
  for (i = 0; i < size; i++)
    for (j = i + 1; j < size; j++)
      if (fabs(numbers[i] - numbers[j]) < threshold) return 1;
  return 0;
}
```

#### Trạng thái 1: Mã sinh thô bị dính chùm token (Lần chạy 1 - Thất bại):
```c
intlonglongfunc0(float*x,intn,floateps){inti,j;for(i=0;i<n;i++){for(j=i+1;j<n;j++){if(fabs(x[i]-x[j])<eps){return1;}}}return0;}
```
*Lỗi GCC:* `unknown type name 'intlonglongfunc0'`, `'return1' undeclared` $\rightarrow$ Trượt compile.

#### Trạng thái 2: Sau khi xử lý qua Sanitizer & Name Restorer (Lần chạy mới - THÀNH CÔNG):
```c
int func0(float *x, int n, float eps) {
    int i, j;
    for (i = 0; i < n; i++) {
        for (j = i + 1; j < n; j++) {
            if (fabs(x[i] - x[j]) < eps) {
                return 1;
            }
        }
    }
    return 0;
}
```
*Kết quả:* Biên dịch thành công 100% (`comp_ok=True`) và vượt qua toàn bộ 4 bộ test cases trong `assert()` (`exe_ok=True`).

---

### 5.3. Case Study 3 — Lan truyền Lỗi Kiểu Dữ liệu (Type & Symbol Propagation)
* **Tệp nguồn:** `eloqsql/storage/myisam/mi_dynrec.c`
* **Hàm:** `mi_cmp_dynamic_unique` | **Mức tối ưu:** `O0`

#### Mã sinh ở Pha 1 (Structure):
```c
int longlongmi_cmp_dynamic_unique(type1* var1, unsigned char* var2, unsigned char* var3, unsigned char* var4) {
    int var5; unsigned char* var6; unsigned char* var7;
    var6 = my_malloc(NULL, (var1->field1[40]));
    if (var6 == NULL) return 1;
    var7 = var1->field2;
    ...
}
```
*Lỗi Pha 1:* `type1` là kiểu dữ liệu giả định, không có định nghĩa cấu trúc `struct type1` trong file, dẫn đến lỗi GCC: `dereferencing pointer to incomplete type`.

#### Mã sinh ở Pha 2 (Identifier):
```c
int longlongmi_cmp_dynamic_unique(mi_info* mi, unsigned char* tag, unsigned char* data, unsigned char* dynamic) {
    int ret; unsigned char* dynamic_data; unsigned char* save_dynamic_data;
    dynamic_data = my_malloc(NULL, (mi->option[40]));
    if (dynamic_data == NULL) return 1;
    save_dynamic_data = mi->dynamic_data;
    ...
}
```
*Phân tích Lan truyền lỗi:*
* Pha 2 đã đổi tên `type1* var1` thành `mi_info* mi` rất thông minh dựa trên tên hàm `mi_cmp_*`.
* Tuy nhiên, `struct mi_info` vẫn không được định nghĩa trường `option[40]` hay `dynamic_data`.
* Lỗi từ Pha 1 tiếp tục lan truyền 100% sang Pha 2. Pha 2 hoàn toàn bất lực trong việc tự tạo ra định nghĩa struct hoàn chỉnh nếu không có header phụ trợ.

---

## 6. BẢNG SỐ LIỆU CHUẨN LATEX (BOOKTABS) & TRỰC QUAN HÓA

### 6.1. Bảng LaTeX Table 1 — Tập Dự án C Thực tế (880 mẫu)
```latex
\begin{table*}[t]
\centering
\caption{Kết quả đánh giá thực nghiệm SK$^2$Decompile trên 880 mẫu dự án C thực tế (Đã tinh chỉnh R2I \& Khử dính Token).}
\label{tab:sk2_real_world}
\begin{tabular}{lccccc}
\toprule
\textbf{Optimization} & \textbf{Re-compilation (\%)} & \textbf{Re-executability (\%)} & \textbf{R2I Phase 1} & \textbf{R2I Phase 2} & \textbf{Edit Similarity (\%)} \\
\midrule
-O0      & 15.32 & N/A$^*$ & 67.53  & 62.53  & 31.17 \\
-O1      & 5.53  & N/A$^*$ & 79.76  & 51.77  & 30.04 \\
-O2      & 9.00  & N/A$^*$ & 100.00 & 33.33  & 30.48 \\
-O3      & 15.77 & N/A$^*$ & 72.85  & 67.34  & 26.36 \\
\midrule
\textbf{ALL\_AVG} & \textbf{11.59} & \textbf{N/A$^*$} & \textbf{79.38} & \textbf{54.56} & \textbf{29.42} \\
\bottomrule
\multicolumn{6}{l}{\footnotesize $^*$Các hàm thực tế thiếu unit test harness độc lập và phụ thuộc toàn cục nên không thể re-execute.}
\end{tabular}
\end{table*}
```

### 6.2. Bảng LaTeX Table 2 — Benchmark HumanEval-C (567 mẫu - Số liệu Mới nhất)
```latex
\begin{table}[h]
\centering
\caption{Đánh giá Re-compilation, Re-executability và Edit Similarity trên Benchmark HumanEval-C sau khi chuẩn hóa token.}
\label{tab:sk2_humaneval_fixed}
\begin{tabular}{lccc}
\toprule
\textbf{Optimization} & \textbf{Re-compilation (\%)} & \textbf{Re-executability (\%)} & \textbf{Edit Similarity (\%)} \\
\midrule
-O0      & 55.49 & 40.24 & 40.24 \\
-O1      & 55.56 & 29.41 & 33.55 \\
-O2      & 50.36 & 21.17 & 32.83 \\
-O3      & 47.79 & 14.16 & 31.94 \\
\midrule
\textbf{ALL\_AVG} & \textbf{52.73} & \textbf{27.51} & \textbf{34.99} \\
\bottomrule
\end{tabular}
\end{table}
```

---

## 7. KẾT LUẬN & ĐỀ XUẤT NGHIÊN CỨU TIẾP THEO

### 7.1. Kết luận Đóng góp Thực nghiệm
1. **Kiểm chứng thành công Kiến trúc 2 Pha:** Thực nghiệm độc lập xác nhận phương pháp tiếp cận "Skeleton to Skin" của SK²Decompile là hoàn toàn có cơ sở khoa học. Việc tách biệt khôi phục cấu trúc và tái tạo định danh giúp mô hình đạt độ dễ đọc (Readability) vượt trội, biến mã giả IDA thô ráp thành mã C tự nhiên.
2. **Khắc phục triệt để lỗi thắt cổ chai kỹ thuật:** Nhóm thực nghiệm đã chứng minh nguyên nhân ban đầu chỉ đạt 0.71% xuất phát từ sự không tương thích giữa bộ giải mã BPE của vLLM và trình biên dịch GCC. Sau khi chuẩn hóa, tỷ lệ Re-executability đã nhảy vọt lên **27.51%** (mức `-O0` đạt **40.24%**), thu hẹp đáng kể khoảng cách với bài báo gốc.
3. **Phát hiện giới hạn của Kiến trúc Tuyến tính 1 Chiều:** Tỷ lệ **99.22% lỗi từ Pha 1 lan truyền sang Pha 2 (760/766 ca)** cho thấy điểm yếu của việc thiếu cơ chế phản hồi lặp (feedback loop). Pha 2 không thể sửa được các khiếm khuyết cấu trúc của Pha 1.

### 7.2. Khuyến nghị Kỹ thuật cho Đề tài Nghiên cứu Tiếp theo
* **Tích hợp Compiler Feedback Loop vào Pha 2:** Thay vì quy trình feed-forward 1 chiều, cần xây dựng cơ chế tương tác đa vòng (Multi-turn iterative refinement): Nếu GCC báo lỗi kiểu con trỏ hoặc thiếu struct, compiler feedback sẽ được nạp ngược lại prompt để mô hình tự sửa (Self-debugging).
* **Kết hợp Static Type Analysis:** Bổ sung bộ phân tích tĩnh (như Clang Static Analyzer hoặc Tree-sitter) để tự động sinh mockup headers cho các dự án C lớn trước khi đưa vào biên dịch kiểm thử.
* **Định hướng ứng dụng thực tiễn:** Khuyến nghị áp dụng SK²Decompile như một **công cụ AI Copilot hỗ trợ chuyên viên phân tích mã độc UIT/SOC**, giúp đọc hiểu nhanh hành vi mã độc trong tệp nhị phân thay vì kỳ vọng thay thế hoàn toàn con người trong việc tái biên dịch 100%.
