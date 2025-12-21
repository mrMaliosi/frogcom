import re
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class VerificationResult:
    is_valid: bool
    content: str = ""
    reason: str = ""
    needs_regeneration: bool = False

class ResponseVerifier:
    def __init__(self):
        # Паттерны остаются те же
        self.block_comment_pattern = re.compile(
            r'/\*[\s\S]*?\*/|"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', 
            re.MULTILINE
        )
        # Однострочные комментарии (Go, C++, Python)
        self.single_line_pattern = re.compile(
            r'^\s*(?://|#(?!#)).*$', 
            re.MULTILINE
        )
        self.markdown_header_pattern = re.compile(r'^(#{1,6})\s+.+$', re.MULTILINE)
        self.question_pattern = r'^\s*(?:\d+\.|-\s).+?\?\s*$'

    def verify_comment(self, content: str) -> VerificationResult:
        content = content.strip()

        # 1. Блочные комментарии (Code style) -> Приоритет: Последний блок
        block_matches = list(self.block_comment_pattern.finditer(content))
        if block_matches:
            last_match = block_matches[-1].group(0)
            if self._is_incomplete_comment(last_match):
                return VerificationResult(False, needs_regeneration=True, reason="Incomplete block comment")
            return VerificationResult(True, last_match, "Last block comment extracted")

        # 2. Markdown документация (Text style) -> Приоритет: Последняя секция
        headers = list(self.markdown_header_pattern.finditer(content))
        if headers:
            min_level = min(len(h.group(1)) for h in headers)
            last_top_level_header = [h for h in headers if len(h.group(1)) == min_level][-1]
            extracted_markdown = content[last_top_level_header.start():].strip()
            return VerificationResult(True, extracted_markdown, "Last markdown section extracted")

        # 3. Однострочные комментарии (Fallback) -> Сложная логика дедупликации
        single_lines = self.single_line_pattern.findall(content)
        if single_lines:
            # Очищаем от лишних пробелов справа, но сохраняем структуру
            cleaned_lines = [line.rstrip() for line in single_lines]
            
            # Попытка найти повторяющиеся блоки и взять последний
            unique_block = self._extract_last_unique_block(cleaned_lines)
            
            return VerificationResult(True, unique_block, "Single line comments extracted and deduplicated")

        return VerificationResult(
            False, 
            needs_regeneration=True, 
            reason="No valid documentation found"
        )

    def _extract_last_unique_block(self, lines: list[str]) -> str:
        """
        Пытается найти повторяющийся паттерн строк и возвращает только одну (последнюю) копию.
        Если повторов нет, возвращает всё как есть.
        """
        if not lines:
            return ""
        
        n = len(lines)
        # Эвристика: ищем повтор первой строки блока
        first_line = lines[0]
        
        # Индексы, где встречается такая же строка (начиная со второй позиции)
        repeats_indices = [i for i, x in enumerate(lines) if x == first_line and i > 0]
        
        if not repeats_indices:
            # Повторов первой строки нет -> считаем, что это один уникальный блок
            return "\n".join(lines)
        
        # Если есть повторы, пытаемся определить длину периода
        # Берем первый повтор. Предполагаемая длина блока = index этого повтора.
        block_len = repeats_indices[0]
        
        # Проверяем гипотезу: действительно ли блок повторяется?
        # Сравниваем lines[0:block_len] с lines[block_len:2*block_len] и т.д.
        is_pattern = True
        for i in range(block_len, n - (n % block_len), block_len):
            chunk = lines[i : i + block_len]
            original = lines[0 : block_len]
            # Сравниваем chunk с оригиналом. 
            # (Можно сделать нестрогое сравнение, но для копипасты LLM строгое обычно ок)
            if chunk != original:
                is_pattern = False
                break
        
        if is_pattern:
            # Если паттерн подтвердился, нам нужен ПОСЛЕДНИЙ (возможно неполный) или ПОЛНЫЙ блок.
            # В вашем примере последний блок может быть обрезан.
            # Но обычно мы хотим получить один ПОЛНЫЙ экземпляр.
            
            # Вариант А: Вернуть один полный эталонный блок (первый)
            # return "\n".join(lines[:block_len])
            
            # Вариант Б: Вернуть последний, если он полный, иначе предпоследний.
            # В контексте генерации кода LLM часто дублирует "старый код -> новый код".
            # Поэтому лучше вернуть ПОСЛЕДНИЙ ПОЛНЫЙ блок.
            
            # Сколько полных блоков влазит?
            full_blocks_count = n // block_len
            
            # Берем последний полный блок
            start_idx = (full_blocks_count - 1) * block_len
            end_idx = start_idx + block_len
            return "\n".join(lines[start_idx:end_idx])

        # Если простой паттерн не найден, возвращаем всё, но можно попробовать
        # найти самый длинный повторяющийся суффикс (более сложный алгоритм),
        # но для LLM часто достаточно вернуть просто join, если структура не очевидна.
        return "\n".join(lines)
    
    def verify_questions_list(self, content: str, expected_count: int) -> VerificationResult:
        questions = re.findall(self.question_pattern, content, re.MULTILINE)
        if len(questions) < expected_count:
            return VerificationResult(
                False, 
                needs_regeneration=True,
                reason=f"Expected {expected_count} questions, found {len(questions)}"
            )
        valid_questions = [q.strip() for q in questions[:expected_count]]
        return VerificationResult(True, "\n".join(valid_questions), f"Extracted {len(valid_questions)} questions")
    
    def _is_incomplete_comment(self, content: str) -> bool:
        if content.startswith('/*') and not content.endswith('*/'): return True
        if content.startswith('"""') and not content.endswith('"""') and len(content) > 3: return True
        if content.startswith("'''") and not content.endswith("'''") and len(content) > 3: return True
        return False
