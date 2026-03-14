"""Seed webapp.db with sample exercises for all grades.

Creates a rich set of exercises spanning all 5 grades, covering major exercise types.
Also seeds vocabulary for Grade 1 and week_info from phan_phoi data.
"""
import os
import sys
import json
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import WEBAPP_DB, YCCD_DB
from db import init_webapp_db, get_webapp_db, get_yccd_db


def seed_week_info():
    """Populate week_info table from phan_phoi data."""
    yccd_conn = get_yccd_db()
    webapp_conn = get_webapp_db()
    cur_y = yccd_conn.cursor()
    cur_w = webapp_conn.cursor()

    for lop in range(1, 6):
        cur_y.execute("""
            SELECT tuan, chu_de, GROUP_CONCAT(ten_bai, ' | ') as bai_hoc
            FROM (SELECT DISTINCT tuan, chu_de, ten_bai FROM phan_phoi WHERE lop = ? ORDER BY tuan, tiet_tong)
            GROUP BY tuan ORDER BY tuan
        """, (lop,))
        for row in cur_y.fetchall():
            tuan = row['tuan']
            chu_de = row['chu_de'] or ''
            bai_hoc = row['bai_hoc'] or ''

            # Get YCCD for this week
            cur_y.execute("""
                SELECT id, noi_dung FROM yccd
                WHERE lop = ? AND tuan_hoc_bat_dau <= ? AND tuan_hoc_ket_thuc >= ?
            """, (lop, tuan, tuan))
            yccds = [{"id": r['id'], "noi_dung": r['noi_dung']} for r in cur_y.fetchall()]

            cur_w.execute("""
                INSERT OR REPLACE INTO week_info (lop, tuan, title_vi, title_en, chu_de_vi, yccd_summary)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (lop, tuan, bai_hoc, '', chu_de, json.dumps(yccds, ensure_ascii=False)))

    webapp_conn.commit()
    yccd_conn.close()
    webapp_conn.close()
    print("✓ Seeded week_info for all grades")


def seed_vocabulary():
    """Seed vocabulary for Grade 1 (key math terms)."""
    conn = get_webapp_db()
    cur = conn.cursor()

    vocab_data = {
        # Week 1-7: Numbers 0-10
        1: [("number","số"), ("count","đếm"), ("zero","không/số 0"), ("one","một"), ("two","hai"), ("three","ba"), ("four","bốn"), ("five","năm")],
        2: [("six","sáu"), ("seven","bảy"), ("eight","tám"), ("nine","chín"), ("ten","mười"), ("how many","bao nhiêu")],
        3: [("more","nhiều hơn"), ("less","ít hơn"), ("equal","bằng nhau"), ("compare","so sánh")],
        4: [("compare","so sánh"), ("greater","lớn hơn"), ("smaller","nhỏ hơn"), ("order","sắp xếp")],
        5: [("and","và"), ("makes","được"), ("part","phần"), ("whole","tổng")],
        # Week 7-8: Shapes
        7: [("square","hình vuông"), ("circle","hình tròn"), ("triangle","hình tam giác"), ("rectangle","hình chữ nhật")],
        8: [("shape","hình dạng"), ("side","cạnh"), ("corner","góc"), ("pattern","mẫu")],
        # Week 9-14: Addition & Subtraction within 10
        9: [("add","cộng"), ("plus","cộng"), ("sum","tổng"), ("total","tổng cộng")],
        10: [("addition","phép cộng"), ("equals","bằng"), ("altogether","tất cả"), ("in all","tổng cộng")],
        11: [("subtract","trừ"), ("minus","trừ"), ("take away","bớt đi"), ("left","còn lại")],
        12: [("subtraction","phép trừ"), ("remain","còn lại"), ("difference","hiệu"), ("fly away","bay đi")],
        13: [("table","bảng"), ("fact family","nhóm phép tính"), ("related","liên quan"), ("opposite","ngược lại")],
        14: [("practice","luyện tập"), ("compute","tính"), ("solve","giải"), ("check","kiểm tra")],
        # Week 15-16: 3D Shapes
        15: [("cube","khối lập phương"), ("rectangular prism","khối hộp chữ nhật"), ("face","mặt"), ("edge","cạnh")],
        16: [("left","bên trái"), ("right","bên phải"), ("above","bên trên"), ("below","bên dưới"), ("in front","phía trước"), ("behind","phía sau")],
        # Week 17-18: Review
        17: [("review","ôn tập"), ("remember","nhớ"), ("write","viết"), ("read","đọc")],
        18: [("test","kiểm tra"), ("correct","đúng"), ("wrong","sai"), ("try again","thử lại")],
        # Week 19-22: Numbers to 100
        19: [("tens","hàng chục"), ("ones","hàng đơn vị"), ("digit","chữ số"), ("two-digit","hai chữ số")],
        20: [("twenty","hai mươi"), ("thirty","ba mươi"), ("forty","bốn mươi"), ("fifty","năm mươi")],
        # Week 22-25: Length
        22: [("length","chiều dài"), ("measure","đo"), ("ruler","thước kẻ"), ("centimeter","xen-ti-mét")],
        # Week 25-29: Add/Sub within 100
        25: [("carry","nhớ"), ("borrow","mượn"), ("without carrying","không nhớ"), ("column","cột")],
        # Week 30-32: Time
        30: [("clock","đồng hồ"), ("hour","giờ"), ("o'clock","giờ đúng"), ("time","thời gian")],
        31: [("calendar","lịch"), ("day","ngày"), ("week","tuần"), ("month","tháng")],
    }

    for lop_week, words in vocab_data.items():
        for en, vi in words:
            cur.execute("INSERT OR IGNORE INTO vocabulary (lop, tuan, word_en, word_vi) VALUES (?,?,?,?)",
                       (1, lop_week, en, vi))

    conn.commit()
    conn.close()
    print("✓ Seeded vocabulary for Grade 1")


def seed_sample_exercises():
    """Create sample exercises for key weeks across all grades."""
    conn = get_webapp_db()
    cur = conn.cursor()

    # Check if already seeded
    cur.execute("SELECT COUNT(*) FROM exercises")
    if cur.fetchone()[0] > 0:
        print("⚠ Exercises already exist. Skipping seed.")
        conn.close()
        return

    exercises = []

    # ═══════════════════════════════════════
    # GRADE 1
    # ═══════════════════════════════════════

    # Week 1: Numbers 0-5
    exercises.append({
        "lop": 1, "tuan": 1, "section": "kham_pha", "sort_order": 1,
        "exercise_type": "fill_in",
        "title_vi": "Đếm và viết số",
        "title_en": "Count and write the number",
        "instruction_vi": "Đếm số đồ vật trong mỗi nhóm và viết số tương ứng.",
        "instruction_en": "Count the objects in each group and write the number.",
        "hint_vi": "Chỉ vào từng đồ vật và đếm: 1, 2, 3...",
        "hint_en": "Point to each object and count: 1, 2, 3...",
        "config": {
            "items": [
                {"expression": "🍎🍎🍎 →", "answer": "3"},
                {"expression": "🌟🌟🌟🌟🌟 →", "answer": "5"},
                {"expression": "🐱🐱 →", "answer": "2"},
                {"expression": "🦋 →", "answer": "1"},
                {"expression": "🎈🎈🎈🎈 →", "answer": "4"},
                {"expression": "(không có gì) →", "answer": "0"},
            ],
            "layout": "grid_2col"
        },
        "yccd_ids": "1"
    })

    exercises.append({
        "lop": 1, "tuan": 1, "section": "hoat_dong", "sort_order": 2,
        "exercise_type": "multiple_choice",
        "title_vi": "Chọn đáp án đúng",
        "title_en": "Choose the correct answer",
        "instruction_vi": "Có bao nhiêu quả cam?",
        "instruction_en": "How many oranges are there?",
        "hint_vi": "Đếm từng quả cam nhé.",
        "hint_en": "Count each orange.",
        "config": {
            "question": {"text_vi": "🍊🍊🍊🍊 Có bao nhiêu quả cam?", "text_en": "🍊🍊🍊🍊 How many oranges?"},
            "choices": [
                {"text_vi": "3", "text_en": "3"},
                {"text_vi": "4", "text_en": "4"},
                {"text_vi": "5", "text_en": "5"},
            ],
            "correct_index": 1
        },
        "yccd_ids": "1"
    })

    # Week 3: Compare numbers
    exercises.append({
        "lop": 1, "tuan": 3, "section": "kham_pha", "sort_order": 1,
        "exercise_type": "fill_in",
        "title_vi": "So sánh: >, < hay =",
        "title_en": "Compare: >, < or =",
        "instruction_vi": "Điền dấu >, < hoặc = vào ô trống.",
        "instruction_en": "Fill in >, < or = in the blank.",
        "hint_vi": "Số lớn hơn thì dùng >, nhỏ hơn dùng <, bằng nhau dùng =.",
        "hint_en": "Greater uses >, less uses <, equal uses =.",
        "config": {
            "items": [
                {"expression": "3 ☐ 5", "answer": "<"},
                {"expression": "7 ☐ 4", "answer": ">"},
                {"expression": "6 ☐ 6", "answer": "="},
                {"expression": "2 ☐ 8", "answer": "<"},
                {"expression": "9 ☐ 1", "answer": ">"},
                {"expression": "5 ☐ 5", "answer": "="},
            ],
            "layout": "grid_2col"
        },
        "yccd_ids": "5"
    })

    # Week 9: Addition within 10
    exercises.append({
        "lop": 1, "tuan": 9, "section": "kham_pha", "sort_order": 1,
        "exercise_type": "fill_in",
        "title_vi": "Phép cộng trong phạm vi 10",
        "title_en": "Addition within 10",
        "instruction_vi": "Tính kết quả mỗi phép cộng.",
        "instruction_en": "Calculate each addition.",
        "hint_vi": "Dùng ngón tay hoặc đồ vật để đếm thêm.",
        "hint_en": "Use fingers or objects to count on.",
        "config": {
            "items": [
                {"expression": "2 + 3 =", "answer": "5"},
                {"expression": "4 + 1 =", "answer": "5"},
                {"expression": "1 + 6 =", "answer": "7"},
                {"expression": "3 + 4 =", "answer": "7"},
                {"expression": "5 + 5 =", "answer": "10"},
                {"expression": "0 + 8 =", "answer": "8"},
            ],
            "layout": "grid_2col"
        },
        "yccd_ids": "6,7"
    })

    # Week 11: Subtraction within 10
    exercises.append({
        "lop": 1, "tuan": 11, "section": "kham_pha", "sort_order": 1,
        "exercise_type": "word_problem",
        "title_vi": "Bài toán có lời văn",
        "title_en": "Word problem",
        "instruction_vi": "Đọc đề và giải.",
        "instruction_en": "Read and solve.",
        "hint_vi": "Có 8 con chim, 3 con bay đi. Lấy 8 trừ 3.",
        "hint_en": "There are 8 birds, 3 fly away. Subtract 3 from 8.",
        "config": {
            "story": {
                "text_vi": "Trên cành cây có 8 con chim đang đậu. 3 con bay đi. Hỏi trên cành còn lại bao nhiêu con chim?",
                "text_en": "There are 8 birds on a branch. 3 fly away. How many birds are left on the branch?",
                "illustration": "🐦🐦🐦🐦🐦🐦🐦🐦 → 🐦🐦🐦✈️",
                "expression": "8 − 3",
                "answer": "5"
            }
        },
        "yccd_ids": "8,9"
    })

    # Week 12: Subtraction (continued)
    exercises.append({
        "lop": 1, "tuan": 12, "section": "hoat_dong", "sort_order": 1,
        "exercise_type": "table_fill",
        "title_vi": "Bảng trừ từ 7",
        "title_en": "Subtraction table from 7",
        "instruction_vi": "Hoàn thành bảng trừ.",
        "instruction_en": "Complete the subtraction table.",
        "hint_vi": "Nhìn hàng trên (7) và hàng hai (số bị trừ). Điền 7 trừ số đó.",
        "hint_en": "Look at the top (7) and second row. Fill in 7 minus that number.",
        "config": {
            "operation": "-",
            "base": 7,
            "operands": [1, 2, 3, 4, 5, 6, 7, 0],
            "answers": [6, 5, 4, 3, 2, 1, 0, 7]
        },
        "yccd_ids": "8,9"
    })

    exercises.append({
        "lop": 1, "tuan": 12, "section": "hoat_dong", "sort_order": 2,
        "exercise_type": "fill_in",
        "title_vi": "Tính (nhiều bước)",
        "title_en": "Compute (multi-step)",
        "instruction_vi": "Tính từ trái sang phải.",
        "instruction_en": "Compute from left to right.",
        "hint_vi": "Ví dụ: 10 − 4 = 6, rồi 6 − 1 = 5.",
        "hint_en": "Example: 10 − 4 = 6, then 6 − 1 = 5.",
        "config": {
            "items": [
                {"expression": "10 − 4 − 1 =", "answer": "5"},
                {"expression": "9 − 2 − 7 =", "answer": "0"},
                {"expression": "1 + 6 − 3 =", "answer": "4"},
                {"expression": "6 + 0 − 5 =", "answer": "1"},
            ],
            "layout": "grid_2col"
        },
        "yccd_ids": "8,9"
    })

    exercises.append({
        "lop": 1, "tuan": 12, "section": "cung_co", "sort_order": 1,
        "exercise_type": "coloring",
        "title_vi": "Tô màu quả hồng",
        "title_en": "Color the persimmons",
        "instruction_vi": "Tô 4 quả XANH trước, rồi 2 quả ĐỎ.",
        "instruction_en": "Color 4 BLUE first, then 2 RED.",
        "hint_vi": "Chọn màu xanh, tô 4 quả. Rồi chọn đỏ, tô 2 quả còn lại.",
        "hint_en": "Pick blue, color 4 fruits. Then pick red, color remaining 2.",
        "config": {
            "total_items": 6,
            "emoji": "🍅",
            "label_vi": "quả hồng",
            "label_en": "persimmons",
            "expression": "6 − 2 = 4",
            "color_targets": [
                {"color": "#3b82f6", "name_vi": "XANH", "name_en": "BLUE", "count": 4},
                {"color": "#ef4444", "name_vi": "ĐỎ", "name_en": "RED", "count": 2}
            ]
        },
        "yccd_ids": "8,9"
    })

    exercises.append({
        "lop": 1, "tuan": 12, "section": "cung_co", "sort_order": 2,
        "exercise_type": "matching",
        "title_vi": "Nối lá với hoa/quả",
        "title_en": "Match leaf to flower/fruit",
        "instruction_vi": "Tính phép tính ở mỗi lá. Nối với hoa/quả có kết quả đúng!",
        "instruction_en": "Compute each leaf. Match to the flower/fruit with the correct answer!",
        "hint_vi": "Nhấn vào lá bên trái, rồi nhấn hoa/quả bên phải có đáp số khớp.",
        "hint_en": "Click a leaf, then click the matching flower/fruit on the right.",
        "config": {
            "pairs": [
                {"left_expr": "9 − 3", "left_label_vi": "Lá ngô", "left_label_en": "Corn leaf", "answer": 6},
                {"left_expr": "8 − 6", "left_label_vi": "Lá loa kèn", "left_label_en": "Lily leaf", "answer": 2},
                {"left_expr": "10 − 5", "left_label_vi": "Lá hoa hồng", "left_label_en": "Rose leaf", "answer": 5},
                {"left_expr": "1 + 6", "left_label_vi": "Lá tre", "left_label_en": "Bamboo leaf", "answer": 7}
            ],
            "right_items": [
                {"value": 6, "label_vi": "Bắp ngô", "label_en": "Corn cob"},
                {"value": 5, "label_vi": "Hoa hồng", "label_en": "Rose"},
                {"value": 7, "label_vi": "Dóng tre", "label_en": "Bamboo stalk"},
                {"value": 2, "label_vi": "Hoa loa kèn", "label_en": "Lily flower"}
            ]
        },
        "yccd_ids": "8,9"
    })

    # Week 13: Addition & Subtraction tables
    exercises.append({
        "lop": 1, "tuan": 13, "section": "kham_pha", "sort_order": 1,
        "exercise_type": "fill_in",
        "title_vi": "Nhóm phép tính (Fact Family)",
        "title_en": "Fact Family",
        "instruction_vi": "Hoàn thành nhóm phép tính liên quan.",
        "instruction_en": "Complete the related fact family.",
        "hint_vi": "Ba số 3, 5, 8 tạo thành 4 phép tính: 3+5=8, 5+3=8, 8-3=5, 8-5=3.",
        "hint_en": "Three numbers 3, 5, 8 make 4 facts: 3+5=8, 5+3=8, 8-3=5, 8-5=3.",
        "config": {
            "items": [
                {"expression": "3 + 5 =", "answer": "8"},
                {"expression": "5 + 3 =", "answer": "8"},
                {"expression": "8 − 3 =", "answer": "5"},
                {"expression": "8 − 5 =", "answer": "3"},
            ],
            "layout": "grid_2col"
        },
        "yccd_ids": "8,9,10"
    })

    # ═══════════════════════════════════════
    # GRADE 2: Addition/Subtraction with carrying
    # ═══════════════════════════════════════
    exercises.append({
        "lop": 2, "tuan": 1, "section": "kham_pha", "sort_order": 1,
        "exercise_type": "fill_in",
        "title_vi": "Ôn tập: Phép cộng trong phạm vi 20",
        "title_en": "Review: Addition within 20",
        "instruction_vi": "Tính các phép cộng sau.",
        "instruction_en": "Calculate the following additions.",
        "hint_vi": "Cộng hàng đơn vị trước, nếu được 10 thì nhớ 1.",
        "hint_en": "Add ones first, carry 1 if sum is 10 or more.",
        "config": {
            "items": [
                {"expression": "9 + 5 =", "answer": "14"},
                {"expression": "8 + 7 =", "answer": "15"},
                {"expression": "6 + 9 =", "answer": "15"},
                {"expression": "7 + 6 =", "answer": "13"},
                {"expression": "8 + 8 =", "answer": "16"},
                {"expression": "9 + 9 =", "answer": "18"},
            ],
            "layout": "grid_2col"
        },
        "yccd_ids": "34,35"
    })

    exercises.append({
        "lop": 2, "tuan": 5, "section": "hoat_dong", "sort_order": 1,
        "exercise_type": "word_problem",
        "title_vi": "Bài toán có lời văn",
        "title_en": "Word problem",
        "instruction_vi": "Đọc đề, viết phép tính và tìm đáp số.",
        "instruction_en": "Read, write the equation, and find the answer.",
        "hint_vi": "Tìm tổng: cộng hai số lại.",
        "hint_en": "Find the sum: add the two numbers.",
        "config": {
            "story": {
                "text_vi": "Tổ 1 trồng được 28 cây. Tổ 2 trồng được 35 cây. Hỏi cả hai tổ trồng được bao nhiêu cây?",
                "text_en": "Team 1 planted 28 trees. Team 2 planted 35 trees. How many trees did both teams plant in total?",
                "illustration": "🌳🌳🌳... (28) + 🌲🌲🌲... (35)",
                "expression": "28 + 35",
                "answer": "63"
            }
        },
        "yccd_ids": "38,39"
    })

    # ═══════════════════════════════════════
    # GRADE 3: Multiplication & Division
    # ═══════════════════════════════════════
    exercises.append({
        "lop": 3, "tuan": 1, "section": "kham_pha", "sort_order": 1,
        "exercise_type": "fill_in",
        "title_vi": "Bảng nhân 2",
        "title_en": "Multiplication table of 2",
        "instruction_vi": "Hoàn thành bảng nhân 2.",
        "instruction_en": "Complete the multiplication table of 2.",
        "hint_vi": "2 × 1 = 2, 2 × 2 = 4, 2 × 3 = 6, ...",
        "hint_en": "2 × 1 = 2, 2 × 2 = 4, 2 × 3 = 6, ...",
        "config": {
            "items": [
                {"expression": "2 × 1 =", "answer": "2"},
                {"expression": "2 × 2 =", "answer": "4"},
                {"expression": "2 × 3 =", "answer": "6"},
                {"expression": "2 × 4 =", "answer": "8"},
                {"expression": "2 × 5 =", "answer": "10"},
                {"expression": "2 × 6 =", "answer": "12"},
                {"expression": "2 × 7 =", "answer": "14"},
                {"expression": "2 × 8 =", "answer": "16"},
                {"expression": "2 × 9 =", "answer": "18"},
                {"expression": "2 × 10 =", "answer": "20"},
            ],
            "layout": "grid_2col"
        },
        "yccd_ids": "87,88"
    })

    exercises.append({
        "lop": 3, "tuan": 3, "section": "hoat_dong", "sort_order": 1,
        "exercise_type": "word_problem",
        "title_vi": "Bài toán nhân",
        "title_en": "Multiplication word problem",
        "instruction_vi": "Đọc đề và giải.",
        "instruction_en": "Read and solve.",
        "hint_vi": "Mỗi hộp có 5 quả. Có 4 hộp → 5 × 4.",
        "hint_en": "Each box has 5 fruits. There are 4 boxes → 5 × 4.",
        "config": {
            "story": {
                "text_vi": "Mỗi hộp có 5 quả táo. Có 4 hộp. Hỏi tất cả có bao nhiêu quả táo?",
                "text_en": "Each box has 5 apples. There are 4 boxes. How many apples are there in total?",
                "illustration": "📦🍎🍎🍎🍎🍎 × 4",
                "expression": "5 × 4",
                "answer": "20"
            }
        },
        "yccd_ids": "87,88"
    })

    # ═══════════════════════════════════════
    # GRADE 4: Fractions, large numbers
    # ═══════════════════════════════════════
    exercises.append({
        "lop": 4, "tuan": 1, "section": "kham_pha", "sort_order": 1,
        "exercise_type": "fill_in",
        "title_vi": "Số có nhiều chữ số",
        "title_en": "Multi-digit numbers",
        "instruction_vi": "Viết số thích hợp.",
        "instruction_en": "Write the appropriate number.",
        "hint_vi": "Đọc kỹ số rồi viết bằng chữ số.",
        "hint_en": "Read the number carefully and write in digits.",
        "config": {
            "items": [
                {"expression": "Năm nghìn ba trăm hai mươi bốn =", "answer": "5324"},
                {"expression": "Bảy nghìn không trăm linh năm =", "answer": "7005"},
                {"expression": "Chín nghìn chín trăm chín mươi chín =", "answer": "9999"},
                {"expression": "Mười nghìn =", "answer": "10000"},
            ]
        },
        "yccd_ids": "158,159"
    })

    exercises.append({
        "lop": 4, "tuan": 10, "section": "kham_pha", "sort_order": 1,
        "exercise_type": "fill_in",
        "title_vi": "Phân số",
        "title_en": "Fractions",
        "instruction_vi": "Viết phân số thích hợp.",
        "instruction_en": "Write the appropriate fraction.",
        "hint_vi": "Tử số là phần tô màu, mẫu số là tổng số phần.",
        "hint_en": "Numerator is the colored part, denominator is the total parts.",
        "config": {
            "items": [
                {"expression": "🟦🟦🟦⬜⬜ (phần tô/tổng) =", "answer": "3/5"},
                {"expression": "🟥🟥⬜⬜⬜⬜ =", "answer": "2/6"},
                {"expression": "🟩🟩🟩🟩⬜⬜⬜⬜ =", "answer": "4/8"},
            ]
        },
        "yccd_ids": "175,176"
    })

    # ═══════════════════════════════════════
    # GRADE 5: Decimals, percentages
    # ═══════════════════════════════════════
    exercises.append({
        "lop": 5, "tuan": 1, "section": "kham_pha", "sort_order": 1,
        "exercise_type": "fill_in",
        "title_vi": "Ôn tập: Phân số và số thập phân",
        "title_en": "Review: Fractions and decimals",
        "instruction_vi": "Chuyển phân số thành số thập phân.",
        "instruction_en": "Convert fractions to decimals.",
        "hint_vi": "Chia tử số cho mẫu số. VD: 1/2 = 0,5.",
        "hint_en": "Divide numerator by denominator. E.g., 1/2 = 0.5.",
        "config": {
            "items": [
                {"expression": "1/2 =", "answer": "0,5"},
                {"expression": "1/4 =", "answer": "0,25"},
                {"expression": "3/4 =", "answer": "0,75"},
                {"expression": "1/5 =", "answer": "0,2"},
                {"expression": "3/10 =", "answer": "0,3"},
            ]
        },
        "yccd_ids": "230,231"
    })

    exercises.append({
        "lop": 5, "tuan": 5, "section": "hoat_dong", "sort_order": 1,
        "exercise_type": "word_problem",
        "title_vi": "Bài toán phần trăm",
        "title_en": "Percentage word problem",
        "instruction_vi": "Đọc đề và giải.",
        "instruction_en": "Read and solve.",
        "hint_vi": "Tìm 25% của 200: lấy 200 × 25 ÷ 100.",
        "hint_en": "Find 25% of 200: compute 200 × 25 ÷ 100.",
        "config": {
            "story": {
                "text_vi": "Một thửa ruộng hình chữ nhật có diện tích 200 m². Người ta trồng lúa trên 25% diện tích. Hỏi diện tích trồng lúa là bao nhiêu m²?",
                "text_en": "A rectangular field has an area of 200 m². 25% of the area is planted with rice. What is the area planted with rice?",
                "expression": "200 × 25 ÷ 100",
                "answer": "50"
            }
        },
        "yccd_ids": "245,246"
    })


    # ═══════════════════════════════════════
    # TUẦN 15 — Phiếu bài tập cuối tuần (trung thành với đề DOCX)
    # ═══════════════════════════════════════

    # T15 Bài 1. Tính.
    exercises.append({
        "lop": 1, "tuan": 15, "section": "practice", "sort_order": 1,
        "exercise_type": "fill_in",
        "title_vi": "Bài 1. Tính",
        "title_en": "Exercise 1. Calculate",
        "instruction_vi": "Tính.",
        "instruction_en": "Calculate.",
        "config": {
            "items": [
                {"expression": "2 + 6", "answer": "8"},
                {"expression": "8 − 5", "answer": "3"},
                {"expression": "4 + 5", "answer": "9"},
                {"expression": "8 − 3", "answer": "5"},
                {"expression": "1 + 7", "answer": "8"},
                {"expression": "6 − 6", "answer": "0"},
                {"expression": "0 + 9", "answer": "9"},
                {"expression": "10 − 4", "answer": "6"},
                {"expression": "6 − 3", "answer": "3"}
            ],
            "layout": "grid_2col"
        },
        "yccd_ids": "8"
    })

    # T15 Bài 2. Nối cho thích hợp (theo mẫu).
    exercises.append({
        "lop": 1, "tuan": 15, "section": "practice", "sort_order": 2,
        "exercise_type": "matching",
        "title_vi": "Bài 2. Nối cho thích hợp (theo mẫu)",
        "title_en": "Exercise 2. Match correctly (follow the example)",
        "instruction_vi": "Nối cho thích hợp (theo mẫu).",
        "instruction_en": "Match correctly (follow the example).",
        "config": {
            "pairs": [
                {"left_expr": "10 − 0", "answer": "10"},
                {"left_expr": "2 + 7", "answer": "9"},
                {"left_expr": "5 + 0", "answer": "5"},
                {"left_expr": "8 − 2", "answer": "6"}
            ],
            "right_items": [
                {"value": "9"},
                {"value": "6"},
                {"value": "5"},
                {"value": "10"}
            ]
        },
        "yccd_ids": "8"
    })

    # T15 Bài 3. Viết số thích hợp vào ô trống (Tháp số).
    # 3 tháp, mỗi tháp 3 hàng (3-2-1). Quy tắc: ô = tổng 2 ô bên dưới.
    # Trung thành theo đề DOCX: tháp 1 từ ảnh gốc, tháp 2 & 3 từ dữ liệu DOCX.
    # Tháp 1 (ảnh): bottom [2,3,0], middle [5,3], top [trống]
    # Tháp 2 (DOCX): bottom [3,3,3], middle [trống,trống], top [trống]
    # Tháp 3 (DOCX): bottom [0,1,0], middle [trống,trống], top [trống]
    exercises.append({
        "lop": 1, "tuan": 15, "section": "practice", "sort_order": 3,
        "exercise_type": "number_pyramid",
        "title_vi": "Bài 3. Viết số thích hợp vào ô trống",
        "title_en": "Exercise 3. Fill in the blanks",
        "instruction_vi": "Viết số thích hợp vào ô trống.",
        "instruction_en": "Fill in the appropriate number in each blank.",
        "config": {
            "pyramids": [
                {
                    "rows": [
                        [2, 3, 0],
                        [5, 3],
                        [None]
                    ]
                },
                {
                    "rows": [
                        [3, 3, 3],
                        [None, None],
                        [None]
                    ]
                },
                {
                    "rows": [
                        [0, 1, 0],
                        [None, None],
                        [None]
                    ]
                }
            ]
        },
        "yccd_ids": "8"
    })

    # T15 Bài 4. Đúng ghi Đ, sai ghi S.
    exercises.append({
        "lop": 1, "tuan": 15, "section": "practice", "sort_order": 4,
        "exercise_type": "true_false",
        "title_vi": "Bài 4. Đúng ghi Đ, sai ghi S",
        "title_en": "Exercise 4. True or False",
        "instruction_vi": "Đúng ghi Đ, sai ghi S.",
        "instruction_en": "Write Đ for correct, S for incorrect.",
        "config": {
            "statements": [
                {"text_vi": "0 + 5 + 1 = 6", "answer": "Đ"},
                {"text_vi": "8 − 3 − 2 = 5", "answer": "S"},
                {"text_vi": "10 + 0 − 10 = 10", "answer": "S"},
                {"text_vi": "4 − 3 + 2 = 1", "answer": "S"},
                {"text_vi": "2 + 5 − 7 = 1", "answer": "S"},
                {"text_vi": "5 + 5 − 5 = 5", "answer": "Đ"}
            ]
        },
        "yccd_ids": "8"
    })

    # T15 Bài 5. Di chuyển một que tính để được phép tính đúng.
    exercises.append({
        "lop": 1, "tuan": 15, "section": "practice", "sort_order": 5,
        "exercise_type": "matchstick_puzzle",
        "title_vi": "Bài 5. Di chuyển que tính",
        "title_en": "Exercise 5. Move a matchstick",
        "instruction_vi": "Dùng các que tính xếp thành phép cộng 1 + 2 = 5 như sau. Di chuyển một que tính để được phép tính đúng.",
        "instruction_en": "Matchsticks form 1 + 2 = 5. Move one matchstick to make a correct equation.",
        "hint_vi": "Thử đổi số 5 thành số khác, hoặc đổi dấu.",
        "config": {
            "initial": "1+2=5",
            "solutions": ["7-2=5", "1+2=3"],
            "max_moves": 1
        },
        "yccd_ids": "8"
    })

    # T15 Bài 6. Viết hai phép tính cộng, hai phép tính trừ thích hợp với mỗi hình.
    # Hình 1: cây xoài 6 quả trên cây, 2 quả rụng → (6, 2, 4)
    # Hình 2: bình hoa 7 bông, 3 đỏ 4 xanh → (7, 3, 4)
    # Đáp án: 6−2=4, 6−4=2, 2+4=6, 4+2=6 | 7−3=4, 7−4=3, 3+4=7, 4+3=7
    exercises.append({
        "lop": 1, "tuan": 15, "section": "practice", "sort_order": 6,
        "exercise_type": "image_equations",
        "title_vi": "Bài 6. Viết phép tính thích hợp với mỗi hình",
        "title_en": "Exercise 6. Write equations for each picture",
        "instruction_vi": "Viết hai phép tính cộng, hai phép tính trừ thích hợp với mỗi hình.",
        "instruction_en": "Write two addition and two subtraction equations for each picture.",
        "config": {
            "groups": [
                {
                    "image": "lop1/week15/img_bai6a.png",
                    "description_vi": "Cây xoài có 6 quả trên cây, 2 quả rụng xuống đất.",
                    "description_en": "A mango tree with 6 fruits on it and 2 fallen on the ground.",
                    "equations": [
                        {"op": "+", "answer": [2, 4, 6]},
                        {"op": "+", "answer": [4, 2, 6]},
                        {"op": "−", "answer": [6, 2, 4]},
                        {"op": "−", "answer": [6, 4, 2]}
                    ],
                    "valid_numbers": [2, 4, 6]
                },
                {
                    "image": "lop1/week15/img_bai6b.png",
                    "description_vi": "Bình hoa có 7 bông hoa: 3 bông đỏ, 4 bông xanh.",
                    "description_en": "A vase with 7 flowers: 3 red and 4 blue.",
                    "equations": [
                        {"op": "+", "answer": [3, 4, 7]},
                        {"op": "+", "answer": [4, 3, 7]},
                        {"op": "−", "answer": [7, 3, 4]},
                        {"op": "−", "answer": [7, 4, 3]}
                    ],
                    "valid_numbers": [3, 4, 7]
                }
            ]
        },
        "yccd_ids": "8"
    })

    # T15 Bài 7. Nối cho thích hợp (theo mẫu).
    # Hàng trên: 7 vật (xúc sắc, hộp sữa, hộp quà, quả bóng rổ, viên gạch, tủ lạnh, hộp phấn)
    # Hàng dưới: 2 khối hình (khối lập phương, khối hộp chữ nhật)
    # HS nối mỗi vật với khối hình phù hợp.
    exercises.append({
        "lop": 1, "tuan": 15, "section": "practice", "sort_order": 7,
        "exercise_type": "classify_match",
        "title_vi": "Bài 7. Nối cho thích hợp (theo mẫu)",
        "title_en": "Exercise 7. Match objects to shapes",
        "instruction_vi": "Nối cho thích hợp (theo mẫu).",
        "instruction_en": "Match each object to the correct shape.",
        "config": {
            "items": [
                {"label": "🎲 Xúc sắc", "image": "lop1/week15/xuc_sac.png", "category": "lap_phuong"},
                {"label": "🧃 Hộp sữa", "image": "lop1/week15/hop_sua.png", "category": "hop_chu_nhat"},
                {"label": "🎁 Hộp quà", "image": "lop1/week15/hop_qua.png", "category": "lap_phuong"},
                {"label": "🏀 Quả bóng rổ", "image": "lop1/week15/bong_ro.png", "category": "hop_chu_nhat"},
                {"label": "🧱 Viên gạch", "image": "lop1/week15/vien_gach.png", "category": "hop_chu_nhat"},
                {"label": "🧊 Hộp phấn", "image": "lop1/week15/hop_phan.png", "category": "lap_phuong"},
                {"label": "📦 Tủ lạnh", "image": "lop1/week15/tu_lanh.png", "category": "hop_chu_nhat"}
            ],
            "categories": [
                {"id": "lap_phuong", "label": "🟦 Khối lập phương", "image": "lop1/week15/khoi_lap_phuong.png"},
                {"id": "hop_chu_nhat", "label": "📦 Khối hộp chữ nhật", "image": "lop1/week15/khoi_hop_cn.png"}
            ]
        },
        "yccd_ids": "15"
    })

    # T15 Bài 9. Nhận biết khối lập phương
    exercises.append({
        "lop": 1, "tuan": 15, "section": "practice", "sort_order": 9,
        "exercise_type": "fill_in",
        "title_vi": "Bài 9. Nhận biết khối lập phương",
        "title_en": "Exercise 9. Identify cubes",
        "instruction_vi": "Trong các hình sau, những hình nào là khối lập phương?",
        "instruction_en": "Which of the following shapes are cubes?",
        "hint_vi": "Khối lập phương có tất cả các mặt đều là hình vuông.",
        "config": {
            "items": [
                {"expression": "Những hình … là khối lập phương →", "answer": "B, D"}
            ],
            "show_labels": False
        },
        "images": ["lop1/week15/img_010.png"],
        "yccd_ids": "15"
    })

    # T15 Bài 10. Mai dùng 2 khối lập phương và 3 khối hộp chữ nhật
    exercises.append({
        "lop": 1, "tuan": 15, "section": "practice", "sort_order": 10,
        "exercise_type": "multiple_choice",
        "title_vi": "Bài 10. Xếp hình từ khối",
        "title_en": "Exercise 10. Build with blocks",
        "instruction_vi": "Mai dùng 2 khối lập phương và 3 khối hộp chữ nhật để xếp hình. Hỏi Mai đã xếp hình nào trong các hình dưới đây?",
        "instruction_en": "Mai uses 2 cubes and 3 rectangular prisms to build a shape. Which shape did Mai build?",
        "config": {
            "question": {"text_vi": "Mai đã xếp hình nào?", "text_en": "Which shape did Mai build?"},
            "choices": [
                {"text_vi": "A", "text_en": "A"},
                {"text_vi": "B", "text_en": "B"},
                {"text_vi": "C", "text_en": "C"},
                {"text_vi": "D", "text_en": "D"}
            ],
            "correct_index": 2
        },
        "yccd_ids": "15"
    })

    # T15 Bài 10b. Vị trí Hải xếp hàng
    exercises.append({
        "lop": 1, "tuan": 15, "section": "practice", "sort_order": 11,
        "exercise_type": "fill_in",
        "title_vi": "Bài 10b. Viết số thích hợp vào chỗ chấm",
        "title_en": "Exercise 10b. Fill in the blanks",
        "instruction_vi": "Viết số thích hợp vào chỗ chấm.",
        "instruction_en": "Fill in the appropriate number.",
        "config": {
            "items": [
                {"expression": "Từ phải sang trái, Hải đứng ở vị trí số →", "answer": "3"},
                {"expression": "Từ trái sang phải, Hải đứng ở vị trí số →", "answer": "4"}
            ]
        },
        "images": ["lop1/week15/img_011.png"],
        "yccd_ids": "13"
    })

    # T15 Bài 11. Hình bên có … khối lập phương.
    exercises.append({
        "lop": 1, "tuan": 15, "section": "practice", "sort_order": 12,
        "exercise_type": "fill_in",
        "title_vi": "Bài 11. Viết số thích hợp vào chỗ chấm",
        "title_en": "Exercise 11. Fill in the blank",
        "instruction_vi": "Viết số thích hợp vào chỗ chấm.",
        "instruction_en": "Fill in the appropriate number.",
        "config": {
            "items": [
                {"expression": "Hình bên có … khối lập phương →", "answer": "4"}
            ],
            "show_labels": False
        },
        "images": ["lop1/week15/img_003.png"],
        "yccd_ids": "15"
    })

    # ═══════════════════════════════════════
    # TUẦN 16
    # ═══════════════════════════════════════

    # T16 Bài 2. Tô màu vào con mèo ở dưới gầm bàn, quả bóng ở trên bàn.
    # (This is a coloring exercise in DOCX — we make it true_false for web)
    exercises.append({
        "lop": 1, "tuan": 16, "section": "practice", "sort_order": 2,
        "exercise_type": "true_false",
        "title_vi": "Bài 2. Nhìn hình, trả lời",
        "title_en": "Exercise 2. Look and answer",
        "instruction_vi": "Tô màu vào con mèo ở dưới gầm bàn, quả bóng ở trên bàn.",
        "instruction_en": "Color the cat under the table and the ball on the table.",
        "hint_vi": "Nhìn kĩ hình, xác định đâu là trên bàn, đâu là dưới gầm bàn.",
        "config": {
            "description_vi": "Trong hình bên, trên bàn có 1 viên bi và 1 con mèo, dưới đất có 1 viên bi và 1 con mèo.",
            "statements": []
        },
        "images": ["lop1/week15/img_005.png"],
        "yccd_ids": "13"
    })

    # T16 Bài 3. Viết "phải", "trái", "giữa" vào chỗ chấm cho thích hợp.
    exercises.append({
        "lop": 1, "tuan": 16, "section": "practice", "sort_order": 3,
        "exercise_type": "fill_in",
        "title_vi": "Bài 3. Viết \"phải\", \"trái\", \"giữa\" vào chỗ chấm",
        "title_en": "Exercise 3. Fill in: right, left, middle",
        "instruction_vi": "Viết \"phải\", \"trái\", \"giữa\" vào chỗ chấm cho thích hợp.",
        "instruction_en": "Fill in \"right\", \"left\" or \"middle\" appropriately.",
        "config": {
            "items": [
                {"expression": "Bông hoa màu đỏ ở bên →", "answer": "phải"},
                {"expression": "Bông hoa màu trắng ở bên →", "answer": "trái"},
                {"expression": "Bông hoa màu xanh ở … bông hoa màu trắng và bông hoa màu đỏ →", "answer": "giữa"}
            ],
            "show_labels": False
        },
        "images": ["lop1/week15/img_008.png"],
        "yccd_ids": "13"
    })

    # T16 Bài 4. Đúng ghi Đ, sai ghi S.
    exercises.append({
        "lop": 1, "tuan": 16, "section": "practice", "sort_order": 4,
        "exercise_type": "true_false",
        "title_vi": "Bài 4. Đúng ghi Đ, sai ghi S",
        "title_en": "Exercise 4. True or False",
        "instruction_vi": "Trong hình bên: Đúng ghi Đ, sai ghi S.",
        "instruction_en": "True or False about the picture.",
        "config": {
            "statements": [
                {"text_vi": "Gấu bông ở trên mặt bàn.", "answer": "Đ"},
                {"text_vi": "Quả bóng ở dưới gầm bàn.", "answer": "Đ"},
                {"text_vi": "Máy ảnh ở trên mặt bàn.", "answer": "Đ"},
                {"text_vi": "Tàu hỏa ở trên mặt bàn.", "answer": "S"},
                {"text_vi": "Khủng long ở dưới gầm bàn.", "answer": "S"},
                {"text_vi": "Quả địa cầu ở trên mặt bàn.", "answer": "Đ"}
            ]
        },
        "images": ["lop1/week15/img_009.png"],
        "yccd_ids": "13"
    })

    # T16 Bài 7. Xếp hàng mua kem
    exercises.append({
        "lop": 1, "tuan": 16, "section": "practice", "sort_order": 7,
        "exercise_type": "fill_in",
        "title_vi": "Bài 7. Xếp hàng mua kem",
        "title_en": "Exercise 7. Queueing for ice cream",
        "instruction_vi": "Các bạn xếp hàng mua kem. Rô-bốt nhận thấy đứng trước mình là bạn Mai, đứng sau mình là bạn Nam. Biết còn 2 bạn nữa đứng trước Mai và cũng còn 2 bạn nữa đứng sau Nam. Hỏi có bao nhiêu bạn xếp hàng mua kem?",
        "instruction_en": "Students queue for ice cream. Robot sees Mai in front, Nam behind. 2 more students before Mai, 2 more after Nam. How many students in the queue?",
        "hint_vi": "Đếm: 2 bạn + Mai + Rô-bốt + Nam + 2 bạn.",
        "config": {
            "items": [
                {"expression": "Có bao nhiêu bạn xếp hàng mua kem? →", "answer": "7"}
            ],
            "show_labels": False
        },
        "yccd_ids": "13"
    })

    # T16 Bài 9. Những hình … là khối lập phương.
    exercises.append({
        "lop": 1, "tuan": 16, "section": "practice", "sort_order": 9,
        "exercise_type": "fill_in",
        "title_vi": "Bài 9. Viết tiếp vào chỗ chấm",
        "title_en": "Exercise 9. Fill in the blanks",
        "instruction_vi": "Trong các hình sau, những hình nào là khối lập phương?",
        "instruction_en": "Which shapes are cubes?",
        "config": {
            "items": [
                {"expression": "Những hình … là khối lập phương →", "answer": "B, D"}
            ],
            "show_labels": False
        },
        "images": ["lop1/week15/img_010.png"],
        "yccd_ids": "15"
    })

    # T16 Bài 10. Vị trí Hải
    exercises.append({
        "lop": 1, "tuan": 16, "section": "practice", "sort_order": 10,
        "exercise_type": "fill_in",
        "title_vi": "Bài 10. Viết số thích hợp vào chỗ chấm",
        "title_en": "Exercise 10. Fill in the numbers",
        "instruction_vi": "Viết số thích hợp vào chỗ chấm.",
        "instruction_en": "Fill in the appropriate number.",
        "config": {
            "items": [
                {"expression": "Từ phải sang trái, Hải đứng ở vị trí số →", "answer": "3"},
                {"expression": "Từ trái sang phải, Hải đứng ở vị trí số →", "answer": "4"}
            ]
        },
        "images": ["lop1/week15/img_011.png"],
        "yccd_ids": "13"
    })

    # T16 Bài 11. Hình bên có … khối lập phương.
    exercises.append({
        "lop": 1, "tuan": 16, "section": "practice", "sort_order": 11,
        "exercise_type": "fill_in",
        "title_vi": "Bài 11. Viết số thích hợp vào chỗ chấm",
        "title_en": "Exercise 11. Fill in the blank",
        "instruction_vi": "Viết số thích hợp vào chỗ chấm.",
        "instruction_en": "Fill in the appropriate number.",
        "config": {
            "items": [
                {"expression": "Hình bên có … khối lập phương →", "answer": "4"}
            ],
            "show_labels": False
        },
        "yccd_ids": "15"
    })

    # ═══════════════════════════════════════
    # TUẦN 17
    # ═══════════════════════════════════════

    # T17 Bài 3. Viết dấu >, < hoặc = vào chỗ chấm
    exercises.append({
        "lop": 1, "tuan": 17, "section": "practice", "sort_order": 3,
        "exercise_type": "fill_in",
        "title_vi": "Bài 3. Viết dấu >, < hoặc =",
        "title_en": "Exercise 3. Write >, < or =",
        "instruction_vi": "Viết dấu >, < hoặc = vào chỗ chấm cho thích hợp.",
        "instruction_en": "Fill in >, < or = appropriately.",
        "config": {
            "items": [
                {"expression": "3 ☐ 5", "answer": "<"},
                {"expression": "8 ☐ 7", "answer": ">"},
                {"expression": "6 ☐ 9", "answer": "<"},
                {"expression": "0 ☐ 1", "answer": "<"},
                {"expression": "3 ☐ 3", "answer": "="},
                {"expression": "6 ☐ 5", "answer": ">"}
            ],
            "layout": "grid_2col"
        },
        "yccd_ids": "5"
    })

    # T17 Bài 4. Viết số thích hợp vào chỗ chấm (dãy số).
    exercises.append({
        "lop": 1, "tuan": 17, "section": "practice", "sort_order": 4,
        "exercise_type": "fill_in",
        "title_vi": "Bài 4. Viết số thích hợp vào chỗ chấm",
        "title_en": "Exercise 4. Fill in the numbers",
        "instruction_vi": "Viết số thích hợp vào chỗ chấm.",
        "instruction_en": "Fill in the missing numbers.",
        "config": {
            "items": [
                {"expression": "a) 4, 5, 6, ☐, ☐, 9 → số thứ 4 →", "answer": "7"},
                {"expression": "a) → số thứ 5 →", "answer": "8"},
                {"expression": "b) 8, ☐, 6, 5, ☐, 3 → số thứ 2 →", "answer": "7"},
                {"expression": "b) → số thứ 5 →", "answer": "4"},
                {"expression": "c) 2, ☐, 6, 8, 10 → số thứ 2 →", "answer": "4"}
            ]
        },
        "yccd_ids": "5"
    })

    # T17 Bài 8. Sắp xếp số
    exercises.append({
        "lop": 1, "tuan": 17, "section": "practice", "sort_order": 8,
        "exercise_type": "fill_in",
        "title_vi": "Bài 8. Sắp xếp số",
        "title_en": "Exercise 8. Order numbers",
        "instruction_vi": "Sắp xếp các số theo thứ tự.",
        "instruction_en": "Arrange the numbers in order.",
        "config": {
            "items": [
                {"expression": "Sắp xếp 2, 9, 7, 5 từ bé đến lớn →", "answer": "2, 5, 7, 9"},
                {"expression": "Sắp xếp 5, 6, 0, 3 từ lớn đến bé →", "answer": "6, 5, 3, 0"}
            ],
            "show_labels": False
        },
        "yccd_ids": "5"
    })

    # T17 Bài 9. Viết số thích hợp vào chỗ chấm (tìm số).
    exercises.append({
        "lop": 1, "tuan": 17, "section": "practice", "sort_order": 9,
        "exercise_type": "fill_in",
        "title_vi": "Bài 9. Viết số thích hợp vào chỗ chấm",
        "title_en": "Exercise 9. Fill in the blanks",
        "instruction_vi": "Viết số thích hợp vào chỗ chấm.",
        "instruction_en": "Fill in the appropriate number.",
        "config": {
            "items": [
                {"expression": "7 + ☐ = 10 →", "answer": "3"},
                {"expression": "5 + ☐ = 9 →", "answer": "4"},
                {"expression": "3 + ☐ = 6 →", "answer": "3"},
                {"expression": "☐ + 9 = 9 →", "answer": "0"},
                {"expression": "☐ + 2 = 8 →", "answer": "6"},
                {"expression": "☐ + 0 = 2 →", "answer": "2"}
            ],
            "layout": "grid_2col"
        },
        "yccd_ids": "8"
    })

    # T17 Bài 11. Bài toán có lời văn: Thu có 7 quyển vở
    exercises.append({
        "lop": 1, "tuan": 17, "section": "practice", "sort_order": 11,
        "exercise_type": "word_problem",
        "title_vi": "Bài 11. Viết số thích hợp vào ô trống",
        "title_en": "Exercise 11. Word problem",
        "instruction_vi": "Viết số thích hợp vào ô trống.",
        "instruction_en": "Fill in the appropriate number.",
        "config": {
            "story": {
                "text_vi": "Thu có 7 quyển vở. Mẹ mua cho Thu thêm 2 quyển vở nữa. Hỏi Thu có tất cả bao nhiêu quyển vở?",
                "text_en": "Thu has 7 notebooks. Mom buys 2 more. How many notebooks does Thu have in total?",
                "expression": "7 + 2",
                "answer": "9"
            }
        },
        "yccd_ids": "8,9"
    })

    # ═══════════════════════════════════════
    # TUẦN 18
    # ═══════════════════════════════════════

    # T18 Bài 1. Viết dấu >, < hoặc = (so sánh biểu thức)
    exercises.append({
        "lop": 1, "tuan": 18, "section": "practice", "sort_order": 1,
        "exercise_type": "fill_in",
        "title_vi": "Bài 1. Viết dấu >, < hoặc =",
        "title_en": "Exercise 1. Compare expressions",
        "instruction_vi": "Viết dấu >, < hoặc = vào chỗ chấm cho thích hợp.",
        "instruction_en": "Fill in >, < or = appropriately.",
        "config": {
            "items": [
                {"expression": "4 + 3 ☐ 6 + 1", "answer": "="},
                {"expression": "2 + 6 ☐ 1 + 6", "answer": ">"},
                {"expression": "5 + 1 ☐ 2 + 5", "answer": "<"},
                {"expression": "0 + 9 ☐ 5 + 2", "answer": ">"},
                {"expression": "6 + 4 ☐ 10 + 0", "answer": "="},
                {"expression": "2 + 5 ☐ 6 + 0 + 2", "answer": "<"},
                {"expression": "3 + 5 ☐ 5 + 3", "answer": "="},
                {"expression": "4 + 2 ☐ 4 + 3", "answer": "<"},
                {"expression": "7 + 2 ☐ 6 + 3 + 0", "answer": "="}
            ],
            "layout": "grid_2col"
        },
        "yccd_ids": "8"
    })

    # T18 Bài 3. Di chuyển que tính: 2 + 2 = 5
    exercises.append({
        "lop": 1, "tuan": 18, "section": "practice", "sort_order": 3,
        "exercise_type": "fill_in",
        "title_vi": "Bài 3. Di chuyển que tính",
        "title_en": "Exercise 3. Move a matchstick",
        "instruction_vi": "Dùng các que tính xếp thành phép cộng 2 + 2 = 5 như sau. Di chuyển 1 que tính để được phép tính đúng.",
        "instruction_en": "Matchsticks form 2 + 2 = 5. Move one matchstick to make a correct equation.",
        "config": {
            "items": [
                {"expression": "Phép tính đúng là →", "answer": "2 + 3 = 5"}
            ],
            "show_labels": False
        },
        "yccd_ids": "8"
    })

    # T18 Bài 4. Di chuyển que tính: 9 − 2 = 8
    exercises.append({
        "lop": 1, "tuan": 18, "section": "practice", "sort_order": 4,
        "exercise_type": "fill_in",
        "title_vi": "Bài 4. Di chuyển que tính",
        "title_en": "Exercise 4. Move a matchstick",
        "instruction_vi": "Dùng các que tính xếp thành phép cộng 9 − 2 = 8 như sau. Di chuyển một que tính để được phép tính đúng.",
        "instruction_en": "Matchsticks form 9 − 2 = 8. Move one matchstick to make a correct equation.",
        "config": {
            "items": [
                {"expression": "Phép tính đúng là →", "answer": "8 − 2 = 6"}
            ],
            "show_labels": False
        },
        "yccd_ids": "8"
    })

    # T18 Bài 5. Bài toán: Quả bóng trong hộp
    exercises.append({
        "lop": 1, "tuan": 18, "section": "practice", "sort_order": 5,
        "exercise_type": "word_problem",
        "title_vi": "Bài 5. Viết số thích hợp vào ô trống",
        "title_en": "Exercise 5. Word problem",
        "instruction_vi": "Viết số thích hợp vào ô trống.",
        "instruction_en": "Fill in the appropriate number.",
        "config": {
            "story": {
                "text_vi": "Trong hộp có 4 quả bóng màu xanh. Tùng cho thêm 4 quả bóng màu đỏ vào hộp. Hỏi trong hộp có tất cả bao nhiêu quả bóng?",
                "text_en": "A box has 4 blue balls. Tùng adds 4 red balls. How many balls are in the box?",
                "expression": "4 + 4",
                "answer": "8"
            }
        },
        "yccd_ids": "8,9"
    })

    # T18 Bài 6. Nam có mấy viên bi?
    exercises.append({
        "lop": 1, "tuan": 18, "section": "practice", "sort_order": 6,
        "exercise_type": "fill_in",
        "title_vi": "Bài 6. Bài toán suy luận",
        "title_en": "Exercise 6. Logic puzzle",
        "instruction_vi": "Mai, Việt và Nam có tất cả 6 viên bi. Biết Mai có số viên bi ít nhất, Việt có số viên bi nhiều nhất. Hỏi Nam có mấy viên bi?",
        "instruction_en": "Mai, Viet and Nam have 6 marbles total. Mai has the fewest, Viet the most. How many does Nam have?",
        "hint_vi": "Mỗi người có ít nhất 1 viên. Nếu Mai = 1, Việt phải lớn nhất → Việt = 3, Nam = 2.",
        "config": {
            "items": [
                {"expression": "Nam có … viên bi →", "answer": "2"}
            ],
            "show_labels": False
        },
        "yccd_ids": "8"
    })

    # T18 Bài 9. Hình trên cùng / dưới cùng có dạng hình gì?
    exercises.append({
        "lop": 1, "tuan": 18, "section": "practice", "sort_order": 9,
        "exercise_type": "fill_in",
        "title_vi": "Bài 9. Nhận dạng hình",
        "title_en": "Exercise 9. Identify shapes",
        "instruction_vi": "Hoà dán các hình trên giấy như sau. Hình trên cùng có dạng hình gì? Hình dưới cùng có dạng hình gì?",
        "instruction_en": "Hoa stacks shapes on paper. What shape is on top? On the bottom?",
        "config": {
            "items": [
                {"expression": "Hình trên cùng có dạng hình →", "answer": "chữ nhật"},
                {"expression": "Hình dưới cùng có dạng hình →", "answer": "tròn"}
            ],
            "show_labels": False
        },
        "yccd_ids": "15"
    })

    # ═══════════════════════════════════════
    # TUẦN 19
    # ═══════════════════════════════════════

    # T19 Bài 3. Viết số thích hợp vào chỗ chấm (dãy số 2 chữ số)
    exercises.append({
        "lop": 1, "tuan": 19, "section": "practice", "sort_order": 3,
        "exercise_type": "fill_in",
        "title_vi": "Bài 3. Viết số thích hợp vào chỗ chấm",
        "title_en": "Exercise 3. Fill in the numbers",
        "instruction_vi": "Viết số thích hợp vào chỗ chấm.",
        "instruction_en": "Fill in the missing numbers.",
        "config": {
            "items": [
                {"expression": "a) ☐, 9, 10, ☐, 12 → số đầu →", "answer": "8"},
                {"expression": "a) → số thứ 4 →", "answer": "11"},
                {"expression": "b) 14, ☐, ☐, 17, 18 → số thứ 2 →", "answer": "15"},
                {"expression": "b) → số thứ 3 →", "answer": "16"},
                {"expression": "c) 15, 14, ☐, ☐, 11 → số thứ 3 →", "answer": "13"},
                {"expression": "c) → số thứ 4 →", "answer": "12"},
                {"expression": "d) 20, 19, ☐, ☐, 16 → số thứ 3 →", "answer": "18"},
                {"expression": "d) → số thứ 4 →", "answer": "17"}
            ]
        },
        "yccd_ids": "3"
    })

    # T19 Bài 4. Hoàn thành bảng (Viết số / Đọc số / Chục / Đơn vị)
    exercises.append({
        "lop": 1, "tuan": 19, "section": "practice", "sort_order": 4,
        "exercise_type": "fill_in",
        "title_vi": "Bài 4. Hoàn thành bảng",
        "title_en": "Exercise 4. Complete the table",
        "instruction_vi": "Hoàn thành bảng sau (Viết số / Đọc số / Chục / Đơn vị).",
        "instruction_en": "Complete the table (Number / Read / Tens / Ones).",
        "hint_vi": "VD: 14 → Mười bốn → 1 chục → 4 đơn vị.",
        "config": {
            "items": [
                {"expression": "90 → đọc là →", "answer": "Chín mươi"},
                {"expression": "90 → chục →", "answer": "9"},
                {"expression": "90 → đơn vị →", "answer": "0"},
                {"expression": "1 chục 6 đơn vị → viết số →", "answer": "16"},
                {"expression": "16 → đọc là →", "answer": "Mười sáu"},
                {"expression": "17 → chục →", "answer": "1"},
                {"expression": "17 → đơn vị →", "answer": "7"},
                {"expression": "3 chục 0 đơn vị → viết số →", "answer": "30"},
                {"expression": "30 → đọc là →", "answer": "Ba mươi"}
            ]
        },
        "yccd_ids": "3,4"
    })

    # T19 Bài 7. Số tròn chục (dãy số)
    exercises.append({
        "lop": 1, "tuan": 19, "section": "practice", "sort_order": 7,
        "exercise_type": "fill_in",
        "title_vi": "Bài 7. Viết số thích hợp vào chỗ chấm",
        "title_en": "Exercise 7. Fill in the numbers",
        "instruction_vi": "Viết số thích hợp vào chỗ chấm.",
        "instruction_en": "Fill in the missing numbers.",
        "config": {
            "items": [
                {"expression": "a) 10, 20, 30, ☐, ☐, 60 → số thứ 4 →", "answer": "40"},
                {"expression": "a) → số thứ 5 →", "answer": "50"},
                {"expression": "b) 90, 80, 70, ☐, ☐, 40 → số thứ 4 →", "answer": "60"},
                {"expression": "b) → số thứ 5 →", "answer": "50"}
            ]
        },
        "yccd_ids": "3,4"
    })

    # T19 Bài 8. Đếm đồ vật trên bàn
    exercises.append({
        "lop": 1, "tuan": 19, "section": "practice", "sort_order": 8,
        "exercise_type": "fill_in",
        "title_vi": "Bài 8. Viết số thích hợp vào chỗ chấm",
        "title_en": "Exercise 8. Count objects",
        "instruction_vi": "Viết số thích hợp vào chỗ chấm. Trên bàn có:",
        "instruction_en": "Fill in the numbers. On the table there are:",
        "config": {
            "items": [
                {"expression": "… quả táo →", "answer": "5"},
                {"expression": "… quả dâu tây →", "answer": "18"},
                {"expression": "… cái bánh →", "answer": "12"}
            ],
            "show_labels": False
        },
        "yccd_ids": "3"
    })

    # ═══════════════════════════════════════
    # TUẦN 20
    # ═══════════════════════════════════════

    # T20 Bài 2. Viết số thích hợp (dãy số 2 chữ số)
    exercises.append({
        "lop": 1, "tuan": 20, "section": "practice", "sort_order": 2,
        "exercise_type": "fill_in",
        "title_vi": "Bài 2. Viết số thích hợp vào chỗ chấm",
        "title_en": "Exercise 2. Fill in the numbers",
        "instruction_vi": "Viết số thích hợp vào chỗ chấm.",
        "instruction_en": "Fill in the missing numbers.",
        "config": {
            "items": [
                {"expression": "a) ☐, 39, 40, ☐, 42 → số đầu →", "answer": "38"},
                {"expression": "a) → số thứ 4 →", "answer": "41"},
                {"expression": "b) 22, 21, ☐, 19, ☐ → số thứ 3 →", "answer": "20"},
                {"expression": "b) → số cuối →", "answer": "18"},
                {"expression": "c) 47, 48, ☐, ☐, 51 → số thứ 3 →", "answer": "49"},
                {"expression": "c) → số thứ 4 →", "answer": "50"},
                {"expression": "d) 40, 39, ☐, ☐, 36 → số thứ 3 →", "answer": "38"},
                {"expression": "d) → số thứ 4 →", "answer": "37"}
            ]
        },
        "yccd_ids": "3"
    })

    # T20 Bài 5. Viết số gồm chục và đơn vị
    exercises.append({
        "lop": 1, "tuan": 20, "section": "practice", "sort_order": 5,
        "exercise_type": "fill_in",
        "title_vi": "Bài 5. Viết số thích hợp vào chỗ chấm",
        "title_en": "Exercise 5. Fill in the numbers",
        "instruction_vi": "Viết số thích hợp vào chỗ chấm, biết số đó gồm:",
        "instruction_en": "Write the number composed of:",
        "config": {
            "items": [
                {"expression": "5 chục và 2 đơn vị →", "answer": "52"},
                {"expression": "3 chục và 6 đơn vị →", "answer": "36"},
                {"expression": "9 chục và 0 đơn vị →", "answer": "90"},
                {"expression": "10 chục →", "answer": "100"}
            ]
        },
        "yccd_ids": "3,4"
    })

    # T20 Bài 7. Bắp ngô (trắc nghiệm)
    exercises.append({
        "lop": 1, "tuan": 20, "section": "practice", "sort_order": 7,
        "exercise_type": "multiple_choice",
        "title_vi": "Bài 7. Khoanh vào chữ đặt trước câu trả lời đúng",
        "title_en": "Exercise 7. Choose the correct answer",
        "instruction_vi": "Sau khi thu hoạch ngô, Tôm cho các bắp ngô vào túi, mỗi túi 10 bắp thì được 4 túi và còn thừa 5 bắp ngô. Hỏi Tôm thu hoạch được tất cả bao nhiêu bắp ngô?",
        "instruction_en": "Tom puts corn in bags of 10 each, gets 4 bags with 5 left over. How many total?",
        "config": {
            "question": {"text_vi": "Tôm thu hoạch được bao nhiêu bắp ngô?", "text_en": "How many ears of corn?"},
            "choices": [
                {"text_vi": "A. 54", "text_en": "A. 54"},
                {"text_vi": "B. 45", "text_en": "B. 45"},
                {"text_vi": "C. 19", "text_en": "C. 19"},
                {"text_vi": "D. 15", "text_en": "D. 15"}
            ],
            "correct_index": 1
        },
        "yccd_ids": "3,4"
    })

    # T20 Bài 8. Rô-bốt mua kẹo
    exercises.append({
        "lop": 1, "tuan": 20, "section": "practice", "sort_order": 8,
        "exercise_type": "fill_in",
        "title_vi": "Bài 8. Viết số thích hợp vào chỗ chấm",
        "title_en": "Exercise 8. Fill in the blank",
        "instruction_vi": "Rô-bốt mua số lượng kẹo như sau. Biết mỗi phong kẹo có 10 cái. Rô-bốt đã mua tất cả … cái kẹo.",
        "instruction_en": "Robot buys candy. Each pack has 10 candies. (3 packs + 6 loose). Total candies?",
        "config": {
            "items": [
                {"expression": "Rô-bốt đã mua tất cả … cái kẹo →", "answer": "36"}
            ],
            "show_labels": False
        },
        "yccd_ids": "3,4"
    })

    # T20 Bài 9. Đếm thẻ số
    exercises.append({
        "lop": 1, "tuan": 20, "section": "practice", "sort_order": 9,
        "exercise_type": "fill_in",
        "title_vi": "Bài 9. Viết số thích hợp vào chỗ chấm",
        "title_en": "Exercise 9. Fill in the blanks",
        "instruction_vi": "Viết số thích hợp vào chỗ chấm.",
        "instruction_en": "Fill in the appropriate number.",
        "images": ["lop1/week20/img_060.png"],
        "config": {
            "items": [
                {"expression": "Có … thẻ ghi số có hai chữ số →", "answer": "5"},
                {"expression": "Có … thẻ ghi số tròn chục →", "answer": "2"}
            ],
            "show_labels": False
        },
        "yccd_ids": "3"
    })

    # ═══════════════════════════════════════
    # TUẦN 21
    # ═══════════════════════════════════════

    # T21 Bài 1. Viết dấu >, < hoặc =
    exercises.append({
        "lop": 1, "tuan": 21, "section": "practice", "sort_order": 1,
        "exercise_type": "fill_in",
        "title_vi": "Bài 1. Viết dấu >, < hoặc =",
        "title_en": "Exercise 1. Write >, < or =",
        "instruction_vi": "Viết dấu >, < hoặc = vào chỗ chấm cho thích hợp.",
        "instruction_en": "Fill in >, < or = appropriately.",
        "config": {
            "items": [
                {"expression": "40 ☐ 39", "answer": ">"},
                {"expression": "50 ☐ 47", "answer": ">"},
                {"expression": "61 ☐ 56", "answer": ">"},
                {"expression": "91 ☐ 19", "answer": ">"},
                {"expression": "27 ☐ 37", "answer": "<"},
                {"expression": "30 ☐ 50", "answer": "<"},
                {"expression": "25 ☐ 26", "answer": "<"},
                {"expression": "40 ☐ 40", "answer": "="},
                {"expression": "29 ☐ 30", "answer": "<"}
            ],
            "layout": "grid_2col"
        },
        "yccd_ids": "5"
    })

    # T21 Bài 3. Đúng ghi Đ, sai ghi S (so sánh).
    exercises.append({
        "lop": 1, "tuan": 21, "section": "practice", "sort_order": 3,
        "exercise_type": "true_false",
        "title_vi": "Bài 3. Đúng ghi Đ, sai ghi S",
        "title_en": "Exercise 3. True or False",
        "instruction_vi": "Đúng ghi Đ, sai ghi S.",
        "instruction_en": "Write Đ for correct, S for incorrect.",
        "config": {
            "statements": [
                {"text_vi": "34 < 21", "answer": "S"},
                {"text_vi": "19 > 17", "answer": "Đ"},
                {"text_vi": "56 = 65", "answer": "S"},
                {"text_vi": "78 > 77", "answer": "Đ"},
                {"text_vi": "89 < 98", "answer": "Đ"},
                {"text_vi": "39 > 50", "answer": "S"}
            ]
        },
        "yccd_ids": "5"
    })

    # T21 Bài 4. Sắp xếp và tìm số
    exercises.append({
        "lop": 1, "tuan": 21, "section": "practice", "sort_order": 4,
        "exercise_type": "fill_in",
        "title_vi": "Bài 4. Sắp xếp số",
        "title_en": "Exercise 4. Order numbers",
        "instruction_vi": "Cho các số: 27, 21, 19, 30.",
        "instruction_en": "Given: 27, 21, 19, 30.",
        "config": {
            "items": [
                {"expression": "Sắp xếp từ bé đến lớn →", "answer": "19, 21, 27, 30"},
                {"expression": "Những số lớn hơn 20 nhưng bé hơn 30 →", "answer": "21, 27"}
            ],
            "show_labels": False
        },
        "yccd_ids": "5"
    })

    # T21 Bài 5. Tìm số lớn nhất, bé nhất
    exercises.append({
        "lop": 1, "tuan": 21, "section": "practice", "sort_order": 5,
        "exercise_type": "fill_in",
        "title_vi": "Bài 5. Tìm số lớn nhất, bé nhất",
        "title_en": "Exercise 5. Find largest and smallest",
        "instruction_vi": "Cho các số: 70, 93, 81, 89.",
        "instruction_en": "Given: 70, 93, 81, 89.",
        "config": {
            "items": [
                {"expression": "Số lớn nhất là →", "answer": "93"},
                {"expression": "Số bé nhất là →", "answer": "70"},
                {"expression": "Viết từ lớn đến bé →", "answer": "93, 89, 81, 70"}
            ],
            "show_labels": False
        },
        "yccd_ids": "5"
    })

    # T21 Bài 7. Trắc nghiệm (tìm số lớn nhất / bé nhất)
    exercises.append({
        "lop": 1, "tuan": 21, "section": "practice", "sort_order": 7,
        "exercise_type": "multiple_choice",
        "title_vi": "Bài 7a. Khoanh vào chữ đặt trước câu trả lời đúng",
        "title_en": "Exercise 7a. Choose the correct answer",
        "instruction_vi": "Trong các số: 34, 29, 30, 35, số lớn nhất là:",
        "instruction_en": "Among 34, 29, 30, 35, the largest is:",
        "config": {
            "question": {"text_vi": "Trong các số: 34, 29, 30, 35, số lớn nhất là:", "text_en": "The largest among 34, 29, 30, 35:"},
            "choices": [
                {"text_vi": "A. 34", "text_en": "A. 34"},
                {"text_vi": "B. 29", "text_en": "B. 29"},
                {"text_vi": "C. 30", "text_en": "C. 30"},
                {"text_vi": "D. 35", "text_en": "D. 35"}
            ],
            "correct_index": 3
        },
        "yccd_ids": "5"
    })

    exercises.append({
        "lop": 1, "tuan": 21, "section": "practice", "sort_order": 8,
        "exercise_type": "multiple_choice",
        "title_vi": "Bài 7b. Khoanh vào chữ đặt trước câu trả lời đúng",
        "title_en": "Exercise 7b. Choose the correct answer",
        "instruction_vi": "Trong các số: 57, 64, 59, 60, số bé nhất là:",
        "instruction_en": "Among 57, 64, 59, 60, the smallest is:",
        "config": {
            "question": {"text_vi": "Trong các số: 57, 64, 59, 60, số bé nhất là:", "text_en": "The smallest among 57, 64, 59, 60:"},
            "choices": [
                {"text_vi": "A. 57", "text_en": "A. 57"},
                {"text_vi": "B. 64", "text_en": "B. 64"},
                {"text_vi": "C. 59", "text_en": "C. 59"},
                {"text_vi": "D. 60", "text_en": "D. 60"}
            ],
            "correct_index": 0
        },
        "yccd_ids": "5"
    })

    # T21 Bài 8. Tuổi Min, Bơ, Bống
    exercises.append({
        "lop": 1, "tuan": 21, "section": "practice", "sort_order": 9,
        "exercise_type": "fill_in",
        "title_vi": "Bài 8. Viết số thích hợp vào chỗ chấm",
        "title_en": "Exercise 8. Fill in the blanks",
        "instruction_vi": "Tuổi của bốn bạn Min, Bơ, Bống là một trong các số 15, 17 và 13. Biết Bơ không phải bạn có số tuổi nhiều nhất cũng không phải bạn có số tuổi ít nhất, tuổi của Bống lớn hơn tuổi của Min.",
        "instruction_en": "Min, Bo, Bong have ages from {15, 17, 13}. Bo isn't oldest or youngest. Bong is older than Min.",
        "config": {
            "items": [
                {"expression": "Tuổi của Min là →", "answer": "13"},
                {"expression": "Tuổi của Bơ là →", "answer": "15"},
                {"expression": "Tuổi của Bống là →", "answer": "17"}
            ],
            "show_labels": False
        },
        "yccd_ids": "5"
    })

    # T21 Bài 9. Di chuyển que tính: số 58, tìm số lớn nhất
    exercises.append({
        "lop": 1, "tuan": 21, "section": "practice", "sort_order": 10,
        "exercise_type": "fill_in",
        "title_vi": "Bài 9. Di chuyển que tính",
        "title_en": "Exercise 9. Move a matchstick",
        "instruction_vi": "Dùng các que tính xếp thành số 58 như sau. Di chuyển 1 que tính để được số lớn nhất.",
        "instruction_en": "Matchsticks form 58. Move one matchstick to get the largest number.",
        "config": {
            "items": [
                {"expression": "Số lớn nhất đó là →", "answer": "99"}
            ],
            "show_labels": False
        },
        "yccd_ids": "5"
    })

    # T21 Bài 11. Chi, Mai, Hương viết số
    exercises.append({
        "lop": 1, "tuan": 21, "section": "practice", "sort_order": 11,
        "exercise_type": "fill_in",
        "title_vi": "Bài 11. Viết số thích hợp vào chỗ chấm",
        "title_en": "Exercise 11. Fill in the blank",
        "instruction_vi": "Mỗi bạn Chi, Mai, Hương viết một trong các số 54, 47, 61.\nChi nói: \"Số tớ viết lớn hơn số của Mai.\"\nHương nói: \"Số Chi viết không phải số lớn nhất.\"",
        "instruction_en": "Chi, Mai, Huong each wrote one of 54, 47, 61. Chi: 'My number is bigger than Mai's.' Huong: 'Chi's number isn't the biggest.'",
        "config": {
            "items": [
                {"expression": "Hương viết số →", "answer": "61"}
            ],
            "show_labels": False
        },
        "yccd_ids": "5"
    })

    # Insert all exercises
    for ex in exercises:
        cur.execute("""
            INSERT INTO exercises (lop, tuan, section, sort_order, exercise_type,
                title_vi, title_en, instruction_vi, instruction_en,
                hint_vi, hint_en, config, images, yccd_ids)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            ex["lop"], ex["tuan"], ex["section"], ex["sort_order"], ex["exercise_type"],
            ex["title_vi"], ex.get("title_en", ""), ex["instruction_vi"], ex.get("instruction_en", ""),
            ex.get("hint_vi", ""), ex.get("hint_en", ""),
            json.dumps(ex["config"], ensure_ascii=False),
            json.dumps(ex.get("images", []), ensure_ascii=False),
            ex.get("yccd_ids", "")
        ))

    conn.commit()
    conn.close()
    print(f"✓ Seeded {len(exercises)} exercises across all grades")


