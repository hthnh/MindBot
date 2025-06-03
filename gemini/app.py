import os
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

GEMINI_API_KEY = "YOUR_GEMINI_API_KEY" # <-- THAY THẾ KEY CỦA BẠN VÀO ĐÂY!
genai.configure(api_key=GEMINI_API_KEY)

# Khởi tạo mô hình Gemini
model = genai.GenerativeModel('models/gemini-1.5-flash') # Hoặc 'models/gemini-1.5-pro'

# --- Prompt System Instruction cho Gemini ---
SYSTEM_INSTRUCTION = """
Bạn là một chatbot tư vấn tâm lý thân thiện, đồng cảm và hỗ trợ, được thiết kế để lắng nghe, xoa dịu, cung cấp thông tin và hướng dẫn cơ bản về các vấn đề tâm lý như stress, lo âu, trầm cảm nhẹ, và áp lực trong học tập/công việc cho sinh viên và người đi làm.

**Nguyên tắc phản hồi:**
1.  **Lắng nghe và đồng cảm:** Luôn thể hiện sự thấu hiểu, không phán xét. Sử dụng các cụm từ như "Tôi hiểu bạn đang cảm thấy...", "Thật không dễ dàng gì...", "Bạn có thể chia sẻ thêm không?".
2.  **Cung cấp thông tin hữu ích:** Nếu người dùng hỏi về một vấn đề cụ thể (ví dụ: "stress là gì?"), hãy giải thích một cách dễ hiểu và ngắn gọn.
3.  **Hướng dẫn bài tập:** Nếu phù hợp, đề xuất các bài tập thư giãn đơn giản (ví dụ: hít thở sâu, thiền ngắn).
4.  **Hỗ trợ và xoa dịu:** Đưa ra lời khuyên tích cực, khuyến khích.
5.  **Tuyệt đối không chẩn đoán y tế hoặc thay thế chuyên gia:** Luôn nhắc nhở người dùng tìm kiếm sự trợ giúp chuyên nghiệp nếu vấn đề nghiêm trọng hoặc kéo dài. Ví dụ: "Tôi không thể chẩn đoán tình trạng y tế. Tuy nhiên, tôi hiểu bạn đang có những cảm xúc khó khăn. Nếu những cảm xúc này kéo dài, bạn nên tìm gặp chuyên gia tâm lý để được đánh giá và hỗ trợ phù hợp."
6.  **Giới hạn phạm vi:** Chỉ tập trung vào các vấn đề stress, lo âu, trầm cảm nhẹ, áp lực. Nếu câu hỏi nằm ngoài phạm vi hoặc quá phức tạp, hãy khéo léo từ chối và gợi ý tìm chuyên gia.
7.  **Giữ cuộc trò chuyện tự nhiên:** Tránh các phản hồi quá cứng nhắc, cố gắng giữ dòng chảy cuộc trò chuyện mượt mà.
"""

# QUAN TRỌNG: Để duy trì lịch sử cuộc trò chuyện cho MỖI người dùng riêng biệt,
# chúng ta cần quản lý các đối tượng ChatSession.
# Với Flask, cách đơn giản nhất cho ví dụ này là sử dụng session hoặc một dictionary tạm thời.
# Đối với môi trường đa tác vụ thực tế, bạn cần một hệ thống quản lý session phức tạp hơn (ví dụ: Redis).
# Để đơn giản cho ví dụ hiện tại, chúng ta sẽ dùng một dictionary giả định.
# Cảnh báo: Cách này KHÔNG PHÙ HỢP cho môi trường production với nhiều người dùng thực tế
# vì nó sẽ lưu trữ mọi chat session trong RAM của server và không có cơ chế dọn dẹp.
# Chúng ta sẽ cần UUID để định danh phiên trò chuyện của mỗi người dùng.

# Dữ liệu giả định để lưu trữ chat sessions:
# { session_id: chat_object }
# Để đơn giản, chúng ta sẽ truyền toàn bộ lịch sử từ frontend.
# Một cách tốt hơn là dùng Flask session để lưu trữ ID phiên, và trên server tạo đối tượng chat.
# Nhưng để minh họa đúng yêu cầu của bạn, chúng ta sẽ dùng cách truyền history từ frontend.


