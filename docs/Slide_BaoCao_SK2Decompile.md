---
marp: true
theme: gaia
_class: lead
paginate: true
backgroundColor: #0f172a
color: #f8fafc
style: |
  section {
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    padding: 40px 50px;
  }
  h1 {
    color: #38bdf8;
    font-size: 1.6em;
  }
  h2 {
    color: #38bdf8;
    font-size: 1.25em;
    border-bottom: 1px solid #334155;
    padding-bottom: 8px;
  }
  h3 {
    color: #818cf8;
    font-size: 1.05em;
  }
  table {
    font-size: 0.72em;
    width: 100%;
    border-collapse: collapse;
  }
  th {
    background-color: #1e293b;
    color: #38bdf8;
  }
  td, th {
    border: 1px solid #334155;
    padding: 6px 10px;
  }
  pre {
    background-color: #020617;
    border: 1px solid #334155;
    font-size: 0.65em;
    padding: 10px;
    border-radius: 6px;
  }
  .highlight {
    color: #10b981;
    font-weight: bold;
  }
  .badge {
    background: #1e293b;
    border: 1px solid #38bdf8;
    color: #38bdf8;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.7em;
  }
---

# BÁO CÁO THỰC NGHIỆM BIÊN DỊCH NGƯỢC HAI PHA SK²DECOMPILE
### Tái lập, Kiểm chứng Độc lập & Đối chiếu Kết quả (arXiv:2509.22114)

**Đơn vị thực hiện:** Nhóm Nghiên cứu & Thực nghiệm UIT  
**Môi trường:** 2x GPU NVIDIA Tesla T4 (vLLM FP16)  
**Quy mô:** 880 mẫu C Thực tế & 567 mẫu HumanEval-C  
**Ngày báo cáo:** 22/11/2026

---

## 1. Đặt Vấn Đề: Rào Cản trong Biên Dịch Ngược

* **Bài toán:** Phục hồi mã nguồn bậc cao (C) từ stripped binaries phục vụ phân tích mã độc (Malware Analysis) và an toàn thông tin.
* **Hạn chế của Decompiler Luật tĩnh (IDA Pro / Ghidra):**
  - Biến vô danh khó hiểu (`v1, v2, a1`), con trỏ thô (`_QWORD, _DWORD`).
  - Mất hoàn toàn ngữ nghĩa của lập trình viên $\rightarrow$ Tốn rất nhiều thời gian dịch ngược thủ công.
* **Điểm nghẽn của LLM Đơn pha (LLM4Decompile):**
  - Quá tải khi vừa giải cấu trúc giải thuật, vừa đoán tên định danh.
  - Sinh ảo giác cú pháp; Re-executability sụt giảm nghiêm trọng ở `-O2/-O3`.
* **Nghịch lý đánh đổi:** Khó cân bằng giữa tính đúng đắn cấu trúc và độ dễ đọc ngữ nghĩa.

---

## 2. Kiến Trúc SK²Decompile: Skeleton to Skin

* **Ý tưởng:** Phân rã bài toán thành 2 pha độc lập tuần tự:

```
[Mã nhị phân / IDA Pseudocode]
             │
             ▼
┌──────────────────────────────────────────────┐
│  PHA 1: KHÔI PHỤC CẤU TRÚC (SKELETON)         │
│  sk2decompile-struct-6.7b | Compiler-guided RL│
│  - Biến tạm generic: var1, var2, func0       │
└──────────────────────────────────────────────┘
             │  [Structure IR]
             ▼
┌──────────────────────────────────────────────┐
│  PHA 2: TÁI TẠO ĐỊNH DANH (SKIN)             │
│  sk2decompile-ident-6.7b  | Semantic Sim RL   │
│  - Định danh giàu ngữ nghĩa: numbers, len,...│
└──────────────────────────────────────────────┘
```

* **Công bố của tác giả:** Đạt **69.00% Re-executability** trên HumanEval-C (vượt GPT-5-mini 56.75%).

---

## 3. Thiết Kế Phương Án Thực Nghiệm Độc Lập

* **Hạ tầng tính toán:** 2x NVIDIA Tesla T4 16GB VRAM (Kaggle Cloud).
* **Framework:** `vLLM v0.34.0` (`tensor_parallel_size=2`, `dtype="half"` FP16, `gpu_memory_utilization=0.85`).
* **Cấu hình suy luận:** `max_model_len=8192`, `max_new_tokens=1536`, `temperature=0.0`.

