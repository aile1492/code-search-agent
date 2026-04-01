"""AST-based code chunking using Tree-sitter.

Splits source code into semantic chunks (functions, classes, methods)
while preserving context (imports, class definitions).
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import tree_sitter_typescript as tstypescript
import tree_sitter_java as tsjava
import tree_sitter_cpp as tscpp
import tree_sitter_go as tsgo
import tree_sitter_rust as tsrust
from tree_sitter import Language, Parser


# Language configurations
LANGUAGE_MAP: dict[str, tuple] = {
    ".py": ("python", tspython.language()),
    ".js": ("javascript", tsjavascript.language()),
    ".jsx": ("javascript", tsjavascript.language()),
    ".ts": ("typescript", tstypescript.language_typescript()),
    ".tsx": ("typescript", tstypescript.language_tsx()),
    ".java": ("java", tsjava.language()),
    ".cpp": ("cpp", tscpp.language()),
    ".cc": ("cpp", tscpp.language()),
    ".h": ("cpp", tscpp.language()),
    ".hpp": ("cpp", tscpp.language()),
    ".go": ("go", tsgo.language()),
    ".rs": ("rust", tsrust.language()),
}

# Node types that represent meaningful code blocks
CHUNK_NODE_TYPES: dict[str, set[str]] = {
    "python": {
        "function_definition", "class_definition", "decorated_definition",
    },
    "javascript": {
        "function_declaration", "class_declaration", "method_definition",
        "arrow_function", "export_statement",
    },
    "typescript": {
        "function_declaration", "class_declaration", "method_definition",
        "arrow_function", "export_statement", "interface_declaration",
        "type_alias_declaration",
    },
    "java": {
        "class_declaration", "method_declaration", "interface_declaration",
        "constructor_declaration",
    },
    "cpp": {
        "function_definition", "class_specifier", "struct_specifier",
        "namespace_definition",
    },
    "go": {
        "function_declaration", "method_declaration", "type_declaration",
    },
    "rust": {
        "function_item", "impl_item", "struct_item", "enum_item",
        "trait_item",
    },
}

# Files/dirs to skip during indexing
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".godot", "android", ".gradle",
    "target", "bin", "obj", ".idea", ".vscode",
}
SKIP_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    ".DS_Store", "Thumbs.db",
}
MAX_FILE_SIZE = 100_000  # 100KB - skip huge generated files


@dataclass
class CodeChunk:
    """A meaningful piece of source code."""
    content: str              # the actual code
    file_path: str            # relative path from project root
    language: str             # "python", "javascript", etc.
    start_line: int
    end_line: int
    chunk_type: str           # "function", "class", "module_header", etc.
    name: str                 # function/class name
    context: str = ""         # imports + class header for context
    metadata: dict = field(default_factory=dict)


def get_parser(ext: str) -> tuple[Parser, str] | None:
    """Get a tree-sitter parser for the given file extension."""
    if ext not in LANGUAGE_MAP:
        return None
    lang_name, lang_ptr = LANGUAGE_MAP[ext]
    language = Language(lang_ptr)
    parser = Parser(language)
    return parser, lang_name


def _extract_context(source_bytes: bytes, tree, lang: str) -> str:
    """Extract imports and top-level context from a file."""
    root = tree.root_node
    context_lines = []

    import_types = {
        "python": {"import_statement", "import_from_statement"},
        "javascript": {"import_statement"},
        "typescript": {"import_statement"},
        "java": {"import_declaration", "package_declaration"},
        "cpp": {"preproc_include", "using_declaration"},
        "go": {"import_declaration", "package_clause"},
        "rust": {"use_declaration"},
    }

    target_types = import_types.get(lang, set())

    for child in root.children:
        if child.type in target_types:
            text = source_bytes[child.start_byte:child.end_byte].decode("utf-8", errors="replace")
            context_lines.append(text)

    return "\n".join(context_lines)


def _node_name(node, source_bytes: bytes) -> str:
    """Extract the name of a function/class node."""
    for child in node.children:
        if child.type in ("identifier", "name", "property_identifier"):
            return source_bytes[child.start_byte:child.end_byte].decode("utf-8", errors="replace")
        # For decorated definitions, look inside
        if child.type in ("function_definition", "class_definition"):
            return _node_name(child, source_bytes)
    return "<anonymous>"


def _chunk_type_label(node_type: str) -> str:
    """Convert AST node type to a human-readable label."""
    if "class" in node_type or "struct" in node_type or "impl" in node_type:
        return "class"
    if "function" in node_type or "method" in node_type or "constructor" in node_type:
        return "function"
    if "interface" in node_type or "trait" in node_type:
        return "interface"
    if "type" in node_type or "enum" in node_type:
        return "type"
    return "block"


def chunk_file(file_path: str, project_root: str) -> list[CodeChunk]:
    """Parse a single file and return code chunks."""
    path = Path(file_path)
    ext = path.suffix.lower()

    result = get_parser(ext)
    if result is None:
        return []

    parser, lang_name = result

    try:
        source = path.read_bytes()
    except (OSError, UnicodeDecodeError):
        return []

    if len(source) > MAX_FILE_SIZE:
        return []

    tree = parser.parse(source)
    root = tree.root_node
    rel_path = os.path.relpath(file_path, project_root).replace("\\", "/")

    # Extract file-level context (imports)
    file_context = _extract_context(source, tree, lang_name)

    chunk_types = CHUNK_NODE_TYPES.get(lang_name, set())
    chunks: list[CodeChunk] = []

    # Collect top-level code that isn't inside a function/class
    top_level_lines = []
    covered_ranges = []

    def visit(node, depth=0):
        if node.type in chunk_types:
            code = source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")
            name = _node_name(node, source)

            # For classes, also extract methods as separate chunks
            if "class" in node.type or "struct" in node.type or "impl" in node.type:
                class_header_end = node.start_byte
                for child in node.children:
                    if child.type == "block" or child.type == "class_body" or child.type == "declaration_list":
                        class_header_end = child.start_byte
                        break
                class_header = source[node.start_byte:class_header_end].decode("utf-8", errors="replace")
                context_with_class = file_context + "\n\n" + class_header if file_context else class_header
            else:
                context_with_class = file_context

            chunks.append(CodeChunk(
                content=code,
                file_path=rel_path,
                language=lang_name,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                chunk_type=_chunk_type_label(node.type),
                name=name,
                context=context_with_class,
            ))
            covered_ranges.append((node.start_point[0], node.end_point[0]))
            return  # don't recurse into already-chunked nodes

        for child in node.children:
            visit(child, depth + 1)

    visit(root)

    # If no chunks found (e.g., script with no functions), treat whole file as one chunk
    if not chunks:
        full_text = source.decode("utf-8", errors="replace").strip()
        if full_text and len(full_text) > 20:
            lines = full_text.split("\n")
            chunks.append(CodeChunk(
                content=full_text,
                file_path=rel_path,
                language=lang_name,
                start_line=1,
                end_line=len(lines),
                chunk_type="module",
                name=path.stem,
                context="",
            ))

    return chunks


def collect_files(project_root: str) -> list[str]:
    """Collect all indexable source files from a project directory."""
    files = []
    for dirpath, dirnames, filenames in os.walk(project_root):
        # Filter out skip directories (in-place modification)
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for fname in filenames:
            if fname in SKIP_FILES:
                continue
            ext = os.path.splitext(fname)[1].lower()
            if ext in LANGUAGE_MAP:
                full_path = os.path.join(dirpath, fname)
                files.append(full_path)
    return files


def chunk_project(project_root: str) -> list[CodeChunk]:
    """Chunk an entire project directory."""
    files = collect_files(project_root)
    all_chunks = []
    for f in files:
        all_chunks.extend(chunk_file(f, project_root))
    return all_chunks
