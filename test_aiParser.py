import unittest
import json
import os
from unittest.mock import patch, MagicMock
from aiParser import AIParser, LocalRuleParser, OpenAIParser, XAIGrokParser, create_parser

class TestLocalRuleParser(unittest.TestCase):
    """測試本地規則解析器"""
    
    def setUp(self):
        """設置測試環境"""
        self.parser = LocalRuleParser()
    
    def test_parse_expense(self):
        """測試解析支出交易"""
        # 測試簡單支出
        result = self.parser.parse_transaction("咖啡 5 元")
        self.assertEqual(result["type"], "expense")
        self.assertEqual(result["item"], "咖啡")
        self.assertEqual(result["category"], "food")
        self.assertEqual(result["amount"], 5.0)
        
        # 測試帶小數點的金額
        result = self.parser.parse_transaction("午餐 12.5 元")
        self.assertEqual(result["type"], "expense")
        self.assertEqual(result["item"], "午餐")
        self.assertEqual(result["category"], "food")
        self.assertEqual(result["amount"], 12.5)
        
        # 測試不同類別
        result = self.parser.parse_transaction("計程車 100 元")
        self.assertEqual(result["type"], "expense")
        self.assertEqual(result["item"], "計程車")
        self.assertEqual(result["category"], "transport")
        self.assertEqual(result["amount"], 100.0)
        
        # 測試沒有單位的金額
        result = self.parser.parse_transaction("電影票 250")
        self.assertEqual(result["type"], "expense")
        self.assertEqual(result["item"], "電影票")
        self.assertEqual(result["category"], "entertainment")
        self.assertEqual(result["amount"], 250.0)
    
    def test_parse_income(self):
        """測試解析收入交易"""
        # 測試簡單收入
        result = self.parser.parse_transaction("薪水收入 30000 元")
        self.assertEqual(result["type"], "income")
        self.assertEqual(result["item"], "薪水收入")
        self.assertEqual(result["category"], "income")
        self.assertEqual(result["amount"], 30000.0)
        
        # 測試其他收入關鍵詞
        result = self.parser.parse_transaction("獎金 5000 元")
        self.assertEqual(result["type"], "income")
        self.assertEqual(result["item"], "獎金")
        self.assertEqual(result["category"], "income")
        self.assertEqual(result["amount"], 5000.0)
    
    def test_guess_category(self):
        """測試類別猜測功能"""
        # 測試食物類別
        self.assertEqual(self.parser._guess_category("咖啡", "expense"), "food")
        self.assertEqual(self.parser._guess_category("早餐", "expense"), "food")
        self.assertEqual(self.parser._guess_category("水果", "expense"), "food")
        
        # 測試交通類別
        self.assertEqual(self.parser._guess_category("計程車", "expense"), "transport")
        self.assertEqual(self.parser._guess_category("高鐵票", "expense"), "transport")
        self.assertEqual(self.parser._guess_category("加油", "expense"), "transport")
        
        # 測試住宿類別
        self.assertEqual(self.parser._guess_category("房租", "expense"), "housing")
        self.assertEqual(self.parser._guess_category("水電費", "expense"), "housing")
        self.assertEqual(self.parser._guess_category("網路費", "expense"), "housing")
        
        # 測試娛樂類別
        self.assertEqual(self.parser._guess_category("電影", "expense"), "entertainment")
        self.assertEqual(self.parser._guess_category("遊戲", "expense"), "entertainment")
        self.assertEqual(self.parser._guess_category("旅遊", "expense"), "entertainment")
        
        # 測試其他類別
        self.assertEqual(self.parser._guess_category("其他項目", "expense"), "other")
        
        # 測試收入類別
        self.assertEqual(self.parser._guess_category("任何項目", "income"), "income")

