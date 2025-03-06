import json
import os
import datetime
from dataStorage import DataStorage

class LocalJsonStorage(DataStorage):
    """
    本地 JSON 存儲實現
    使用本地 JSON 文件存儲交易和用戶數據
    """
    
    def __init__(self, file_path="transactions.json"):
        """
        初始化本地 JSON 存儲
        
        Args:
            file_path (str): JSON 文件路徑
        """
        self.file_path = file_path
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """確保 JSON 文件存在，如果不存在則創建"""
        if not os.path.exists(self.file_path):
            initial_data = {
                "transactions": [],
                "user": {
                    "points": 0,
                    "streak": 0,
                    "last_record_date": None
                }
            }
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
    
    def _read_data(self):
        """讀取 JSON 文件數據"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _write_data(self, data):
        """寫入數據到 JSON 文件"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_transaction(self, transaction):
        """
        保存交易數據
        
        Args:
            transaction (dict): 交易數據，包含 type, item, category, amount
            
        Returns:
            bool: 是否成功保存
        """
        try:
            # 添加日期
            transaction['date'] = datetime.datetime.now().strftime('%Y-%m-%d')
            
            # 讀取現有數據
            data = self._read_data()
            
            # 添加新交易
            data['transactions'].insert(0, transaction)  # 新交易放在最前面
            
            # 更新遊戲化數據
            self._update_gamification_internal(data)
            
            # 保存數據
            self._write_data(data)
            
            return True
        except Exception as e:
            print(f"保存交易錯誤: {str(e)}")
            return False
    
    def get_data(self):
        """
        獲取所有數據，包括交易和用戶遊戲化數據
        
        Returns:
            dict: 包含 transactions 和 user 的字典
        """
        try:
            data = self._read_data()
            
            # 添加總覽數據
            summary = self.get_monthly_summary()
            data['summary'] = summary
            
            return data
        except Exception as e:
            print(f"獲取數據錯誤: {str(e)}")
            return {"transactions": [], "user": {"points": 0, "streak": 0}, "summary": {"income": 0, "expense": 0, "savings": 0}}
    
    def get_monthly_summary(self):
        """
        獲取當月交易總覽
        
        Returns:
            dict: 包含 income, expense, savings 的字典
        """
        try:
            data = self._read_data()
            
            # 獲取當前年月
            current_year_month = datetime.datetime.now().strftime('%Y-%m')
            
            # 計算當月收入和支出
            income = 0
            expense = 0
            
            for transaction in data['transactions']:
                # 檢查是否為當月交易
                if transaction['date'].startswith(current_year_month):
                    if transaction['type'] == 'income':
                        income += transaction['amount']
                    else:  # expense
                        expense += transaction['amount']
            
            # 計算儲蓄
            savings = income - expense
            
            return {
                "income": income,
                "expense": expense,
                "savings": savings
            }
        except Exception as e:
            print(f"獲取月度總覽錯誤: {str(e)}")
            return {"income": 0, "expense": 0, "savings": 0}
    
    def update_gamification(self):
        """
        更新遊戲化數據，包括點數和連續記錄天數
        
        Returns:
            dict: 更新後的用戶遊戲化數據
        """
        try:
            data = self._read_data()
            self._update_gamification_internal(data)
            self._write_data(data)
            return data['user']
        except Exception as e:
            print(f"更新遊戲化數據錯誤: {str(e)}")
            return {"points": 0, "streak": 0}
    
    def _update_gamification_internal(self, data):
        """
        內部更新遊戲化數據
        
        Args:
            data (dict): 完整數據字典
        """
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        user = data['user']
        
        # 如果是第一次記錄
        if user['last_record_date'] is None:
            user['points'] = 10
            user['streak'] = 1
            user['last_record_date'] = today
            return
        
        # 如果今天已經記錄過，不重複計算
        if user['last_record_date'] == today:
            return
        
        # 計算上次記錄和今天的日期差
        last_date = datetime.datetime.strptime(user['last_record_date'], '%Y-%m-%d')
        current_date = datetime.datetime.strptime(today, '%Y-%m-%d')
        days_diff = (current_date - last_date).days
        
        # 如果是連續記錄（昨天記錄過）
        if days_diff == 1:
            user['streak'] += 1
        # 如果中斷了連續記錄
        elif days_diff > 1:
            user['streak'] = 1
        
        # 每天記錄獲得 10 點
        user['points'] += 10
        user['last_record_date'] = today 