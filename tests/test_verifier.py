import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from frogcom.internal.services.response_verifier import ResponseVerifier, VerificationResult

class TestCommentVerifier:
    @pytest.fixture
    def verifier(self):
        return ResponseVerifier()

    # --- Python Tests ---
    def test_valid_python_docstring(self, verifier):
        content = '"""This is a valid Python docstring."""'
        result = verifier.verify_comment(content)
        assert result.is_valid is True
        assert result.was_cleaned is False
        assert "Python" in result.reason

    def test_valid_python_single_quotes(self, verifier):
        content = "'''Single quotes docstring.'''"
        result = verifier.verify_comment(content)
        assert result.is_valid is True

    def test_python_with_extra_code(self, verifier):
        content = 'print("hello")\n"""Real Docstring"""'
        result = verifier.verify_comment(content)
        assert result.is_valid is True
        assert result.was_cleaned is True
        assert '"""Real Docstring"""' in result.content

    # --- JSDoc / JavaDoc Tests ---
    def test_valid_jsdoc(self, verifier):
        content = "/**\n * Description\n * @param {string} x\n */"
        result = verifier.verify_comment(content)
        assert result.is_valid is True
        assert result.was_cleaned is False

    def test_jsdoc_with_noise(self, verifier):
        content = "function foo() {}\n/**\n * Comment\n */"
        result = verifier.verify_comment(content)
        assert result.is_valid is True
        assert result.was_cleaned is True

    # --- C# XML Tests ---
    def test_valid_csharp_xml(self, verifier):
        content = "/// <summary>\n/// Summary\n/// </summary>"
        result = verifier.verify_comment(content)
        assert result.is_valid is True
        assert "C#" in result.reason

    def test_csharp_mixed(self, verifier):
        content = "public class A {}\n/// <summary>Test</summary>"
        result = verifier.verify_comment(content)
        assert result.is_valid is True
        assert result.was_cleaned is True

    # --- GoDoc Tests ---
    def test_valid_godoc(self, verifier):
        content = "// Package main is the entry point.\n// It does things."
        result = verifier.verify_comment(content)
        assert result.is_valid is True
        assert "GoDoc" in result.reason

    # --- Markdown Tests ---
    def test_valid_markdown(self, verifier):
        content = "# Header\n\n- List item\n- Another item"
        result = verifier.verify_comment(content)
        assert result.is_valid is True
        assert "Markdown" in result.reason

    def test_invalid_markdown_with_code(self, verifier):
        # Если текст выглядит как код, markdown не должен срабатывать как комментарий
        content = "def foo():\n    pass"
        result = verifier.verify_comment(content)
        # В текущей логике это упадет в False, так как нет комментариев и не подходит под MD эвристику
        assert result.is_valid is False

    # --- Negative Tests ---
    def test_empty_content(self, verifier):
        result = verifier.verify_comment("")
        assert result.is_valid is False
        assert "Empty" in result.reason

    def test_random_text(self, verifier):
        content = "This is just random text without format."
        result = verifier.verify_comment(content)
        assert result.is_valid is False

    def test_incomplete_comment(self, verifier):
        content = "/** This comment is not closed"
        result = verifier.verify_comment(content)
        # JSDoc паттерн требует закрытия */, поэтому это должно быть False или извлечено частично
        # В нашей реализации строгий матч на весь контент вернет False
        assert result.is_valid is False 

    # --- Logic Verification ---
    def test_return_structure(self, verifier):
        content = '"""Test"""'
        result = verifier.verify_comment(content)
        assert isinstance(result, VerificationResult)
        assert hasattr(result, 'is_valid')
        assert hasattr(result, 'content')
        assert hasattr(result, 'was_cleaned')

# === Дополнительные тесты для специфических случаев ===

class TestRealWorldComments:
    """Тесты на реальных примерах из запроса"""

    @pytest.fixture
    def verifier(self):
        return ResponseVerifier()

