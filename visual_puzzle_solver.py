# visual_puzzle_solver.py
# This module will analyze and solve visual puzzles.

import cv2
import numpy as np
from PIL import Image

def solve_visual_puzzle(image_path_or_object):
    """分析並嘗試解決視覺謎題。

    Args:
        image_path_or_object: 圖片的檔案路徑或 PIL Image 物件。

    Returns:
        一個包含分析結果或潛在解決方案的字串。
    """
    try:
        if isinstance(image_path_or_object, str):
            # 從檔案路徑讀取圖片
            # PIL Image.open() 用於 image_handler，但 OpenCV 通常使用 cv2.imread()
            # 為了保持一致性，如果傳入路徑，我們先用 PIL 開啟，再轉換為 OpenCV 格式
            pil_image = Image.open(image_path_or_object)
            # 將 PIL Image 轉換為 OpenCV 格式 (BGR)
            image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        elif isinstance(image_path_or_object, Image.Image):
            # 如果是 PIL Image 物件，直接轉換
            pil_image = image_path_or_object
            image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        elif isinstance(image_path_or_object, np.ndarray):
            # 假設如果是 numpy array，它已經是 OpenCV 格式 (BGR 或灰階)
            image = image_path_or_object
        else:
            raise ValueError("輸入必須是檔案路徑、PIL Image 物件或 OpenCV 圖像 (NumPy array)")

        if image is None:
            return "錯誤：無法載入圖片。"

        # --- 通用圖像分析與解謎框架 --- #
        height, width = image.shape[:2]
        analysis_result = f"圖片尺寸：寬={width}, 高={height}\n"

        # 1. 預處理 (例如：灰階、模糊、邊緣檢測)
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        analysis_result += "已將圖片轉換為灰階。\n"

        # 邊緣檢測 (Canny)
        edges = cv2.Canny(gray_image, threshold1=50, threshold2=150)
        analysis_result += "已執行 Canny 邊緣檢測。\n"
        # 可以在此處選擇性地顯示或保存邊緣圖片以供調試
        # cv2.imshow("Edges", edges)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        # 2. 特徵提取 (例如：輪廓、形狀、顏色、紋理)
        contours, hierarchy = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        analysis_result += f"偵測到的外部輪廓數量：{len(contours)}\n"

        # 範例：分析最大的輪廓
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            perimeter = cv2.arcLength(largest_contour, True)
            analysis_result += f"最大輪廓的面積：{area:.2f}, 周長：{perimeter:.2f}\n"

            # 嘗試進行形狀識別 (非常基礎)
            approx = cv2.approxPolyDP(largest_contour, 0.03 * perimeter, True)
            num_vertices = len(approx)
            shape_name = "未知形狀"
            if num_vertices == 3:
                shape_name = "三角形"
            elif num_vertices == 4:
                # 可以進一步檢查是否為矩形或正方形
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = float(w) / h
                if 0.95 <= aspect_ratio <= 1.05:
                    shape_name = "正方形/菱形"
                else:
                    shape_name = "矩形/四邊形"
            elif num_vertices == 5:
                shape_name = "五邊形"
            elif num_vertices > 5:
                shape_name = "圓形或橢圓形 (近似)" # 實際上圓形會有更多頂點
            analysis_result += f"最大輪廓的近似形狀：{shape_name} (頂點數：{num_vertices})\n"

        # 3. 模式識別與邏輯推斷 (這是最複雜且依賴謎題類型的部分)
        #    - 找不同 (比較兩張或多張圖片/區域的差異)
        #    - 序列預測 (分析一系列圖形或數字的規律)
        #    - 物件計數
        #    - 顏色匹配/識別
        #    - 空間關係分析 (例如，A 在 B 的左邊)

        # 由於這是通用框架，我們在此僅返回初步分析
        analysis_result += "\n視覺謎題分析完成。要獲得具體的解決方案，需要針對特定謎題類型實作更進階的邏輯。"
        analysis_result += "\n可能的下一步包括：顏色分析、紋理分析、更進階的形狀識別、物件偵測與分類等。"

        return analysis_result

    except FileNotFoundError:
        if isinstance(image_path_or_object, str):
            return f"錯誤：找不到圖片檔案 {image_path_or_object}"
        return "錯誤：提供的圖片路徑無效。"
    except ValueError as ve:
        return f"輸入錯誤：{ve}"
    except Exception as e:
        return f"分析視覺謎題時發生未預期的錯誤：{e}"

if __name__ == '__main__':
    # 測試視覺謎題求解器
    # 請將 'path/to/your/puzzle_image.png' 替換為實際的謎題圖片檔案路徑
    # 您可以使用簡單的形狀圖片進行初步測試
    test_image_path = 'path/to/your/puzzle_image.png' # 您需要修改此路徑以進行測試

    print(f"嘗試分析視覺謎題圖片：{test_image_path}\n")
    solution_or_analysis = solve_visual_puzzle(test_image_path)
    print(f"分析結果：\n{solution_or_analysis}\n")

    # 測試 PIL Image 物件輸入
    try:
        # 假設您有一個 PIL Image 物件 (例如，從 image_handler 模組載入的)
        from image_handler import load_image_from_file
        pil_img = load_image_from_file(test_image_path) # 再次使用相同路徑進行測試
        if pil_img:
            print(f"\n嘗試使用 PIL Image 物件分析視覺謎題...\n")
            solution_or_analysis_pil = solve_visual_puzzle(pil_img)
            print(f"PIL 物件分析結果：\n{solution_or_analysis_pil}\n")
        elif test_image_path == 'path/to/your/puzzle_image.png':
             print(f"提醒：測試 PIL Image 物件需要將 '{test_image_path}' 替換為有效的圖片路徑。")
        else:
            print(f"未能從 {test_image_path} 載入 PIL Image 物件進行測試。")

    except ImportError:
        print("無法匯入 image_handler，跳過 PIL Image 物件的測試。")
    except FileNotFoundError:
        print(f"測試 PIL Image 物件時找不到檔案：{test_image_path}。請確保路徑正確。")
    except Exception as e:
        print(f"測試 PIL Image 物件時發生錯誤：{e}")