| Tiêu chí | Pha 1: Structure (struct-6.7b) | Pha 2: Identifier (ident-6.7b) |
| :--- | :---: | :---: |
| Thời gian nạp mô hình | 413.16s (~6.9m) | 386.06s (~6.4m) |
| Thời gian suy luận (880 mẫu) | 4,153.99s (~69.2m) | 3,904.69s (~65.1m) |
| Tốc độ sinh token | **75.22 tokens/s** | **80.54 tokens/s** |
| Chiếm dụng VRAM mỗi GPU | 13,007 MiB (84.7%) | 12,999 MiB (84.6%) |
| **Tổng thời gian GPU 2 pha** | \multicolumn{2}{c}{**~8,058 giây (~2.24 giờ GPU liên tục)**} |

---

## 4. Ba Kỹ Thuật Đảm Bảo Khả Năng Tái Lập

1. **Khử lỗi BPE Detokenizer của vLLM (`Ġ`, `Ċ`, `ĉ`):**
   - Bộ giải mã BPE ánh xạ khoảng trắng thành `Ġ`, newline thành `Ċ`, tab thành `ĉ`.
   - Bắt buộc xử lý thay thế chuỗi trước khi biên dịch, tránh lỗi GCC `stray \304 in program` khiến Re-compilation rơi về 0%.
2. **Nâng Ngữ cảnh 8192 & Safe Prompt Trimming:**
   - Ở mức `-O2/-O3`, loop unrolling và inlining đẩy kích thước prompt > 6,000 tokens.
   - Cắt gọt an toàn (`MAX_PROMPT_TOKENS = 8192 - 1536 - 64`) triệt tiêu hoàn toàn lỗi CUDA OOM.
3. **Bộ Header Chuẩn Thay Thế `psychec`:**
   - Parser `psychec` trong repo tác giả hay bị Segmentation Fault trên struct phức tạp.
   - Dùng bộ `STD_HEADERS` chuẩn kết hợp mock signatures giúp cô lập lỗi thuần túy do mô hình.

---

## 5. Kết Quả trên Tập Dự Án C Thực Tế (880 mẫu - Đã tinh chỉnh R2I)

* **Nguồn dữ liệu:** Trích từ các dự án mã nguồn mở lớn (MariaDB, MySQL, EloqSQL).
* **Đặc điểm:** Hàm trích rời, thiếu global context/unit test $\rightarrow$ Cột Re-exec ghi nhận **N/A**.

| Mức tối ưu (Opt) | Re-compilation (%) | Re-executability (%) | R2I Phase 1 / Phase 2 | Edit Similarity (%) |
| :---: | :---: | :---: | :---: | :---: |
| **-O0** | 15.32 | N/A* | 67.53 / 62.53 | 31.17 |
| **-O1** | 5.53 | N/A* | 79.76 / 51.77 | 30.04 |
| **-O2** | 9.00 | N/A* | 100.00 / 33.33 | 30.48 |
| **-O3** | 15.77 | N/A* | 72.85 / 67.34 | 26.36 |
| **ALL_AVG** | **11.59** | **N/A\*** | **79.38 / 54.56** | **29.42** |

* **Đột phá R2I:** Khắc phục lỗi zero-imputation; R2I phản ánh trung thực chất lượng AST: Pha 1 đạt **79.38 điểm**, Pha 2 đạt **54.56 điểm**.
* **Phân bố lỗi biên dịch:** Lỗi thiếu struct/kiểu chiếm **66.82%** (588 ca); Lỗi cú pháp chiếm **20.23%** (178 ca); Biên dịch thành công: **12.95%** (114 ca).

---

## 6. Điểm Nghẽn Kiến Trúc: Lan Truyền Lỗi 1 Chiều

* **Phân tích định lượng từ `sk2_error_classification.json`:**
  - **Lan truyền lỗi trực tiếp:** Có tới **760 ca** trong tổng 766 ca lỗi từ Pha 1 kéo dài sang Pha 2 (**99.22%**).
  - **Khả năng tự sửa của Pha 2:** Vỏn vẹn **6 ca** (chiếm **0.78%**).
  - **Lỗi cú pháp phát sinh mới ở Pha 2:** Tăng từ 178 ca lên 270 ca (do đổi tên gây đụng từ khóa hoặc gán kiểu không tương thích).

```
[766 ca lỗi ở Pha 1]
         │
         ├───► 760 ca (99.22%) tiếp tục lỗi ở Pha 2 (Lan truyền tất định)
         └───► 6 ca (0.78%) được Pha 2 tự sửa
```

