import os
import glob
from markitdown import MarkItDown

source_dir = r"c:\Users\Joe，\OneDrive\Desktop\dachuang\dachuang\文献\经济研究论文示例"
target_dir = r"c:\Users\Joe，\OneDrive\Desktop\dachuang\dachuang\文献\md格式论文副本\经济研究"

os.makedirs(target_dir, exist_ok=True)

md = MarkItDown()

pdf_files = glob.glob(os.path.join(source_dir, "*.pdf"))
print(f"Found {len(pdf_files)} PDF files to convert.")

for pdf_file in pdf_files:
    filename = os.path.basename(pdf_file)
    name, _ = os.path.splitext(filename)
    md_file = os.path.join(target_dir, f"{name}.md")
    
    if os.path.exists(md_file):
        print(f"Skipping {filename}, already converted.")
        continue
        
    print(f"Converting {filename}...")
    try:
        result = md.convert(pdf_file)
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(result.text_content)
        print(f"Successfully saved to {md_file}")
    except Exception as e:
        print(f"Failed to convert {filename}: {e}")

print("Batch conversion completed.")
