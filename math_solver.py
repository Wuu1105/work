# math_solver.py
# This module will parse and solve mathematical equations.

from sympy import sympify, solve, SympifyError
from sympy.parsing.mathematica import parse_mathematica

def solve_equation(equation_str):
    """解析並求解數學方程式字串。

    Args:
        equation_str: 包含數學方程式的字串。

    Returns:
        方程式的解，或在發生錯誤時返回錯誤訊息字串。
    """
    try:
        # 嘗試使用 sympify 直接解析，適用於標準 Python 數學語法
        # 並替換一些常見的 OCR 錯誤或口語化表達
        equation_str = equation_str.replace('x', '*x') # 處理隱含乘法，例如 2x -> 2*x
        equation_str = equation_str.replace('X', '*X') # 處理隱含乘法，例如 2X -> 2*X
        equation_str = equation_str.replace('=', '-(') + ')' # 將 eq = 0 轉換為 eq
        equation_str = equation_str.replace('^', '**') # 冪運算子

        # 移除任何可能由 OCR 產生的多餘空格
        equation_str = ''.join(equation_str.split())

        # 嘗試定義變數 x，如果方程式中包含 x
        # Sympy 需要明確的變數定義
        # 這裡我們假設 'x' 是最常見的變數，您可以擴展此邏輯以處理其他變數
        if 'x' in equation_str.lower():
            from sympy.abc import x
        # 您可以為其他常見變數添加類似的邏輯，例如 y, z, a, b, c
        # elif 'y' in equation_str.lower():
        #     from sympy.abc import y

        parsed_expr = sympify(equation_str)
        solution = solve(parsed_expr)
        return solution
    except SympifyError as e_sympify:
        # 如果直接 sympify 失敗，嘗試使用 Mathematica 語法解析器
        # 這有助於處理更複雜或不同格式的輸入
        try:
            # Mathematica 解析器可能對空格更敏感，或有不同的期望
            # 我們再次處理字串，確保其格式適合 parse_mathematica
            # Mathematica 通常使用 == 表示等式
            # 我們需要將單個 = 轉換為表達式，或者如果它是等式的一部分，則轉換為 ==
            # 為了簡單起見，我們假設 OCR 的 = 意指要求解的表達式等於 0
            # 或者，如果使用者輸入 "x+5=10"，我們需要將其轉換為 "x+5-(10)"
            # 這裡的邏輯與上面的 sympify 相似，但可能需要針對 Mathematica 進行調整

            # 重新處理原始字串以用於 Mathematica 解析器
            # 這裡的替換邏輯可能需要根據 Mathematica 的語法進行調整
            # 例如，Mathematica 使用 == 表示等式，並使用 ^ 表示冪
            # 我們假設 OCR 提取的方程式是 "expr = value" 或 "expr"
            # 如果是 "expr = value"，我們將其轉換為 "expr - (value)"
            # 如果只是 "expr"，我們假設它等於 0

            # 為了簡化，我們將重複使用 sympify 的清理步驟，並進行調整
            # 這部分可能需要進一步的測試和完善，以處理各種 Mathematica 輸入格式
            # 暫時，我們將依賴 sympify 的錯誤，並提示使用者
            return f"無法使用標準解析器解析方程式：{e_sympify}。嘗試 Mathematica 解析器也可能遇到問題，因為輸入格式可能不相容。"

        except Exception as e_mathematica:
            return f"使用標準解析器解析失敗：{e_sympify}。嘗試 Mathematica 解析器也失敗：{e_mathematica}"
    except NameError as e_name:
        # 這通常發生在方程式包含未定義的變數時
        return f"方程式中可能包含未定義的變數：{e_name}。請確保所有變數都已定義或常見（如 x）。"
    except Exception as e:
        return f"求解方程式時發生未預期的錯誤：{e}"

if __name__ == '__main__':
    # 測試案例
    equations = [
        "2*x - 4",         # 簡單線性方程式，預期解 x=2
        "x**2 - 4",        # 二次方程式，預期解 x=2, x=-2
        "x**2 + x + 1",    # 二次方程式，複數解
        "sin(x) - 0.5",    # 三角函數方程式 (solve 可能返回一個主解或一個集合)
        "2*x = 4",         # 包含等號的方程式
        "y*2 - 10",        # 使用不同變數 (需要修改程式碼以處理 'y')
        "log(x) - 1",      # 對數方程式 (solve 可能需要指定定義域)
        "gibberish",       # 無法解析的字串
        "2x-4",            # 測試隱含乘法
        "X^2 - 9",         # 測試大寫變數和冪運算子
    ]

    for eq_str in equations:
        print(f"方程式：{eq_str}")
        # 為了測試，我們需要手動處理包含 '=' 的情況，將其轉換為表達式
        # 或者修改 solve_equation 以更好地處理等號
        if '=' in eq_str:
            parts = eq_str.split('=')
            if len(parts) == 2:
                # 轉換為 expr - (value) 的形式
                processed_eq_str = f"({parts[0].strip()}) - ({parts[1].strip()})"
            else:
                # 無法處理多個等號或格式不正確的等式
                print(f"  無法處理的等式格式：{eq_str}")
                solution = "格式錯誤"
                print(f"  解：{solution}\n")
                continue
        else:
            processed_eq_str = eq_str

        solution = solve_equation(processed_eq_str)
        print(f"  處理後的字串：{processed_eq_str}")
        print(f"  解：{solution}\n")

    # 測試 Mathematica 解析器 (目前在 solve_equation 中未完全啟用)
    # mathematica_eq = "x^2 + 2x + 1 == 0"
    # print(f"Mathematica 方程式: {mathematica_eq}")
    # try:
    #     # 需要確保 x 被定義
    #     from sympy.abc import x
    #     # Mathematica 解析器通常期望等式，而不是表達式
    #     # parsed_mathematica = parse_mathematica(mathematica_eq)
    #     # solution_mathematica = solve(parsed_mathematica, x) # 指定求解的變數
    #     # print(f"  Mathematica 解: {solution_mathematica}\n")
    # except Exception as e:
    #     print(f"  Mathematica 解析失敗: {e}\n")