* **Kết luận khoa học:** Pha 2 thuần túy đổi tên (Renaming); hoàn toàn bất lực trong việc sửa chữa sai lệch cấu trúc của Pha 1.

---

## 7. Bước Nhảy Vọt trên Benchmark HumanEval-C (567 mẫu)

* Khắc phục hiện tượng Token Collapsing và hoàn thiện hàm khôi phục tên hàm:

| Mức tối ưu | Re-comp (Lần 1) | Re-comp (Mới nhất) | Re-exec (Lần 1) | Re-exec (Mới nhất) | Hệ số cải thiện |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **-O0** | 1.22% | **55.49%** | 1.22% | **40.24%** | <span class="highlight">x33.0 lần</span> |
| **-O1** | 0.65% | **55.56%** | 0.65% | **29.41%** | <span class="highlight">x45.2 lần</span> |
| **-O2** | 0.73% | **50.36%** | 0.73% | **21.17%** | <span class="highlight">x29.0 lần</span> |
| **-O3** | 0.00% | **47.79%** | 0.00% | **14.16%** | <span class="highlight">Từ đáy 0%</span> |
| **ALL_AVG** | **0.71%** | **52.73%** | **0.71%** | **27.51%** | <span class="highlight">x38.7 lần</span> |

* **Re-compilation:** Tăng vọt lên **52.73%** (đạt 65% con số của tác giả).
* **Re-executability:** Tăng lên **27.51%** (mức `-O0` đạt tới **40.24%**).

---

## 8. Phân Tích Khoảng Cách (Gap Analysis)

### Tại sao Lần chạy 1 chỉ đạt 0.71%?
* Hiện tượng **Token Collapsing**: vLLM giải mã dính chùm từ khóa: `intlonglongfunc0`, `return1;`, `::char**`.
* Hàm `restore_func_name` cũ không nhận dạng được tên hàm do dính tiền tố C++.

### Nguyên nhân khoảng cách còn lại (27.51% vs 69.00% của Bài báo):
1. **Harness & AST Sanitizer độc quyền:** Tác giả tích hợp luật AST tự động ép kiểu toán học (`math.h`, `fmin`, `round`).
2. **Suy giảm theo bậc tối ưu (-O0: 40.24% ➔ -O3: 14.16%):** Loop unrolling & inlining làm phẳng đồ thị CFG; mô hình 6.7B khó đảo ngược phép toán bitwise phức tạp.
3. **Semantic Drift:** Mô hình tự đổi `float` thành `double` làm lệch độ chính xác khi so sánh số thực `fabs()`.

---

## 9. Đối Chiếu với Bài Báo Gốc & Các Baseline SOTA

| Mô hình / Phương pháp | HE-C Re-exec (AVG) | Mức -O0 | Mức -O3 | Đánh giá Khả dụng Thực tế |
| :--- | :---: | :---: | :---: | :--- |
| **SK²Decompile (Tác giả)** | **69.00%** | 86.59% | 57.52% | SOTA; trong pipeline kín |
| **GPT-5-mini (Baseline)** | 56.75% | 67.07% | 49.56% | Tốt nhưng tốn phí API |
| **LLM4Decompile (Baseline)** | 41.71% | 67.07% | 28.32% | Đơn pha; sụp đổ ở -O3 |
| **Idioms (Rule-based)** | 29.81% | 70.73% | 10.62% | Kém ở vòng lặp phức tạp |
| **SK²Decompile (Lần 1)** | 0.71% | 1.22% | 0.00% | Bị nghẽn bởi lỗi BPE |
| **SK²Decompile (Mới nhất)** | **27.51%** | **40.24%** | **14.16%** | **Re-comp 52.73%; khôi phục định danh cực tốt** |

* **Nhận định:** Tại mức không tối ưu hóa (`-O0`), thực nghiệm độc lập đạt **40.24% Re-executability**, khẳng định năng lực vượt trội của mô hình.

---

## 10. Case Study 1: Thành Công Tái Tạo Định Danh

**Hàm:** `dump_header_page` (`ma_loghandler.c`, MariaDB, `-O0`)

* **Pha 1 (Structure IR - Khung xương biến tạm):**
```c
void dump_header_page(unsigned char *var1) {
    struct type1 var14; int var8, var9, var10;
    translog_interpret_file_header(&var14, var1);
    localtime_r(&var14.field1, &var14.field2);
    var8 = var14.field2.field3 + 1900;
    printf("Timestamp: %04d.%02d.%02d...", var8, var9, var10);
}
```

