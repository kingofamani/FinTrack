from flask import Flask, request, jsonify, render_template
import re
import json
import os
from localJsonStorage import LocalJsonStorage
from aiParser import create_parser

app = Flask(__name__)
data_storage = LocalJsonStorage()

# 配置檔案路徑
CONFIG_FILE = 'config.json'

# 讀取配置檔案
def load_config():
    """
    讀取配置檔案
    
    Returns:
        dict: 配置數據
    """
    default_config = {
        "parser_type": "local",
        "openai_api_key": None,
        "xai_grok_api_key": None,
        "openai_model": "gpt-3.5-turbo"
    }
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合併預設配置和讀取的配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
    except Exception as e:
        print(f"讀取配置檔案錯誤: {str(e)}")
    
    return default_config

# 載入配置
config = load_config()

# 創建解析器
# 優先使用環境變量，其次使用配置檔案
parser_type = os.environ.get("AI_PARSER_TYPE", config.get("parser_type", "local"))

# 準備解析器參數
parser_kwargs = {}
if parser_type == "openai":
    api_key = os.environ.get("OPENAI_API_KEY", config.get("openai_api_key"))
    model = os.environ.get("OPENAI_MODEL", config.get("openai_model", "gpt-3.5-turbo"))
    if api_key:
        parser_kwargs["api_key"] = api_key
        parser_kwargs["model"] = model
elif parser_type == "xai_grok":
    api_key = os.environ.get("XAI_GROK_API_KEY", config.get("xai_grok_api_key"))
    if api_key:
        parser_kwargs["api_key"] = api_key

try:
    # 嘗試創建指定類型的解析器
    transaction_parser = create_parser(parser_type, **parser_kwargs)
except Exception as e:
    print(f"無法創建 {parser_type} 解析器: {str(e)}，使用本地規則解析器作為備用")
    transaction_parser = create_parser("local")

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
        
        # 使用 AI 解析器解析文本
        transaction = transaction_parser.parse_transaction(text)
        
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