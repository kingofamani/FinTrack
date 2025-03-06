import unittest
import json
import os
from app import app, validate_transaction, load_config
from unittest.mock import patch, MagicMock

class TestApp(unittest.TestCase):
    """測試 Flask 應用程式"""
    
    def setUp(self):
        """設置測試環境"""
        app.config['TESTING'] = True
        self.client = app.test_client()
        
    def test_index_route(self):
        """測試首頁路由"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
    @patch('app.transaction_parser')
    def test_parse_text_route(self, mock_parser):
        """測試解析文本路由"""
        # 模擬解析器返回值
        mock_parser.parse_transaction.return_value = {
            "type": "expense",
            "item": "咖啡",
            "category": "food",
            "amount": 5.0
        }
        
        # 發送請求
        response = self.client.post('/api/parse', 
                                   json={"text": "咖啡 5 元"},
                                   content_type='application/json')
        
        # 驗證結果
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["type"], "expense")
        self.assertEqual(data["item"], "咖啡")
        self.assertEqual(data["category"], "food")
        self.assertEqual(data["amount"], 5.0)
        
        # 驗證解析器被正確調用
        mock_parser.parse_transaction.assert_called_once_with("咖啡 5 元")
        
    @patch('app.data_storage')
    def test_record_transaction_route_valid(self, mock_storage):
        """測試記錄有效交易"""
        # 模擬存儲返回值
        mock_storage.save_transaction.return_value = True
        
        # 有效交易數據
        transaction = {
            "type": "expense",
            "item": "咖啡",
            "category": "food",
            "amount": 5.0
        }
        
        # 發送請求
        response = self.client.post('/api/record', 
                                   json=transaction,
                                   content_type='application/json')
        
        # 驗證結果
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        
        # 驗證存儲被正確調用
        mock_storage.save_transaction.assert_called_once_with(transaction)
        
    @patch('app.data_storage')
    def test_record_transaction_route_invalid(self, mock_storage):
        """測試記錄無效交易"""
        # 無效交易數據（缺少必要欄位）
        transaction = {
            "type": "expense",
            "item": "咖啡",
            # 缺少 category
            "amount": 5.0
        }
        
        # 發送請求
        response = self.client.post('/api/record', 
                                   json=transaction,
                                   content_type='application/json')
        
        # 驗證結果
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        
        # 驗證存儲未被調用
        mock_storage.save_transaction.assert_not_called()
        
    @patch('app.data_storage')
    def test_get_data_route(self, mock_storage):
        """測試獲取數據路由"""
        # 模擬存儲返回值
        mock_data = {
            "transactions": [
                {
                    "type": "expense",
                    "item": "咖啡",
                    "category": "food",
                    "amount": 5.0,
                    "date": "2025-03-06"
                }
            ],
            "user": {
                "points": 10,
                "streak": 1,
                "last_record_date": "2025-03-06"
            },
            "summary": {
                "income": 0,
                "expense": 5.0,
                "savings": -5.0
            }
        }
        mock_storage.get_data.return_value = mock_data
        
        # 發送請求
        response = self.client.get('/api/data')
        
        # 驗證結果
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data, mock_data)
        
        # 驗證存儲被正確調用
        mock_storage.get_data.assert_called_once()
        
    def test_validate_transaction(self):
        """測試交易驗證功能"""
        # 有效交易
        valid_transaction = {
            "type": "expense",
            "item": "咖啡",
            "category": "food",
            "amount": 5.0
        }
        self.assertTrue(validate_transaction(valid_transaction))
        
        # 無效交易 - 缺少欄位
        invalid_transaction1 = {
            "type": "expense",
            "item": "咖啡",
            # 缺少 category
            "amount": 5.0
        }
        self.assertFalse(validate_transaction(invalid_transaction1))
        
        # 無效交易 - 無效類型
        invalid_transaction2 = {
            "type": "invalid_type",
            "item": "咖啡",
            "category": "food",
            "amount": 5.0
        }
        self.assertFalse(validate_transaction(invalid_transaction2))
        
        # 無效交易 - 無效金額
        invalid_transaction3 = {
            "type": "expense",
            "item": "咖啡",
            "category": "food",
            "amount": -5.0
        }
        self.assertFalse(validate_transaction(invalid_transaction3))
        
        # 無效交易 - 金額不是數字
        invalid_transaction4 = {
            "type": "expense",
            "item": "咖啡",
            "category": "food",
            "amount": "not_a_number"
        }
        self.assertFalse(validate_transaction(invalid_transaction4))
        
    @patch('app.os.path.exists')
    @patch('builtins.open')
    def test_load_config(self, mock_open, mock_exists):
        """測試配置檔案載入功能"""
        # 模擬配置檔案存在
        mock_exists.return_value = True
        
        # 模擬檔案內容
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = json.dumps({
            "parser_type": "openai",
            "openai_api_key": "test_key",
            "openai_model": "gpt-4"
        })
        mock_open.return_value = mock_file
        
        # 調用函數
        config = load_config()
        
        # 驗證結果
        self.assertEqual(config["parser_type"], "openai")
        self.assertEqual(config["openai_api_key"], "test_key")
        self.assertEqual(config["openai_model"], "gpt-4")
        self.assertIsNone(config["xai_grok_api_key"])
        
        # 模擬配置檔案不存在
        mock_exists.return_value = False
        
        # 調用函數
        config = load_config()
        
        # 驗證結果
        self.assertEqual(config["parser_type"], "local")
        self.assertIsNone(config["openai_api_key"])
        self.assertIsNone(config["xai_grok_api_key"])
        self.assertEqual(config["openai_model"], "gpt-3.5-turbo")

if __name__ == '__main__':
    unittest.main() 