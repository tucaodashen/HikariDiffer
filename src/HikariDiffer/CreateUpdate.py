import hashlib
import os


def calculate_sha256(file_path):
    # 创建一个 sha256 类型的哈希对象
    sha256_hash = hashlib.sha256()

    try:
        with open(file_path, "rb") as f:
            # 分块读取，每次读取 4096 字节（4KB）
            # 对于超大文件，这种方法非常节省内存
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        # 返回十六进制格式的哈希值
        return sha256_hash.hexdigest()

    except FileNotFoundError:
        return "错误：找不到该文件"

class Comparer:
    def __init__(self,origin : str,history : dict,dest : str):
        self.origin = origin
        self.history = history
        self.dest = dest

        self.all_file_mapping = {}


    def create_origin_mapping(self):
        for dirpath, dirnames, filenames in os.walk(self.origin):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                relative_path = os.path.relpath(file_path, self.origin)
                self.all_file_mapping[relative_path] = calculate_sha256(file_path)

    def make_curd(self):
        new_file_mapping = {}
        decline_file_mapping = {}

        for k, v in self.history.items():
            for dirp, dirn, filenames in os.walk(v):
                # 遍历 filenames 列表中的每一个具体文件名
                for filename in filenames:
                    # 现在的 filename 是字符串了，可以 join
                    file_path = os.path.join(dirp, filename)
                    relative_path = os.path.relpath(file_path, v)

                    if relative_path not in self.all_file_mapping:
                        sha256 = calculate_sha256(file_path)
                        new_file_mapping[relative_path] = sha256
                    else:
                        sha256 = calculate_sha256(file_path)
                        if self.all_file_mapping[relative_path] != sha256:
                            new_file_mapping[relative_path] = sha256
        return new_file_mapping


if __name__ == "__main__":
    comparer = Comparer(r"D:\Project\Python\InvisibleVideoWatermarkNEXT\HikariDiffer\datatottest\origin",{"1":r"D:\Project\Python\InvisibleVideoWatermarkNEXT\HikariDiffer\datatottest\hist1"}, "D:/Project/Python/InvisibleVideoWatermarkNEXT/HikariDiffer/test/dest")
    comparer.create_origin_mapping()
    print(comparer.all_file_mapping)
    print(comparer.make_curd())
