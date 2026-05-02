from .base_gen import BaseGenerator

class ItemGenerator(BaseGenerator):
    def generate_index(self, items: list):
        """item/index.html を生成"""
        pass

    def generate_details(self, items):
        # templates/item_detail.j2 を読み込む
        template = self.env.get_template("item_detail.j2")
        
        for item in items:
            # 出力先の決定 (例: dist/item/SwordIron.html)
            output_path = os.path.join(self.output_root, "item", f"{item.id}.html")
            self.ensure_dir(os.path.dirname(output_path))

            # HTMLの書き出し
            # root_pathは、一つ上の階層に戻るための相対パス (../)
            html_content = template.render(
                item=item, 
                root_path="../",
                title=f"Item: {item.name}"
            )
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)