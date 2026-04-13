"""SPL 2.0 Lexer: character-by-character scanner producing a token stream.

Extends SPL 1.0 lexer with := operator, : colon, % percent, and { } braces.
"""

from spl.tokens import Token, TokenType, KEYWORDS


class LexerError(Exception):
    """Raised when the lexer encounters an invalid character sequence."""

    def __init__(self, message: str, line: int, column: int):
        self.line = line
        self.column = column
        super().__init__(f"Lexer error at {line}:{column}: {message}")


class Lexer:
    """Tokenize SPL 2.0 source code into a list of Tokens."""

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        """Scan the entire source and return a list of tokens."""
        while self.pos < len(self.source):
            self._skip_whitespace_and_comments()
            if self.pos >= len(self.source):
                break

            ch = self.source[self.pos]

            if ch == '$' and self._peek(1) == '$':
                self._read_dollar_dollar()
            elif ch in ('"', "'") and self._peek(1) == ch and self._peek(2) == ch:
                self._read_triple_string(ch)
            elif ch in ('"', "'"):
                self._read_string(ch)
            elif (ch == 'f' or ch == 'F') and self._peek(1) == '"' and self._peek(2) == '"' and self._peek(3) == '"':
                self._read_triple_fstring()
            elif (ch == 'f' or ch == 'F') and self._peek(1) in ('"', "'"):
                self._read_fstring()
            elif ch.isdigit():
                self._read_number()
            elif ch.isalpha() or ch == '_':
                self._read_identifier()
            elif ch == '.':
                self._emit(TokenType.DOT, '.')
                self._advance()
            elif ch == ',':
                self._emit(TokenType.COMMA, ',')
                self._advance()
            elif ch == '(':
                self._emit(TokenType.LPAREN, '(')
                self._advance()
            elif ch == ')':
                self._emit(TokenType.RPAREN, ')')
                self._advance()
            elif ch == '{':
                self._emit(TokenType.LBRACE, '{')
                self._advance()
            elif ch == '}':
                self._emit(TokenType.RBRACE, '}')
                self._advance()
            elif ch == '[':
                self._emit(TokenType.LBRACKET, '[')
                self._advance()
            elif ch == ']':
                self._emit(TokenType.RBRACKET, ']')
                self._advance()
            elif ch == ';':
                self._emit(TokenType.SEMICOLON, ';')
                self._advance()
            elif ch == '*':
                self._emit(TokenType.STAR, '*')
                self._advance()
            elif ch == '+':
                self._emit(TokenType.PLUS, '+')
                self._advance()
            elif ch == '-':
                self._emit(TokenType.MINUS, '-')
                self._advance()
            elif ch == '@':
                self._emit(TokenType.AT, '@')
                self._advance()
            elif ch == '%':
                self._emit(TokenType.PERCENT, '%')
                self._advance()
            elif ch == '~':
                self._emit(TokenType.TILDE, '~')
                self._advance()
            elif ch == ':':
                # SPL 2.0: := assignment operator or : colon
                if self._peek(1) == '=':
                    self._emit(TokenType.ASSIGN, ':=')
                    self._advance()
                    self._advance()
                else:
                    self._emit(TokenType.COLON, ':')
                    self._advance()
            elif ch == '=':
                self._emit(TokenType.EQ, '=')
                self._advance()
            elif ch == '!':
                if self._peek(1) == '=':
                    self._emit(TokenType.NEQ, '!=')
                    self._advance()
                    self._advance()
                else:
                    raise LexerError(f"Unexpected character '!'", self.line, self.column)
            elif ch == '>':
                if self._peek(1) == '=':
                    self._emit(TokenType.GTE, '>=')
                    self._advance()
                    self._advance()
                else:
                    self._emit(TokenType.GT, '>')
                    self._advance()
            elif ch == '<':
                if self._peek(1) == '=':
                    self._emit(TokenType.LTE, '<=')
                    self._advance()
                    self._advance()
                else:
                    self._emit(TokenType.LT, '<')
                    self._advance()
            elif ch == '|':
                if self._peek(1) == '|':
                    self._emit(TokenType.PIPE_PIPE, '||')
                    self._advance()
                    self._advance()
                else:
                    self._emit(TokenType.PIPE, '|')
                    self._advance()
            else:
                raise LexerError(f"Unexpected character {ch!r}", self.line, self.column)

        self._emit(TokenType.EOF, '')
        return self.tokens

    def _advance(self) -> str:
        """Advance position by one character and return it."""
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _peek(self, offset: int = 0) -> str:
        """Peek at a character at current position + offset without advancing."""
        idx = self.pos + offset
        if idx < len(self.source):
            return self.source[idx]
        return '\0'

    def _emit(self, token_type: TokenType, value: str):
        """Emit a token at the current position."""
        self.tokens.append(Token(token_type, value, self.line, self.column))

    def _skip_whitespace_and_comments(self):
        """Skip whitespace and line comments (-- or #)."""
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch in (' ', '\t', '\r', '\n'):
                self._advance()
            elif (ch == '-' and self._peek(1) == '-') or ch == '#':
                # Line comment: skip until end of line
                while self.pos < len(self.source) and self.source[self.pos] != '\n':
                    self._advance()
            else:
                break

    def _read_string(self, quote: str):
        """Read a string literal enclosed in single or double quotes."""
        start_line = self.line
        start_col = self.column
        self._advance()  # skip opening quote
        value_chars: list[str] = []

        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch == '\\':
                # Escape sequence
                self._advance()
                if self.pos < len(self.source):
                    escaped = self.source[self.pos]
                    escape_map = {'n': '\n', 't': '\t', '\\': '\\', "'": "'", '"': '"'}
                    value_chars.append(escape_map.get(escaped, escaped))
                    self._advance()
            elif ch == quote:
                self._advance()  # skip closing quote
                value = ''.join(value_chars)
                self.tokens.append(Token(TokenType.STRING, value, start_line, start_col))
                return
            else:
                value_chars.append(ch)
                self._advance()

        raise LexerError(f"Unterminated string literal", start_line, start_col)

    def _read_number(self):
        """Read an integer or float literal."""
        start_line = self.line
        start_col = self.column
        num_chars: list[str] = []
        is_float = False

        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch.isdigit():
                num_chars.append(ch)
                self._advance()
            elif ch == '.' and not is_float:
                # Check if next char is a digit (float) vs dot accessor
                if self._peek(1).isdigit():
                    is_float = True
                    num_chars.append(ch)
                    self._advance()
                else:
                    break
            else:
                break

        value = ''.join(num_chars)
        token_type = TokenType.FLOAT if is_float else TokenType.INTEGER
        self.tokens.append(Token(token_type, value, start_line, start_col))

    def _read_identifier(self):
        """Read an identifier or keyword."""
        start_line = self.line
        start_col = self.column
        id_chars: list[str] = []

        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch.isalnum() or ch == '_':
                id_chars.append(ch)
                self._advance()
            else:
                break

        value = ''.join(id_chars)
        lower = value.lower()

        # Check if it's a keyword
        token_type = KEYWORDS.get(lower, TokenType.IDENTIFIER)
        self.tokens.append(Token(token_type, value, start_line, start_col))

    def _read_triple_string(self, quote: str):
        """Read a triple-quoted string: '''...''' or \"\"\"...\"\"\"
        Emits a STRING token. Content may span multiple lines.
        """
        start_line = self.line
        start_col = self.column
        self._advance()  # skip first quote
        self._advance()  # skip second quote
        self._advance()  # skip third quote
        value_chars: list[str] = []
        while self.pos < len(self.source):
            if (self.source[self.pos] == quote
                    and self._peek(1) == quote
                    and self._peek(2) == quote):
                self._advance()  # skip first closing quote
                self._advance()  # skip second closing quote
                self._advance()  # skip third closing quote
                self.tokens.append(Token(TokenType.STRING, ''.join(value_chars), start_line, start_col))
                return
            value_chars.append(self.source[self.pos])
            self._advance()
        raise LexerError("Unterminated triple-quoted string", start_line, start_col)

    def _read_triple_fstring(self):
        """Read a triple-quoted f-string: f\"\"\"...\"\"\"
        Emits an FSTRING token with raw template content.
        """
        start_line = self.line
        start_col = self.column
        self._advance()  # skip 'f' prefix
        self._advance()  # skip first "
        self._advance()  # skip second "
        self._advance()  # skip third "
        value_chars: list[str] = []
        while self.pos < len(self.source):
            if (self.source[self.pos] == '"'
                    and self._peek(1) == '"'
                    and self._peek(2) == '"'):
                self._advance()
                self._advance()
                self._advance()
                self.tokens.append(Token(TokenType.FSTRING, ''.join(value_chars), start_line, start_col))
                return
            value_chars.append(self.source[self.pos])
            self._advance()
        raise LexerError("Unterminated triple-quoted f-string", start_line, start_col)

    def _read_fstring(self):
        """Read an f-string literal: f'...' or f"..."
        Emits a single FSTRING token whose value is the raw template string
        with {@varname} placeholders preserved for the executor to interpolate.
        Example: f'Chunk {@chunk_index} of {@chunk_count}' →
                 Token(FSTRING, 'Chunk {@chunk_index} of {@chunk_count}')
        """
        start_line = self.line
        start_col = self.column
        self._advance()  # skip 'f' prefix
        quote = self.source[self.pos]
        self._advance()  # skip opening quote

        value_chars: list[str] = []
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch == '\\':
                self._advance()
                if self.pos < len(self.source):
                    escaped = self.source[self.pos]
                    escape_map = {'n': '\n', 't': '\t', '\\': '\\', "'": "'", '"': '"'}
                    value_chars.append(escape_map.get(escaped, escaped))
                    self._advance()
            elif ch == quote:
                self._advance()  # skip closing quote
                self.tokens.append(
                    Token(TokenType.FSTRING, ''.join(value_chars), start_line, start_col)
                )
                return
            else:
                value_chars.append(ch)
                self._advance()

        raise LexerError("Unterminated f-string literal", start_line, start_col)

    def _read_dollar_dollar(self):
        """Read $$...$$  — emit opening DOLLAR_DOLLAR, then body as raw STRING."""
        start_line = self.line
        start_col = self.column
        self._advance()  # skip first $
        self._advance()  # skip second $
        self.tokens.append(Token(TokenType.DOLLAR_DOLLAR, '$$', start_line, start_col))

        # Consume everything until the closing $$ as a single raw string
        body_chars: list[str] = []
        body_line = self.line
        body_col = self.column
        while self.pos < len(self.source):
            if self.source[self.pos] == '$' and self._peek(1) == '$':
                self.tokens.append(Token(TokenType.STRING, ''.join(body_chars), body_line, body_col))
                self._advance()  # skip first closing $
                self._advance()  # skip second closing $
                return
            body_chars.append(self.source[self.pos])
            self._advance()
        raise LexerError("Unterminated $$ string", start_line, start_col)
