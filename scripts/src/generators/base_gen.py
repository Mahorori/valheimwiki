import os

class BaseGenerator:
    def __init__(self, template_env, output_root: str):
        self.env = template_env
        self.output_root = output_root

    def render_to_file(self, template_name: str, output_path: str, context: dict):
        """テンプレートとデータを合成してファイルに書き出す共通処理"""
        pass

    def ensure_dir(self, path: str):
        """出力先ディレクトリが存在することを確認する"""
        pass