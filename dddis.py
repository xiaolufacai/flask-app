import dis
import marshal
import os

# pyc 文件路径
pyc_path = os.path.join(".", "app", "services", "__pycache__", "snap_service.cpython-311.pyc")

# 1. 打开 pyc 文件
with open(pyc_path, "rb") as f:
    f.read(16)  # 跳过前 16 个字节（pyc 文件头）
    code_obj = marshal.load(f)  # 读取顶级 code 对象

# 2. 打印顶级字节码指令
print("=== 顶级指令 ===")
dis.dis(code_obj)

# 3. 打印所有函数内部指令
print("\n=== 函数内部指令 ===")
for const in code_obj.co_consts:
    if isinstance(const, type(code_obj)):
        print(f"\nFunction: {const.co_name}")
        dis.dis(const)
