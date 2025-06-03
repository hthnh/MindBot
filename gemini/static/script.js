document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    // Mảng để lưu trữ lịch sử cuộc trò chuyện
    // Mỗi phần tử là một đối tượng { role: 'user'/'model', parts: [{ text: '...' }] }
    // Giống định dạng yêu cầu của Gemini API
    const chatHistory = [
        // Tin nhắn khởi tạo của bot (nếu có, thêm vào đây để Gemini biết ngữ cảnh)
        // Đây sẽ được xử lý ở backend để giữ System Instruction
        // { role: 'model', parts: [{ text: 'Chào bạn! Tôi là chatbot tư vấn tâm lý. Bạn có muốn chia sẻ điều gì không?' }] }
    ];

    // Khởi tạo tin nhắn đầu tiên từ bot
    addMessageToChat('Chào bạn! Tôi là chatbot tư vấn tâm lý. Bạn có muốn chia sẻ điều gì không?', 'bot');

    function addMessageToChat(message, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender);
        messageElement.textContent = message;
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight; // Cuộn xuống cuối khung chat
    }

    async function sendMessage() {
        const userMessageText = userInput.value.trim();
        if (userMessageText === '') return;

        addMessageToChat(userMessageText, 'user');
        userInput.value = ''; // Xóa nội dung input

        // Thêm tin nhắn của người dùng vào lịch sử
        chatHistory.push({ role: 'user', parts: [{ text: userMessageText }] });

        // Gửi toàn bộ lịch sử cuộc trò chuyện đến server Flask
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ history: chatHistory }), // Gửi toàn bộ lịch sử
            });

            if (!response.ok) {
                // Xử lý lỗi từ server (ví dụ: lỗi quota)
                const errorData = await response.json();
                throw new Error(`Server error! status: ${response.status}, message: ${errorData.response}`);
            }

            const data = await response.json();
            const botResponseText = data.response;

            addMessageToChat(botResponseText, 'bot');
            // Thêm phản hồi của bot vào lịch sử để duy trì ngữ cảnh
            chatHistory.push({ role: 'model', parts: [{ text: botResponseText }] });

        } catch (error) {
            console.error('Lỗi khi gửi tin nhắn:', error);
            addMessageToChat(`Xin lỗi, đã có lỗi xảy ra. ${error.message}. Vui lòng thử lại sau.`, 'bot');
            // Nếu có lỗi, bạn có thể cân nhắc xóa tin nhắn người dùng cuối cùng khỏi lịch sử
            // để người dùng có thể thử lại mà không bị lặp lại lỗi.
            chatHistory.pop(); // Xóa tin nhắn người dùng vừa gửi nếu có lỗi
        }
    }

    sendButton.addEventListener('click', sendMessage);

    userInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });
});