#     # --- Тест 1: Java + JavaDoc (код после комментария) ---
#     def test_javadoc_with_java_code(self, verifier):
#         """JavaDoc комментарий, за которым следует код метода"""
#         content = '''/**
#  * Записывает состояние объекта в формат NBT. 
#  * Включает вызов родительского метода и сохраняет содержимое стека в поле INV_TAG.
#  * Если стек не пуст, его состояние сохраняется в отдельном теге NBT.
#  */
# @Override
# public void writeToNBT(NBTTagCompound nbt) {
#     super.writeToNBT(nbt);
#     if (stack != null) {
#         NBTTagCompound inventoryTag = new NBTTagCompound();
#         stack.writeToNBT(inventoryTag);
#         nbt.setTag(INV_TAG, inventoryTag);
#     }
# }'''
#         result = verifier.verify_comment(content)
        
#         assert result.is_valid is True, f"Expected valid, got: {result.reason}"
#         assert result.was_cleaned is True, "Should have cleaned Java code"
#         assert "/**" in result.content and "*/" in result.content
#         assert "@Override" not in result.content, "Java code should be removed"
#         assert "Записывает состояние объекта" in result.content

    def test_javadoc_garbage(self, verifier):
        """JavaDoc комментарий, за которым следует код метода"""
        content = """```java
    /**
    * Записывает состояние объекта в формат NBT.
    * Включает вызов родительского метода и сохраняет содержимое стека в поле INV_TAG.
    * Если стек не пуст, его состояние сохраняется в отдельном теге NBT.
    */
    @Override
    public void writeToNBT(NBTTagCompound nbt) {
        super.writeToNBT(nbt);

        if (stack != null) {
            NBTTagCompound inventoryTag = new NBTTagCompound();
            stack.writeToNBT(inventoryTag);
            nbt.setTag(INV_TAG, inventoryTag);
        }
    }
    ```"""

        result = verifier.verify_comment(content)

        assert result.is_valid is True, f"Expected valid, got: {result.reason}"
        assert result.was_cleaned is True, "Should have cleaned Java code"
        assert result.content == """/**
    * Записывает состояние объекта в формат NBT.
    * Включает вызов родительского метода и сохраняет содержимое стека в поле INV_TAG.
    * Если стек не пуст, его состояние сохраняется в отдельном теге NBT.
    */"""

    def test_meta_explanation_is_not_comment(self, verifier):
        content = (
            "В этом обновлённом комментарии:\n"
            "1. Использован Google-style Docstring для Python.\n"
            "2. Добавлены теги @param и @return, соответствующие требованиям GoDoc.\n"
            "3. Оформлены примеры вида \"Example:\" и \"Output:\"."
        )
        result = verifier.verify_comment(content)

        assert result.is_valid is False
        assert "Meta explanation" in result.reason

    def test_blockquote_meta_response_is_not_comment(self, verifier):
        content = (
            "> ✅ *Все использованные в функции и документации названия методов*.\n"
            "В этом случае документация соответствует требованиям к внутреннему документированию."
        )
        result = verifier.verify_comment(content)

        assert result.is_valid is False
        assert "Meta explanation" in result.reason

    def test_quote_heavy_response_is_not_comment(self, verifier):
        content = (
            ">\n"
            "> ✅ *Все использованные в функции и документации названия методов*.\n"
            "> В этом случае документация соответствует требованиям к внутреннему документированию.\n"
            "> В этом случае документация соответствует требованиям к внутреннему документированию."
        )
        result = verifier.verify_comment(content)

        assert result.is_valid is False
        assert "Blockquote/meta response" in result.reason or "Meta explanation" in result.reason

    def test_mixed_comment_and_questions_is_invalid(self, verifier):
        content = (
            "В комментарии добавлены примеры и описание возвращаемого значения.\n"
            "def editPartOfEntity(self, operatingSystemId: int, operatingSystemDTO: OperatingSystemDTO) -> OperatingSystemDTO:\n"
            "\t\"\"\"\n"
            "\tUpdates an existing operating system entity with new data.\n"
            "\t\"\"\"\n"
            "Вопросы:\n"
            "1. Какой тип данных ожидается в параметре `operatingSystemDTO`?\n"
            "2. Какой тип данных возвращает функция `editPartOfEntity`?\n"
            "3. Почему описание и реализация расходятся?"
        )
        result = verifier.verify_comment(content)

        assert result.is_valid is False
        assert "Question section detected" in result.reason

    def test_go_block_comment_extracted_from_markdown_code_block(self, verifier):
        content = """Только документация в нужном формате.

```go
/*
\teditPartOfEntity updates an existing operating system entity with new data.
\tIt retrieves the entity by ID, maps the provided DTO to the persistent entity,
\tsaves the updated entity to the database, and returns a new DTO representation.
*/
func (s *OperatingSystemService) editPartOfEntity(operatingSystemId int, operatingSystemDTO OperatingSystemDTO) OperatingSystemDTO {
\treturn OperatingSystemDTO{}
}
```"""
        result = verifier.verify_comment(content)

        assert result.is_valid is True
        assert result.was_cleaned is True
        assert result.content == """/*
\teditPartOfEntity updates an existing operating system entity with new data.
\tIt retrieves the entity by ID, maps the provided DTO to the persistent entity,
\tsaves the updated entity to the database, and returns a new DTO representation.
*/"""

    def test_java_doc_extracted_without_method_body(self, verifier):
        content = """Не включай в себя блоки кода.

```java
/**
 * Останавливает чтение книги для указанного пользователя.
 *
 * @param name название книги, которую пользователь хочет завершить чтение
 * @throws NullPointerException если пользователь не начал чтение указанной книги
 * @see Status#find(java.lang.String, java.lang.String, java.lang.String)
 * @see Admin#index()
 */
public static void StopRead(String name) {
    String user = session.get("username");
    Admin.index();
}
```"""
        result = verifier.verify_comment(content)

        assert result.is_valid is True
        assert result.was_cleaned is True
        assert result.content == """/**
 * Останавливает чтение книги для указанного пользователя.
 *
 * @param name название книги, которую пользователь хочет завершить чтение
 * @throws NullPointerException если пользователь не начал чтение указанной книги
 * @see Status#find(java.lang.String, java.lang.String, java.lang.String)
 * @see Admin#index()
 */"""

    def test_repeated_broken_java_blocks_extract_single_javadoc(self, verifier):
        content = """В комментарии добавлены ссылки на методы Status.find и Admin.index, которые используются в коде.
```java
/**
 * Останавливает чтение книги для указанного пользователя.
 *
 * @param name название книги, которую пользователь хочет завершить чтение
 * @throws NullPointerException если пользователь не начал чтение указанной книги
 * @see Status#find(java.lang.String, java.lang.String, java.lang.String)
 * @see Admin#index()
 */
public static void StopRead(String name) {
    Admin.index();
}
```java
/**
 * Останавливает чтение книги для указанного пользователя.
 *
 * @param name название книги, которую пользователь хочет завершить чтение
 * @throws NullPointerException если пользователь не начал чтение указанной книги
 * @see Status#find(java.lang.String, java.lang.String, java.lang.String)
 * @see Admin#index()
 */
public static void StopRead(String name) {
    Admin.index();
}
```java
/**
 * Останавливает чтение книги для указанного пользователя.
 *
 * @param name название книги, которую пользователь хочет завершить чтение
 * @throws NullPointerException если пользователь не начал чтение указанной книги
 * @see Status#find(java.lang.String, java.lang.String, java.lang.String)
 * @see Admin#index()
 */
public static void StopRead(String name) {
    Status st = Status.find("byNickAndTitle", "u", "b").first();
    try {
        st.delete();
    } catch (NullPointerException e"""
        result = verifier.verify_comment(content)

        assert result.is_valid is True
        assert result.was_cleaned is True
        assert result.content == """/**
 * Останавливает чтение книги для указанного пользователя.
 *
 * @param name название книги, которую пользователь хочет завершить чтение
 * @throws NullPointerException если пользователь не начал чтение указанной книги
 * @see Status#find(java.lang.String, java.lang.String, java.lang.String)
 * @see Admin#index()
 */"""

    def test_instructional_template_with_repetition_is_invalid(self, verifier):
        content = (
            "Не используйте markdown.\n\n"
            "Документация должна включать:\n"
            "- Краткое описание функции\n"
            "- Параметры функции\n\n"
            "Параметры должны быть описаны с использованием официального языка.\n"
            "Параметры должны быть описаны с использованием официального языка.\n"
            "Параметры должны быть описаны с использованием официального языка.\n"
            "Параметры должны быть описаны с использованием официального языка.\n"
            "Параметры должны быть описаны с использованием официального языка.\n"
        )
        result = verifier.verify_comment(content)

        assert result.is_valid is False
        assert (
            "Instructional template detected" in result.reason
            or "Excessive repetition detected" in result.reason
            or "Meta explanation" in result.reason
        )