def seed_exercise_templates():
    """Seed the exercise template library (kho dạng bài tập)."""
    conn = get_webapp_db()
    cur = conn.cursor()

    templates = []

    # ═══════════════════════════════════════
    # Dạng 1: Điền kết quả (Fill in result)
    # Ref: Tuần 15 Bài 1 — "Tính"
    # ═══════════════════════════════════════
    templates.append({
        "name": "Điền kết quả phép tính",
        "slug": "dien_ket_qua",
        "description": "Cho sẵn các phép tính (cộng, trừ, nhân, chia), học sinh điền kết quả vào chỗ trống. "
                       "Hiển thị dạng lưới 2 cột. Mỗi phép tính có 1 ô trống để điền đáp án.",
        "exercise_type": "fill_in",
        "instruction_template": "Tính.",
        "default_config": {
            "items": [
                {"expression": "... + ...", "answer": ""},
                {"expression": "... − ...", "answer": ""}
            ],
            "layout": "grid_2col"
        },
        "sample_config": {
            "items": [
                {"expression": "2 + 6", "answer": "8"},
                {"expression": "8 − 5", "answer": "3"},
                {"expression": "4 + 5", "answer": "9"},
                {"expression": "8 − 3", "answer": "5"},
                {"expression": "1 + 7", "answer": "8"},
                {"expression": "6 − 6", "answer": "0"},
                {"expression": "0 + 9", "answer": "9"},
                {"expression": "10 − 4", "answer": "6"},
                {"expression": "6 − 3", "answer": "3"}
            ],
            "layout": "grid_2col"
        },
        "applicable_grades": [1, 2, 3, 4, 5],
        "tags": ["tính", "cộng", "trừ", "điền số"]
    })

    # ═══════════════════════════════════════
    # Dạng 2: Đúng ghi Đ, sai ghi S
    # Ref: Tuần 15 Bài 4
    # ═══════════════════════════════════════
    templates.append({
        "name": "Đúng ghi Đ, sai ghi S",
        "slug": "dung_sai",
        "description": "Cho các phép tính hoặc mệnh đề toán học, học sinh chọn Đ (đúng) hoặc S (sai). "
                       "Mỗi câu có 2 nút Đ/S để học sinh bấm chọn.",
        "exercise_type": "true_false",
        "instruction_template": "Đúng ghi Đ, sai ghi S.",
        "default_config": {
            "statements": [
                {"text_vi": "... = ...", "answer": "Đ"},
                {"text_vi": "... = ...", "answer": "S"}
            ]
        },
        "sample_config": {
            "statements": [
                {"text_vi": "0 + 5 + 1 = 6", "answer": "Đ"},
                {"text_vi": "8 − 3 − 2 = 5", "answer": "S"},
                {"text_vi": "10 + 0 − 10 = 10", "answer": "S"},
                {"text_vi": "4 − 3 + 2 = 1", "answer": "S"},
                {"text_vi": "2 + 5 − 7 = 1", "answer": "S"},
                {"text_vi": "5 + 5 − 5 = 5", "answer": "Đ"}
            ]
        },
        "applicable_grades": [1, 2, 3, 4, 5],
        "tags": ["đúng sai", "Đ/S", "kiểm tra"]
    })

    # ═══════════════════════════════════════
    # Dạng 3: Tháp số (Number Pyramid)
    # Ref: Tuần 15 Bài 3 — "Viết số thích hợp vào ô trống"
    # Quy tắc: mỗi ô = tổng 2 ô ngay bên dưới
    # rows: từ dưới lên. null = ô trống (HS điền).
    # Phiên bản 3 hàng: 3-2-1 (6 ô), mở rộng 4 hàng: 4-3-2-1 (10 ô)
    # ═══════════════════════════════════════
    templates.append({
        "name": "Tháp số",
        "slug": "thap_so",
        "description": "Các ô/khối xếp thành hình tháp. Hàng dưới cùng nhiều ô nhất, "
                       "hàng trên ít hơn 1 ô, đỉnh tháp 1 ô. Quy tắc: số ở mỗi ô (2 hàng trên) "
                       "luôn bằng tổng 2 số ở 2 ô ngay bên dưới nó. "
                       "Phiên bản cơ bản: 3 hàng (3-2-1 = 6 ô). "
                       "Phiên bản mở rộng: 4 hàng (4-3-2-1 = 10 ô). "
                       "Một bài có thể chứa nhiều tháp (pyramids).",
        "exercise_type": "number_pyramid",
        "instruction_template": "Viết số thích hợp vào ô trống.",
        "default_config": {
            "pyramids": [
                {
                    "rows": [
                        [None, None, None],
                        [None, None],
                        [None]
                    ]
                }
            ]
        },
        "sample_config": {
            "pyramids": [
                {
                    "rows": [
                        [2, 3, 0],
                        [5, 3],
                        [None]
                    ]
                },
                {
                    "rows": [
                        [4, None, 1],
                        [None, None],
                        [10]
                    ]
                },
                {
                    "rows": [
                        [None, 2, None],
                        [5, 6],
                        [None]
                    ]
                }
            ]
        },
        "applicable_grades": [1, 2, 3, 4, 5],
        "tags": ["tháp số", "pyramid", "cộng", "điền số", "tư duy"]
    })

    # Template 4: Nối phép tính với kết quả (matching)
    templates.append({
        "name": "Nối phép tính với kết quả",
        "slug": "noi_phep_tinh",
        "description": "Học sinh nối mỗi phép tính ở hàng trên với kết quả đúng ở hàng dưới. Có đường nối trực quan SVG.",
        "exercise_type": "matching",
        "instruction_template": "Nối phép tính với kết quả đúng:",
        "default_config": {
            "pairs": [
                {"left_expr": "2 + 3", "answer": "5"},
                {"left_expr": "4 + 1", "answer": "5"},
                {"left_expr": "6 - 2", "answer": "4"},
                {"left_expr": "7 - 3", "answer": "4"}
            ],
            "right_items": ["5", "4"]
        },
        "sample_config": {
            "pairs": [
                {"left_expr": "9 - 1", "answer": "8"},
                {"left_expr": "4 + 4", "answer": "8"},
                {"left_expr": "10 - 3", "answer": "7"},
                {"left_expr": "2 + 5", "answer": "7"}
            ],
            "right_items": ["8", "7"]
        },
        "applicable_grades": [1, 2, 3],
        "tags": ["nối", "matching", "phép tính", "kết quả"]
    })

    # Template 5: Di chuyển que diêm (matchstick_puzzle)
    templates.append({
        "name": "Di chuyển que diêm",
        "slug": "que_diem",
        "description": "Học sinh di chuyển que diêm để tạo phép tính đúng. Hiển thị 7-segment, tương tác kéo thả que.",
        "exercise_type": "matchstick_puzzle",
        "instruction_template": "Di chuyển {moves} que diêm để được phép tính đúng:",
        "default_config": {
            "initial": "1+2=5",
            "moves": 1,
            "solutions": ["7-2=5", "1+2=3"]
        },
        "sample_config": {
            "initial": "1+2=5",
            "moves": 1,
            "solutions": ["7-2=5", "1+2=3"]
        },
        "applicable_grades": [1, 2, 3, 4, 5],
        "tags": ["que diêm", "matchstick", "tư duy", "tương tác", "puzzle"]
    })

    # Template 6: Viết phép tính từ hình (image_equations)
    templates.append({
        "name": "Viết phép tính từ hình",
        "slug": "viet_phep_tinh_tu_hinh",
        "description": "Cho hình ảnh minh họa, học sinh viết 2 phép cộng và 2 phép trừ thích hợp. Có kiểm tra kết quả tự động.",
        "exercise_type": "image_equations",
        "instruction_template": "Viết hai phép tính cộng, hai phép tính trừ thích hợp với mỗi hình:",
        "default_config": {
            "groups": [
                {
                    "image": "",
                    "description": "Hình minh họa",
                    "equations": [
                        {"type": "addition", "count": 2},
                        {"type": "subtraction", "count": 2}
                    ],
                    "valid_numbers": [3, 5, 8]
                }
            ]
        },
        "sample_config": {
            "groups": [
                {
                    "image": "/static/img/exercises/lop1/week15/img_bai6a.png",
                    "description": "6a",
                    "equations": [
                        {"type": "addition", "count": 2},
                        {"type": "subtraction", "count": 2}
                    ],
                    "valid_numbers": [3, 5, 8]
                },
                {
                    "image": "/static/img/exercises/lop1/week15/img_bai6b.png",
                    "description": "6b",
                    "equations": [
                        {"type": "addition", "count": 2},
                        {"type": "subtraction", "count": 2}
                    ],
                    "valid_numbers": [2, 8, 10]
                }
            ]
        },
        "applicable_grades": [1, 2, 3],
        "tags": ["viết phép tính", "hình ảnh", "cộng", "trừ", "image"]
    })

    # Template 7: Phân loại - Nối vật với khối hình (classify_match)
    templates.append({
        "name": "Nối vật với khối hình",
        "slug": "phan_loai_noi",
        "description": "Học sinh phân loại các vật thể vào nhóm khối hình học tương ứng. Click chọn vật rồi click nhóm để nối, có đường nối SVG.",
        "exercise_type": "classify_match",
        "instruction_template": "Nối mỗi vật với dạng khối hình học phù hợp:",
        "default_config": {
            "items": [
                {"id": "item1", "label": "Hộp sữa", "category": "cat1"},
                {"id": "item2", "label": "Quả bóng", "category": "cat2"},
                {"id": "item3", "label": "Cái phễu", "category": "cat3"}
            ],
            "categories": [
                {"id": "cat1", "label": "Hình hộp chữ nhật"},
                {"id": "cat2", "label": "Hình cầu"},
                {"id": "cat3", "label": "Hình nón"}
            ]
        },
        "sample_config": {
            "items": [
                {"id": "i1", "label": "🧊 Viên gạch", "category": "c1"},
                {"id": "i2", "label": "⚽ Quả bóng", "category": "c2"},
                {"id": "i3", "label": "🥫 Lon nước", "category": "c3"},
                {"id": "i4", "label": "🎄 Cái nón", "category": "c4"},
                {"id": "i5", "label": "📦 Hộp quà", "category": "c1"},
                {"id": "i6", "label": "🔮 Viên bi", "category": "c2"},
                {"id": "i7", "label": "🪵 Khúc gỗ", "category": "c3"}
            ],
            "categories": [
                {"id": "c1", "label": "Khối hộp chữ nhật"},
                {"id": "c2", "label": "Khối cầu"},
                {"id": "c3", "label": "Khối trụ"},
                {"id": "c4", "label": "Khối nón"}
            ]
        },
        "applicable_grades": [1, 2, 3, 4, 5],
        "tags": ["phân loại", "khối hình", "nối", "hình học", "classify"]
    })

    for tpl in templates:
        cur.execute("SELECT id FROM exercise_templates WHERE slug = ?", (tpl["slug"],))
        if cur.fetchone():
            continue
        cur.execute("""
            INSERT INTO exercise_templates
                (name, slug, description, exercise_type, instruction_template,
                 default_config, sample_config, applicable_grades, tags)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            tpl["name"], tpl["slug"], tpl["description"], tpl["exercise_type"],
            tpl["instruction_template"],
            json.dumps(tpl["default_config"], ensure_ascii=False),
            json.dumps(tpl["sample_config"], ensure_ascii=False),
            json.dumps(tpl["applicable_grades"]),
            json.dumps(tpl["tags"], ensure_ascii=False)
        ))

    conn.commit()
    conn.close()
    print(f"✓ Seeded {len(templates)} exercise templates")


def main():
    print("=" * 50)
    print("  Seeding webapp.db")
    print("=" * 50)
    init_webapp_db()
    seed_week_info()
    seed_vocabulary()
    seed_sample_exercises()
    seed_exercise_templates()
    print("\n✓ Done! Run: cd webapp && python app.py")


if __name__ == "__main__":
    main()
