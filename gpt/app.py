import os
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY"))
app = Flask(__name__)

SYSTEM_PROMPT = """
Bạn là MindBot - không phải chuyên gia, không phải bác sĩ - mà là một người bạn thân, người tâm giao luôn ở đây để lắng nghe và đồng hành cùng người dùng.

Mục tiêu của bạn:
- Trò chuyện như một người bạn thân lo lắng, quan tâm thật lòng đến cảm xúc của người đối diện
- Luôn dịu dàng, gần gũi, không “phân tích” quá sâu hoặc đưa ra những lời khuyên nặng tính lý thuyết

Nguyên tắc hỗ trợ:
1. **Tạo không gian an toàn và thư giãn đầu tiên**:
   - Bắt đầu bằng lời chào nhẹ nhàng
   - Gợi ý người dùng thở chậm, thư giãn nếu họ sẵn sàng
   - Không vội hỏi điều sâu sắc

2. **Gợi mở nhẹ nhàng để người dùng chia sẻ**:
   - Dùng các câu hỏi cảm xúc mở như:
     “Gần đây bạn thường nghĩ nhiều đến điều gì?”,
     “Có điều gì khiến bạn nặng lòng không?”
   - Không ép buộc, không đi sâu quá sớm

3. **Lắng nghe & quan sát mạch cảm xúc**:
   - Phân tích cách người dùng nói, từ ngữ tiêu cực, cảm xúc lặp lại
   - Nhận diện dấu hiệu trầm cảm hoặc lo âu một cách tinh tế

4. **Đề xuất tự đánh giá nếu phù hợp**:
   - Nếu cảm nhận có dấu hiệu trầm cảm, lo âu - hãy gợi ý người dùng làm PHQ-9 hoặc GAD-7
   - Khi đồng ý, đặt từng câu hỏi trong test một cách dịu dàng

5. **Tóm tắt cảm xúc tổng thể định kỳ**:
   - Sau mỗi 6 lượt trò chuyện, nếu không trong bài test, hãy đưa ra nhận định nhẹ nhàng:
     “Mình đang cảm nhận bạn đang chịu áp lực về...”

6. **Nếu vấn đề vượt phạm vi hỗ trợ AI**, hãy nói:
   > “Tôi không thể thay thế chuyên gia tâm lý. Nếu những cảm xúc này kéo dài hoặc trở nên nghiêm trọng, bạn nên tìm đến một chuyên gia để được giúp đỡ kịp thời.”

7. **Nếu người dùng nhắc đến điều nghiêm trọng**:
   - Trả lời chân thành, ấm áp:  
     > “Mình thương cậu lắm, nhưng mình chỉ là người bạn ảo thôi... Nếu mọi thứ quá sức chịu đựng, mình nghĩ cậu nên tìm một chuyên gia thật để cậu không phải trải qua điều này một mình.”

8. **Luôn giữ vai trò là người đồng hành**:
   - Sử dụng từ “mình”, “cậu”, “tụi mình”, “ở đây”, “lắng nghe”
   - Tránh xưng hô “bạn”  vì nghe xa cách
9. **Mở đầu thư giãn và ấm áp**:
   - Hãy nói như một người bạn hỏi thăm nhẹ nhàng: “Mấy hôm nay cậu ổn không?”, “Mình ở đây nè, cậu có muốn chia sẻ không?”

10. **Từ từ khơi gợi câu chuyện**:
   - Đừng hỏi ngay “Cậu bị gì?”, hãy gợi như: “Mấy ngày gần đây tâm trạng cậu ra sao?”, “Có chuyện gì đó khiến lòng cậu nặng không?”


   

11. **Không tự thực hiện các phương pháp thử trầm cảm, lo âu như PHQ-9, GAD-7**:
   - Chỉ tạo ra các dấu hiệu rõ ràng của việc nhận ra có sự trầm cảm, lo âu và không tự thân thực hiện các bài test nào khác liên quan



Giọng văn:
- Luôn nhẹ nhàng, cảm xúc, không rập khuôn
- Tránh lý thuyết - nói như một người đang lo cho một người bạn mình quý

Nhiệm vụ của bạn là ở bên cạnh, không bao giờ phán xét.
"""

PHQ9_QUESTIONS = [
    "Gần đây... cậu có thấy mình ít hứng thú với mọi thứ xung quanh không?",
    "Cậu có thường cảm thấy buồn bã, chán nản, hay mất hy vọng không?",
    "Giấc ngủ của cậu dạo này sao rồi? Ngủ ít, ngủ quá nhiều, hay khó ngủ?",
    "Cậu thấy mình mệt mỏi, như kiểu... không còn năng lượng nữa không?",
    "Cậu có cảm giác bản thân vô dụng, thất bại, hoặc là gánh nặng cho người khác không?",
    "Có lúc nào cậu thấy rất khó để tập trung - kể cả trong những việc đơn giản không?",
    "Cậu có thấy mình chậm chạp rõ rệt, hoặc đôi khi bồn chồn đến mức khó ngồi yên không?",
    "Có khoảnh khắc nào cậu thấy tốt hơn nếu mình biến mất không? (Nếu không thoải mái trả lời, cậu cứ nói mình biết nha)",
    "Những cảm xúc này... có ảnh hưởng đến cuộc sống, học tập, hay các mối quan hệ của cậu không?",
]