class TestQuestionsVerifier:
    @pytest.fixture
    def verifier(self):
        return ResponseVerifier()

    def test_valid_questions_list(self, verifier):
        content = "1. What does this function return?\n2. What are edge cases?\n3. Is input validated?"
        result = verifier.verify_questions_list(content, expected_count=3)

        assert result.is_valid is True
        assert result.content == content
        assert "Extracted 3 questions" in result.reason

    def test_questions_are_renumbered_sequentially(self, verifier):
        content = (
            "1. Что именно возвращает функция: новый DTO или обновленный объект?\n"
            "2. Какой тип данных ожидается в параметре `operatingSystemDTO`?\n"
            "5. Комментарий содержит пример вызова функции `EditPartOfEntity`."
        )
        result = verifier.verify_questions_list(content, expected_count=3)

        assert result.is_valid is True
        assert result.content == (
            "1. Что именно возвращает функция: новый DTO или обновленный объект?\n"
            "2. Какой тип данных ожидается в параметре `operatingSystemDTO`?\n"
            "3. Комментарий содержит пример вызова функции `EditPartOfEntity`."
        )

    def test_questions_inside_markdown_fence(self, verifier):
        content = """```text
1. Why is this lock needed?
2. What happens on timeout?
3. Can this panic?
```"""
        result = verifier.verify_questions_list(content, expected_count=3)

        assert result.is_valid is True
        assert "```" not in result.content
        assert result.content.splitlines()[0].startswith("1.")

    def test_not_enough_questions(self, verifier):
        content = "1. Is this documented?\n2. Is this tested?"
        result = verifier.verify_questions_list(content, expected_count=3)

        assert result.is_valid is False
        assert "Expected 3 questions, found 2" in result.reason

