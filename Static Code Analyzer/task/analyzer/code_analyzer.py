import os.path
import sys
import re
import ast

MAX_LENGTH = 79


class Pep8:

    def __init__(self, file: 'path to a file'):
        self.file_path = file
        self.blank_lines = 0

        with open(file, 'r') as _f:
            self.source = _f.readlines()

        with open(file, 'r') as _f:
            self.full_source = _f.read()

    def s001(self, line: str) -> bool:
        return len(line) > MAX_LENGTH

    def s002(self, line: str) -> bool:
        if len(line.strip()) > 0:
            return (len(line) - len(line.lstrip())) % 4 != 0
        return False

    def s003(self, line: str) -> bool:
        line.strip().endswith(';')
        return line.strip().endswith(';')

    def s004(self, line: str, comment: str) -> bool:
        if not line.startswith('#'):
            return not line[:line.rfind('#', 0, -len(comment))].endswith('  ')
        return False

    def s005(self, comment: str) -> bool:
        return 'todo' in comment.lower()

    def s006(self, line: str) -> bool:
        if len(line.strip()) == 0:
            self.blank_lines += 1
        else:
            if self.blank_lines > 2:
                self.blank_lines = 0
                return True
            self.blank_lines = 0
        return False

    def s007(self, line: str) -> (bool, str):
        line = line.lstrip()
        template = r'^\w+\s\S+'
        if line.startswith('class'):
            return re.match(template, line) is None, 'class'
        if line.startswith('def'):
            return re.match(template, line) is None, 'def'
        return False, ''

    def s008(self, line: str) -> (bool, str):
        template = r'^class +[A-Z][a-z]+([A-Z][a-z]+)?+\(?([a-zA-Z]+)?\)?:$'
        if line.startswith('class '):
            class_name = re.findall(r' \w+', line)
            return re.match(template, line) is None, class_name[0][1:]
        return False, ''

    def s009(self, line_no: int) -> (bool, str):
        # line = line.lstrip()
        template_func_name = r'^[a-z_]+[a-z_0-9]?$'
        tree = ast.parse(self.full_source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if line_no == node.lineno:
                    if not re.match(template_func_name, node.name):
                        self.print_warning(node.lineno, '009', f'Function name \'{node.name}\' should be written snake_case')
                    # check for argument name
                    for argument in node.args.args:
                        if not re.match(template_func_name, argument.arg):
                            self.print_warning(node.lineno, '010', f'Argument name \'{argument.arg}\' should be snake_case')
                    # check for variables
                    for child in ast.iter_child_nodes(node):
                        if isinstance(child, ast.Assign):
                            _var = child.targets[0]
                            if isinstance(_var, ast.Name) and isinstance(_var.ctx, ast.Store):
                                if not re.match(template_func_name, _var.id):
                                    self.print_warning(node.lineno + 1, '011', f'Variable \'{_var.id}\' in function should be snake_case')
                    # check for mutable default arguments
                    for argument in node.args.defaults:

                        if isinstance(argument, (ast.List, ast.Set, ast.Dict)):
                            self.print_warning(node.lineno, '012', 'Default argument value is mutable')
        # if line.startswith('def '):
        #     fun_name = re.findall(r' \w+', line)
        #     return re.match(template_func_name, line) is None, fun_name[0][1:]
        # return False, ''

    def s010(self):
        template = r'^[a-z_]+$'
        tree = ast.parse('\n'.join(self.source))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # check for s011
                for a in node.args.args:
                    if not re.match(template, a.arg):
                        self.print_warning(a.lineno, '011', f'Argument name \'{a.arg}\' should be snake_case')
                # check for s012
                for d in node.args.defaults:
                    if isinstance(d, ast.List) or isinstance(d, ast.Dict) or isinstance(d, ast.Set):
                        self.print_warning(d.lineno, '012', 'Default argument value is mutable')
                # check for s010
                for e in node.body:

                    if isinstance(e, ast.Assign):
                        var_name = e.targets[0].id
                        if not re.match(template, var_name):
                            self.print_warning(e.lineno, '010', f'Variable \'{var_name}\' in function should be '
                                                                f'snake_case')

    def find_comment(self, line: str) -> tuple:
        split_line = line.split('#')
        if len(split_line) > 1:
            # possible there is a comment
            possible_comment = '#'.join(split_line[1:]).strip()
            # check if it is an inline comment, not inside a string
            # if split_line[0].count('"') % 2 == 0 and split_line[0].count("'") % 2 == 0:
            return possible_comment, split_line[0]
        return None, None

    def print_warning(self, index, code, message):
        print(f'{self.file_path}: Line {index}: S{code} {message}')

    def run(self):
        for index, line in enumerate(self.source, start=1):
            if self.s001(line):
                self.print_warning(index, '001', 'Too long')
            if self.s002(line):
                self.print_warning(index, '002', 'Indentation is not a multiple of four')
            _comment, line_without_comment = self.find_comment(line)
            if _comment:
                line_bak = line
                line = line_without_comment
            if self.s003(line):
                self.print_warning(index, '003', 'Unnecessary semicolon')
            if _comment:
                if self.s004(line_bak, _comment):
                    self.print_warning(index, '004', 'At least two spaces required before inline comments')
                if self.s005(_comment):
                    self.print_warning(index, '005', 'TODO found')
            if not _comment:
                if self.s006(line):
                    self.print_warning(index, '006', 'More than two blank lines used before this line')
            _s007, _type = self.s007(line)
            if _s007:
                self.print_warning(index, '007', f'Too many spaces after \'{_type}\'')
            _s008, _name = self.s008(line)
            if _s008:
                self.print_warning(index, '008', f'Class name \'{_name}\' should be written CamelCase')
            self.s009(index)
            # if _s009:
            #     self.print_warning(index, '009', f'Function name \'{_name}\' should be written snake_case')
            # self.s010()

path = sys.argv[1]
if os.path.isdir(path):
    for _file in sorted(os.listdir(path)):
        if _file.endswith('.py'):
            analyzer = Pep8(os.path.join(path, _file))
            analyzer.run()
elif path.endswith('.py'):
    analyzer = Pep8(path)
    analyzer.run()
