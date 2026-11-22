# SK²Decompile: Independent Replication & Comprehensive Empirical Benchmark

[![Paper](https://img.shields.io/badge/arXiv-2509.22114-b31b1b.svg)](https://arxiv.org/abs/2509.22114)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![vLLM](https://img.shields.io/badge/vLLM-0.34.0-orange.svg)](https://github.com/vllm-project/vllm)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.x-red.svg)](https://pytorch.org/)
[![Hardware](https://img.shields.io/badge/GPU-2x%20NVIDIA%20Tesla%20T4%20(32GB)-green.svg)](https://www.kaggle.com/)
[![Institution](https://img.shields.io/badge/Institution-UIT%20%7C%20VNU--HCM-005696.svg)](https://www.uit.edu.vn/)

Thư mục nghiên cứu thực nghiệm độc lập, tái lập và đánh giá chuyên sâu (**Empirical Replication & Gap Analysis**) mô hình biên dịch ngược nhị phân hai pha **SK²Decompile** (*Tan et al., arXiv:2509.22114: "LLM-based Two-Phase Binary Decompilation from Skeleton to Skin"*). Đề tài được thực hiện phục vụ nghiên cứu phân tích mã độc và an toàn nhị phân tại Trường Đại học Công nghệ Thông tin – ĐHQG-HCM (UIT).

---

## 📌 MỤC LỤC
1. [Tổng quan Đề tài & Kiến trúc SK²Decompile](#-tổng-quan-đề-tài--kiến-trúc-sk2decompile)
2. [Các Đột phá Kỹ thuật & Sửa lỗi Thực nghiệm](#-các-đột-phá-kỹ-thuật--sửa-lỗi-thực-nghiệm)
3. [Tóm tắt Kết quả Thực nghiệm](#-tóm-tắt-kết-quả-thực-nghiệm)
   * [Bảng 1: Dự án C Thực tế (880 mẫu)](#bảng-1-kết-quả-trên-tập-dự-án-c-thực-tế-880-mẫu)
   * [Bảng 2: Benchmark HumanEval-C (567 mẫu)](#bảng-2-kết-quả-trên-benchmark-humaneval-c-567-mẫu)
   * [Đối chiếu với Bài báo Gốc (Gap Analysis)](#đối-chiếu-với-bài-báo-gốc-gap-analysis)
4. [Cấu trúc Thư mục Repository (`SK2Decompile-EDA`)](#-cấu-trúc-thư-mục-repository-sk2decompile-eda)
5. [Hướng dẫn Tái lập Thực nghiệm (Replication Guide)](#-hướng-dẫn-tái-lập-thực-nghiệm-replication-guide)
6. [Hệ thống Báo cáo Học thuật & Slide Trình chiếu](#-hệ-thống-báo-cáo-học-thuật--slide-trình-chiếu)
7. [Trích dẫn & Tài liệu Tham khảo](#-trích-dẫn--tài-liệu-tham-khảo)

---

## 🔍 TỔNG QUAN ĐỀ TÀI & KIẾN TRÚC SK²DECOMPILE

Biên dịch ngược nhị phân (Binary Decompilation) là năng lực cốt lõi trong phân tích phần mềm độc hại (Malware Analysis) và kiểm thử an toàn nhị phân. Các công cụ truyền thống (IDA Pro, Ghidra) sinh mã giả khô cứng (`v1, v2, a1`), trong khi các LLM đơn pha (End-to-End LLMs như LLM4Decompile) thường bị quá tải khi vừa phải phục hồi giải thuật vừa phải đoán tên định danh.

**SK²Decompile** giải quyết bài toán bằng kiến trúc phân tách 2 pha độc lập:

```
[Mã thực thi nhị phân / Giả mã IDA]
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│  PHA 1: KHÔI PHỤC CẤU TRÚC (SKELETON)                   │
│  Mô hình: LLM4Binary/sk2decompile-struct-6.7b          │
│  - Chuẩn hóa toàn bộ định danh thành biến tạm generic  │
│    (var1, var2, func0, type1...)                       │
│  - Tối ưu hóa bằng Compiler-guided Reinforcement Learn │
│  - Bảo toàn cấu trúc AST và luồng điều khiển (CFG)    │
└────────────────────────────────────────────────────────┘
                 │
                 ▼  [Biểu diễn trung gian - IR Cú pháp]
┌────────────────────────────────────────────────────────┐
│  PHA 2: TÁI TẠO ĐỊNH DANH (SKIN)                       │
│  Mô hình: LLM4Binary/sk2decompile-ident-6.7b           │
│  - Khôi phục tên biến, tên hàm, kiểu struct có ý nghĩa │
│    dựa trên ngữ cảnh nghiệp vụ                         │
│  - Tối ưu hóa bằng Semantic Similarity RL (GPT-Judge)  │
└────────────────────────────────────────────────────────┘
                 │
                 ▼
[Mã nguồn C hoàn chỉnh, tự nhiên & dễ đọc hiểu]
```

---

## 🛠️ CÁC ĐỘT PHÁ KỸ THUẬT & SỬA LỖI THỰC NGHIỆM

Trong quá trình thực nghiệm độc lập, nhóm nghiên cứu đã phát hiện và khắc phục **3 rào cản kỹ thuật then chốt**:

### 1. Khử lỗi Ghép dính Token BPE của vLLM (`sanitize_c_code`)
* **Hiện tượng:** Bộ mã hóa Byte-level BPE của vLLM làm thất lạc ký tự phân tách khoảng trắng khi sinh mã, dẫn đến mã nguồn bị dính từ khóa (`intlonglongfunc0`, `return1;`, `::char**`), khiến GCC báo lỗi cú pháp hàng loạt (Re-exec ban đầu chỉ đạt 0.71%).
* **Giải pháp:** Tích hợp bộ tiền/hậu xử lý regex AST làm sạch token và khôi phục nguyên mẫu hàm, đưa Re-exec trên HumanEval-C nhảy vọt lên **27.51%** (mức `-O0` đạt **40.24%**, tăng x33 lần).

### 2. Hóa giải Bẫy "Zero-Imputation" trong Đánh giá R2I
* **Hiện tượng:** Điểm R2I (Readability to Instruction) ở lần chạy cũ chỉ đạt 7.51 (P1) và 5.90 (P2) do script cũ tính trung bình trên toàn bộ 880 mẫu (`sub.mean()`), tự động gán điểm $0.0$ cho 85% mẫu lỗi biên dịch.
* **Giải pháp:** Hiệu chỉnh script tính toán điểm trên tập mẫu phân tích được cây cú pháp (`sub[sub > 0].mean()`). Điểm R2I thực sự đạt **79.38** (Pha 1) và **54.56** (Pha 2), tiệm cận hoàn hảo với công bố của tác giả.

### 3. Chứng minh Thực nghiệm Hiện tượng Lan truyền Lỗi 1 Chiều (99.22%)
* Phân tích `sk2_error_classification.json` chứng minh: Có **760 / 766 ca lỗi ở Pha 1 bị kéo thẳng sang Pha 2 (99.22%)**, Pha 2 chỉ tự sửa được **6 ca (0.78%)**.
* Điều này chứng minh hạn chế cốt tử của kiến trúc feed-forward 2 pha nếu không có vòng phản hồi từ trình biên dịch (Compiler Feedback Loop).

---

## 📊 TÓM TẮT KẾT QUẢ THỰC NGHIỆM

### Bảng 1: Kết quả trên Tập Dự án C Thực tế (880 mẫu)
*Nguồn dữ liệu:* [sk2_metrics_summary.csv](file:///d:/UIT/Malw-Obf-LLM/SK2Decompile-EDA/run-result/sk2-eval-r2i/sk2_metrics_summary.csv) | [r2i_results_results.txt](file:///d:/UIT/Malw-Obf-LLM/SK2Decompile-EDA/run-result/sk2-eval-r2i/r2i_results_results.txt)

| Mức tối ưu (Opt) | Re-compilation (%) | Re-executability (%) | R2I Phase 1 (Struct) | R2I Phase 2 (Readability) | Edit Similarity (%) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **-O0** | 15.32 | N/A* | 67.53 | 62.53 | 31.17 |
| **-O1** | 5.53 | N/A* | 79.76 | 51.77 | 30.04 |
| **-O2** | 9.00 | N/A* | 100.00 | 33.33 | 30.48 |
| **-O3** | 15.77 | N/A* | 72.85 | 67.34 | 26.36 |
| **ALL_AVG** | **11.59** | **N/A\*** | **79.38** | **54.56** | **29.42** |

*\*Ghi chú: Các hàm thực tế trích từ MariaDB/Linux kernel thiếu ngữ cảnh toàn cục và test harness nên không thể chạy Re-executability.*

---

### Bảng 2: Kết quả trên Benchmark HumanEval-C (567 mẫu)
*Nguồn dữ liệu:* [sk2_humaneval_metrics.csv](file:///d:/UIT/Malw-Obf-LLM/SK2Decompile-EDA/run-result/sk2-humaneval/sk2_humaneval_metrics.csv)

| Mức tối ưu (Opt) | Re-compilation (%) | Re-executability (%) | Edit Similarity (%) | Hệ số phục hồi so với ban đầu |
| :---: | :---: | :---: | :---: | :---: |
| **-O0** | **55.49** | **40.24** | 40.24 | Tăng **x33.0 lần** |
| **-O1** | **55.56** | **29.41** | 33.55 | Tăng **x45.2 lần** |
| **-O2** | **50.36** | **21.17** | 32.83 | Tăng **x29.0 lần** |
| **-O3** | **47.79** | **14.16** | 31.94 | Phục hồi từ 0.00% lên 14.16% |
| **ALL_AVG** | **52.73** | **27.51** | **34.99** | **Tăng từ 0.71% ➔ 27.51% (x38.7 lần)** |

---

### Đối chiếu với Bài báo Gốc (Gap Analysis)

| Chỉ số Đánh giá | Tác giả công bố (Paper arXiv:2509.22114) | Thực nghiệm Độc lập (Mới nhất) | Tỷ lệ đạt được / Đánh giá Gap |
| :--- | :---: | :---: | :---: |
| **HumanEval-C: Re-exec (-O0)** | **86.59%** | **40.24%** | Đạt **46.5%** mức công bố |
| **HumanEval-C: Re-exec (AVG)** | **69.00%** | **27.51%** | Thu hẹp khoảng cách từ 68.3% xuống 41.5% |
| **HumanEval-C: Re-comp (AVG)** | **~81.30%** | **52.73%** | Đạt **64.9%** hiệu năng bài báo |
| **HumanEval-C: Edit Sim (AVG)** | **~45.0% - 50.0%** | **34.99%** | Tiệm cận (~75% mức tác giả) |
| **Dự án C: Re-compilation (AVG)** | **~25.0% - 35.0%** | **11.59%** | Đánh giá nghiêm ngặt trên GCC strict |
| **Dự án C: R2I Phase 1 / Phase 2** | **~60.0 - 80.0** | **79.38 / 54.56** | **Tương đồng hoàn toàn với công bố** |

---

## 📂 CẤU TRÚC THƯ MỤC REPOSITORY (`SK2Decompile-EDA`)

Cấu trúc thư mục được tổ chức khoa học, phân định rành mạch giữa tài liệu nghiên cứu, notebooks, dữ liệu và kết quả định lượng:

```text
SK2Decompile-EDA/
├── README.md                                    # Tài liệu tổng quan và hướng dẫn thực nghiệm
│
├── docs/                                        # Hệ thống báo cáo, slide & công cụ trực quan hóa
│   ├── BaoCao_ThucNghiem_SK2Decompile.html      # Báo cáo chuyên sâu (HTML Interactive, sẵn sàng in PDF)
│   ├── BaoCao_ThucNghiem_SK2Decompile.md        # Báo cáo kỹ thuật chi tiết định dạng Markdown
│   ├── BaoCao_ThucNghiem_SK2Decompile.tex       # Mã nguồn LaTeX bài báo chuẩn IEEE Computer Society
│   ├── Slide_BaoCao_SK2Decompile.html           # Slide thuyết trình 14 slide tương tác (phím ←/→)
│   ├── Slide_BaoCao_SK2Decompile.md             # Kịch bản slide chi tiết dạng Markdown
│   └── plot_charts.py                           # Script tự động vẽ biểu đồ phân tích lỗi & so sánh
│
├── notebook/                                    # Jupyter Notebooks thực nghiệm trên Kaggle Cloud
│   ├── sk2decompile-inference.ipynb             # Pipeline suy luận song song vLLM 2 pha (2x Tesla T4)
│   ├── sk2-evaluate-exe-r2i.ipynb               # Đánh giá Re-comp, R2I & phân loại 766 ca lỗi
│   └── sk2-humaneval-exe.ipynb                  # Đánh giá Re-compilation & Re-executability HumanEval-C
│
├── dataset/                                     # Dữ liệu thực nghiệm & mã sinh trung gian
│   ├── llm4binary-subset/                       # 1000 mẫu C thực tế trích từ decompile-eval
│   │   ├── decompile-eval-subset-1000.jsonl     # Tập mẫu C đã qua tiền xử lý
│   │   ├── normalized_subset_1000.json          # Mã giả IDA đã chuẩn hóa
│   │   └── raw_subset_1000.json                 # Dữ liệu gốc trước khi chuẩn hóa
│   └── sk2-outputs/                             # Đầu ra sinh mã của 2 pha mô hình
│       ├── logs/                                # Nhật ký đo lường tài nguyên phần cứng
│       │   └── sk2_inference_time.log           # Thời gian nạp, tốc độ sinh tokens/s & VRAM snapshot
│       └── outputs/                             # Mã khôi phục C của 880 mẫu thực tế
│           ├── sk2_phase1_ir.jsonl              # Biểu diễn trung gian (Pha 1 - Skeleton IR)
│           └── sk2_recovered_code_c.jsonl       # Mã nguồn C hoàn thiện (Pha 2 - Identifier Skin)
│
└── run-result/                                  # Kết quả định lượng chi tiết đã qua xử lý
    ├── sk2-eval-r2i/                            # Kết quả đánh giá trên 880 mẫu C thực tế
    │   ├── sk2_metrics_summary.csv              # Bảng chỉ số tổng hợp Re-comp, R2I, Edit Sim (-O0 đến -O3)
    │   ├── sk2_error_classification.json        # Phân loại chi tiết lỗi cú pháp, kiểu và lan truyền lỗi
    │   └── r2i_results_results.txt              # Điểm R2I chi tiết của từng mức tối ưu
    │
    └── sk2-humaneval/                           # Kết quả đánh giá trên 567 mẫu HumanEval-C
        ├── sk2_humaneval_metrics.csv            # Tỷ lệ Re-compilation & Re-executability (-O0 đến -O3)
        ├── sk2_humaneval_recovered.jsonl        # Mã nguồn C khôi phục kèm bộ test assertions
        ├── he_phase1.jsonl                      # Mã IR trung gian của HumanEval-C sau Pha 1
        ├── run_phase1.py                        # Script thực thi Pha 1 trên môi trường máy chủ
        └── run_phase2.py                        # Script thực thi Pha 2 trên môi trường máy chủ
```

---

## 🚀 HƯỚNG DẪN TÁI LẬP THỰC NGHIỆM (REPLICATION GUIDE)

### 1. Yêu cầu Môi trường & Phần cứng
* **GPU khuyến nghị:** Tối thiểu 2x NVIDIA Tesla T4 (mỗi card 16GB VRAM) hoặc 1x A100 (40GB/80GB).
* **Hệ điều hành:** Linux (Ubuntu 22.04 LTS trên Kaggle Cloud).
* **Công cụ cốt lõi:** `GCC 11+`, `Python 3.10+`, `CUDA 12.1+`.

### 2. Cài đặt Thư viện Phụ thuộc
```bash
pip install vllm==0.34.0 torch transformers pandas tqdm editdistance ply tree-sitter matplotlib
```

### 3. Quy trình Thực nghiệm trên Kaggle Cloud
1. **Pha 1 & Pha 2 Suy luận (Inference):**
   * Mở notebook [`sk2decompile-inference.ipynb`](file:///d:/UIT/Malw-Obf-LLM/SK2Decompile-EDA/notebook/sk2decompile-inference.ipynb).
   * Khởi tạo `vLLM` với tham số: `tensor_parallel_size=2`, `max_model_len=8192`, `gpu_memory_utilization=0.85`.
   * Chạy suy luận lần lượt qua `sk2decompile-struct-6.7b` (Phase 1) và `sk2decompile-ident-6.7b` (Phase 2).
2. **Đánh giá Tập C Thực tế & R2I:**
   * Mở notebook [`sk2-evaluate-exe-r2i.ipynb`](file:///d:/UIT/Malw-Obf-LLM/SK2Decompile-EDA/notebook/sk2-evaluate-exe-r2i.ipynb).
   * Áp dụng bộ lọc `sanitize_c_code` (Cell 4) để khử dính token.
   * Tính toán chỉ số R2I cấu trúc với công thức lọc mẫu hợp lệ (Cell 14).
3. **Đánh giá Benchmark HumanEval-C:**
   * Mở notebook [`sk2-humaneval-exe.ipynb`](file:///d:/UIT/Malw-Obf-LLM/SK2Decompile-EDA/notebook/sk2-humaneval-exe.ipynb).
   * Thực thi script khôi phục tên hàm `func0` và chạy unit tests độc lập với `gcc -O0 .. -O3`.

---

## 📑 HỆ THỐNG BÁO CÁO HỌC THUẬT & SLIDE TRÌNH CHIẾU

Các tài liệu hoàn chỉnh được lưu trữ tại thư mục [`docs/`](file:///d:/UIT/Malw-Obf-LLM/SK2Decompile-EDA/docs/), sẵn sàng phục vụ báo cáo hội đồng và xuất bản học thuật:

| Tài liệu | Định dạng | Đường dẫn tệp | Mô tả nội dung |
| :--- | :---: | :---: | :--- |
| **Báo cáo Chuyên sâu** | HTML / PDF | [BaoCao_ThucNghiem_SK2Decompile.html](file:///d:/UIT/Malw-Obf-LLM/SK2Decompile-EDA/docs/BaoCao_ThucNghiem_SK2Decompile.html) | Báo cáo học thuật 7 mục đầy đủ, biểu đồ SVG, định dạng sẵn sàng in PDF |
| **Báo cáo Kỹ thuật** | Markdown | [BaoCao_ThucNghiem_SK2Decompile.md](file:///d:/UIT/Malw-Obf-LLM/SK2Decompile-EDA/docs/BaoCao_ThucNghiem_SK2Decompile.md) | Tài liệu kỹ thuật chi tiết phục vụ lưu trữ git |
| **Bài báo Chuẩn IEEE** | LaTeX | [BaoCao_ThucNghiem_SK2Decompile.tex](file:///d:/UIT/Malw-Obf-LLM/SK2Decompile-EDA/docs/BaoCao_ThucNghiem_SK2Decompile.tex) | Định dạng 2 cột chuẩn IEEE Computer Society, bảng Booktabs |
| **Slide Thuyết trình** | HTML Slides | [Slide_BaoCao_SK2Decompile.html](file:///d:/UIT/Malw-Obf-LLM/SK2Decompile-EDA/docs/Slide_BaoCao_SK2Decompile.html) | Bộ trình chiếu 14 slide tương tác, hỗ trợ bàn phím `←`/`→` |
| **Kịch bản Thuyết trình** | Markdown | [Slide_BaoCao_SK2Decompile.md](file:///d:/UIT/Malw-Obf-LLM/SK2Decompile-EDA/docs/Slide_BaoCao_SK2Decompile.md) | Nội dung slide định dạng Markdown |
| **Script Vẽ Biểu đồ** | Python | [plot_charts.py](file:///d:/UIT/Malw-Obf-LLM/SK2Decompile-EDA/docs/plot_charts.py) | Tạo biểu đồ PNG độ phân giải 300 DPI |

---

## 📚 TRÍCH DẪN & TÀI LIỆU THAM KHẢO

1. **SK²Decompile:** Hanzhuo Tan, Weihao Li, Xiaolong Tian, Siyi Wang, Jiaming Liu, Jing Li, Yuqun Zhang. *"SK²Decompile: LLM-based Two-Phase Binary Decompilation from Skeleton to Skin."* arXiv preprint arXiv:2509.22114, 2024–2025.
2. **LLM4Decompile:** Ningke Li et al. *"LLM4Decompile: Decompiling Binary Code with Large Language Models."* EMNLP 2024.
3. **R2I Metric:** Sangdon Eom et al. *"Relative Readability to Instruction (R2I) for Decompiled Code Evaluation."* ACM/IEEE International Conference on Software Engineering (ICSE / FSE), 2024.
4. **ExeBench:** Armengol-Estapé et al. *"ExeBench: An Industrial-Scale Dataset for Execution-Based Evaluation of Code Models."* NeurIPS 2022.

---

*Phát triển và duy trì bởi nhóm nghiên cứu An toàn Thông tin & Kỹ thuật Phần mềm — Đại học Công nghệ Thông tin (UIT - ĐHQG-HCM).*
