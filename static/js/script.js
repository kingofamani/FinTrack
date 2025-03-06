/**
 * FinTrack MVP 主要 JavaScript 文件
 * 處理語音識別和與後端的交互
 */
document.addEventListener('DOMContentLoaded', function() {
    // DOM 元素
    const voiceBtn = document.getElementById('voice-btn');
    const recordingStatus = document.getElementById('recording-status');
    const transcriptionResult = document.getElementById('transcription-result');
    const transcriptionText = document.getElementById('transcription-text');
    const previewType = document.getElementById('preview-type');
    const previewItem = document.getElementById('preview-item');
    const previewCategory = document.getElementById('preview-category');
    const previewAmount = document.getElementById('preview-amount');
    const confirmBtn = document.getElementById('confirm-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    const totalIncome = document.getElementById('total-income');
    const totalExpense = document.getElementById('total-expense');
    const totalSavings = document.getElementById('total-savings');
    const recentTransactions = document.getElementById('recent-transactions');
    const totalPoints = document.getElementById('total-points');
    const streakDays = document.getElementById('streak-days');

    // 當前交易數據
    let currentTransaction = null;
    // 錄音狀態
    let isRecording = false;

    // 初始化語音識別
    let recognizer;
    try {
        recognizer = new WebSpeechRecognizer();
        recognizer.setLanguage('zh-TW');

        // 設置結果回調
        recognizer.onResult(handleSpeechResult);

        // 設置錯誤回調
        recognizer.onError(function(error) {
            recordingStatus.textContent = `錯誤: ${error}`;
            resetRecordingState();
        });

        // 設置結束回調
        recognizer.onEnd(function() {
            // 只有在仍處於錄音狀態時才顯示結束訊息
            // 這樣可以區分手動停止和自動結束
            if (isRecording) {
                recordingStatus.textContent = '語音識別已結束';
                resetRecordingState();
            }
        });
    } catch (error) {
        voiceBtn.disabled = true;
        voiceBtn.textContent = '語音識別不可用';
        recordingStatus.textContent = `錯誤: ${error.message}`;
    }

    // 語音按鈕點擊事件
    voiceBtn.addEventListener('click', function() {
        if (!recognizer) return;
        
        if (!isRecording) {
            // 開始錄音
            startRecording();
        } else {
            // 停止錄音
            stopRecording();
        }
    });

    // 開始錄音
    function startRecording() {
        voiceBtn.textContent = '停止錄音';
        voiceBtn.classList.add('recording');
        recordingStatus.textContent = '請說出交易內容，例如「咖啡 5 元」';
        transcriptionResult.classList.add('hidden');
        isRecording = true;
        recognizer.start();
    }

    // 停止錄音
    function stopRecording() {
        recognizer.stop();
        recordingStatus.textContent = '正在處理語音...';
    }

    // 重置錄音狀態
    function resetRecordingState() {
        voiceBtn.textContent = '開始語音輸入';
        voiceBtn.classList.remove('recording');
        voiceBtn.disabled = false;
        isRecording = false;
    }

    // 確認按鈕點擊事件
    confirmBtn.addEventListener('click', function() {
        if (currentTransaction) {
            saveTransaction(currentTransaction);
        }
    });

    // 取消按鈕點擊事件
    cancelBtn.addEventListener('click', function() {
        transcriptionResult.classList.add('hidden');
        currentTransaction = null;
    });

    // 處理語音識別結果
    function handleSpeechResult(text) {
        transcriptionText.textContent = text;
        
        // 發送到後端進行解析
        fetch('/api/parse', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: text })
        })
        .then(response => response.json())
        .then(data => {
            // 顯示解析結果
            currentTransaction = data;
            previewType.textContent = data.type === 'expense' ? '支出' : '收入';
            previewItem.textContent = data.item;
            previewCategory.textContent = data.category;
            previewAmount.textContent = data.amount;
            
            transcriptionResult.classList.remove('hidden');
        })
        .catch(error => {
            recordingStatus.textContent = `解析錯誤: ${error.message}`;
        });
    }

    // 保存交易
    function saveTransaction(transaction) {
        fetch('/api/record', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(transaction)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                transcriptionResult.classList.add('hidden');
                currentTransaction = null;
                recordingStatus.textContent = '交易已記錄！';
                
                // 更新數據顯示
                fetchData();
            } else {
                recordingStatus.textContent = `錯誤: ${data.message}`;
            }
        })
        .catch(error => {
            recordingStatus.textContent = `保存錯誤: ${error.message}`;
        });
    }

    // 獲取數據並更新 UI
    function fetchData() {
        fetch('/api/data')
        .then(response => response.json())
        .then(data => {
            updateSummary(data.summary);
            updateTransactions(data.transactions);
            updateGamification(data.user);
        })
        .catch(error => {
            console.error('獲取數據錯誤:', error);
        });
    }

    // 更新總覽數據
    function updateSummary(summary) {
        totalIncome.textContent = `${summary.income} 元`;
        totalExpense.textContent = `${summary.expense} 元`;
        totalSavings.textContent = `${summary.savings} 元`;
    }

    // 更新交易列表
    function updateTransactions(transactions) {
        if (transactions.length === 0) {
            recentTransactions.innerHTML = '<p>尚無交易記錄</p>';
            return;
        }

        let html = '';
        // 只顯示最近 5 筆交易
        const recentTrans = transactions.slice(0, 5);
        
        recentTrans.forEach(transaction => {
            const typeClass = transaction.type === 'expense' ? 'expense' : 'income';
            const typeSign = transaction.type === 'expense' ? '-' : '+';
            
            html += `
                <div class="transaction-item">
                    <div>
                        <span class="item-name">${transaction.item}</span>
                        <span class="item-category">${transaction.category}</span>
                    </div>
                    <div class="item-amount ${typeClass}">${typeSign}${transaction.amount} 元</div>
                </div>
            `;
        });
        
        recentTransactions.innerHTML = html;
    }

    // 更新遊戲化數據
    function updateGamification(user) {
        totalPoints.textContent = user.points;
        streakDays.textContent = `${user.streak} 天`;
    }

    // 初始加載數據
    fetchData();
}); 