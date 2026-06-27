import re

class Tokenizer:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.tokens = []
        
    def tokenize(self):
        source = re.sub(r'//.*', '', self.source)
        
        patterns = [
            ('FUNC',    r'\bfunc\b'),
            ('VAR',     r'\bvar\b'),
            ('REG',     r'\breg\b'),
            ('RET',     r'\bret\b'),
            ('GOTO',    r'\bgoto\b'),
            ('IF',      r'\bif\b'),
            ('WHILE',   r'\bwhile\b'),
            ('PUSH',    r'\bpush\b'),
            ('POP',     r'\bpop\b'),
            ('NUMBER',  r'0x[0-9a-fA-F]+|\d+'),
            ('REGISTER', r'R\d+'),
            ('LABEL',   r'\w+:'),
            ('NAME',    r'[a-zA-Z_]\w*'),
            ('LBRACK',  r'\['),
            ('RBRACK',  r'\]'),
            ('LPAREN',  r'\('),
            ('RPAREN',  r'\)'),
            ('LBRACE',  r'\{'),
            ('RBRACE',  r'\}'),
            ('COMMA',   r','),
            ('PLUS',    r'\+'),
            ('MINUS',   r'-'),
            ('STAR',    r'\*'),
            ('SLASH',   r'/'),
            ('PERCENT', r'%'),
            ('AND',     r'&'),
            ('OR',      r'\|'),
            ('CARET',   r'\^'),
            ('TILDE',   r'~'),
            ('SHL',     r'<<'),
            ('SHR',     r'>>'),
            ('EQEQ',    r'=='),
            ('NOTEQ',   r'!='),
            ('LTE',     r'<='),
            ('GTE',     r'>='),
            ('LT',      r'<'),
            ('GT',      r'>'),
            ('EQUALS',  r'='),
            ('NEWLINE', r'\n'),
            ('WHITESPACE', r'[ \t]+'),
        ]
        
        master = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in patterns)
        
        for match in re.finditer(master, source):
            kind = match.lastgroup
            value = match.group()
            
            if kind == 'WHITESPACE':
                continue
            elif kind == 'NEWLINE':
                self.tokens.append(('NEWLINE', '\n'))
            elif kind == 'NUMBER':
                if value.startswith('0x'):
                    self.tokens.append(('NUMBER', int(value, 16)))
                else:
                    self.tokens.append(('NUMBER', int(value)))
            elif kind == 'NAME':
                keywords = {'func', 'var', 'reg', 'ret', 'goto', 'if', 'while', 'push', 'pop'}
                if value in keywords:
                    self.tokens.append((kind.upper(), value))
                else:
                    self.tokens.append(('NAME', value))
            else:
                self.tokens.append((kind, value))
        
        return self.tokens


