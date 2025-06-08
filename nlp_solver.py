# nlp_solver.py
# This module will understand and answer text-based problems.

import spacy
import ocr_module # 匯入 ocr_module 以使用 Gemini API

# 載入 spaCy 的英文模型
# 第一次執行時，如果模型尚未下載，您可能需要執行：
# python -m spacy download en_core_web_sm
NLP = None
try:
    NLP = spacy.load('en_core_web_sm')
except OSError:
    print("錯誤：找不到 spaCy 的 'en_core_web_sm' 模型。")
    print("請執行 'python -m spacy download en_core_web_sm' 來下載模型。")
    # 您可以在此處決定是否要引發異常或允許程式在沒有 NLP 功能的情況下繼續

def answer_text_question(text):
    """使用 NLP 理解並嘗試回答文字型問題。
       對於複雜問題或應用題，會嘗試使用 Gemini API 求解。
    Args:
        text: 包含問題的文字字串。

    Returns:
        一個包含潛在答案或分析的字串。
        如果 NLP 模型未載入，則返回錯誤訊息。
    """
    if NLP is None and not ocr_module.API_KEY: # 如果兩者都不可用
        return "錯誤：spaCy NLP 模型未成功載入，且 Gemini API 金鑰未設定。無法處理文字問題。"
    
    # 優先嘗試使用 Gemini API 解決問題，因為它可能能處理更複雜的語義和應用題
    # 我們可以定義一些啟發式規則來決定何時使用 Gemini vs. 本地知識庫
    # 例如，如果問題長度較長，包含數字，或者 spaCy 分析顯示它是一個複雜的問句

    # 簡易的啟發式規則：如果問題包含數字或長度超過一定閾值，或者包含 CJK 字元，
    # 則認為它可能是應用題或複雜問題，優先使用 Gemini。
    contains_digits = any(char.isdigit() for char in text)
    is_long_question = len(text) > 50 # 可調整的閾值
    
    # 檢查 CJK (與 專題.py 中的 _is_cjk 類似，但這裡直接檢查)
    contains_cjk = False
    for char_val in text:
        if ('\u4e00' <= char_val <= '\u9fff') or \
           ('\u3400' <= char_val <= '\u4dbf') or \
           ('\uac00' <= char_val <= '\ud7af') or \
           ('\u3040' <= char_val <= '\u309f') or \
           ('\u30a0' <= char_val <= '\u30ff'):
            contains_cjk = True
            break

    # 判斷是否應該使用 Gemini API
    # 這裡的邏輯是：如果是中文問題，或者問題看起來像應用題（包含數字且較長），
    # 或者是非常短但非典型的知識庫查詢，都嘗試用 Gemini。
    should_use_gemini = False
    if ocr_module.API_KEY and ocr_module.API_KEY not in ["YOUR_GEMINI_API_KEY", "GEMINI_API_KEY"]:
        if contains_cjk: # 中文問題優先使用 Gemini
            should_use_gemini = True
        elif contains_digits and is_long_question: # 可能是英文應用題
            should_use_gemini = True
        elif len(text.split()) > 7: # 較長的英文問題也可能適合 Gemini
             should_use_gemini = True
        # 也可以加入其他判斷，例如如果 spaCy 分析不出什麼結果，也轉交 Gemini

    if should_use_gemini:
        print("資訊：偵測到可能複雜的文字問題，嘗試使用 Gemini API 進行解答...")
        gemini_answer = ocr_module.solve_text_problem_with_gemini(text)
        # 檢查 Gemini 是否成功返回了答案，而不是錯誤訊息
        if not gemini_answer.startswith("錯誤："):
            return f"(Gemini AI 解答):\n{gemini_answer}"
        else:
            print(f"警告：Gemini API 處理失敗 ({gemini_answer})。將嘗試使用本地 NLP 分析。")
            # 如果 Gemini 失敗，可以選擇回退到 spaCy 或知識庫，或者直接顯示 Gemini 的錯誤
            # 這裡我們選擇回退

    # --- 如果不使用 Gemini 或 Gemini 失敗，則執行以下 spaCy 和知識庫邏輯 ---
    if NLP is None:
        return "錯誤：spaCy NLP 模型未成功載入。Gemini API 嘗試失敗或未啟用。"

    doc = NLP(text)
    question_type = "未知"
    entities = [ent.text for ent in doc.ents]
    noun_phrases = [chunk.text for chunk in doc.noun_chunks]
    verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]
    
    # 標準化文字以便進行關鍵字比對
    lower_text = text.lower()

    first_token_lower = doc[0].text.lower()
    if first_token_lower in ["what", "who", "where", "when", "why", "how"]:
        question_type = first_token_lower

    # --- 模擬知識庫 ---
    # 擴展此知識庫以包含更多問答對
    knowledge_base = {
        "capital_of_france": "Paris",
        "capital_of_japan": "Tokyo",
        "capital_of_germany": "Berlin",
        "capital_of_united_states": "Washington D.C.",
        "painter_of_mona_lisa": "Leonardo da Vinci",
        "chemical_symbol_for_water": "H2O",
        "president_of_the_united_states": "Joe Biden" # 注意：這類資訊會過時
    }
    
    # --- 增強的問答邏輯 ---
    
    # 處理 "What is the capital of [Country]?"
    if question_type == "what" and "capital of" in lower_text:
        # 嘗試從實體中找到國家名稱
        country_name = None
        for ent in doc.ents:
            if ent.label_ == "GPE": # GPE (Geopolitical Entity) 通常指國家、城市等
                country_name = ent.text
                break
        if country_name:
            key = f"capital_of_{country_name.lower().replace(' ', '_')}"
            if key in knowledge_base:
                return f"{country_name} 的首都是 {knowledge_base[key]}。"
            else:
                return f"抱歉，我不知道 {country_name} 的首都是什麼。"
        else:
            # 如果 spaCy 未能識別國家，嘗試從名詞短語中提取
            # 這是一個更簡化的後備方案
            possible_country_phrase = lower_text.split("capital of")[-1].strip().replace("?","")
            if possible_country_phrase:
                key = f"capital_of_{possible_country_phrase.replace(' ', '_')}"
                if key in knowledge_base:
                     return f"{possible_country_phrase.capitalize()} 的首都是 {knowledge_base[key]}。"
                else:
                    return f"抱歉，我不太確定您指的是哪個國家/地區的首都，或者我不知道答案。"
            else:
                return "抱歉，我無法從您的問題中識別出國家名稱。"

    # 處理 "Who painted the Mona Lisa?"
    elif question_type == "who" and "painted" in lower_text and ("mona lisa" in lower_text or "Mona Lisa" in text):
        if "painter_of_mona_lisa" in knowledge_base:
            return f"《蒙娜麗莎》是由 {knowledge_base['painter_of_mona_lisa']} 繪製的。"
        else:
            return "抱歉，我不知道誰畫了《蒙娜麗莎》。"

    # 處理 "What is the chemical symbol for water?"
    elif question_type == "what" and "chemical symbol" in lower_text and "water" in lower_text:
        if "chemical_symbol_for_water" in knowledge_base:
            return f"水的化學符號是 {knowledge_base['chemical_symbol_for_water']}。"
        else:
            return "抱歉，我不知道水的化學符號是什麼。"
            
    # 處理 "Who is the president of the United States?"
    elif question_type == "who" and "president" in lower_text and ("united states" in lower_text or "US" in text or "U.S." in text):
        if "president_of_the_united_states" in knowledge_base:
            return f"美國的現任總統是 {knowledge_base['president_of_the_united_states']}。(請注意，此資訊可能已過時)"
        else:
            return "抱歉，我不知道美國的現任總統是誰。"

    # 如果本地知識庫沒有匹配，且未使用/未成功使用 Gemini，則返回 spaCy 的基本分析
    analysis_response = f"(spaCy 分析):\n偵測到的問題類型：{question_type}\n"
    analysis_response += f"偵測到的實體：{entities}\n"
    analysis_response += f"偵測到的名詞短語：{noun_phrases}\n"
    analysis_response += f"偵測到的主要動詞 (詞元)：{verbs}\n\n"

    if not entities and not noun_phrases and question_type == "未知":
        analysis_response += "這似乎不是一個包含足夠資訊的問題，或者我無法正確解析它。"
    else:
        analysis_response += "這是一個初步的分析。我目前無法直接回答這個問題，但以上是我的理解。"
        
    return analysis_response

if __name__ == '__main__':
    if NLP is None:
        print("由於 spaCy 模型未載入，無法執行 nlp_solver.py 的測試。")
    else:
        test_questions = [
            "What is the capital of France?",
            "What is the capital of Japan", # 測試沒有問號
            "Tell me the capital of Germany.", # 測試不同句型
            "Who painted the Mona Lisa?",
            "What is the chemical symbol for water?",
            "Who is the president of the United States?",
            "Where is the Eiffel Tower located?", # 尚未處理
            "When was the first moon landing?", # 尚未處理
            "How does photosynthesis work?", # 尚未處理
            "Tell me about black holes.", # 尚未處理
            "This is not a question.",
            "What is the capital of Elbonia?" # 測試知識庫中沒有的國家
        ]

        for q_text in test_questions:
            print(f"問題：{q_text}")
            answer = answer_text_question(q_text)
            print(f"回答：{answer}\n")
