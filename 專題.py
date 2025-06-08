# 專題.py - 主應用程式邏輯

import os
# os.environ['TESSDATA_PREFIX'] = r'D:\\新增資料夾\\Tesseract OCR\\tessdata' # 已移至 ocr_module.py

from PIL import Image

# 匯入我們建立的模組
import image_handler
import ocr_module
import math_solver
import nlp_solver
import visual_puzzle_solver

def _is_cjk(char):
    """輔助函數，檢查字元是否在常見的 CJK Unicode 範圍內。"""
    # 中文、日文、韓文的常見範圍
    return ('\u4e00' <= char <= '\u9fff') or \
           ('\u3400' <= char <= '\u4dbf') or \
           ('\uac00' <= char <= '\ud7af') or \
           ('\u3040' <= char <= '\u309f') or \
           ('\u30a0' <= char <= '\u30ff')

def determine_problem_type(ocr_text, image_obj):
    """根據 OCR 文字和圖片內容來判斷問題類型。"""
    if not ocr_text or ocr_text.isspace():
        return "visual"

    # --- CJK 字元檢查 (優先處理主要為 CJK 的文字) ---
    # 使用原始 ocr_text 進行此檢查，因為轉換為小寫對 CJK 字元影響不大
    cjk_char_count = 0
    total_non_whitespace_chars = 0
    for char_val in ocr_text: # Iterate through each character in the OCR text
        if not char_val.isspace(): # Check if the character is not whitespace
            total_non_whitespace_chars += 1 # Increment count of non-whitespace characters
            if _is_cjk(char_val): # Check if the non-whitespace character is CJK
                cjk_char_count += 1 # Increment count of CJK characters
    
    # 確保有足夠的非空白字元來進行有意義的判斷，並避免除以零的錯誤。
    # 條件：總非空白字元數需大於 5，且 CJK 字元佔比超過 50%。
    if total_non_whitespace_chars > 5: 
        cjk_ratio = cjk_char_count / total_non_whitespace_chars
        if cjk_ratio > 0.5:
            return "text" # 非常可能是中日韓文的文字問題

    lower_ocr_text = ocr_text.lower()
    
    # --- 特徵定義 --- 
    # 字元集，用於判斷是否包含極不可能是數學表達式的字元
    # 例如 '°', '@', '$' (如果您的使用場景中 '$' 不用於特殊數學表示法)
    # 根據您的範例錯誤，'°' 和 '@' 是主要問題
    very_bad_chars = {'°', '@', ':', '$'} # Expanded to include : and $

    # --- EARLY FILTER for obviously corrupt/non-math OCR ---
    if any(char in lower_ocr_text for char in very_bad_chars):
        # If it has these bad chars, it's unlikely to be a clean math problem.
        # It might be a visual puzzle with weird symbols, or just bad OCR.
        # If it still looks like a question, let NLP try.
        # Check for question-like endings or beginnings
        is_question_like_despite_bad_chars = False
        if lower_ocr_text.endswith('?') or lower_ocr_text.endswith("?)"):
            is_question_like_despite_bad_chars = True
        else:
            # Check common question starters even with bad characters elsewhere
            # Need to split words first to check the first word
            temp_words = lower_ocr_text.split()
            temp_first_word = temp_words[0] if temp_words else ""
            question_starters_for_filter = [
                "what", "who", "where", "when", "why", "how", "is", "are", "do", "does", "did",
                "was", "were", "can", "could", "will", "would", "should", "may", "might",
                "which", "list", "define", "explain", "describe", "calculate", "name", "tell"
            ]
            if temp_first_word in question_starters_for_filter:
                is_question_like_despite_bad_chars = True
        
        if is_question_like_despite_bad_chars:
            return "text" # Let NLP see if it can make sense of it
        return "visual" # Default to visual if bad chars are present and not clearly a question

    words = lower_ocr_text.split()
    first_word = words[0] if words else ""

    # 1. 明確問句檢查 (優先判斷為 "text")
    question_starters = [
        "what", "who", "where", "when", "why", "how", "is", "are", "do", "does", "did",
        "was", "were", "can", "could", "will", "would", "should", "may", "might",
        "which", "list", "define", "explain", "describe", "calculate", "name", "tell"
    ]
    
    # 檢查是否以問號或 "?)" 結尾
    ends_with_question_variant = False
    if lower_ocr_text.endswith('?'):
        ends_with_question_variant = True
    elif lower_ocr_text.endswith("?)"): # 處理像 "word?)" 這樣的情況
        ends_with_question_variant = True

    is_definitely_question = ends_with_question_variant or \
                             (first_word in question_starters and not (first_word == "solve" and '=' in lower_ocr_text))

    if is_definitely_question:
        # 例如 "Calculate the derivative of x^2" 仍應由 NLP 理解問題語境
        return "text"

    # 2. 數學問題檢查 (如果不是明確的問句)
    has_equals_sign = '=' in ocr_text
    has_math_operators = any(op in ocr_text for op in "+-*/^")
    has_digits = any(char.isdigit() for char in ocr_text)
    
    # 明確的數學求解片語
    explicit_math_phrases = ["solve for", "find x", "find the value of x", "derivative of", "integral of", "factorize", "simplify:"]
    if any(phrase in lower_ocr_text for phrase in explicit_math_phrases):
        if not any(char in lower_ocr_text for char in very_bad_chars): # ADDED CHECK
            return "math"
        
    # 一般數學關鍵字 + 結構 (例如 "solve 2x+5=0", "equation: y=mx+c")
    if (has_equals_sign and has_math_operators) or \
       (first_word == "solve" and has_math_operators and (has_digits or any(c.isalpha() for c in ocr_text))): # 允許變數
        num_math_symbols = sum(1 for char in ocr_text if char.isdigit() or char in "+-*/=^().") # 包含括號和點
        num_alpha_symbols = sum(1 for char in ocr_text if char.isalpha())
        # 如果數學字元顯著，或字母很少（像方程式）
        if num_math_symbols > num_alpha_symbols * 0.3 or num_alpha_symbols < 10 or first_word == "solve":
            if not any(char in lower_ocr_text for char in very_bad_chars): # ADDED CHECK
                return "math"

    # 純算術表達式 (例如 "2 + 2", "10 / 5")
    is_pure_arithmetic = False
    if has_digits and any(op in ocr_text for op in "+-*/^"): # 必須有數字和基本運算子
        is_pure_arithmetic = True
        valid_arithmetic_chars = set("0123456789+-*/^(). ") # 允許括號、小數點和空格
        for char_token in ocr_text:
            if char_token not in valid_arithmetic_chars:
                is_pure_arithmetic = False
                break
    
    if is_pure_arithmetic and len(ocr_text.strip()) > 0:
        # 再次確認包含運算子，避免將 "123" 或 "3.14" 誤判
        if any(op in ocr_text for op in "+-*/^"):
             if not any(char in lower_ocr_text for char in very_bad_chars): # ADDED CHECK
                return "math"

    # 3. 如果包含大量字母內容，且未被歸類為數學或明確問句，則預設為 "text"
    num_alpha_chars = sum(1 for char in ocr_text if char.isalpha())
    if num_alpha_chars > len(ocr_text) * 0.5 and len(ocr_text) > 10:
        return "text"

    # 4. 回退到 "visual"
    # 如果文字很短，或不符合其他類別
    if len(ocr_text.strip()) < 15: 
        # 如果包含數學特徵但未被捕獲，最後嘗試一次 math
        if has_math_operators and has_digits:
            if not any(char in lower_ocr_text for char in very_bad_chars): # ADDED CHECK
                return "math"
        return "visual"
        
    # 如果仍有未分類的文字內容，最後嘗試 "text"
    if has_digits or any(c.isalpha() for c in ocr_text):
        # 同上，最後檢查一次 math
        if has_math_operators and has_digits:
            if not any(char in lower_ocr_text for char in very_bad_chars): # ADDED CHECK
                return "math"
        return "text"

    return "visual" #最終回退

