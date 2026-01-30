import hashlib
import json
import os
import shutil
import uuid
import tempfile
from contextlib import contextmanager

import py7zr

SOP = [
    "check_origin_hash",
    "backup",
    "delete",
    "check_new_hash",
    "apply_update",
]


@contextmanager
def pushd(new_dir):
    """临时切换工作目录的上下文管理器"""
    previous_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(previous_dir)


def compress_to_7z(source_dir, output_file):
    # 先获取输出文件的绝对路径，防止切换目录后找不到保存位置
    output_file_abs = os.path.abspath(output_file)
    source_dir_abs = os.path.abspath(source_dir)

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file_abs), exist_ok=True)

    # 切换到源目录内部执行压缩
    with pushd(source_dir_abs):
        with py7zr.SevenZipFile(output_file_abs, 'w') as archive:
            # 使用 "." 代表当前目录（即 source_dir 内部）
            archive.writeall(".", arcname="")

    print(f"压缩成功，已排除盘符层级：{output_file_abs}")

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
        self.latest = origin
        self.history = history
        self.dest = dest

        self.all_file_mapping = {}
        self.latest_uid_mapping = {}


    def create_origin_mapping(self):
        for dirpath, dirnames, filenames in os.walk(self.latest):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                relative_path = os.path.relpath(file_path, self.latest)
                self.all_file_mapping[relative_path] = calculate_sha256(file_path)
                self.latest_uid_mapping[relative_path] = str(uuid.uuid4())

    def make_curd(self):
        temp_old_mapping = {}

        new_file_mapping = {}
        del_file_mapping = {}

        for k, v in self.history.items():
            curversion = str(k)
            for pth,dirs,files in os.walk(v):
                for filename in files:
                    file_path = os.path.join(pth, filename)
                    relative_path = os.path.relpath(file_path, v)
                    temp_old_mapping[relative_path] = calculate_sha256(file_path)

            for relpath,sha in self.all_file_mapping.items():
                if relpath not in temp_old_mapping.keys():
                    new_file_mapping[relpath] = sha
                else:
                    if temp_old_mapping[relpath] != sha:
                        new_file_mapping[relpath] = sha
                        del_file_mapping[relpath] = temp_old_mapping[relpath]
            for dirp, dirn, filenames in os.walk(v):
                for fi in filenames:
                    filepath = os.path.join(dirp, fi)
                    relative_path = os.path.relpath(filepath, v)
                    if relative_path not in self.all_file_mapping:
                        sha256 = calculate_sha256(filepath)
                        del_file_mapping[relative_path] = sha256
            with tempfile.TemporaryDirectory() as temp_dir:
                print(temp_dir)
                for k,i in new_file_mapping.items():
                    filepath = os.path.join(self.latest,k)
                    shutil.copy2(filepath,os.path.join(temp_dir,self.latest_uid_mapping[k]))
                self.generate_instruction(new_file_mapping,del_file_mapping,temp_dir)
                new_dict = {v: k for k, v in self.latest_uid_mapping.items()}
                with open(os.path.join(temp_dir, "mapping.json"), "w") as f:
                    json.dump(new_dict, f, indent=4)
                with open(os.path.join(temp_dir, "identify.json"), "w") as f:
                    json.dump(curversion, f, indent = 4)
                compress_to_7z(temp_dir, os.path.join(self.dest, f"{curversion}.bundle"))
                print(del_file_mapping,new_file_mapping)







    def construct_plain_folder(self):
        temp_path = f"./temp-{uuid.uuid4()}"
        os.mkdir(temp_path)
        for i,a in self.latest_uid_mapping.items():
            filepath = os.path.join(self.latest,i)
            shutil.copy2(filepath,os.path.join(temp_path,a))



    @staticmethod
    def generate_instruction(new_list,del_list,target):
        with open(os.path.join(target,"new.json"),"w") as f:
            json.dump(new_list,f,indent=4)
        with open(os.path.join(target,"del.json"),"w") as f:
            json.dump(del_list,f,indent=4)
        with open(os.path.join(target,"instruction.json"),"w") as f:
            json.dump(SOP,f,indent=4)




if __name__ == "__main__":
    comparer = Comparer(r"D:\Project\Python\InvisibleVideoWatermarkNEXT\HikariDiffer\datatottest\latest",{"1":r"D:\Project\Python\InvisibleVideoWatermarkNEXT\HikariDiffer\datatottest\v1"}, "D:\Project\Python\InvisibleVideoWatermarkNEXT\HikariDiffer\datatottest")
    comparer.create_origin_mapping()
    print(comparer.all_file_mapping)
    print(comparer.latest_uid_mapping)
    print(comparer.make_curd())
    # comparer.construct_plain_folder()
