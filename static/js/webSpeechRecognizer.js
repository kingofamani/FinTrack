/**
 * WebSpeechRecognizer 類
 * 使用 Web Speech API 實現語音識別
 * 繼承自 SpeechRecognizer 接口
 */
class WebSpeechRecognizer extends SpeechRecognizer {
    constructor() {
        super();
        
        // 檢查瀏覽器是否支持 Web Speech API
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            throw new Error("您的瀏覽器不支持語音識別功能");
        }
        
        // 創建 SpeechRecognition 實例
        this.recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        
        // 設置基本配置
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = 'zh-TW';
        
        // 初始化回調函數
        this.resultCallback = null;
        this.errorCallback = null;
        this.endCallback = null;
        
        // 綁定事件處理
        this.recognition.onresult = (event) => {
            if (event.results.length > 0) {
                const result = event.results[event.results.length - 1];
                if (result.isFinal && this.resultCallback) {
                    this.resultCallback(result[0].transcript);
                }
            }
        };
        
        this.recognition.onerror = (event) => {
            if (this.errorCallback) {
                this.errorCallback(event.error);
            }
        };
        
        this.recognition.onend = () => {
            if (this.endCallback) {
                this.endCallback();
            }
        };
    }
    
    /**
     * 開始語音識別
     */
    start() {
        this.recognition.start();
    }
    
    /**
     * 停止語音識別
     */
    stop() {
        this.recognition.stop();
    }
    
    /**
     * 設置語音識別的語言
     * @param {string} language - 語言代碼，例如 'zh-TW'
     */
    setLanguage(language) {
        this.recognition.lang = language;
    }
    
    /**
     * 設置識別結果回調函數
     * @param {Function} callback - 回調函數，接收識別結果文本
     */
    onResult(callback) {
        this.resultCallback = callback;
    }
    
    /**
     * 設置錯誤回調函數
     * @param {Function} callback - 回調函數，接收錯誤信息
     */
    onError(callback) {
        this.errorCallback = callback;
    }
    
    /**
     * 設置識別結束回調函數
     * @param {Function} callback - 回調函數
     */
    onEnd(callback) {
        this.endCallback = callback;
    }
} 