#     # --- Тест 2: Markdown code fence с Java внутри ---
#     def test_javadoc_in_markdown_fence(self, verifier):
#         """JavaDoc внутри markdown-блока кода ```java"""
#         content = '''```java
# /**
#  * Записывает состояние объекта в формат NBT. 
#  */
# @Override
# public void writeToNBT(NBTTagCompound nbt) {}
# ```'''
#         result = verifier.verify_comment(content)
        
#         assert result.is_valid is True, f"Expected valid, got: {result.reason}"
#         assert result.was_cleaned is True
#         assert "/**" in result.content
#         assert "```" not in result.content

#     # --- Тест 3: GoDoc с функцией ---
#     def test_godoc_with_function_signature(self, verifier):
#         """GoDoc комментарий с подписью функции"""
#         content = '''// add добавляет 1 к каждому значению из входного канала и отправляет результат в выходной канал.
# // Функция работает в фоновом режиме и завершается, когда канал doneCh закрывается.
# //
# // Параметры:
# //   - doneCh: канал struct{}, который используется для сигнализации о завершении работы.
# //   - inputCh: канал int, из которого берутся значения для увеличения на 1.
# //
# // Возвращает:
# //   - chan int: канал с результатами.
# func add(doneCh chan struct{}, inputCh chan int) chan int'''
#         result = verifier.verify_comment(content)
        
#         assert result.is_valid is True, f"Expected valid, got: {result.reason}"
#         assert "// add добавляет" in result.content or "add добавляет" in result.content

