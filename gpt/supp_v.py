from openai import OpenAI
client = OpenAI(api_key="")  # Dán API key thật vào đây

models = client.models.list()
for model in models.data:
    print(model.id)
