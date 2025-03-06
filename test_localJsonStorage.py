import unittest
import json
import os
import datetime
from unittest.mock import patch, mock_open, MagicMock
from localJsonStorage import LocalJsonStorage

class TestLocalJsonStorage(unittest.TestCase):
    """測試本地 JSON 存儲"""
    
    def setUp(self):
        """設置測試環境"""
        # 使用臨時檔案路徑
        self.test_file = "test_transactions.json"
        self.storage = LocalJsonStorage(self.test_file)
    
    def tearDown(self):
        """清理測試環境"""
        # 刪除測試檔案
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_ensure_file_exists(self, mock_file, mock_exists):
        """測試確保檔案存在的功能"""
        # 模擬檔案不存在
        mock_exists.return_value = False
        
        # 創建存儲實例
        storage = LocalJsonStorage(self.test_file)
        
        # 驗證檔案創建
        mock_file.assert_called_once_with(self.test_file, 'w', encoding='utf-8')
        mock_file().write.assert_called_once()
        
        # 驗證寫入的內容
        write_arg = mock_file().write.call_args[0][0]
        data = json.loads(write_arg)
        self.assertIn("transactions", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["points"], 0)
        self.assertEqual(data["user"]["streak"], 0)
        self.assertIsNone(data["user"]["last_record_date"])
    
    @patch('builtins.open', new_callable=mock_open)
    def test_read_data(self, mock_file):
        """測試讀取數據功能"""
        # 模擬檔案內容
        mock_file.return_value.read.return_value = json.dumps({
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
            }
        })
        
        # 調用函數
        data = self.storage._read_data()
        
        # 驗證結果
        self.assertIn("transactions", data)
        self.assertIn("user", data)
        self.assertEqual(len(data["transactions"]), 1)
        self.assertEqual(data["transactions"][0]["item"], "咖啡")
        self.assertEqual(data["user"]["points"], 10)
    
    @patch('builtins.open', new_callable=mock_open)
    def test_write_data(self, mock_file):
        """測試寫入數據功能"""
        # 測試數據
        test_data = {
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
            }
        }
        
        # 調用函數
        self.storage._write_data(test_data)
        
        # 驗證結果
        mock_file.assert_called_once_with(self.test_file, 'w', encoding='utf-8')
        mock_file().write.assert_called_once()
        
        # 驗證寫入的內容
        write_arg = mock_file().write.call_args[0][0]
        data = json.loads(write_arg)
        self.assertEqual(data, test_data)
    
    @patch('localJsonStorage.LocalJsonStorage._read_data')
    @patch('localJsonStorage.LocalJsonStorage._write_data')
    @patch('localJsonStorage.LocalJsonStorage.update_gamification')
    def test_save_transaction(self, mock_update, mock_write, mock_read):
        """測試保存交易功能"""
        # 模擬讀取的數據
        mock_read.return_value = {
            "transactions": [],
            "user": {
                "points": 0,
                "streak": 0,
                "last_record_date": None
            }
        }
        
        # 測試交易數據
        transaction = {
            "type": "expense",
            "item": "咖啡",
            "category": "food",
            "amount": 5.0
        }
        
        # 調用函數
        result = self.storage.save_transaction(transaction)
        
        # 驗證結果
        self.assertTrue(result)
        mock_read.assert_called_once()
        mock_write.assert_called_once()
        mock_update.assert_called_once()
        
        # 驗證寫入的數據
        write_data = mock_write.call_args[0][0]
        self.assertEqual(len(write_data["transactions"]), 1)
        saved_transaction = write_data["transactions"][0]
        self.assertEqual(saved_transaction["type"], "expense")
        self.assertEqual(saved_transaction["item"], "咖啡")
        self.assertEqual(saved_transaction["category"], "food")
        self.assertEqual(saved_transaction["amount"], 5.0)
        self.assertIn("date", saved_transaction)
    
    @patch('localJsonStorage.LocalJsonStorage._read_data')
    @patch('localJsonStorage.LocalJsonStorage.get_monthly_summary')
    def test_get_data(self, mock_summary, mock_read):
        """測試獲取數據功能"""
        # 模擬讀取的數據
        mock_read.return_value = {
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
            }
        }
        
        # 模擬月度總覽
        mock_summary.return_value = {
            "income": 0,
            "expense": 5.0,
            "savings": -5.0
        }
        
        # 調用函數
        data = self.storage.get_data()
        
        # 驗證結果
        self.assertIn("transactions", data)
        self.assertIn("user", data)
        self.assertIn("summary", data)
        self.assertEqual(len(data["transactions"]), 1)
        self.assertEqual(data["transactions"][0]["item"], "咖啡")
        self.assertEqual(data["user"]["points"], 10)
        self.assertEqual(data["summary"]["expense"], 5.0)
    
    @patch('localJsonStorage.LocalJsonStorage._read_data')
    def test_get_monthly_summary(self, mock_read):
        """測試獲取月度總覽功能"""
        # 獲取當前年月
        now = datetime.datetime.now()
        current_year = now.year
        current_month = now.month
        
        # 模擬讀取的數據
        mock_read.return_value = {
            "transactions": [
                # 當月支出
                {
                    "type": "expense",
                    "item": "咖啡",
                    "category": "food",
                    "amount": 5.0,
                    "date": f"{current_year}-{current_month:02d}-01"
                },
                # 當月收入
                {
                    "type": "income",
                    "item": "薪水",
                    "category": "income",
                    "amount": 30000.0,
                    "date": f"{current_year}-{current_month:02d}-15"
                },
                # 非當月交易
                {
                    "type": "expense",
                    "item": "午餐",
                    "category": "food",
                    "amount": 10.0,
                    "date": f"{current_year}-{(current_month-1):02d}-01" if current_month > 1 else f"{current_year-1}-12-01"
                }
            ],
            "user": {
                "points": 10,
                "streak": 1,
                "last_record_date": "2025-03-06"
            }
        }
        
        # 調用函數
        summary = self.storage.get_monthly_summary()
        
        # 驗證結果
        self.assertEqual(summary["income"], 30000.0)
        self.assertEqual(summary["expense"], 5.0)
        self.assertEqual(summary["savings"], 29995.0)
    
    @patch('localJsonStorage.LocalJsonStorage._read_data')
    @patch('localJsonStorage.LocalJsonStorage._write_data')
    def test_update_gamification(self, mock_write, mock_read):
        """測試更新遊戲化數據功能"""
        # 獲取當前日期
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 模擬讀取的數據（上次記錄是昨天）
        mock_read.return_value = {
            "transactions": [],
            "user": {
                "points": 10,
                "streak": 1,
                "last_record_date": yesterday
            }
        }
        
        # 調用函數
        result = self.storage.update_gamification()
        
        # 驗證結果
        self.assertEqual(result["points"], 20)  # 10 + 10
        self.assertEqual(result["streak"], 2)   # 1 + 1
        self.assertEqual(result["last_record_date"], today)
        
        # 驗證寫入的數據
        mock_write.assert_called_once()
        write_data = mock_write.call_args[0][0]
        self.assertEqual(write_data["user"]["points"], 20)
        self.assertEqual(write_data["user"]["streak"], 2)
        self.assertEqual(write_data["user"]["last_record_date"], today)

if __name__ == '__main__':
    unittest.main() 