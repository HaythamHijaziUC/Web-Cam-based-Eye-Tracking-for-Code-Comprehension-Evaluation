import ast

class CognitiveComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.nesting_level = 0
        self.line_scores = {}

    def add_score(self, lineno, score):
        if lineno not in self.line_scores:
            self.line_scores[lineno] = 0
        self.line_scores[lineno] += score

    def visit_FunctionDef(self, node):
        old_nesting = self.nesting_level
        self.nesting_level = 0
        self.generic_visit(node)
        self.nesting_level = old_nesting

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_If(self, node):
        is_elif = getattr(node, 'is_elif', False)
        
        # Rule 2 & 3: Decision node increment
        inc = 1 + self.nesting_level
        self.add_score(node.lineno, inc)
        
        # Rule 4: Nesting increases AFTER counting node. ELIF does not increase nesting.
        old_nesting = self.nesting_level
        if not is_elif:
            self.nesting_level += 1
            
        self.visit(node.test)
        
        for stmt in node.body:
            self.visit(stmt)
            
        # Revert nesting exiting the block
        self.nesting_level = old_nesting
        
        # Rule 4 exception and Rule 5 (Else blocks)
        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                # This is an elif!
                node.orelse[0].is_elif = True
                self.visit(node.orelse[0])
            else:
                # Else block: does not add complexity, but inherits nesting_level
                for stmt in node.orelse:
                    self.visit(stmt)

    def visit_For(self, node):
        self.add_score(node.lineno, 1 + self.nesting_level)
        old_nesting = self.nesting_level
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level = old_nesting

    def visit_AsyncFor(self, node):
        self.visit_For(node)

    def visit_While(self, node):
        self.add_score(node.lineno, 1 + self.nesting_level)
        old_nesting = self.nesting_level
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level = old_nesting

    def visit_ExceptHandler(self, node):
        self.add_score(node.lineno, 1 + self.nesting_level)
        old_nesting = self.nesting_level
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level = old_nesting

    def visit_BoolOp(self, node):
        # Rule 7: Boolean conditions (and/or). Each op adds +1 (no nesting penalty)
        score = len(node.values) - 1
        self.add_score(node.lineno, score)
        self.generic_visit(node)
        
    def visit_ListComp(self, node):
        # Rule 8: Comprehensions count as +1, do not increase nesting
        self.add_score(node.lineno, 1)
        self.generic_visit(node)
        
    def visit_SetComp(self, node):
        self.add_score(node.lineno, 1)
        self.generic_visit(node)
        
    def visit_DictComp(self, node):
        self.add_score(node.lineno, 1)
        self.generic_visit(node)
        
    def visit_GeneratorExp(self, node):
        self.add_score(node.lineno, 1)
        self.generic_visit(node)

def extract_full_file_complexity(code_content):
    """
    Parses the full file to generate a map of line_number -> complexity_score.
    Returns an empty dict if the file contains syntax errors.
    """
    try:
        tree = ast.parse(code_content)
        visitor = CognitiveComplexityVisitor()
        visitor.visit(tree)
        return visitor.line_scores
    except SyntaxError:
        return {}

def compute_region_complexity(line_scores, start_line, end_line):
    """
    Sums the cognitive complexity mapped to the specific lines spanning a semantic region.
    """
    total = 0
    # 1-indexed lines from AST
    for i in range(start_line, end_line + 1):
        total += line_scores.get(i, 0)
    return total