class TestOpenAIParser(unittest.TestCase):
    """測試 OpenAI 解析器"""
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def setUp(self):
        """設置測試環境"""
        self.parser = OpenAIParser()
    
    @patch('requests.post')
    def test_parse_transaction(self, mock_post):
        """測試使用 OpenAI API 解析交易"""
        # 模擬 API 回應
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "type": "expense",
                            "item": "咖啡",
                            "category": "food",
                            "amount": 5.0
                        })
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # 調用函數
        result = self.parser.parse_transaction("咖啡 5 元")
        
        # 驗證結果
        self.assertEqual(result["type"], "expense")
        self.assertEqual(result["item"], "咖啡")
        self.assertEqual(result["category"], "food")
        self.assertEqual(result["amount"], 5.0)
        
        # 驗證 API 調用
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://api.openai.com/v1/chat/completions")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test_key")
        self.assertEqual(kwargs["json"]["model"], "gpt-3.5-turbo")
        self.assertIn("咖啡 5 元", kwargs["json"]["messages"][0]["content"])
    
    @patch('requests.post')
    def test_api_error_fallback(self, mock_post):
        """測試 API 錯誤時的備用解析"""
        # 模擬 API 錯誤
        mock_post.side_effect = Exception("API 錯誤")
        
        # 調用函數
        result = self.parser.parse_transaction("咖啡 5 元")
        
        # 驗證結果（應該使用備用解析）
        self.assertEqual(result["type"], "expense")
        self.assertEqual(result["item"], "咖啡")
        self.assertEqual(result["category"], "food")
        self.assertEqual(result["amount"], 5.0)

class TestXAIGrokParser(unittest.TestCase):
    """測試 XAI Grok 解析器"""
    
    @patch.dict(os.environ, {"XAI_GROK_API_KEY": "test_key"})
    def setUp(self):
        """設置測試環境"""
        self.parser = XAIGrokParser()
    
    @patch('requests.post')
    def test_parse_transaction(self, mock_post):
        """測試使用 XAI Grok API 解析交易"""
        # 模擬 API 回應
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "type": "expense",
                            "item": "咖啡",
                            "category": "food",
                            "amount": 5.0
                        })
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # 調用函數
        result = self.parser.parse_transaction("咖啡 5 元")
        
        # 驗證結果
        self.assertEqual(result["type"], "expense")
        self.assertEqual(result["item"], "咖啡")
        self.assertEqual(result["category"], "food")
        self.assertEqual(result["amount"], 5.0)
        
        # 驗證 API 調用
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://api.groq.com/openai/v1/chat/completions")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test_key")
        self.assertEqual(kwargs["json"]["model"], "mixtral-8x7b-32768")
        self.assertIn("咖啡 5 元", kwargs["json"]["messages"][0]["content"])
    
    @patch('requests.post')
    def test_api_error_fallback(self, mock_post):
        """測試 API 錯誤時的備用解析"""
        # 模擬 API 錯誤
        mock_post.side_effect = Exception("API 錯誤")
        
        # 調用函數
        result = self.parser.parse_transaction("咖啡 5 元")
        
        # 驗證結果（應該使用備用解析）
        self.assertEqual(result["type"], "expense")
        self.assertEqual(result["item"], "咖啡")
        self.assertEqual(result["category"], "food")
        self.assertEqual(result["amount"], 5.0)

class TestCreateParser(unittest.TestCase):
    """測試解析器工廠函數"""
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key", "XAI_GROK_API_KEY": "test_key"})
    def test_create_parser(self):
        """測試創建不同類型的解析器"""
        # 測試創建本地規則解析器
        parser = create_parser("local")
        self.assertIsInstance(parser, LocalRuleParser)
        
        # 測試創建 OpenAI 解析器
        parser = create_parser("openai")
        self.assertIsInstance(parser, OpenAIParser)
        self.assertEqual(parser.api_key, "test_key")
        self.assertEqual(parser.model, "gpt-3.5-turbo")
        
        # 測試創建 OpenAI 解析器（自定義參數）
        parser = create_parser("openai", api_key="custom_key", model="gpt-4")
        self.assertIsInstance(parser, OpenAIParser)
        self.assertEqual(parser.api_key, "custom_key")
        self.assertEqual(parser.model, "gpt-4")
        
        # 測試創建 XAI Grok 解析器
        parser = create_parser("xai_grok")
        self.assertIsInstance(parser, XAIGrokParser)
        self.assertEqual(parser.api_key, "test_key")
        
        # 測試創建 XAI Grok 解析器（自定義參數）
        parser = create_parser("xai_grok", api_key="custom_key")
        self.assertIsInstance(parser, XAIGrokParser)
        self.assertEqual(parser.api_key, "custom_key")
        
        # 測試無效類型（應該返回本地規則解析器）
        parser = create_parser("invalid_type")
        self.assertIsInstance(parser, LocalRuleParser)

if __name__ == '__main__':
    unittest.main() 