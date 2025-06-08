# ocr_module.py - 使用 Gemini API 進行圖片文字提取

import requests
import base64
import io
from PIL import Image

# 使用者提供的 API 金鑰和模型名稱
API_KEY = "AIzaSyCqtUNwaaVV_K8iSuUC6JD_k8thhxkSb0w"
MODEL_NAME = "gemini-2.0-flash" # 從使用者的 curl 指令中獲取
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

def extract_text_from_image(image_obj: Image.Image):
    """
    使用 Google Gemini API 從圖片物件中提取文字。

    Args:
        image_obj: Pillow Image 物件。

    Returns:
        提取到的文字字串，或錯誤訊息。
    """
    if not API_KEY or API_KEY == "YOUR_GEMINI_API_KEY" or API_KEY == "GEMINI_API_KEY":
        return "錯誤：Gemini API 金鑰未設定或仍為預設值。請在 ocr_module.py 中設定有效的 API_KEY。"

    try:
        # 將 PIL Image 物件轉換為位元組流
        img_byte_arr = io.BytesIO()
        
        # 確定圖片格式，Gemini 支援 PNG, JPEG, WEBP, HEIC, HEIF
        # Pillow 的 image_obj.format 可能為 None (例如從剪貼簿貼上時)
        # 預設使用 PNG，因為它無損且廣泛支援
        img_format = image_obj.format if image_obj.format else 'PNG'
        
        # 將常見格式轉換為 Gemini API 接受的標準格式名稱
        if img_format.upper() == 'JPG':
            img_format = 'JPEG'
        
        if img_format.upper() not in ['PNG', 'JPEG', 'WEBP', 'HEIC', 'HEIF']:
            print(f"警告：圖片原始格式 {img_format} 可能不直接被 Gemini API 支援，將嘗試轉換為 PNG。")
            img_format = 'PNG' # 轉換為支援的格式

        image_obj.save(img_byte_arr, format=img_format)
        img_bytes = img_byte_arr.getvalue()
        
        # Base64 編碼
        base64_image = base64.b64encode(img_bytes).decode('utf-8')

        # 準備 API payload
        mime_type = f"image/{img_format.lower()}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        # 您可以根據需要調整此提示
                        {"text": "從這張圖片中提取所有可見的文字。請直接輸出文字內容，不要包含任何額外的解釋或標籤。"},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64_image
                            }
                        }
                    ]
                }
            ],
            "generationConfig": { # 可選的生成設定
                "temperature": 0.1, # 較低的溫度以獲得更確定的 OCR 結果
                "maxOutputTokens": 4096 # 根據需要調整
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        # 發送 POST 請求
        response = requests.post(API_URL, json=payload, headers=headers, timeout=60) # 增加 timeout
        response.raise_for_status()  # 如果 HTTP 狀態碼是 4xx 或 5xx，則引發異常

        result = response.json()

        # 解析 API 回應以提取文字
        # Gemini API 的回應結構可能會變化，這裡嘗試一種常見的結構
        if ('candidates' in result and result['candidates'] and
            'content' in result['candidates'][0] and
            'parts' in result['candidates'][0]['content'] and
            result['candidates'][0]['content']['parts'] and
            'text' in result['candidates'][0]['content']['parts'][0]):
            extracted_text = result['candidates'][0]['content']['parts'][0]['text']
            return extracted_text.strip()
        elif 'promptFeedback' in result and 'blockReason' in result['promptFeedback']:
            block_reason = result['promptFeedback']['blockReason']
            safety_ratings_info = result['promptFeedback'].get('safetyRatings', '')
            return f"錯誤：Gemini API 請求因安全原因被拒絕。原因：{block_reason}。安全評級詳情：{safety_ratings_info}"
        else:
            # 如果主要結構中找不到文字，嘗試備用結構或記錄完整回應以供偵錯
            # print(f"偵錯：Gemini API 完整回應：{result}") # 取消註解以進行偵錯
            # 嘗試從 parts 陣列中組合所有文字部分
            if result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
                all_text_parts = [part.get("text", "") for part in result["candidates"][0]["content"]["parts"]]
                combined_text = "".join(all_text_parts).strip()
                if combined_text:
                    return combined_text
            return "錯誤：無法從 Gemini API 回應中提取文字。回應結構未知或不包含預期的文字欄位。"

    except requests.exceptions.Timeout:
        return "錯誤：呼叫 Gemini API 時發生超時。"
    except requests.exceptions.RequestException as e:
        return f"錯誤：呼叫 Gemini API 時發生網路或請求錯誤：{e}"
    except KeyError as e:
        # 確保在 KeyEror 時能存取 result
        response_content_for_error = "無法獲取回應內容"
        try:
            response_content_for_error = response.json() if 'response' in locals() and response else "N/A"
        except: # response.json() 可能再次失敗
            pass
        return f"錯誤：解析 Gemini API 回應時發生索引錯誤 (KeyError: {e})。回應內容：{response_content_for_error}"
    except Exception as e:
        return f"錯誤：處理圖片或呼叫 Gemini API 時發生未預期的錯誤：{e}"

def solve_text_problem_with_gemini(problem_text: str):
    """
    使用 Google Gemini API 來嘗試解決純文字問題。

    Args:
        problem_text: 包含問題的文字字串。

    Returns:
        AI 生成的解答字串，或錯誤訊息。
    """
    if not API_KEY or API_KEY == "YOUR_GEMINI_API_KEY" or API_KEY == "GEMINI_API_KEY":
        return "錯誤：Gemini API 金鑰未設定或仍為預設值。請在 ocr_module.py 中設定有效的 API_KEY。"

    try:
        # 準備 API payload
        # 這裡的提示可以根據需要進行優化，以獲得更好的結果
        # 例如，可以更明確地指示 AI 的角色或期望的答案格式
        prompt = f"請解決以下問題並提供詳細的步驟和最終答案：\n\n問題：{problem_text}\n\n解答："
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7, # 允許一些創造性，但仍偏向事實
                "maxOutputTokens": 2048,
                # "topP": 0.9, # 可以考慮調整 topP 和 topK
                # "topK": 40
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        # 發送 POST 請求
        response = requests.post(API_URL, json=payload, headers=headers, timeout=90) # 針對可能較長的解題時間，增加 timeout
        response.raise_for_status()  # 如果 HTTP 狀態碼是 4xx 或 5xx，則引發異常

        result = response.json()

        # 解析 API 回應以提取文字
        if ('candidates' in result and result['candidates'] and
            'content' in result['candidates'][0] and
            'parts' in result['candidates'][0]['content'] and
            result['candidates'][0]['content']['parts'] and
            'text' in result['candidates'][0]['content']['parts'][0]):
            solution_text = result['candidates'][0]['content']['parts'][0]['text']
            return solution_text.strip()
        elif 'promptFeedback' in result and 'blockReason' in result['promptFeedback']:
            block_reason = result['promptFeedback']['blockReason']
            safety_ratings_info = result['promptFeedback'].get('safetyRatings', '')
            return f"錯誤：Gemini API 請求因安全原因被拒絕。原因：{block_reason}。安全評級詳情：{safety_ratings_info}"
        else:
            # print(f"偵錯：Gemini API (solve_text_problem) 完整回應：{result}") # 取消註解以進行偵錯
            if result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
                all_text_parts = [part.get("text", "") for part in result["candidates"][0]["content"]["parts"]]
                combined_text = "".join(all_text_parts).strip()
                if combined_text:
                    return combined_text
            return "錯誤：無法從 Gemini API 回應中提取解答。回應結構未知或不包含預期的文字欄位。"

    except requests.exceptions.Timeout:
        return "錯誤：呼叫 Gemini API (solve_text_problem) 時發生超時。"
    except requests.exceptions.RequestException as e:
        return f"錯誤：呼叫 Gemini API (solve_text_problem) 時發生網路或請求錯誤：{e}"
    except KeyError as e:
        response_content_for_error = "無法獲取回應內容"
        try:
            response_content_for_error = response.json() if 'response' in locals() and response else "N/A"
        except:
            pass
        return f"錯誤：解析 Gemini API 回應 (solve_text_problem) 時發生索引錯誤 (KeyError: {e})。回應內容：{response_content_for_error}"
    except Exception as e:
        return f"錯誤：使用 Gemini API 解決文字問題時發生未預期的錯誤：{e}"

if __name__ == '__main__':
    print("OCR 模組已更新為使用 Google Gemini API。")
    print("請確保：")
    print("1. `requests` 套件已安裝 (pip install requests)。")
    print(f"2. `API_KEY` (目前設定為: {'********' + API_KEY[-4:] if API_KEY and len(API_KEY) > 4 else '未設定或過短'}) 和 `MODEL_NAME` (目前為: {MODEL_NAME}) 在 ocr_module.py 中已正確設定。")
    print("3. 網路連線正常。")
    print("\\n若要進行單元測試，您可以取消註解以下程式碼並提供一張測試圖片路徑。")
    
    # --- 單元測試範例 (取消註解並修改圖片路徑以進行測試) ---
    # test_image_path = "test.png"  # 將 "test.png" 替換為您的測試圖片路徑
    # try:
    #     print(f"\\n正在嘗試載入測試圖片：{test_image_path}")
    #     img = Image.open(test_image_path)
    #     print("圖片載入成功。正在呼叫 Gemini API 進行文字提取...")
    #     text = extract_text_from_image(img)
    #     print(f"--- Gemini API 回傳 ---")
    #     print(text)
    #     print(f"--- 結束 ---")
    # except FileNotFoundError:
    #     print(f"錯誤：找不到測試圖片 '{test_image_path}'。請確認路徑是否正確。")
    # except Exception as e:
    #     print(f"測試過程中發生錯誤：{e}")
    # --- 結束單元測試範例 ---
