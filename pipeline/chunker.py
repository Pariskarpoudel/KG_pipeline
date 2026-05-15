import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

TARGET_TOKENS = 400
MAX_TOKENS    = 550
MIN_TOKENS    = 50


def _token_count(text: str) -> int:
    return len(text.split())


def _clean(text: str) -> str:
    text = text.replace(" @-@ ", "-")
    text = text.replace(" @,@ ", ",")
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _flush(buffer, title, section_path, chunk_index, chunks):
    if not buffer:
        return chunk_index
    text = _clean(" ".join(buffer))
    if _token_count(text) >= MIN_TOKENS:
        chunks.append({
            "article_title": title,
            "section_path":  section_path,
            "chunk_text":    text,
            "chunk_index":   chunk_index,
            "token_approx":  _token_count(text),
        })
        return chunk_index + 1
    return chunk_index


def _parse_heading(line: str):
    """
    Parse WikiText-103 spaced heading format.
    '= Title ='           → level 1, 'Title'
    '= = Section = ='     → level 2, 'Section'
    '= = = Sub = = ='     → level 3, 'Sub'
    Returns (level, name) or (None, None) if not a heading.
    """
    tokens = line.strip().split()
    if not tokens or tokens[0] != '=':
        return None, None
    # Count leading '=' tokens
    level = 0
    for t in tokens:
        if t == '=':
            level += 1
        else:
            break
    # Must also end with same number of '='
    trailing = 0
    for t in reversed(tokens):
        if t == '=':
            trailing += 1
        else:
            break
    if level != trailing or level == 0:
        return None, None
    # Name is everything between leading and trailing '='
    name_tokens = tokens[level: len(tokens) - trailing]
    if not name_tokens:
        return None, None
    return level, " ".join(name_tokens)


def chunk_article(filepath: str) -> List[Dict]:
    """
    Chunk a WikiText-103 article from a .txt file.
    Use for quick single-article testing.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()
    lines         = raw.splitlines()
    title         = ""
    header_stack  = []
    chunks        = []
    buffer        = []
    buffer_tokens = 0
    chunk_index   = 0

    def get_path():
        return " / ".join(name for _, name in header_stack) or "Introduction"

    for line in lines:
        line = line.strip()
        if not line:
            continue
        level, name = _parse_heading(line)
        if level is not None:
            chunk_index = _flush(buffer, title, get_path(), chunk_index, chunks)
            buffer, buffer_tokens = [], 0
            if level == 1:
                title = name
                header_stack = []
            else:
                while header_stack and header_stack[-1][0] >= level:
                    header_stack.pop()
                header_stack.append((level, name))
            continue
        # Regular text
        para_tokens = _token_count(line)
        if buffer_tokens + para_tokens > MAX_TOKENS:
            chunk_index = _flush(buffer, title, get_path(), chunk_index, chunks)
            buffer, buffer_tokens = [], 0
        # Single paragraph too long → split at sentence level
        if para_tokens > MAX_TOKENS:
            sentences = re.split(r'(?<=[.!?])\s+', line)
            sub_buffer, sub_tokens = [], 0
            for sent in sentences:
                st = _token_count(sent)
                if sub_tokens + st > MAX_TOKENS:
                    chunk_index = _flush(sub_buffer, title, get_path(), chunk_index, chunks)
                    sub_buffer, sub_tokens = [], 0
                sub_buffer.append(sent)
                sub_tokens += st
            chunk_index = _flush(sub_buffer, title, get_path(), chunk_index, chunks)
            continue
        buffer.append(line)
        buffer_tokens += para_tokens
    _flush(buffer, title, get_path(), chunk_index, chunks)
    logger.info(f"'{title}' → {len(chunks)} chunks")
    return chunks


def chunk_wiki_record(record: dict) -> List[Dict]:
    """
    Chunk a WikiGraphs JSONL record.
    Record keys: id, title, text.
    """
    title         = record["title"]
    lines         = record["text"].splitlines()
    header_stack  = []
    chunks        = []
    buffer        = []
    buffer_tokens = 0
    chunk_index   = 0

    def get_path():
        return " / ".join(name for _, name in header_stack) or "Introduction"

    for line in lines:
        line = line.strip()
        if not line:
            continue
        level, name = _parse_heading(line)
        if level is not None:
            chunk_index = _flush(buffer, title, get_path(), chunk_index, chunks)
            buffer, buffer_tokens = [], 0
            if level == 1:
                header_stack = []
            else:
                while header_stack and header_stack[-1][0] >= level:
                    header_stack.pop()
                header_stack.append((level, name))
            continue
        # Regular text
        para_tokens = _token_count(line)
        if buffer_tokens + para_tokens > MAX_TOKENS:
            chunk_index = _flush(buffer, title, get_path(), chunk_index, chunks)
            buffer, buffer_tokens = [], 0
        # Single paragraph too long → split at sentence level
        if para_tokens > MAX_TOKENS:
            sentences = re.split(r'(?<=[.!?])\s+', line)
            sub_buffer, sub_tokens = [], 0
            for sent in sentences:
                st = _token_count(sent)
                if sub_tokens + st > MAX_TOKENS:
                    chunk_index = _flush(sub_buffer, title, get_path(), chunk_index, chunks)
                    sub_buffer, sub_tokens = [], 0
                sub_buffer.append(sent)
                sub_tokens += st
            chunk_index = _flush(sub_buffer, title, get_path(), chunk_index, chunks)
            continue
        buffer.append(line)
        buffer_tokens += para_tokens
    _flush(buffer, title, get_path(), chunk_index, chunks)
    logger.info(f"'{title}' → {len(chunks)} chunks")
    return chunks



#strategy3
def chunk_essay(record: dict) -> List[Dict]:
    title   = record["essay_title"]
    content = record["essay_content"].strip()

    raw_paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

    chunks = []
    for i, para in enumerate(raw_paragraphs):
        chunks.append({
            "article_title": title,
            "section_path":  "paragraph",
            "chunk_text":    para,
            "chunk_index":   i,
            "token_approx":  _token_count(para),
        })

    logger.info(f"'{title}' → {len(chunks)} chunks (one-per-paragraph mode)")
    return chunks



# strategy2
# def chunk_essay(record: dict) -> List[Dict]:
#     """
#     MINE-1 JSONL record → single chunk (no splitting).
#     Each essay is short enough (~592 words) to process whole.
#     Record keys: essay_title, essay_content.
#     """
#     title   = record["essay_title"]
#     content = _clean(record["essay_content"])

