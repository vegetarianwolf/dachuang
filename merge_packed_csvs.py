import os
import glob

def merge_csvs_streaming(input_dir, output_file):
    if not os.path.exists(input_dir):
        print(f"Directory {input_dir} not found. Skipping.")
        return
        
    files = glob.glob(os.path.join(input_dir, "*.csv"))
    if not files:
        print(f"No CSVs found in {input_dir}. Skipping.")
        return
        
    print(f"Merging {len(files)} files from {input_dir} -> {output_file}")
    
    total_rows = 0
    header_written = False
    
    with open(output_file, 'w', encoding='utf-8-sig', errors='ignore') as outfile:
        for f in files:
            print(f"  Processing {os.path.basename(f)}...")
            with open(f, 'r', encoding='utf-8-sig', errors='ignore') as infile:
                for i, line in enumerate(infile):
                    if i == 0:
                        if not header_written:
                            outfile.write(line)
                            header_written = True
                    else:
                        outfile.write(line)
                        total_rows += 1
                        
    print(f"Done. Wrote {total_rows} data rows to {output_file}\n")

def main():
    output_dir = "csmar_data_export"
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. SRDI_EntInfo
    info_dir = r"c:\csmardata\1478748526687064064"
    out_info = os.path.join(output_dir, "SRDI_EntInfo_Full.csv")
    merge_csvs_streaming(info_dir, out_info)
    
    # 2. SRDI_EntPatentInfo
    patent_dir = r"c:\csmardata\1478748833051611136"
    out_patent = os.path.join(output_dir, "SRDI_EntPatentInfo_Full.csv")
    merge_csvs_streaming(patent_dir, out_patent)

if __name__ == "__main__":
    main()
