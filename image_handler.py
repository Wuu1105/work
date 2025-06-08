# image_handler.py
# This module will handle loading images from files or clipboard.

from PIL import Image, ImageGrab

def load_image_from_file(file_path):
    """從指定的檔案路徑載入圖片。"""
    try:
        img = Image.open(file_path)
        return img
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 {file_path}")
        return None
    except Exception as e:
        print(f"載入圖片時發生錯誤：{e}")
        return None

def paste_image_from_clipboard():
    """從剪貼簿貼上圖片。"""
    try:
        img = ImageGrab.grabclipboard()
        if img:
            return img
        else:
            print("剪貼簿中沒有圖片。")
            return None
    except Exception as e:
        # 在某些系統上，如果剪貼簿為空或不包含圖片資料，ImageGrab.grabclipboard() 可能會引發異常
        # 例如在 WSL 或無頭伺服器上
        print(f"從剪貼簿貼上圖片時發生錯誤：{e}")
        print("請確保您已將圖片複製到剪貼簿，且您的環境支援剪貼簿存取。")
        return None

if __name__ == '__main__':
    # 測試從檔案載入圖片
    # 請將 'path/to/your/image.png' 替換為實際的圖片檔案路徑
    test_image_path = 'path/to/your/image.png' # 您需要修改此路徑以進行測試
    img_from_file = load_image_from_file(test_image_path)
    if img_from_file:
        try:
            img_from_file.show()
            print(f"已成功從檔案 {test_image_path} 載入圖片。")
        except Exception as e:
            print(f"顯示從檔案載入的圖片時發生錯誤: {e}。可能是因為沒有可用的顯示環境。")


    # 測試從剪貼簿貼上圖片
    # 執行此部分之前，請先複製一張圖片到剪貼簿
    print("\n嘗試從剪貼簿貼上圖片...")
    img_from_clipboard = paste_image_from_clipboard()
    if img_from_clipboard:
        try:
            img_from_clipboard.show()
            print("已成功從剪貼簿貼上圖片。")
        except Exception as e:
            print(f"顯示從剪貼簿貼上的圖片時發生錯誤: {e}。可能是因為沒有可用的顯示環境。")
    else:
        print("未能從剪貼簿貼上圖片。")
