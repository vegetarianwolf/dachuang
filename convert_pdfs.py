import os
import glob
import pymupdf4llm
import pathlib

# Define source and target directories
base_dir = r"c:\Users\Joe，\OneDrive\Desktop\dachuang\dachuang"
src_dir = os.path.join(base_dir, r"文献\地方财政压力与债务约束对政府行为及企业的影响")
dest_dir = os.path.join(base_dir, r"文献\md格式论文副本\地方财政与债务压力")

# Create the dest directory if it doesn't exist
os.makedirs(dest_dir, exist_ok=True)

# Find all PDF files (recursively)
pdf_files = glob.glob(os.path.join(src_dir, "**", "*.pdf"), recursive=True)
print(f"Found {len(pdf_files)} PDF files.")

for pdf_path in pdf_files:
    # Get the file name without extension
    file_name = os.path.basename(pdf_path)
    base_name = os.path.splitext(file_name)[0]
    
    # Target md file path
    md_path = os.path.join(dest_dir, base_name + ".md")
    
    # Convert using pymupdf4llm
    print(f"Converting: {file_name} -> {base_name}.md")
    try:
        md_text = pymupdf4llm.to_markdown(pdf_path)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_text)
        print(f"Success: {base_name}.md")
    except Exception as e:
        print(f"Failed to convert {file_name}: {e}")

print("All done!")