* **Pha 2 (Identifier Skinning - Da thịt giàu ngữ nghĩa):**
```c
void dump_header_page(unsigned char *page) {
    struct translog_file_header header; int year, month, day;
    translog_interpret_file_header(&header, page);
    localtime_r(&header.timestamp, &header.tm);
    year  = header.tm.tm_year + 1900;
    printf("Timestamp: %04d.%02d.%02d...", year, month, day);
}
```
$\rightarrow$ `var1` $\rightarrow$ `page`, `var14` $\rightarrow$ `header`, `var8..10` $\rightarrow$ `year, month, day` chuẩn xác 100%!

---

## 11. Case Study 2: Sửa Lỗi Token Collapsing (func0)

**Mẫu:** `HumanEval-C-0` (Tìm cặp số thực có khoảng cách < ngưỡng threshold)

* **Trước khi sửa (Lần 1 - FAIL):**
```c
intlonglongfunc0(float*x,intn,floateps){
    inti,j; for(i=0;i<n;i++) for(j=i+1;j<n;j++)
        if(fabs(x[i]-x[j])<eps) return1; // <-- Lỗi GCC: 'return1' undeclared
    return0;
}
// GCC: unknown type 'intlonglongfunc0' -> FAIL
```

* **Sau khi lọc qua Sanitizer (Lần chạy mới - PASS):**
```c
int func0(float *x, int n, float eps) {
    int i, j;
    for (i = 0; i < n; i++)
        for (j = i + 1; j < n; j++)
            if (fabs(x[i] - x[j]) < eps) return 1;
    return 0;
}
// GCC: Biên dịch 100% -> PASS toàn bộ 4/4 assertions unit test!
```

---

## 12. Kết Luận & Đóng Góp Thực Nghiệm

1. **Kiểm chứng tính khả thi của kiến trúc Two-Phase:**
   - Việc tách biệt khôi phục cấu trúc và tái tạo định danh là hoàn toàn đúng đắn.
   - Pha 2 giải quyết triệt để bài toán Readability cho chuyên gia dịch ngược mã độc.
2. **Khắc phục điểm nghẽn kỹ thuật triển khai:**
   - Chứng minh sự sụt giảm ở lần 1 do lỗi detokenizer; sau khi chuẩn hóa, Re-compilation đạt **52.73%** và Re-executability đạt **27.51%** (O0 đạt **40.24%**).
3. **Phát hiện giới hạn lan truyền lỗi 1 chiều:**
   - 99.05% lỗi từ Pha 1 kéo dài sang Pha 2; kiến trúc tuần tự không thể tự chữa lành nếu Pha 1 sai lệch cấu trúc.
4. **Giá trị ứng dụng thực tiễn:**
   - Là công cụ **AI Copilot bán tự động** hỗ trợ đắc lực cho đội ngũ SOC/Reverse Engineering tại UIT.

---

## 13. Đề Xuất Nghiên Cứu Mở Rộng

* **Tích hợp Compiler Feedback Loop vào Pha 2:**
  - Xây dựng cơ chế tự sửa sai nhiều vòng (Multi-turn Self-debugging): khi GCC báo lỗi kiểu con trỏ, compiler feedback nạp ngược lại prompt để mô hình sửa.
* **Bộ Tiền Xử Lý AST Lexer:**
  - Tích hợp module tách token ngữ pháp tự động trước khi chuyển qua GCC.
* **Tự Động Sinh Mockup Header:**
  - Kết hợp Clang Static Analyzer để tự động suy diễn struct cho các hàm C lớn.

---

## 14. Q&A - Cảm Ơn Thầy Cô & Các Bạn!

### Báo cáo Thực nghiệm Dịch ngược Nhị phân với SK²Decompile
* **Tài liệu báo cáo chi tiết:** `BaoCao_ThucNghiem_SK2Decompile.pdf`
* **Mã nguồn slide:** `Slide_BaoCao_SK2Decompile.html` & `Slide_BaoCao_SK2Decompile.md`
* **Đơn vị:** Trường Đại học Công nghệ Thông tin (UIT) - ĐHQG-HCM

**Xin trân trọng cảm ơn sự chú ý theo dõi của Thầy Cô và các bạn!**  
*(Sẵn sàng cho phần Hỏi & Đáp)*
