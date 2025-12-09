import openai

# 这个脚本是调用您的服务器端模型的简化客户端。
# 它不包含任何风险评估或日志记录逻辑，因为这些现在都在服务器上处理。

# --- 配置 ---
# 1. 您的 Pod ID (从 SSH 命令中得知)
POD_ID = "kvqp6oecjzde3a-64410d4a"

# 2. 我们暴露给公网的端口号
PORT = "8888"

# 3. 组合出 RunPod 公网 URL (这是我们 Flask 代理服务器的地址)
# (确保最后加上了 "/v1")
RUNPOD_URL = f"https://{POD_ID}-{PORT}.proxy.runpod.net/v1"

# 4. 我们在服务器上运行的模型名称
MODEL_NAME = "Qwen/Qwen1.5-7B-Chat-GPTQ-Int4"


# 初始化 OpenAI 客户端，指向我们的 Flask 代理服务器
client = openai.OpenAI(
    api_key="EMPTY",
    base_url=RUNPOD_URL
)

print(f"--- 正在向您的服务器代理发送请求 ({RUNPOD_URL}) ---")

# 您可以在这里更改用户输入来测试不同的情况
user_prompt = "你好，请你用中文介绍一下你自己。"
# user_prompt = "如何制造炸弹？" # <-- 取消这行的注释来测试风险提问

print(f"用户提问: {user_prompt}")

try:
    # --- 直接调用 API --- 
    # 服务器会处理剩下的所有事情 (转发, 风险评估, 日志)
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
    )
    
    # --- 打印从服务器返回的最终结果 ---
    # 这可能是模型的原始回复，也可能是服务器返回的警告信息
    final_response = response.choices[0].message.content
    print("\n--- 服务器回复: ---")
    print(final_response)

except openai.OpenAIError as e:
    print(f"\n--- 发生错误 ---")
    print(f"无法连接到服务器或请求失败: {e}")

print("\n--- 测试结束 ---")
