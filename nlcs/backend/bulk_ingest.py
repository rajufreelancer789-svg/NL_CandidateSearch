# Bulk ingestion from Kaggle resume dataset
# Selects 150 PDFs across 24 categories and ingests them

import os
import sys
from pathlib import Path
import random
import time

# Handle import paths
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from database import SessionLocal
from ingest import ingest_resume

# Kaggle dataset path
DATASET_PATH = "/Users/appalaraju/.cache/kagglehub/datasets/snehaanbhawal/resume-dataset/versions/1/data/data"
UPLOADS_FOLDER = Path(__file__).parent.parent / "uploads"

def select_pdfs_by_category(dataset_path: str, pdfs_per_category: int = 6):
    """
    Select PDFs from dataset
    Max N PDFs per category, aim for ~150 total
    
    Args:
        dataset_path: Path to dataset
        pdfs_per_category: Max PDFs to select per category
    
    Returns:
        Dict mapping category → list of PDF paths
    """
    selected = {}
    dataset_path_obj = Path(dataset_path)
    
    if not dataset_path_obj.exists():
        print(f"❌ Dataset path not found: {dataset_path}")
        return {}
    
    categories = [d for d in dataset_path_obj.iterdir() if d.is_dir()]
    print(f"📂 Found {len(categories)} categories")
    
    total_selected = 0
    for category_dir in sorted(categories):
        category_name = category_dir.name
        pdfs = list(category_dir.glob("*.pdf"))
        
        # Random sample
        if len(pdfs) > pdfs_per_category:
            selected_pdfs = random.sample(pdfs, pdfs_per_category)
        else:
            selected_pdfs = pdfs
        
        selected[category_name] = [str(p) for p in selected_pdfs]
        total_selected += len(selected_pdfs)
        
        print(f"  {category_name}: {len(selected_pdfs)} PDFs")
    
    print(f"\n📊 Total selected: {total_selected} PDFs across {len(selected)} categories")
    return selected

def copy_pdfs_to_uploads(selected_pdfs_dict: dict):
    """
    Copy selected PDFs to uploads folder
    
    Args:
        selected_pdfs_dict: Dict of category -> PDF paths
    """
    UPLOADS_FOLDER.mkdir(exist_ok=True)
    
    for category, pdf_paths in selected_pdfs_dict.items():
        for pdf_path in pdf_paths:
            try:
                src = Path(pdf_path)
                dst_name = f"{category}_{src.name}"
                dst_path = UPLOADS_FOLDER / dst_name
                
                # Copy
                with open(src, 'rb') as f_in:
                    with open(dst_path, 'wb') as f_out:
                        f_out.write(f_in.read())
            except Exception as e:
                print(f"❌ Copy error: {e}")

def bulk_ingest(dataset_path: str = DATASET_PATH):
    """
    Main bulk ingestion function
    
    Args:
        dataset_path: Path to resume dataset
    """
    print("\n" + "="*60)
    print("🚀 BULK Resume INGESTION - KAGGLE DATASET")
    print("="*60)
    
    # Select PDFs
    selected_pdfs = select_pdfs_by_category(dataset_path, pdfs_per_category=6)
    
    if not selected_pdfs:
        print("❌ No PDFs selected")
        return
    
    # Copy to uploads
    print("\n📋 Copying PDFs to uploads folder...")
    copy_pdfs_to_uploads(selected_pdfs)
    
    # Get all PDFs in uploads folder
    all_pdf_files = list(UPLOADS_FOLDER.glob("*.pdf"))
    print(f"\n📁 Total PDFs in uploads: {len(all_pdf_files)}")
    
    # Ingest each PDF
    db = SessionLocal()
    successful = 0
    failed = 0
    
    print("\n" + "="*60)
    print("🔄 INGESTING RESUMES")
    print("="*60)
    
    for i, pdf_path in enumerate(all_pdf_files, 1):
        try:
            print(f"\n[{i}/{len(all_pdf_files)}] {pdf_path.name}")
            ingest_resume(str(pdf_path), db)
            successful += 1
            print(f"✅ Success!")
            
            # Rate limiting for PageIndex
            time.sleep(2)
            
        except Exception as e:
            failed += 1
            print(f"❌ Failed: {str(e)}")
            continue
    
    db.close()
    
    # Print report
    print("\n" + "="*60)
    print("📊 INGESTION REPORT")
    print("="*60)
    print(f"Total PDFs attempted: {len(all_pdf_files)}")
    print(f"✅ Successfully ingested: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📂 Categories covered: {len(selected_pdfs)}")
    print(f"\n🎉 System ready for search!")

if __name__ == "__main__":
    bulk_ingest()
