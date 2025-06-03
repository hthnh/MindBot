document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input'); // Đây là textarea
    const sendButton = document.getElementById('send-button');
    const themeToggleButton = document.getElementById('theme-toggle'); // Nút chuyển đổi chủ đề

    const chatHistory = [];
    let sessionS = { "state": "normal" };

    // Khởi tạo tin nhắn đầu tiên từ bot
    // Thêm tin nhắn ban đầu không có hiệu ứng gõ phím (hoặc bạn có thể thêm nếu muốn)
    const initialMessageElement = document.querySelector('.message.initial-message');
    if (initialMessageElement) {
        initialMessageElement.style.opacity = '1'; // Hiển thị ngay
    }
    // Nếu muốn tin nhắn đầu tiên cũng có hiệu ứng gõ, hãy gọi addMessageToChat với nó
    addMessageToChat("Chào bạn, mình là MindBot - một người bạn tâm lý luôn sẵn sàng lắng nghe.\nNếu bạn muốn, chúng ta có thể hít thở nhẹ một chút để thư giãn, rồi mình sẽ cùng trò chuyện nhé.", "bot",true);

    // Hàm thêm tin nhắn vào chatbox với hiệu ứng gõ phím
    function addMessageToChat(message, sender, typeEffect = false) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender);
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight; // Cuộn xuống cuối khung chat

        if (typeEffect) {
            let i = 0;
            // Hàm này sẽ hiển thị từng ký tự một
            const typingInterval = setInterval(() => {
                if (i < message.length) {
                    messageElement.textContent += message.charAt(i);
                    i++;
                    chatBox.scrollTop = chatBox.scrollHeight; // Cuộn xuống mỗi khi thêm ký tự
                } else {
                    clearInterval(typingInterval);
                }
            }, 30); // Tốc độ gõ: 30ms mỗi ký tự
        } else {
            messageElement.textContent = message;
            messageElement.style.opacity = '1'; // Đảm bảo tin nhắn hiện lên ngay lập tức
        }
    }

    // Hàm điều chỉnh chiều cao của textarea
    function autoResizeTextarea() {
        userInput.style.height = 'auto'; // Reset chiều cao về auto để tính toán lại
        userInput.style.height = userInput.scrollHeight + 'px'; // Đặt chiều cao bằng scrollHeight
        chatBox.scrollTop = chatBox.scrollHeight; // Cuộn xuống cuối khung chat khi textarea thay đổi
    }

    // Gán sự kiện input cho textarea để tự động điều chỉnh chiều cao
    userInput.addEventListener('input', autoResizeTextarea);

    // Xử lý chuyển đổi chế độ sáng/tối
    themeToggleButton.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        // Lưu trạng thái vào localStorage để ghi nhớ lựa chọn của người dùng
        if (document.body.classList.contains('dark-mode')) {
            localStorage.setItem('theme', 'dark');
            themeToggleButton.textContent = '☀️'; // Đổi biểu tượng sang mặt trời
        } else {
            localStorage.setItem('theme', 'light');
            themeToggleButton.textContent = '🌙'; // Đổi biểu tượng sang mặt trăng
        }
    });

    // Kiểm tra trạng thái chủ đề đã lưu khi tải trang
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        themeToggleButton.textContent = '☀️';
    } else {
        themeToggleButton.textContent = '🌙';
    }

    async function sendMessage() {
        const userMessageText = userInput.value.trim();
        if (userMessageText === '') return;

        // Thêm tin nhắn người dùng (không có hiệu ứng gõ)
        addMessageToChat(userMessageText, 'user', false); 
        userInput.value = ''; // Xóa nội dung input
        autoResizeTextarea(); // Reset chiều cao textarea

        // Thêm tin nhắn của người dùng vào lịch sử
        chatHistory.push({ role: 'user', parts: [{ text: userMessageText }] });

        // Gửi toàn bộ lịch sử cuộc trò chuyện và biến sessionS hiện tại đến server Flask
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ history: chatHistory, session: sessionS }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`Server error! status: ${response.status}, message: ${errorData.response}`);
            }

            const data = await response.json();
            const botResponseText = data.response;

            if (data.session) {
                sessionS = data.session;
                console.log('Session updated:', sessionS);
            }

            // Thêm phản hồi của bot với hiệu ứng gõ phím
            addMessageToChat(botResponseText, 'bot', true); 
            // Thêm phản hồi của bot vào lịch sử để duy trì ngữ cảnh
            chatHistory.push({ role: 'model', parts: [{ text: botResponseText }] });

        } catch (error) {
            console.error('Lỗi khi gửi tin nhắn:', error);
            addMessageToChat(`Xin lỗi, đã có lỗi xảy ra. ${error.message}. Vui lòng thử lại sau.`, 'bot');
            chatHistory.pop(); // Xóa tin nhắn người dùng vừa gửi nếu có lỗi
        }
    }

    sendButton.addEventListener('click', sendMessage);

    userInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) { // Bấm Enter để gửi, Shift + Enter để xuống dòng
            event.preventDefault(); // Ngăn hành vi mặc định của Enter (tạo dòng mới)
            sendMessage();
        }
    });
});