class ACCLCompiler:
    def __init__(self):
        self.vars = {}
        self.regs = {}
        self.output = []
        self.label_counter = 0
        self.current_func = None
        
    def _new_label(self, prefix="L"):
        self.label_counter += 1
        return f"{prefix}_{self.label_counter}"
        
    def _resolve_value(self, tok):
        """Given a token, return an assembly operand string."""
        if tok[0] == 'NUMBER':
            return str(tok[1])
        elif tok[0] == 'REGISTER':
            return tok[1]
        elif tok[0] == 'NAME':
            if tok[1] in self.regs:
                return f'R{self.regs[tok[1]]}'
            elif tok[1] in self.vars:
                return f'0x{self.vars[tok[1]]:02X}'
        return str(tok[1])
    
    def _get_reg_num(self, tok):
        """Get register number from a token."""
        if tok[0] == 'REGISTER':
            return int(tok[1][1:])
        elif tok[0] == 'NAME' and tok[1] in self.regs:
            return self.regs[tok[1]]
        return None
        
    def _emit_branch(self, cond_tok, reg1, val_tok, label):
        """Emit a conditional branch."""
        branch_map = {
            'EQEQ': 'BEQ', 'EQUALS': 'BEQ',
            'NOTEQ': 'BNE',
            'LT': 'BLT', 'GT': 'BGT',
            'LTE': 'BLE', 'GTE': 'BGE',
        }
        op = branch_map.get(cond_tok[0], 'BEQ')
        
        reg2 = self._resolve_value(val_tok)
        
        # If comparing with a number, load into R8 first
        if val_tok[0] == 'NUMBER':
            self.output.append(f'    LDI R8, {val_tok[1]}')
            self.output.append(f'    {op} {reg1}, R8, {label}')
        else:
            self.output.append(f'    {op} {reg1}, {reg2}, {label}')
    
    def compile(self, source):
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()
        print(tokens)
        self._parse(tokens)
        return '\n'.join(self.output)
    
    def _parse(self, tokens):
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            
            if tok[0] == 'NEWLINE':
                i += 1
                continue
            
            # Label
            if tok[0] == 'LABEL':
                self.output.append(tok[1])
                i += 1
                continue
            
            # Variable declaration
            if tok[0] == 'VAR':
                name = tokens[i+1][1]
                addr = tokens[i+3][1]
                self.vars[name] = addr
                i += 4
                continue
            
            # Named register
            if tok[0] == 'REG':
                name = tokens[i+1][1]
                reg = tokens[i+3][1]
                regnum = int(reg[1:])
                self.regs[name] = regnum
                i += 4
                continue
            
            # ret
            if tok[0] == 'RET':
                self.output.append('    RTS')
                i += 1
                continue
            
            # goto
            if tok[0] == 'GOTO':
                label = tokens[i+1][1]
                self.output.append(f'    JMP {label}')
                i += 2
                continue
            
            # if
            if tok[0] == 'IF':
                reg = tokens[i+1][1]
                cond = tokens[i+2]
                val = tokens[i+3]
                label = tokens[i+5][1]
                self._emit_branch(cond, reg, val, label)
                i += 6
                continue
            
            # while REG COND VALUE {
            if tok[0] == 'WHILE':
                start_label = self._new_label("while_start")
                end_label = self._new_label("while_end")
                
                self.output.append(f'{start_label}:')
                
                reg = tokens[i+1][1]
                cond = tokens[i+2]
                val = tokens[i+3]
                
                # Emit opposite branch to exit
                self._emit_branch(cond, reg, val, end_label)  # Need opposite logic here
                
                # Skip the '{'
                i += 4
                if i < len(tokens) and tokens[i][0] == 'LBRACE':
                    i += 1
                continue
            
            # } (end while)
            if tok[0] == 'RBRACE':
                # This is simplified - in real code you'd track nesting
                self.output.append(f'    JMP while_start_placeholder')
                self.output.append(f'while_end_placeholder:')
                i += 1
                continue
            
            # Memory write: [ADDR] = EXPR  or  [REGH, REGL] = EXPR
            if tok[0] == 'LBRACK':
                first = tokens[i+1]
                
                # Indirect: [REGH, REGL] = VALUE
                if (i+4 < len(tokens) and 
                    tokens[i+2][0] == 'COMMA' and
                    tokens[i+3][0] == 'REGISTER'):
                    reg_high = first[1]
                    reg_low = tokens[i+3][1]
                    value = tokens[i+6]  # After RBRACK, EQUALS
                    
                    if value[0] == 'REGISTER':
                        self.output.append(f'    STIND {value[1]}, {reg_high}, {reg_low}')
                    elif value[0] == 'NUMBER':
                        self.output.append(f'    LDI R8, {value[1]}')
                        self.output.append(f'    STIND R8, {reg_high}, {reg_low}')
                    i += 7
                    continue
                
                # Zero page: [ADDR] = VALUE
                addr_val = first
                value = tokens[i+4]  # After RBRACK, EQUALS
                addr_str = self._resolve_value(addr_val)
                
                if value[0] == 'NUMBER':
                    self.output.append(f'    LDI R8, {value[1]}')
                    self.output.append(f'    STZP R8, {addr_str}')
                elif value[0] == 'REGISTER':
                    self.output.append(f'    STZP {value[1]}, {addr_str}')
                elif value[0] == 'NAME':
                    val_str = self._resolve_value(value)
                    self.output.append(f'    STZP {val_str}, {addr_str}')
                
                i += 6
                continue
            
            # Arithmetic / Assignment with '='
            if i+2 < len(tokens) and tokens[i+1][0] == 'EQUALS':
                target = tok
                value_tokens = tokens[i+2:]
                
                # REG = EXPR (with possible operators)
                if target[0] == 'REGISTER':
                    dst = target[1]
                    
                    # Indirect read: REG = [REGH, REGL]
                    if (value_tokens[0][0] == 'LBRACK' and 
                        len(value_tokens) >= 4 and
                        value_tokens[2][0] == 'COMMA'):
                        reg_high = value_tokens[1][1]  # REGISTER token
                        reg_low = value_tokens[3][1]   # REGISTER token
                        self.output.append(f'    LDIND {dst}, {reg_high}, {reg_low}')
                        i += 6  # REG = [ REG , REG ]
                        continue
                    
                    # Memory read: REG = [ADDR] (zero page)
                    if value_tokens[0][0] == 'LBRACK':
                        addr = self._resolve_value(value_tokens[1])
                        self.output.append(f'    LDZP {dst}, {addr}')
                        i += 5
                        continue
                    
                    # Simple assignment: REG = VALUE
                    if value_tokens[0][0] in ('NUMBER', 'REGISTER', 'NAME'):
                        # Check if next token is operator or end-of-line
                        if len(value_tokens) == 1 or value_tokens[1][0] in ('NEWLINE',):
                            val = value_tokens[0]
                            if val[0] == 'NUMBER':
                                self.output.append(f'    LDI {dst}, {val[1]}')
                            elif val[0] == 'REGISTER':
                                if dst != val[1]:
                                    self.output.append(f'    TRA {dst}, {val[1]}')
                            elif val[0] == 'NAME':
                                val_str = self._resolve_value(val)
                                if val_str.startswith('R'):
                                    self.output.append(f'    TRA {dst}, {val_str}')
                                else:
                                    self.output.append(f'    LDZP {dst}, {val_str}')
                            i += 3
                            continue
                    
                    # Arithmetic: REG = REG OP REG/NUMBER
                    if len(value_tokens) >= 3:
                        src1 = value_tokens[0]
                        op_tok = value_tokens[1]
                        src2 = value_tokens[2]
                        
                        op_map = {
                            'PLUS': 'ADD', 'MINUS': 'SUB',
                            'STAR': 'MUL', 'SLASH': 'DIV', 'PERCENT': 'MOD',
                            'AND': 'AND', 'OR': 'OR', 'CARET': 'XOR', 'SHL': 'SHL',
                            'SHR': 'SHR'
                        }
                        
                        if op_tok[0] in op_map:
                            src1_str = self._resolve_value(src1)
                            src2_str = self._resolve_value(src2)
                            
                            if src2[0] == 'NUMBER':
                                self.output.append(f'    LDI R9, {src2[1]}')
                                self.output.append(f'    {op_map[op_tok[0]]} {dst}, {src1_str}, R9')
                            else:
                                self.output.append(f'    {op_map[op_tok[0]]} {dst}, {src1_str}, {src2_str}')
                            i += 5
                            continue
                
                # Variable assignment: VARNAME = EXPR
                if target[0] == 'NAME':
                    if target[1] in self.vars:
                        addr = self.vars[target[1]]
                        val = value_tokens[0]
                        
                        if val[0] == 'NUMBER':
                            self.output.append(f'    LDI R8, {val[1]}')
                            self.output.append(f'    STZP R8, 0x{addr:02X}')
                        elif val[0] == 'REGISTER':
                            self.output.append(f'    STZP {val[1]}, 0x{addr:02X}')
                        elif val[0] == 'NAME':
                            val_str = self._resolve_value(val)
                            self.output.append(f'    STZP {val_str}, 0x{addr:02X}')
                        
                        i += 3
                        continue
                    elif target[1] in self.regs:
                        reg = self.regs[target[1]]
                        val = value_tokens[0]
                        
                        if val[0] == 'NUMBER':
                            self.output.append(f'    LDI R{reg}, {val[1]}')
                        elif val[0] == 'REGISTER':
                            self.output.append(f'    TRA E{reg}, R{val[0]}')
                        elif val[0] == 'NAME':
                            val_str = self._resolve_value(val)
                            if val[1] in self.regs:
                                # Named register to named register
                                src_reg = self.regs[val[1]]
                                self.output.append(f'    TRA R{reg}, R{src_reg}')
                            elif val[1] in self.vars:
                                # Load variable into named register
                                addr = self.vars[val[1]]
                                self.output.append(f'    LDZP R{reg}, 0x{addr:02X}')
                            else:
                                # Assume it's a label or something else
                                val_str = self._resolve_value(val)
                                self.output.append(f'    TRA R{reg}, {val_str}')
                        
                        i += 3
                        continue
            # Function call
            if tok[0] == 'NAME' and i+1 < len(tokens) and tokens[i+1][0] == 'LPAREN':
                funcname = tok[1]
                self.output.append(f'    JSR {funcname}')
                i += 3
                continue
            
            # PUSH regs
            if tok[0] == 'PUSH':
                regs = []
                j = i + 1
                while j < len(tokens) and tokens[j][0] in ('REGISTER', 'COMMA'):
                    if tokens[j][0] == 'REGISTER':
                        regs.append(tokens[j][1])
                    j += 1
                for reg in regs:
                    self.output.append(f'    PSH {reg}')
                i = j
                continue
            
            # POP regs
            if tok[0] == 'POP':
                regs = []
                j = i + 1
                while j < len(tokens) and tokens[j][0] in ('REGISTER', 'COMMA'):
                    if tokens[j][0] == 'REGISTER':
                        regs.append(tokens[j][1])
                    j += 1
                for reg in reversed(regs):
                    self.output.append(f'    POP {reg}')
                i = j
                continue
            
            # Unknown
            i += 1

import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python accl.py input.accl [output.asm]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.accl', '.asm')
    
    with open(input_file, 'r') as f:
        source = f.read()
    
    
    compiler = ACCLCompiler()
    asm = compiler.compile(source)
    
    with open(output_file, 'w') as f:
        f.write(asm)
    
    print(f"Compiled {input_file} -> {output_file}")
