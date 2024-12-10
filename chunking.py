import re


def chunk_text(text, min_words=3000, max_words=3500):
    # If the entire text is smaller than the minimum chunk size, return it as a single chunk
    if len(text.split()) <= min_words:
        return [text]

    chunks = []
    current_chunk = ""
    current_word_count = 0

    # Split the text into paragraphs
    paragraphs = text.split('\n')

    for paragraph in paragraphs:
        words = paragraph.split()
        
        if current_word_count + len(words) <= max_words:
            current_chunk += paragraph + '\n'
            current_word_count += len(words)
        else:
            # If adding this paragraph exceeds max_words, we need to split
            if current_word_count >= min_words:
                # If current chunk is already within range, add it to chunks
                chunks.append(current_chunk.strip())
                current_chunk = paragraph + '\n'
                current_word_count = len(words)
            else:
                # We need to split the paragraph
                remaining_words = max_words - current_word_count
                split_point = remaining_words

                # Look for a period to split on
                for i in range(remaining_words, 0, -1):
                    if paragraph[i] == '.':
                        split_point = i + 1
                        break

                current_chunk += paragraph[:split_point] + '\n'
                chunks.append(current_chunk.strip())

                # Start new chunk with remainder of paragraph
                current_chunk = paragraph[split_point:] + '\n'
                current_word_count = len(paragraph[split_point:].split())

        # Check if we've reached the end of the text
        if current_word_count >= min_words:
            chunks.append(current_chunk.strip())
            current_chunk = ""
            current_word_count = 0

    # Add any remaining text as the last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks