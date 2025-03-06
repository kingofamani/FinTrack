from flask import Flask, request, jsonify, render_template
import re
import json
from localJsonStorage import LocalJsonStorage

app = Flask(__name__)
data_storage = LocalJsonStorage()

@app.route('/')
def index():
    """渲染主頁"""
    return render_template('index.html')

@app.route('/api/parse', methods=['POST'])
def parse_text():
    """
    解析語音文本
    
    接收語音識別的文本，解析為交易數據
    """
    try:
        data = request.json
        text = data.get('text', '')
        
        # 解析文本
        transaction = parse_transaction_text(text)
        
        return jsonify(transaction)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/record', methods=['POST'])
def record_transaction():
    """
    記錄交易
    
    接收交易數據並保存
    """
    try:
        transaction = request.json
        
        # 驗證交易數據
        if not validate_transaction(transaction):
            return jsonify({"success": False, "message": "無效的交易數據"}), 400
        
        # 保存交易
        success = data_storage.save_transaction(transaction)
        
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "保存交易失敗"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/data', methods=['GET'])
def get_data():
    """
    獲取數據
    
    返回交易和遊戲化數據
    """
    try:
        data = data_storage.get_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def parse_transaction_text(text):
    """
    解析交易文本
    
    Args:
        text (str): 語音識別文本，例如「咖啡 5 元」
        
    Returns:
        dict: 解析後的交易數據
    """
    # 預設為支出
    transaction_type = "expense"
    
    # 檢查是否包含收入關鍵詞
    income_keywords = ["收入", "薪水", "薪資", "工資", "獎金", "紅包"]
    for keyword in income_keywords:
        if keyword in text:
            transaction_type = "income"
            break
    
    # 提取金額
    amount_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:元|塊|圓|dollars?|NT\$?)?', text)
    amount = float(amount_match.group(1)) if amount_match else 0
    
    # 提取項目名稱（假設金額前的文字為項目名稱）
    item = text
    if amount_match:
        item = text[:amount_match.start()].strip()
    
    # 如果項目為空，使用預設值
    if not item:
        item = "未命名項目"
    
    # 根據項目名稱猜測類別
    category = guess_category(item, transaction_type)
    
    return {
        "type": transaction_type,
        "item": item,
        "category": category,
        "amount": amount
    }

def guess_category(item, transaction_type):
    """
    根據項目名稱猜測類別
    
    Args:
        item (str): 項目名稱
        transaction_type (str): 交易類型
        
    Returns:
        str: 猜測的類別
    """
    if transaction_type == "income":
        return "income"
    
    # 食物類別關鍵詞
    food_keywords = ["咖啡", "飯", "餐", "食", "麵", "早餐", "午餐", "晚餐", "宵夜", "飲料", "水果"]
    for keyword in food_keywords:
        if keyword in item:
            return "food"
    
    # 交通類別關鍵詞
    transport_keywords = ["車", "票", "捷運", "公車", "計程車", "高鐵", "火車", "油", "加油"]
    for keyword in transport_keywords:
        if keyword in item:
            return "transport"
    
    # 住宿類別關鍵詞
    housing_keywords = ["房租", "水電", "電費", "水費", "瓦斯", "網路費"]
    for keyword in housing_keywords:
        if keyword in item:
            return "housing"
    
    # 娛樂類別關鍵詞
    entertainment_keywords = ["電影", "遊戲", "玩", "旅遊", "旅行", "門票"]
    for keyword in entertainment_keywords:
        if keyword in item:
            return "entertainment"
    
    # 預設類別
    return "other"

def validate_transaction(transaction):
    """
    驗證交易數據
    
    Args:
        transaction (dict): 交易數據
        
    Returns:
        bool: 是否有效
    """
    required_fields = ["type", "item", "category", "amount"]
    
    # 檢查必要欄位
    for field in required_fields:
        if field not in transaction:
            return False
    
    # 檢查類型
    if transaction["type"] not in ["income", "expense"]:
        return False
    
    # 檢查金額
    try:
        amount = float(transaction["amount"])
        if amount <= 0:
            return False
    except (ValueError, TypeError):
        return False
    
    return True

if __name__ == '__main__':
    app.run(debug=True) 