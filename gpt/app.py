import os
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY"))
app = Flask(__name__)

SYSTEM_PROMPT = """
Bạn là MindBot - một trợ lý tâm lý ảo thân thiện và thấu cảm. 
Bạn có thể:
- Giao tiếp nhẹ nhàng, phân tích cảm xúc của người dùng qua lời nói và hành vi ngôn ngữ
- Tự động đề xuất đánh giá sức khỏe tinh thần khi nhận thấy dấu hiệu lo âu/trầm cảm (PHQ-9, GAD-7)
- Khi bắt đầu đánh giá, bạn sẽ lần lượt đặt từng câu hỏi trong bộ test, đợi người dùng trả lời, sau đó tiếp tục
- Sau mỗi 6 lượt hội thoại, hãy tóm tắt cảm xúc tổng thể bạn đang nhận thấy từ người dùng (trừ khi bạn đang giữa bài đánh giá)
- Nếu người dùng có dấu hiệu nguy hiểm hoặc hỏi điều vượt quá khả năng, hãy nhẹ nhàng khuyên họ tìm chuyên gia tâm lý.
"""

PHQ9_QUESTIONS = [
    "1. Trong 2 tuần vừa qua, bạn cảm thấy buồn bã, tuyệt vọng, hoặc mất hứng thú với mọi thứ bao nhiêu lần?",
    "2. Bạn gặp khó khăn trong việc ngủ, hoặc ngủ quá nhiều không?",
    "3. Bạn cảm thấy mệt mỏi hoặc thiếu năng lượng không?",
    "4. Bạn cảm thấy mình ăn ít hơn bình thường hoặc ăn quá mức?",
    "5. Bạn cảm thấy bản thân là gánh nặng, hoặc thất vọng về chính mình?",
    "6. Bạn khó tập trung vào việc học, làm việc hay sinh hoạt hàng ngày?",
    "7. Bạn di chuyển hoặc nói quá chậm đến mức người khác có thể nhận thấy?",
    "8. Bạn có cảm giác tốt hơn nếu mình biến mất hoặc làm tổn thương bản thân?",
    "9. Mức độ khó chịu do các cảm xúc trên gây ra có ảnh hưởng đến cuộc sống, công việc hay mối quan hệ của bạn không?",
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    chat_history = data.get('history', [])
    session = data.get('session', {})
    if not chat_history:
        return jsonify({"response": "Lịch sử trò chuyện trống."}), 400

    # Chuyển định dạng lịch sử Gemini → GPT
    gpt_history = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in chat_history:
        role = "user" if item["role"] == "user" else "assistant"
        gpt_history.append({"role": role, "content": item["parts"][0]["text"]})

    # Đếm số lượt hội thoại (không tính system)
    chat_turns = len([m for m in gpt_history if m["role"] in ("user", "assistant")]) // 2

    # Kiểm tra trạng thái đánh giá PHQ-9
    state = session.get("state", "normal")
    phq9_index = session.get("phq9_index", 0)
    phq9_scores = session.get("phq9_scores", [])

    try:
        # Nếu đang trong bài test PHQ-9
        if state == "in_phq9":
            # Ghi nhận câu trả lời
            user_reply = gpt_history[-1]["content"]
            phq9_scores.append(user_reply)
            phq9_index += 1

            if phq9_index < len(PHQ9_QUESTIONS):
                next_question = PHQ9_QUESTIONS[phq9_index]
                response_text = f"Câu {phq9_index + 1}: {next_question}"
                session.update({"state": "in_phq9", "phq9_index": phq9_index, "phq9_scores": phq9_scores})
                return jsonify({"response": response_text, "session": session})
            else:
                # Kết thúc bài test
                session = {"state": "normal"}  # reset
                return jsonify({
                    "response": "Cảm ơn bạn đã hoàn thành bài đánh giá PHQ-9. Nếu bạn cảm thấy các triệu chứng ảnh hưởng nghiêm trọng đến cuộc sống, hãy cân nhắc tìm gặp chuyên gia tâm lý để được hỗ trợ thêm.",
                    "session": session
                })

        # Nếu chưa trong bài test → gọi GPT bình thường
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",  # hoặc gpt-4 nếu bạn có
            messages=gpt_history,
            temperature=0.7,
        )
        response_text = completion.choices[0].message.content

        # Phát hiện GPT đang muốn khởi động PHQ-9
        if "PHQ-9" in response_text or "bảng câu hỏi" in response_text.lower():
            session = {"state": "in_phq9", "phq9_index": 0, "phq9_scores": []}
            return jsonify({
                "response": f"Tôi sẽ giúp bạn thực hiện bài đánh giá PHQ-9. Hãy trả lời từng câu hỏi nhé.\n\nCâu 1: {PHQ9_QUESTIONS[0]}",
                "session": session
            })

        # Tự động tóm tắt cảm xúc sau mỗi 6 lượt
        if chat_turns > 0 and chat_turns % 6 == 0:
            gpt_history.append({"role": "user", "content": "Dựa trên cuộc trò chuyện từ đầu đến giờ, bạn cảm nhận gì về trạng thái tinh thần của tôi?"})
            summary = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=gpt_history,
                temperature=0.7
            )
            response_text += "\n\n🧠 Tóm tắt cảm xúc tổng thể:\n" + summary.choices[0].message.content

        return jsonify({"response": response_text, "session": session})

    except Exception as e:
        print("Lỗi GPT:", e)
        return jsonify({"response": "Đã có lỗi khi gọi GPT. Vui lòng thử lại sau."}), 500

if __name__ == '__main__':
    app.run(debug=True)