def main():
    print("歡迎使用 AI 問題求解器！")
    print("="*30)

    # 載入 NLP 模型 (如果 nlp_solver 中有此邏輯，確保它被呼叫一次)
    if nlp_solver.NLP is None:
        print("注意：NLP 模型未載入，文字問題處理功能將受限。")
        print("請確保已執行 'python -m spacy download en_core_web_sm' 並重新啟動程式。")


    while True:
        print("\n請選擇圖片輸入方式：")
        print("1. 從檔案路徑載入")
        print("2. 從剪貼簿貼上")
        print("0. 退出程式")
        choice = input("請輸入選項 (0-2): ")

        img = None
        if choice == '1':
            file_path = input("請輸入圖片檔案的完整路徑: ")
            if not os.path.exists(file_path):
                print(f"錯誤：檔案 {file_path} 不存在。請檢查路徑。")
                continue
            img = image_handler.load_image_from_file(file_path)
            if img:
                print(f"已從 {file_path} 載入圖片。")
        elif choice == '2':
            print("請確保您已將圖片複製到剪貼簿...")
            img = image_handler.paste_image_from_clipboard()
            if img:
                print("已從剪貼簿載入圖片。")
        elif choice == '0':
            print("感謝使用，程式即將退出。")
            break
        else:
            print("無效的選項，請重新輸入。")
            continue

        if img is None:
            print("未能成功載入圖片，請重試。")
            continue

        # 顯示圖片 (可選，但對於 CLI 可能不太方便，除非用外部檢視器)
        # try:
        #     img.show()
        # except Exception as e:
        #     print(f"無法顯示圖片（可能在無 GUI 環境中）：{e}")

        # 進行 OCR
        print("\n正在對圖片進行 OCR 文字提取...")
        ocr_text = ocr_module.extract_text_from_image(img)
        if ocr_text:
            print(f"OCR 提取的文字內容：\n'''{ocr_text}'''")
        else:
            print("OCR 未能提取任何文字，或者發生錯誤。")
            ocr_text = "" # 確保 ocr_text 是字串

        # 判斷問題類型
        # 在實際應用中，這裡可能需要更複雜的邏輯，甚至讓使用者確認
        problem_type = determine_problem_type(ocr_text, img)
        print(f"\n根據分析，判斷問題類型為：{problem_type}")

        # 讓使用者有機會修正判斷
        user_override = input(f"是否同意此判斷？若要修改，請輸入 (m)數學, (t)文字, (v)視覺，否則直接按 Enter: ").lower()
        if user_override == 'm':
            problem_type = "math"
        elif user_override == 't':
            problem_type = "text"
        elif user_override == 'v':
            problem_type = "visual"
        
        print(f"最終問題類型：{problem_type}")
        print("-" * 20)


        # 呼叫對應的求解器
        solution = None
        if problem_type == "math":
            if not ocr_text or ocr_text.isspace():
                print("錯誤：數學問題需要從圖片中提取到方程式文字。")
            else:
                print("正在嘗試使用數學求解器...")
                # 預處理 OCR 文字以符合 math_solver 的期望
                # 例如，math_solver 可能期望 "2*x - 4" 而不是 "2x-4=0"
                # 這裡的轉換邏輯需要與 math_solver 中的 parse_equation 協調
                # 目前 math_solver.solve_equation 內部已有一些處理
                solution = math_solver.solve_equation(ocr_text)
        elif problem_type == "text":
            if not ocr_text or ocr_text.isspace():
                print("錯誤：文字問題需要從圖片中提取到文字內容。")
            elif nlp_solver.NLP is None:
                 solution = "NLP 模型未載入，無法處理文字問題。"
            else:
                print("正在嘗試使用 NLP 求解器...")
                solution = nlp_solver.answer_text_question(ocr_text)
        elif problem_type == "visual":
            print("正在嘗試使用視覺謎題求解器...")
            solution = visual_puzzle_solver.solve_visual_puzzle(img) # 視覺解謎器直接使用圖片物件
        else:
            solution = "錯誤：未知的問題類型。"

        # 顯示結果
        print("\n" + "="*15 + " 解答/分析結果 " + "="*15)
        if solution is not None:
            if isinstance(solution, list) and not solution: # Sympy solve 可能返回空列表
                print("數學求解器未能找到明確的數值解，或者表達式本身就是解。")
                print(f"原始表達式/方程式: {ocr_text}")
            else:
                print(solution)
        else:
            print("未能獲得解答或分析結果。可能的原因包括：")
            if not ocr_text or ocr_text.isspace():
                print("- OCR 未能從圖片中提取到任何有效文字。")
            else:
                print(f"- OCR 提取的文字為：\'\'\'{ocr_text}\'\'\'")
                print(f"- 判斷的問題類型為：{problem_type}")
                if problem_type == "math":
                    print("- 數學求解器可能無法解析此表達式，或方程式無解/過於複雜。")
                elif problem_type == "text":
                    print("- NLP 求解器可能無法理解此問題，或知識庫中沒有相關答案。")
                    if nlp_solver.NLP is None:
                        print("  - 注意：NLP 模型未載入，這會影響文字問題的處理。")
                elif problem_type == "visual":
                    print("- 視覺謎題求解器可能無法分析此類圖片，或謎題過於複雜。")
            print("- 請檢查圖片品質、OCR 結果和問題類型判斷是否正確。")
        print("="*40)

if __name__ == "__main__":
    main()
