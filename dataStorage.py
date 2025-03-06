from abc import ABC, abstractmethod

class DataStorage(ABC):
    """
    資料存儲接口
    定義存儲和讀取交易數據的方法
    """
    
    @abstractmethod
    def save_transaction(self, transaction):
        """
        保存交易數據
        
        Args:
            transaction (dict): 交易數據，包含 type, item, category, amount
            
        Returns:
            bool: 是否成功保存
        """
        pass
    
    @abstractmethod
    def get_data(self):
        """
        獲取所有數據，包括交易和用戶遊戲化數據
        
        Returns:
            dict: 包含 transactions 和 user 的字典
        """
        pass
    
    @abstractmethod
    def get_monthly_summary(self):
        """
        獲取當月交易總覽
        
        Returns:
            dict: 包含 income, expense, savings 的字典
        """
        pass
    
    @abstractmethod
    def update_gamification(self):
        """
        更新遊戲化數據，包括點數和連續記錄天數
        
        Returns:
            dict: 更新後的用戶遊戲化數據
        """
        pass 