#     # --- Тест 4: C# XML Documentation ---
#     def test_csharp_xml_doc_with_code(self, verifier):
#         """C# XML-документация с кодом метода"""
#         content = '''/// <summary>
# /// Устанавливает фокус на элемент в зависимости от типа модели.
# /// </summary>
# /// <remarks>
# /// Поддерживает три типа моделей.
# /// </remarks>
# public virtual void SetFocus()
# {
#     switch (TypeModel) {
#         case ModelType.Physical:
#             FocusedElement = Focuses.Name;
#             break;
#     }
# }'''
#         result = verifier.verify_comment(content)
        
#         assert result.is_valid is True, f"Expected valid, got: {result.reason}"
#         assert result.was_cleaned is True, "Should remove C# method body"
#         assert "/// <summary>" in result.content
#         assert "public virtual void" not in result.content

#     # --- Тест 5: Markdown документация ---
#     def test_markdown_documentation(self, verifier):
#         """Markdown-документация с заголовками и таблицами"""
#         content = '''### Документация к функции `canMoveAt`

# #### **Описание**
# Функция проверяет возможность перемещения фигуры.

# #### **Параметры**
# | Параметр | Тип | Описание |
# |--------|-----|---------|
# | `coordinates` | `Coordinates` | Целевая позиция. |

# #### **Возвращаемое значение**
# - **Тип**: `boolean`'''
#         result = verifier.verify_comment(content)
        
#         assert result.is_valid is True, f"Expected valid Markdown, got: {result.reason}"
#         assert result.was_cleaned is False
#         assert "### Документация" in result.content
#         assert "| Параметр |" in result.content

#     # --- Тест 6: Только комментарий без кода (edge case) ---
#     def test_javadoc_only_no_code(self, verifier):
#         """Только JavaDoc без последующего кода"""
#         content = '''/**
#  * Простой комментарий.
#  * @param x значение
#  * @return результат
#  */'''
#         result = verifier.verify_comment(content)
        
#         assert result.is_valid is True
#         assert result.was_cleaned is False, "No cleaning needed for pure comment"
#         assert result.content.strip() == content.strip()

#     # --- Тест 7: Экранированные кавычки в C# ---
#     def test_csharp_escaped_quotes(self, verifier):
#         """C# XML с экранированными кавычками (как в исходном запросе)"""
#         content = '''/// <summary>
# /// Текст с <see cref=\\"TypeModel\\"/> внутри.
# /// </summary>'''
#         result = verifier.verify_comment(content)
        
#         assert result.is_valid is True
#         assert "/// <summary>" in result.content

#     # --- Тест 8: Пустой комментарий внутри кода ---
#     def test_empty_comment_in_code(self, verifier):
#         """Минимальный комментарий с кодом — должен извлечь комментарий"""
#         content = '''/** */
# public void foo() {}'''
#         result = verifier.verify_comment(content)
        
#         # Пустой JSDoc структурно валиден, но код должен быть отрезан
#         assert result.is_valid is True
#         assert result.was_cleaned is True, "Code after empty comment should be cleaned"
#         assert result.content.strip() == "/** */"

#     # --- Тест 9: Множественные комментарии (берём последний) ---
#     def test_multiple_comments_take_last(self, verifier):
#         """Если несколько комментариев, должен извлекаться ПОСЛЕДНИЙ"""
#         content = '''// Первый комментарий
# /**
#  * Первый JSDoc
#  */
# // Второй комментарий
# /**
#  * Второй JSDoc - должен быть извлечён
#  * @returns {boolean}
#  */
# function test() {}'''
#         result = verifier.verify_comment(content)
        
#         assert result.is_valid is True
#         assert result.was_cleaned is True
#         # Проверяем, что извлечён ВТОРОЙ (последний) комментарий
#         assert "Первый JSDoc" not in result.content, "Should not contain first comment"
#         assert "@returns" in result.content or "Второй JSDoc" in result.content

#     def test_code_without_comments_invalid(self, verifier):
#         """Чистый код без документации должен возвращать False"""
#         content = '''public void calculate() {
#     int x = 5 + 3;
#     return x * 2;
# }'''
#         result = verifier.verify_comment(content)
#         assert result.is_valid is False
#         assert "No valid documentation" in result.reason