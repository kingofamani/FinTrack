/**
 * SpeechRecognizer 接口
 * 定義語音識別的基本方法和事件處理
 */
class SpeechRecognizer {
    constructor() {
        if (this.constructor === SpeechRecognizer) {
            throw new Error("SpeechRecognizer 是抽象類，不能直接實例化");
        }
    }

    /**
     * 開始語音識別
     */
    start() {
        throw new Error("子類必須實現 start 方法");
    }

    /**
     * 停止語音識別
     */
    stop() {
        throw new Error("子類必須實現 stop 方法");
    }

    /**
     * 設置語音識別的語言
     * @param {string} language - 語言代碼，例如 'zh-TW'
     */
    setLanguage(language) {
        throw new Error("子類必須實現 setLanguage 方法");
    }

    /**
     * 設置識別結果回調函數
     * @param {Function} callback - 回調函數，接收識別結果文本
     */
    onResult(callback) {
        throw new Error("子類必須實現 onResult 方法");
    }

    /**
     * 設置錯誤回調函數
     * @param {Function} callback - 回調函數，接收錯誤信息
     */
    onError(callback) {
        throw new Error("子類必須實現 onError 方法");
    }

    /**
     * 設置識別結束回調函數
     * @param {Function} callback - 回調函數
     */
    onEnd(callback) {
        throw new Error("子類必須實現 onEnd 方法");
    }
} 