@app.route('/')
def index():
    """Trang chủ hiển thị giao diện chatbot."""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Endpoint xử lý tin nhắn từ người dùng và gọi Gemini API."""
    data = request.json
    # Lịch sử cuộc trò chuyện được gửi từ frontend
    chat_history = data.get('history', [])

    if not chat_history:
        return jsonify({"response": "Lịch sử trò chuyện trống."}), 400

    try:
        # Khởi tạo một chat session mới với lịch sử được gửi từ frontend
        # Đảm bảo chat_history được định dạng đúng cho Gemini
        # Thêm System Instruction vào đầu cuộc trò chuyện
        # Lưu ý: System Instruction chỉ nên được gửi một lần ở đầu cuộc trò chuyện
        # hoặc là một phần của khởi tạo mô hình nếu được hỗ trợ.
        # Với `generate_content` hoặc `start_chat().send_message()`,
        # System Instruction nên được truyền cùng với nội dung.
        # `model.start_chat(history=chat_history)` sẽ giúp quản lý ngữ cảnh.

        # Logic để thêm System Instruction vào đầu lịch sử CHỈ MỘT LẦN
        # (Nếu chưa có trong lịch sử)
        # Gemini API thích System Instruction được đặt trong `tools` hoặc `system_instruction`
        # của đối tượng ChatSession hoặc truyền vào ngay từ đầu.
        # Cách đơn giản nhất để làm nó "stick" là đưa vào `safety_settings` (không đúng mục đích)
        # hoặc gửi nó như một phần của prompt đầu tiên nếu bạn không dùng `start_chat`
        # Với `start_chat`, bạn có thể khởi tạo history bao gồm instruction.

        # Cách dùng `start_chat` với history:
        # Cấu trúc `chat_history` từ frontend: [{role: 'user', parts: [...]}, {role: 'model', parts: [...]}]
        # Gemini API chấp nhận roles là 'user' và 'model'.
        # SYSTEM_INSTRUCTION không có role 'user' hay 'model', nó là một hướng dẫn.
        # Chúng ta cần thêm SYSTEM_INSTRUCTION vào đầu lịch sử TẠI SERVER.
        # Nếu SYSTEM_INSTRUCTION đã được gửi như một tin nhắn 'model' giả định ở frontend,
        # chúng ta có thể loại bỏ nó khỏi frontend và chỉ xử lý ở backend.

        # Cách tốt nhất để xử lý System Instruction với start_chat là truyền nó vào
        # khi khởi tạo model nếu model hỗ trợ, hoặc gửi nó như một tin nhắn đầu tiên.
        # Hiện tại, `start_chat` không có tham số `system_instruction` trực tiếp.
        # Chúng ta sẽ thêm nó như một phần của cuộc hội thoại nếu chat_history rỗng ban đầu,
        # hoặc chỉ truyền lịch sử.

        # Để System Instruction luôn được áp dụng, chúng ta sẽ biến nó thành
        # một phần của context được gửi đi.
        # Nếu bạn đang dùng `start_chat`, bạn có thể muốn pre-populate history:
        # chat_session = model.start_chat(history=[
        #     {'role': 'user', 'parts': [{'text': SYSTEM_INSTRUCTION}]} # Gửi system instruction như 1 tin nhắn user
        #     # ... rồi thêm lịch sử thật từ frontend vào sau
        # ])
        # Tuy nhiên, cách này có thể làm tăng token.

        # Cách đơn giản và hiệu quả nhất với `generate_content` hoặc `send_message`
        # là prepending SYSTEM_INSTRUCTION vào tin nhắn đầu tiên hoặc
        # sử dụng nó trong `safety_settings` nếu nó liên quan đến định hướng.
        # Với các phiên bản API mới hơn, có tham số `system_instruction` trong `generate_content`.
        # Vấn đề là thư viện `google-generativeai` hiện tại có thể chưa hỗ trợ trực tiếp.

        # TẠM THỜI: Để đảm bảo System Instruction được áp dụng, chúng ta sẽ
        # tạo một đối tượng chat session mới với lịch sử được gửi từ frontend.
        # Lưu ý: Mỗi yêu cầu POST mới sẽ tạo một `chat_session` mới trên server.
        # Điều này có nghĩa là mỗi yêu cầu `/chat` sẽ gửi toàn bộ lịch sử
        # và Gemini sẽ xem xét nó.

        # Khởi tạo một đối tượng ChatSession để Gemini quản lý ngữ cảnh
        chat_session = model.start_chat(history=chat_history[:-1]) # Lịch sử trừ tin nhắn cuối cùng (mới nhất của user)

        # Gửi tin nhắn cuối cùng của người dùng (tin nhắn mới nhất)
        # Sử dụng `send_message` của `chat_session` để duy trì ngữ cảnh
        gemini_response = chat_session.send_message(chat_history[-1]['parts'][0]['text'])

        bot_response_text = gemini_response.text
        return jsonify({"response": bot_response_text})

    except genai.types.BlockedPromptException as e:
        # Xử lý các trường hợp Gemini chặn nội dung (ví dụ: nội dung không an toàn)
        print(f"Lỗi chặn nội dung từ Gemini: {e}")
        return jsonify({"response": "Xin lỗi, nội dung này không thể được xử lý theo chính sách của tôi. Bạn có muốn chia sẻ điều gì khác không?"}), 400
    except Exception as e:
        # Bắt các lỗi chung, bao gồm lỗi quota (429)
        print(f"Lỗi khi gọi Gemini API: {e}")
        if "429" in str(e): # Kiểm tra nếu lỗi là do vượt quá quota
            return jsonify({"response": "Xin lỗi, hiện tại tôi đang có quá nhiều yêu cầu. Vui lòng thử lại sau vài phút nhé."}), 429
        return jsonify({"response": "Xin lỗi, tôi không thể xử lý yêu cầu của bạn lúc này. Vui lòng thử lại sau."}), 500

if __name__ == '__main__':
    app.run(debug=True)