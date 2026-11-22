import matplotlib.pyplot as plt
import numpy as np

# Cấu hình font và phong cách hiển thị
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

# ==========================================
# BIỂU ĐỒ 1: So sánh Re-compilation & Re-executability trên HumanEval-C (Sau khi fix Gap)
# ==========================================
opts = ['-O0', '-O1', '-O2', '-O3', 'ALL_AVG']
x = np.arange(len(opts))
width = 0.22

# Số liệu thực nghiệm mới của tôi (sau khi fix Token Collapsing & Regex khôi phục tên hàm)
re_comp_my = [55.49, 55.56, 50.36, 47.79, 52.73]
re_exe_my = [40.24, 29.41, 21.17, 14.16, 27.51]

# Số liệu công bố của tác giả (Paper arXiv:2509.22114)
re_exe_paper = [86.59, 70.59, 61.31, 57.52, 69.00]

fig, ax = plt.subplots(figsize=(11, 6), dpi=300)

rects1 = ax.bar(x - width, re_exe_paper, width, label='Tác giả (Paper) - Re-executability', color='#1f77b4', alpha=0.9)
rects2 = ax.bar(x, re_comp_my, width, label='Thực nghiệm của tôi - Re-compilation (Đã fix)', color='#ff7f0e', alpha=0.9)
rects3 = ax.bar(x + width, re_exe_my, width, label='Thực nghiệm của tôi - Re-executability (Đã fix)', color='#2ca02c', alpha=0.9)

ax.set_ylabel('Tỷ lệ thành công (%)', fontsize=12, fontweight='bold')
ax.set_title('So sánh Re-executability & Re-compilation trên HumanEval-C qua các mức tối ưu\n(Đối chiếu kết quả tác giả vs Thực nghiệm mới nhất)', fontsize=13, fontweight='bold', pad=15)
ax.set_xticks(x)
ax.set_xticklabels(opts, fontsize=11, fontweight='bold')
ax.legend(fontsize=10, loc='upper right', framealpha=0.9)
ax.grid(axis='y', linestyle='--', alpha=0.5)
ax.set_ylim(0, 100)

# Hiển thị nhãn giá trị trên các cột
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        if height > 0:
            ax.annotate(f'{height:.2f}%',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8, fontweight='bold')

autolabel(rects1)
autolabel(rects2)
autolabel(rects3)

plt.tight_layout()
plt.savefig('humaneval_comparison_chart.png', dpi=300)
print("Đã lưu biểu đồ 1: humaneval_comparison_chart.png")
plt.close()

# ==========================================
# BIỂU ĐỒ 2: Phân bố lỗi & Lan truyền lỗi giữa Pha 1 và Pha 2 (Dự án C thực tế - 880 mẫu)
# ==========================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300)

# Subplot 1: So sánh loại lỗi giữa Pha 1 và Pha 2
categories = ['Lỗi cú pháp\n(Syntax Error)', 'Lỗi kiểu & Định danh\n(Type/Symbol Error)', 'Biên dịch thành công\n(Compilation Pass)']
phase1_counts = [178, 588, 114]
phase2_counts = [270, 508, 102]

x_cat = np.arange(len(categories))
w = 0.35

ax1.bar(x_cat - w/2, phase1_counts, w, label='Pha 1 (Structure IR)', color='#d62728', alpha=0.85)
ax1.bar(x_cat + w/2, phase2_counts, w, label='Pha 2 (Identifier Skin)', color='#9467bd', alpha=0.85)

ax1.set_ylabel('Số lượng mẫu (trên tổng 880)', fontsize=11, fontweight='bold')
ax1.set_title('Phân bố kết quả biên dịch: Pha 1 vs Pha 2', fontsize=12, fontweight='bold')
ax1.set_xticks(x_cat)
ax1.set_xticklabels(categories, fontsize=10)
ax1.legend(fontsize=10)
ax1.grid(axis='y', linestyle='--', alpha=0.5)

for i in range(len(categories)):
    ax1.annotate(f'{phase1_counts[i]}', xy=(x_cat[i] - w/2, phase1_counts[i]), xytext=(0, 3), textcoords="offset points", ha='center', fontweight='bold')
    ax1.annotate(f'{phase2_counts[i]}', xy=(x_cat[i] + w/2, phase2_counts[i]), xytext=(0, 3), textcoords="offset points", ha='center', fontweight='bold')

# Subplot 2: Biểu đồ tròn thể hiện tỷ lệ lan truyền lỗi từ Pha 1 sang Pha 2 (766 ca lỗi ở Pha 1)
labels_prop = ['Lỗi kéo thẳng sang Pha 2\n(Propagated: 760 ca - 99.22%)', 'Pha 2 tự sửa được lỗi\n(Fixed: 6 ca - 0.78%)']
sizes_prop = [760, 6]
colors_prop = ['#ff9999', '#66b3ff']
explode = (0, 0.15)

ax2.pie(sizes_prop, explode=explode, labels=labels_prop, colors=colors_prop, autopct='%1.2f%%',
        shadow=True, startangle=140, textprops={'fontsize': 10, 'weight': 'bold'})
ax2.set_title('Tính chất lan truyền lỗi 1 chiều của kiến trúc 2 pha\n(766 ca lỗi ở Pha 1)', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('sk2_error_propagation_chart.png', dpi=300)
print("Đã lưu biểu đồ 2: sk2_error_propagation_chart.png")
plt.close()
