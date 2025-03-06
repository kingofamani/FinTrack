from abc import ABC, abstractmethod
import json
import re
import os
import requests

class AIParser(ABC):
    """
    AI 解析器接口
    定義使用 AI 解析交易文本的方法
    """
    
    @abstractmethod
    def parse_transaction(self, text):
        """
        解析交易文本
        
        Args:
            text (str): 語音識別文本，例如「咖啡 5 元」
            
        Returns:
            dict: 解析後的交易數據，包含 type, item, category, amount
        """
        pass

class OpenAIParser(AIParser):
    """
    使用 OpenAI API 解析交易文本
    """
    
    def __init__(self, api_key=None, model="gpt-3.5-turbo"):
        """
        初始化 OpenAI 解析器
        
        Args:
            api_key (str): OpenAI API 密鑰，如果為 None，則從環境變量獲取
            model (str): 使用的模型名稱
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API 密鑰未提供，請設置 OPENAI_API_KEY 環境變量或在初始化時提供")
        
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    def parse_transaction(self, text):
        """
        使用 OpenAI API 解析交易文本
        
        Args:
            text (str): 語音識別文本，例如「咖啡 5 元」
            
        Returns:
            dict: 解析後的交易數據
        """
        try:
            # 構建 API 請求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 構建提示詞
            prompt = f"""
            請解析以下交易文本，並以 JSON 格式返回結果。
            文本: "{text}"
            
            請返回以下格式的 JSON:
            {{
                "type": "expense" 或 "income" (支出或收入),
                "item": "項目名稱",
                "category": "類別",
                "amount": 金額 (數字)
            }}
            
            規則:
            1. 如果文本包含「收入」、「薪水」、「薪資」、「工資」、「獎金」、「紅包」等關鍵詞，則 type 為 "income"，否則為 "expense"
            2. 項目名稱應該是金額前的文字
            3. 類別應根據項目名稱猜測，例如「咖啡」屬於 "food"，「房租」屬於 "housing" 等
            4. 金額應該是文本中的數字
            
            只返回 JSON 格式的結果，不要有其他文字。
            """
            
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
            
            # 發送請求
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            
            # 解析回應
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # 提取 JSON 部分
            json_match = re.search(r'({.*})', content, re.DOTALL)
            if json_match:
                transaction_data = json.loads(json_match.group(1))
            else:
                transaction_data = json.loads(content)
            
            # 確保數據格式正確
            transaction_data["amount"] = float(transaction_data["amount"])
            
            return transaction_data
            
        except Exception as e:
            print(f"OpenAI 解析錯誤: {str(e)}")
            # 如果 API 調用失敗，使用備用方法解析
            return self._fallback_parse(text)
    
    def _fallback_parse(self, text):
        """
        備用解析方法，當 API 調用失敗時使用
        
        Args:
            text (str): 語音識別文本
            
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
        category = self._guess_category(item, transaction_type)
        
        return {
            "type": transaction_type,
            "item": item,
            "category": category,
            "amount": amount
        }
    
    def _guess_category(self, item, transaction_type):
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

class XAIGrokParser(AIParser):
    """
    使用 XAI Grok 解析交易文本
    """
    
    def __init__(self, api_key=None, api_url=None):
        """
        初始化 XAI Grok 解析器
        
        Args:
            api_key (str): XAI Grok API 密鑰，如果為 None，則從環境變量獲取
            api_url (str): XAI Grok API URL，如果為 None，則使用預設值
        """
        self.api_key = api_key or os.environ.get("XAI_GROK_API_KEY")
        if not self.api_key:
            raise ValueError("XAI Grok API 密鑰未提供，請設置 XAI_GROK_API_KEY 環境變量或在初始化時提供")
        
        self.api_url = api_url or "https://api.groq.com/openai/v1/chat/completions"
    
    def parse_transaction(self, text):
        """
        使用 XAI Grok 解析交易文本
        
        Args:
            text (str): 語音識別文本，例如「咖啡 5 元」
            
        Returns:
            dict: 解析後的交易數據
        """
        try:
            # 構建 API 請求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 構建提示詞
            prompt = f"""
            請解析以下交易文本，並以 JSON 格式返回結果。
            文本: "{text}"
            
            請返回以下格式的 JSON:
            {{
                "type": "expense" 或 "income" (支出或收入),
                "item": "項目名稱",
                "category": "類別",
                "amount": 金額 (數字)
            }}
            
            規則:
            1. 如果文本包含「收入」、「薪水」、「薪資」、「工資」、「獎金」、「紅包」等關鍵詞，則 type 為 "income"，否則為 "expense"
            2. 項目名稱應該是金額前的文字
            3. 類別應根據項目名稱猜測，例如「咖啡」屬於 "food"，「房租」屬於 "housing" 等
            4. 金額應該是文本中的數字
            
            只返回 JSON 格式的結果，不要有其他文字。
            """
            
            data = {
                "model": "mixtral-8x7b-32768",  # 使用 Grok 的模型
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
            
            # 發送請求
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            
            # 解析回應
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # 提取 JSON 部分
            json_match = re.search(r'({.*})', content, re.DOTALL)
            if json_match:
                transaction_data = json.loads(json_match.group(1))
            else:
                transaction_data = json.loads(content)
            
            # 確保數據格式正確
            transaction_data["amount"] = float(transaction_data["amount"])
            
            return transaction_data
            
        except Exception as e:
            print(f"XAI Grok 解析錯誤: {str(e)}")
            # 如果 API 調用失敗，使用備用方法解析
            return self._fallback_parse(text)
    
    def _fallback_parse(self, text):
        """
        備用解析方法，當 API 調用失敗時使用
        
        Args:
            text (str): 語音識別文本
            
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
        category = self._guess_category(item, transaction_type)
        
        return {
            "type": transaction_type,
            "item": item,
            "category": category,
            "amount": amount
        }
    
    def _guess_category(self, item, transaction_type):
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

class LocalRuleParser(AIParser):
    """
    使用本地規則解析交易文本
    不需要 API 調用，作為備用方案
    """
    
    def parse_transaction(self, text):
        """
        使用本地規則解析交易文本
        
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
        category = self._guess_category(item, transaction_type)
        
        return {
            "type": transaction_type,
            "item": item,
            "category": category,
            "amount": amount
        }
    
    def _guess_category(self, item, transaction_type):
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

# 工廠函數，用於創建解析器實例
def create_parser(parser_type="local", **kwargs):
    """
    創建解析器實例
    
    Args:
        parser_type (str): 解析器類型，可選值為 "openai", "xai_grok", "local"
        **kwargs: 傳遞給解析器的參數
        
    Returns:
        AIParser: 解析器實例
    """
    if parser_type == "openai":
        return OpenAIParser(**kwargs)
    elif parser_type == "xai_grok":
        return XAIGrokParser(**kwargs)
    else:  # 預設使用本地規則
        return LocalRuleParser() 