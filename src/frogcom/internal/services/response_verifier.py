import re
from typing import List, Optional, Union
from dataclasses import dataclass

@dataclass
class VerificationResult:
    is_valid: bool
    content: Optional[str] = None
    was_cleaned: bool = False
    reason: str = ""

class ResponseVerifier:
    def __init__(self):
        # Паттерны для различных языков
        # \A и \Z — начало/конец ВСЕЙ строки (не линии, в отличие от ^/$ с MULTILINE)
        self.patterns = {
            # Python - triple quotes
            'python': re.compile(r'\A[\s]*("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')[\s]*\Z'),
            'python_extract': re.compile(r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')'),
            
            # JSDoc/JavaDoc - /** */
            'jsdoc': re.compile(r'\A[\s]*/\*\*[\s\S]*?\*/[\s]*\Z'),
            'jsdoc_extract': re.compile(r'/\*\*[\s\S]*?\*/'),

            # C/Go block comment - /* */
            'c_block': re.compile(r'\A[\s]*/\*[\s\S]*?\*/[\s]*\Z'),
            'c_block_extract': re.compile(r'/\*[\s\S]*?\*/'),
            
            # C# XML - /// (одна или более строк)
            'csharp': re.compile(r'\A[\s]*(///[^\n]*\n?)+[\s]*\Z'),
            'csharp_extract': re.compile(r'((?:///[^\n]*\n?)+)'),
            
            # Go - // (одна или более строк)
            'go': re.compile(r'\A[\s]*(//[^\n]*\n?)+[\s]*\Z'),
            'go_extract': re.compile(r'((?://[^\n]*\n?)+)'),
        }

        self.question_line_pattern = re.compile(r'^\s*(?:\d+\.\s*|-\s+)(.+?)\s*$', re.MULTILINE)
        
        self.md_code_block = re.compile(r'```(?:\w+)?\s*\n([\s\S]*?)\n?```')

        # Паттерн для удаления внешних markdown code fences
        self.markdown_fence = re.compile(r'^```(?:\w+)?\s*\n([\s\S]*?)\n?```\s*$', re.DOTALL)

    def verify_comment(self, content: str) -> VerificationResult:
        strict = False
        if not content or not content.strip():
            return VerificationResult(is_valid=False, reason="Empty content")

        original = content  # Сохраняем оригинал для извлечения
        original_stripped = content.strip()
        
        code_blocks = self._extract_code_blocks(original_stripped)
        
        if code_blocks:
            # В строгом режиме: если есть код, проверяем только последний блок
            # (так как модели часто дублируют код, добавляя комментарий в конце)
            candidates = [code_blocks[-1]] if strict else code_blocks
            
            for block in candidates:
                extracted_doc = self._extract_doc_from_mixed_code(block)
                if extracted_doc:
                    return VerificationResult(
                        is_valid=True,
                        content=extracted_doc,
                        was_cleaned=True,
                        reason="Valid doc extracted from markdown block (mixed code cleanup)",
                    )

                # Рекурсивно проверяем очищенный блок кода
                # Важно: передаем strict=False, чтобы внутри блока сработало извлечение
                result = self._check_raw_content(block, strict=False)
                if result.is_valid:
                    return VerificationResult(
                        is_valid=True, 
                        content=result.content, 
                        was_cleaned=True, 
                        reason=f"Valid doc extracted from markdown block ({result.reason})"
                    )
            
            # Если в блоках кода ничего не нашли, а режим строгий - фейл
            if strict:
                return VerificationResult(is_valid=False, reason="No valid doc found in code blocks (strict mode)")

        # === ШАГ 2: Проверка "сырого" контента (если нет markdown или не строгий режим) ===
        # Здесь применяем вашу оригинальную логику, но с проверкой на "чистоту"
        result = self._check_raw_content(original_stripped, strict)
        
        if result.is_valid and strict:
            # В строгом режиме проверяем, не является ли ответ "помойкой"
            # Если извлеченный контент составляет малую часть от исходного - это подозрительно
            if result.was_cleaned and len(result.content) < len(original_stripped) * 0.5:
                 return VerificationResult(is_valid=False, reason="Content is too noisy (strict mode)")
                 
        return result
    
    def _extract_code_blocks(self, content: str) -> List[str]:
        """Извлекает содержимое markdown code fences из ответа."""
        return [
            match.group(1).strip()
            for match in self.md_code_block.finditer(content)
            if match.group(1).strip()
        ]

    def _extract_doc_from_mixed_code(self, content: str) -> Optional[str]:
        """Извлекает документационный блок из смеси комментария и кода."""
        extraction_order = ("jsdoc_extract", "c_block_extract", "python_extract")
        for pattern_key in extraction_order:
            matches = list(self.patterns[pattern_key].finditer(content))
            if matches:
                return matches[-1].group(0).strip()
        return None


    def _check_raw_content(self, content: str, strict: bool) -> VerificationResult:
        """Внутренний метод для проверки строки на соответствие паттернам."""

        if self._contains_question_section(content):
            return VerificationResult(is_valid=False, reason="Question section detected in comment response")

        if self._is_meta_explanation(content):
            return VerificationResult(is_valid=False, reason="Meta explanation detected instead of documentation")

        if self._has_instructional_template(content):
            return VerificationResult(is_valid=False, reason="Instructional template detected instead of documentation")

        if self._has_excessive_repetition(content):
            return VerificationResult(is_valid=False, reason="Excessive repetition detected")
        
        # === 1. Python (triple quotes: """ или ''') ===
        if self.patterns['python'].match(content):
            return VerificationResult(is_valid=True, content=content, reason="Valid Python Docstring (exact)")
        
        python_matches = list(self.patterns['python_extract'].finditer(content))
        if python_matches:
            last_match = python_matches[-1].group(0).strip()
            if len(last_match) >= 6:
                return VerificationResult(is_valid=True, content=last_match, was_cleaned=True, reason="Python Docstring extracted")

        # === 2. JavaScript/Java (JSDoc/JavaDoc: /** */) ===
        if self.patterns['jsdoc'].match(content):
            return VerificationResult(is_valid=True, content=content, reason="Valid JSDoc/JavaDoc (exact)")
        
        jsdoc_matches = list(self.patterns['jsdoc_extract'].finditer(content))
        if jsdoc_matches:
            last_match = jsdoc_matches[-1].group(0).strip()
            if len(last_match) >= 6:
                return VerificationResult(is_valid=True, content=last_match, was_cleaned=True, reason="JSDoc/JavaDoc extracted")

        # === 2.1 C/Go block comments (/* */) ===
        if self.patterns['c_block'].match(content):
            return VerificationResult(is_valid=True, content=content, reason="Valid C/Go block comment (exact)")

        c_block_matches = list(self.patterns['c_block_extract'].finditer(content))
        if c_block_matches:
            last_match = c_block_matches[-1].group(0).strip()
            if len(last_match) >= 6:
                return VerificationResult(
                    is_valid=True,
                    content=last_match,
                    was_cleaned=True,
                    reason="C/Go block comment extracted",
                )

        # === 3. C# (XML Documentation: ///) ===
        if self.patterns['csharp'].match(content):
            return VerificationResult(is_valid=True, content=content, reason="Valid C# XML Doc (exact)")
        
        csharp_matches = list(self.patterns['csharp_extract'].finditer(content))
        if csharp_matches:
            last_match = "\n".join(m.group(0).strip() for m in csharp_matches).strip()
            if last_match and len(last_match) >= 6:
                return VerificationResult(is_valid=True, content=last_match, was_cleaned=True, reason="C# XML Doc extracted")

        # === 4. Go (GoDoc: //) ===
        if self.patterns['go'].match(content):
            return VerificationResult(is_valid=True, content=content, reason="Valid GoDoc (exact)")
        
        go_matches = list(self.patterns['go_extract'].finditer(content))
        if go_matches:
            last_match = "\n".join(m.group(0).strip() for m in go_matches).strip()
            if last_match and len(last_match) >= 6:
                return VerificationResult(is_valid=True, content=last_match, was_cleaned=True, reason="GoDoc extracted")

        # === 5. Markdown эвристика (только если не strict режим) ===
        if not strict:
            if self._looks_like_blockquote_response(content):
                return VerificationResult(is_valid=False, reason="Blockquote/meta response detected")

            if self._count_nonempty_lines(content) < 3:
                return VerificationResult(is_valid=False, reason="Too few lines for markdown documentation")

            has_md_struct = bool(
                re.search(r'^#+\s', content, re.MULTILINE) or 
                re.search(r'^[\s]*[-*+]\s', content, re.MULTILINE)
            )
            has_code_keywords = bool(re.search(
                r'^\s*(def |class |function |import |from |public |private |protected |func |package |interface |enum )', 
                content, re.MULTILINE
            ))
            
            if has_md_struct and not has_code_keywords:
                return VerificationResult(is_valid=True, content=content, reason="Valid Markdown (heuristic)")

        # === 6. Проверка на незавершенные комментарии (артефакты генерации) ===
        if self._is_incomplete_comment(content):
            return VerificationResult(is_valid=False, reason="Incomplete comment block detected")

        # === 7. Финал: ничего не подошло ===
        return VerificationResult(is_valid=False, reason="No valid documentation format found")
        


    def verify_questions_list(self, content: str, expected_count: int) -> VerificationResult:
        prepared_content = content.strip()
        markdown_match = self.markdown_fence.match(prepared_content)
        if markdown_match:
            prepared_content = markdown_match.group(1).strip()

        matches = self.question_line_pattern.findall(prepared_content)
        questions = [question.strip() for question in matches if question.strip()]
        if len(questions) < expected_count:
            return VerificationResult(
                is_valid=False,
                reason=f"Expected {expected_count} questions, found {len(questions)}"
            )
        valid_questions = [f"{index}. {question}" for index, question in enumerate(questions[:expected_count], start=1)]
        return VerificationResult(
            is_valid=True,
            content="\n".join(valid_questions),
            reason=f"Extracted {len(valid_questions)} questions",
        )
    
    def _is_incomplete_comment(self, content: str) -> bool:
        if content.startswith('/*') and not content.endswith('*/'): return True
        if content.startswith('"""') and not content.endswith('"""') and len(content) > 3: return True
        if content.startswith("'''") and not content.endswith("'''") and len(content) > 3: return True
        return False

    def _is_meta_explanation(self, content: str) -> bool:
        normalized = re.sub(r'\s+', ' ', content.strip().lower())
        meta_patterns = (
            r'в этом обновл[её]нном комментарии',
            r'^в комментарии\b',
            r'^не используйте markdown',
            r'^документация должна включать',
            r'документац[ияи]\s+соответствует\s+требованиям',
            r'требования к формату документации соблюдены',
            r'добавлены теги @param и @return',
            r'использован\s+google-style\s+docstring',
            r'^\s*>\s*✅',
        )
        return any(re.search(pattern, normalized) for pattern in meta_patterns)

    def _looks_like_blockquote_response(self, content: str) -> bool:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if not lines:
            return False
        blockquote_lines = [line for line in lines if line.startswith(">")]
        return len(blockquote_lines) / len(lines) >= 0.5

    def _count_nonempty_lines(self, content: str) -> int:
        return sum(1 for line in content.splitlines() if line.strip())

    def _contains_question_section(self, content: str) -> bool:
        lowered = content.lower()
        return ("вопросы:" in lowered) or ("questions:" in lowered)

    def _has_instructional_template(self, content: str) -> bool:
        normalized = re.sub(r'\s+', ' ', content.strip().lower())
        patterns = (
            r'документация должна включать',
            r'параметры должны быть',
            r'не используйте markdown',
            r'краткое описание функции',
        )
        return sum(bool(re.search(pattern, normalized)) for pattern in patterns) >= 2

    def _has_excessive_repetition(self, content: str) -> bool:
        normalized_lines = [
            re.sub(r'\s+', ' ', line.strip().lower())
            for line in content.splitlines()
            if line.strip()
        ]
        if not normalized_lines:
            return False

        line_counts: dict[str, int] = {}
        for line in normalized_lines:
            line_counts[line] = line_counts.get(line, 0) + 1

        return max(line_counts.values()) >= 5
