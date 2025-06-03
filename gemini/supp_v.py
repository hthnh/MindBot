import google.generativeai as genai
import os

# Đảm bảo bạn đã cấu hình API Key của mình
# Tạm thời để ở đây để kiểm tra, nhưng hãy nhớ bảo mật sau này
GEMINI_API_KEY = "" # <-- THAY THẾ KEY CỦA BẠN VÀO ĐÂY!
genai.configure(api_key=GEMINI_API_KEY)

print("Các mô hình khả dụng:")
for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(m.name)