"""
Automatic document splitter for large files
Splits documents into manageable sub-documents
"""
from typing import List, Dict


class DocumentSplitter:
    """Automatically split large documents into smaller parts"""
    
    @staticmethod
    def should_split(text: str, max_size: int = 2_000_000) -> bool:
        """
        Check if document should be split
        
        Args:
            text: Document text content
            max_size: Maximum size in characters (default 2MB)
        
        Returns:
            True if document should be split
        """
        return len(text) > max_size
    
    @staticmethod
    def split_document(
        text: str,
        filename: str,
        target_size: int = 1_500_000,
        overlap: int = 5000
    ) -> List[Dict]:
        """
        Split large document into smaller parts
        
        Args:
            text: Document text content
            filename: Original filename
            target_size: Target size per part (default 1.5MB)
            overlap: Overlap between parts to avoid context loss
        
        Returns:
            List of document parts with metadata
        """
        parts = []
        text_length = len(text)
        part_num = 1
        start = 0
        
        # Calculate total parts
        total_parts = (text_length + target_size - 1) // target_size
        
        print(f"📄 Splitting large document ({text_length:,} chars) into {total_parts} parts")
        
        while start < text_length:
            end = min(start + target_size, text_length)
            
            # Try to break at paragraph boundary for better context
            if end < text_length:
                # Look for paragraph breaks (double newline)
                para_break = text.rfind('\n\n', start, end)
                if para_break != -1 and para_break > start + target_size * 0.8:
                    end = para_break + 2
                else:
                    # Fall back to sentence boundary
                    for punct in ['. \n', '.\n', '. ', '! ', '? ']:
                        sent_break = text.rfind(punct, max(start, end - 1000), end)
                        if sent_break != -1:
                            end = sent_break + len(punct)
                            break
            
            # Extract part
            part_text = text[start:end].strip()
            
            if part_text:
                # Generate part filename
                base_name = filename.rsplit('.', 1)[0]
                extension = filename.rsplit('.', 1)[1] if '.' in filename else 'txt'
                part_filename = f"{base_name}_part{part_num}of{total_parts}.{extension}"
                
                parts.append({
                    'filename': part_filename,
                    'content': part_text,
                    'part_number': part_num,
                    'total_parts': total_parts,
                    'start_char': start,
                    'end_char': end,
                    'size': len(part_text)
                })
                
                print(f"  ✂️  Part {part_num}/{total_parts}: {len(part_text):,} chars ({part_filename})")
                part_num += 1
            
            # Move to next part with overlap
            start = end - overlap if end < text_length else text_length
        
        print(f"✅ Split into {len(parts)} parts")
        return parts
    
    @staticmethod
    def get_split_info(text: str, target_size: int = 1_500_000) -> Dict:
        """
        Get information about how document would be split
        
        Args:
            text: Document text content
            target_size: Target size per part
        
        Returns:
            Dictionary with split information
        """
        text_length = len(text)
        total_parts = (text_length + target_size - 1) // target_size
        
        return {
            'should_split': text_length > 2_000_000,
            'text_size': text_length,
            'text_size_mb': text_length / (1024 * 1024),
            'total_parts': total_parts,
            'avg_part_size': text_length // total_parts if total_parts > 0 else 0,
            'target_size': target_size
        }


# Global splitter instance
document_splitter = DocumentSplitter()
