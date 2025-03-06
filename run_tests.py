import unittest
import sys

# 導入測試模塊
from test_app import TestApp
from test_aiParser import TestLocalRuleParser, TestOpenAIParser, TestXAIGrokParser, TestCreateParser
from test_localJsonStorage import TestLocalJsonStorage

if __name__ == '__main__':
    # 創建測試套件
    test_suite = unittest.TestSuite()
    
    # 添加 app.py 測試
    test_suite.addTest(unittest.makeSuite(TestApp))
    
    # 添加 aiParser.py 測試
    test_suite.addTest(unittest.makeSuite(TestLocalRuleParser))
    test_suite.addTest(unittest.makeSuite(TestOpenAIParser))
    test_suite.addTest(unittest.makeSuite(TestXAIGrokParser))
    test_suite.addTest(unittest.makeSuite(TestCreateParser))
    
    # 添加 localJsonStorage.py 測試
    test_suite.addTest(unittest.makeSuite(TestLocalJsonStorage))
    
    # 運行測試
    result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    # 設置退出碼
    sys.exit(not result.wasSuccessful()) 