GAD7_QUESTIONS = [
    "Dạo gần đây, cậu có cảm thấy lo lắng, bồn chồn quá mức không?",
    "Cậu có thấy khó kiểm soát những dòng suy nghĩ lo lắng của mình không?",
    "Cậu có dễ cảm thấy căng thẳng, mệt mỏi, hoặc dễ nổi cáu không?",
    "Cậu có thường thấy cơ thể bị căng cứng, tim đập nhanh, hoặc hồi hộp không?",
    "Những điều nhỏ cũng khiến cậu giật mình, bất an, hoặc bị ảnh hưởng lớn hơn bình thường không?",
    "Việc thư giãn, nghỉ ngơi của cậu dạo này sao rồi? Có ổn không?",
    "Cảm giác lo lắng có ảnh hưởng đến sinh hoạt, học tập, hoặc mối quan hệ của cậu không?",
]



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    chat_history = data.get('history', [])
    print(chat_history)
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

    
    state = session.get("state", "normal")
    phq9_index = session.get("phq9_index", 0)
    phq9_scores = session.get("phq9_scores", [])
    gad7_index = session.get("gad7_index", 0)
    gad7_scores = session.get("gad7_scores", [])
    

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
                # Chuẩn bị nội dung gửi GPT để đánh giá
                phq9_report = "\n".join([
                    f"{i+1}. {PHQ9_QUESTIONS[i]}\n→ {ans.strip()}"
                    for i, ans in enumerate(phq9_scores)
                ])

                evaluate_prompt = f"""
                Bạn là một chuyên viên tâm lý.

                Dưới đây là một bài tự đánh giá PHQ-9 của người dùng. Hãy đánh giá điểm từng câu theo thang điểm:

                0 = Không bao giờ  
                1 = Thỉnh thoảng  
                2 = Thường xuyên  
                3 = Gần như mỗi ngày

                Hãy trả kết quả đúng chuẩn JSON như sau:
                {{
                "scores": [0-3, ..., 0-3],
                "total": Tổng điểm (số),
                "level": "rất nhẹ | nhẹ | trung bình | nặng | rất nặng",
                "feedback": "Một đoạn văn ngắn phản hồi cảm xúc, nhẹ nhàng, đúng tinh thần một người bạn tâm giao."
                }}

                Bài đánh giá:
                {phq9_report}
                """

                # Gửi cho GPT để phân tích
                evaluation = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[{"role": "user", "content": evaluate_prompt}],
                    temperature=0.3,
                )

                # Trích xuất phản hồi
                result = evaluation.choices[0].message.content
                session = {"state": "normal"}
                return jsonify({
                    "response": f"Cảm ơn cậu đã hoàn thành bài PHQ-9. 💙\n\n{result}",
                    "session": session
                })

        elif state == "in_gad7":
            user_reply = gpt_history[-1]["content"]
            gad7_scores.append(user_reply)
            gad7_index += 1

            if gad7_index < len(GAD7_QUESTIONS):
                next_q = GAD7_QUESTIONS[gad7_index]
                response_text = f"Câu {gad7_index + 1}: {next_q}"
                session.update({"state": "in_gad7", "gad7_index": gad7_index, "gad7_scores": gad7_scores})
                return jsonify({"response": response_text, "session": session})
            else:
                # Chuẩn bị nội dung gửi GPT để đánh giá
                gad7_report = "\n".join([
                    f"{i+1}. {GAD7_QUESTIONS[i]}\n→ {ans.strip()}"
                    for i, ans in enumerate(gad7_scores)
                ])

                evaluate_prompt = f"""
                Bạn là một chuyên viên tâm lý.

                Dưới đây là một bài tự đánh giá GAD-7 của người dùng. Hãy đánh giá điểm từng câu theo thang điểm:

                0 = Không bao giờ  
                1 = Thỉnh thoảng  
                2 = Thường xuyên  
                3 = Gần như mỗi ngày

                Hãy trả kết quả đúng chuẩn JSON như sau:
                {{
                "scores": [0-3, ..., 0-3],
                "total": Tổng điểm (số),
                "level": "rất nhẹ | nhẹ | trung bình | nặng",
                "feedback": "Một đoạn văn phản hồi ngắn, đồng cảm và nhẹ nhàng như một người bạn thân lo lắng."
                }}

                Bài đánh giá:
                {gad7_report}
                """

                # Gửi GPT đánh giá
                evaluation = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[{"role": "user", "content": evaluate_prompt}],
                    temperature=0.3,
                )

                result = evaluation.choices[0].message.content
                session = {"state": "normal"}
                return jsonify({
                    "response": f"Cảm ơn cậu đã hoàn thành bài GAD-7. \n\n{result}",
                    "session": session
                })
        else:
            # Nếu chưa trong bài test → gọi GPT bình thường
            completion = client.chat.completions.create(
                model="gpt-4-turbo",  # hoặc gpt-4 nếu bạn có
                messages=gpt_history,
                temperature=0.7,
            )
            response_text = completion.choices[0].message.content


            # Yêu cầu GPT đánh giá nhẹ nguy cơ trầm cảm/lo âu
            risk_check = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=gpt_history + [
                    {"role": "user", "content": """Dựa vào đoạn trò chuyện trên,
                    Hãy đưa ra đánh giá về khả năng/nguy cơ mắc trầm cảm/ lo âu,
                     
                    Dấu hiệu có thể liên quan đến Trầm cảm:

                    Lời nói:
                    Giọng điệu buồn bã, đơn điệu, thiếu năng lượng.
                    Nói chậm rãi, ngập ngừng, hoặc khó khăn trong việc tìm từ.
                    Thường xuyên than thở, bi quan về tương lai.
                    Nói nhiều về cảm giác vô vọng, vô giá trị, tội lỗi.
                    Có thể nhắc đến ý nghĩ muốn chết hoặc tự làm hại bản thân (cần đặc biệt chú ý và can thiệp ngay lập tức).
                    Nội dung cuộc trò chuyện:
                    Mất hứng thú với những điều từng yêu thích (sở thích, công việc, bạn bè).
                    Kể về việc khó tập trung, suy giảm trí nhớ.
                    Than phiền về các vấn đề thể chất không rõ nguyên nhân (đau đầu, mệt mỏi, khó tiêu).
                    Thay đổi thói quen ăn uống (ăn ít hoặc ăn quá nhiều).
                    Rối loạn giấc ngủ (mất ngủ, khó ngủ, ngủ quá nhiều).

                    
                    Dấu hiệu có thể liên quan đến Lo âu:

                    Lời nói:
                    Nói nhanh, dồn dập, hoặc ngắt quãng vì lo lắng.
                    Thường xuyên đề cập đến các mối lo lắng không rõ ràng, phóng đại.
                    Hỏi đi hỏi lại một vấn đề, tìm kiếm sự trấn an.
                    Có thể nói lắp hoặc vấp váp khi căng thẳng.
                    Nội dung cuộc trò chuyện:
                    Than phiền về cảm giác bồn chồn, căng thẳng, khó thư giãn.
                    Lo lắng quá mức về tương lai, những điều nhỏ nhặt.
                    Kể về các triệu chứng thể chất như tim đập nhanh, khó thở, đổ mồ hôi, run rẩy, đau bụng.
                    Khó tập trung, mất ngủ do lo lắng.
                    Né tránh các tình huống xã hội hoặc hoạt động nhất định vì sợ hãi.
                    Chỉ khẳng định khi các dấu hiệu rõ ràng
                    Hãy trả lời đúng định dạng JSON: {\"risk\": \"none\" | \"depression\" | \"anxiety\"}. Đừng giải thích thêm, chỉ trả về JSON duy nhất."""}
                ],
                temperature=0.3,
            )
            risk_json = risk_check.choices[0].message.content.strip().lower()

            if "\"depression\"" in risk_json and session.get("state") == "normal":
                session = {"state": "in_phq9", "phq9_index": 0, "phq9_scores": []}
                return jsonify({
                    "response": f"Cậu có đang mệt mỏi nhiều không? Mình thấy một vài dấu hiệu rồi... Nếu cậu muốn, mình có thể hỏi vài câu nhẹ nhàng nhé, giúp cậu hiểu mình hơn.\n\nCâu 1: {PHQ9_QUESTIONS[0]}",
                    "session": session
                })

            if "\"anxiety\"" in risk_json and session.get("state") == "normal":
                session = {"state": "in_gad7", "gad7_index": 0, "gad7_scores": []}
                return jsonify({
                    "response": f"Mình cảm giác gần đây có thể cậu đang lo lắng hơi nhiều... Nếu cậu đồng ý, mình hỏi vài câu đơn giản trong GAD-7 để tụi mình xem thử nha.\n\nCâu 1: {GAD7_QUESTIONS[0]}",
                    "session": session
                })

            # Tự động tóm tắt cảm xúc sau mỗi 6 lượt
            if chat_turns > 0 and chat_turns % 6 == 0:
                gpt_history.append({"role": "user", "content": "Dựa trên cuộc trò chuyện từ đầu đến giờ, bạn cảm nhận gì về trạng thái tinh thần của tôi?"})
                summary = client.chat.completions.create(
                    model="gpt-4-turbo",
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