#     chunks = [{
#         "article_title": title,
#         "section_path":  "full_article",
#         "chunk_text":    content,
#         "chunk_index":   0,
#         "token_approx":  _token_count(content),
#     }]

#     logger.info(f"'{title}' → 1 chunk ({_token_count(content)} tokens) [no-split mode]")
#     return chunks








# strategy1
# def chunk_essay(record: dict) -> List[Dict]:
#     """
#     Chunk a MINE-1 JSONL record.
#     Record keys: essay_title, essay_content.
#     Plain prose — no heading parsing. section_path is always 'Introduction'.
#     """
#     title         = record["essay_title"]
#     lines         = record["essay_content"].splitlines()
#     chunks        = []
#     buffer        = []
#     buffer_tokens = 0
#     chunk_index   = 0
#     section_path  = "Introduction"

#     for line in lines:
#         line = line.strip()
#         if not line:
#             continue
#         para_tokens = _token_count(line)
#         if buffer_tokens + para_tokens > MAX_TOKENS:
#             chunk_index = _flush(buffer, title, section_path, chunk_index, chunks)
#             buffer, buffer_tokens = [], 0
#         # Single paragraph too long → split at sentence level
#         if para_tokens > MAX_TOKENS:
#             sentences = re.split(r'(?<=[.!?])\s+', line)
#             sub_buffer, sub_tokens = [], 0
#             for sent in sentences:
#                 st = _token_count(sent)
#                 if sub_tokens + st > MAX_TOKENS:
#                     chunk_index = _flush(sub_buffer, title, section_path, chunk_index, chunks)
#                     sub_buffer, sub_tokens = [], 0
#                 sub_buffer.append(sent)
#                 sub_tokens += st
#             chunk_index = _flush(sub_buffer, title, section_path, chunk_index, chunks)
#             continue
#         buffer.append(line)
#         buffer_tokens += para_tokens
#     _flush(buffer, title, section_path, chunk_index, chunks)
#     logger.info(f"'{title}' → {len(chunks)} chunks")
#     return chunks