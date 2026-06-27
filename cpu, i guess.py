import random
import sys
from assembler import Assembler

class CPU:
    def __init__(self):
        self.registers = [0] * 16
        self.sp = 0x0FFF
        
        self.rom = [0] * (56*1024)
        self.ram = [0] * ((64-56)*1024)
        
        reset_high = self.rom[0xDFFF]
        reset_low = self.rom[0xDFFE]
        self.pc = (reset_high << 8) | reset_low
        
        self.running = False
        
        self.serial_input_buffer = []  # Queue for incoming characters
        self.serial_output_buffer = []  # For echo if needed
    
    def read_byte(self, mem_location):
        if(mem_location == 0x0003):
            return random.randint(0, 255)
        elif mem_location == 0x0004:  # Serial status
            # Bit 0: data available, Bit 1: ready to transmit
            status = 0
            if self.serial_input_buffer:
                status |= 0x01  # Data available
            status |= 0x02  # Always ready to transmit
            return status
        elif mem_location == 0x0005:  # Serial data read
            if self.serial_input_buffer:
                return self.serial_input_buffer.pop(0)
            return 0
        elif(mem_location >= 0x2000):
            return self.rom[mem_location-0x2000]
        else:
            return self.ram[mem_location]
    
    def write_byte(self, mem_location, byte):
        byte &= 0xFF
        if mem_location == 0x0005:  # Serial output
            sys.stdout.write(chr(byte))
            sys.stdout.flush()
            return
        elif mem_location < 0x2000:
            self.ram[mem_location] = byte
        elif mem_location >= 0x2400:
            self.rom[mem_location-0x2000] = byte
        else:
            raise ValueError(f"Memory location {mem_location} not in RAM")
    
    def push_byte(self, byte):
        if self.sp > 0:
            byte &= 0xFF
            self.ram[self.sp] = byte
            self.sp -= 1
        else:
            raise ValueError("Stack overflowed. Please don't forget a stopping case if doing recursion.")
    
    def pop_byte(self):
        if self.sp < 0x1FFF:
            self.sp += 1
            return self.ram[self.sp]
        else:
            raise ValueError("Stack underflowed. Either there is ACE or you royally messed up.")
    
    def jsr(self, jmp_location):
        if jmp_location <= 0xFFFF:
            self.push_byte((self.pc >> 8) & 0xFF)
            self.push_byte(self.pc & 0xFF)
            self.pc = jmp_location
        else:
            raise ValueError("Jump outside of range. How did you mess up this bad?")
    
    def rts(self):
        low_byte = self.pop_byte() & 0xFF
        high_byte = self.pop_byte() & 0xFF
        self.pc = (high_byte << 8) | low_byte

    def exec_instruction(self, opcode):
        match opcode:
            case 0x00: #LDI
                dst = (self.read_byte(self.pc + 1) >> 4) & 0xF
                self.pc += 1
                imm = self.read_byte(self.pc + 1)
                self.pc += 1
                self.registers[dst] = imm
            case 0x01: #TRA
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                dst = (regs >> 4) & 0xF
                src = regs & 0xF
                self.registers[dst] = self.registers[src]
            case 0x02: #LDM
                dst = (self.read_byte(self.pc + 1) >> 4) & 0xF
                self.pc += 1
                low_byte = self.read_byte(self.pc + 1)
                self.pc += 1
                high_byte = self.read_byte(self.pc + 1)
                self.pc += 1
                addr = (high_byte << 8) | low_byte
                self.registers[dst] = self.read_byte(addr)
            case 0x03: #LDZP
                dst = (self.read_byte(self.pc + 1) >> 4) & 0xF
                self.pc += 1
                addr = self.read_byte(self.pc + 1)
                self.pc += 1
                self.registers[dst] = self.read_byte(addr)
            case 0x04: #STM
                src = self.read_byte(self.pc + 1) & 0xF
                self.pc += 1
                low_byte = self.read_byte(self.pc + 1)
                self.pc += 1
                high_byte = self.read_byte(self.pc + 1)
                self.pc += 1
                addr = (high_byte << 8) | low_byte
                self.write_byte(addr, self.registers[src])
            case 0x05: #STZP
                src = self.read_byte(self.pc + 1) & 0xF
                self.pc += 1
                addr = self.read_byte(self.pc + 1)
                self.pc += 1
                self.write_byte(addr, self.registers[src])
            case 0x06: #LDIND
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                dst = (regs >> 4) & 0xF
                reg_high = (regs & 0x0F)
                reg_low = self.read_byte(self.pc + 1) & 0x0F
                self.pc += 1
                addr = (self.registers[reg_high] << 8) | self.registers[reg_low]
                self.registers[dst] = self.read_byte(addr)
            case 0x07: #STIND
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                src = (regs >> 4) & 0xF
                reg_high = (regs & 0x0F)
                reg_low = self.read_byte(self.pc + 1) & 0x0F
                self.pc += 1
                addr = (self.registers[reg_high] << 8) | self.registers[reg_low]
                self.write_byte(addr, self.registers[src])
            case 0x08: #PSH
                reg = self.read_byte(self.pc + 1) & 0xF
                self.pc += 1
                self.push_byte(self.registers[reg])
            case 0x09: #POP
                reg = self.read_byte(self.pc + 1) & 0xF
                self.pc += 1
                self.registers[reg] = self.pop_byte()
            case 0x10: #ADD
                dst = (self.read_byte(self.pc + 1) >> 4) & 0xF
                self.pc += 1
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                src2 = (regs >> 4) & 0xF
                src1 = regs & 0xF
                self.registers[dst] = (self.registers[src1] + self.registers[src2]) & 0xFF
            case 0x11: #SUB
                dst = (self.read_byte(self.pc + 1) >> 4) & 0xF
                self.pc += 1
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                src2 = (regs >> 4) & 0xF
                src1 = regs & 0xF
                self.registers[dst] = (self.registers[src1] - self.registers[src2]) & 0xFF
            case 0x12: #MUL
                dsts = self.read_byte(self.pc + 1)
                self.pc += 1
                dst1 = (dsts >> 4) & 0xF
                dst2 = dsts & 0xF
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                src2 = (regs >> 4) & 0xF
                src1 = regs & 0xF
                result = src1 * src2
                self.registers[dst2] = (result >> 8) & 0xFF
                self.registers[dst1] = result & 0xFF
            case 0x13: #DIV
                dst = (self.read_byte(self.pc + 1) >> 4) & 0xF
                self.pc += 1
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                src2 = (regs >> 4) & 0xF
                src1 = regs & 0xF
                try:
                    self.registers[dst] = self.registers[src1] // self.registers[src2]
                except ZeroDivisionError:
                    print(f"Zero division error at instruction {self.pc-2}, check for bugs. Set register R{dst} to 0.")
                    self.registers[dst] = 0
            case 0x14: #MOD
                dst = (self.read_byte(self.pc + 1) >> 4) & 0xF
                self.pc += 1
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                src2 = (regs >> 4) & 0xF
                src1 = regs & 0xF
                try:
                    self.registers[dst] = self.registers[src1] % self.registers[src2]
                except ZeroDivisionError:
                    print(f"Zero division error at instruction {self.pc - 2}, check for bugs. Set register R{dst} to 0.")
                    self.registers[dst] = 0
            case 0x15: #AND
                dst = (self.read_byte(self.pc + 1) >> 4) & 0xF
                self.pc += 1
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                src2 = (regs >> 4) & 0xF
                src1 = regs & 0xF
                self.registers[dst] = self.registers[src1] & self.registers[src2]
            case 0x16: #OR
                dst = (self.read_byte(self.pc + 1) >> 4) & 0xF
                self.pc += 1
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                src2 = (regs >> 4) & 0xF
                src1 = regs & 0xF
                self.registers[dst] = self.registers[src1] | self.registers[src2]
            case 0x17: #NOT
                dst = (self.read_byte(self.pc + 1) >> 4) & 0xF
                src = self.read_byte(self.pc + 1) & 0xF
                self.pc += 1
                self.registers[dst] = (~self.registers[src]) & 0xFF
            case 0x18: #NAND
                dst = (self.read_byte(self.pc + 1) >> 4) & 0xF
                self.pc += 1
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                src2 = (regs >> 4) & 0xF
                src1 = regs & 0xF
                self.registers[dst] = (~(self.registers[src1] & self.registers[src2])) & 0xFF
            case 0x19: #NOR
                dst = (self.read_byte(self.pc + 1) >> 4) & 0xF
                self.pc += 1
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                src2 = (regs >> 4) & 0xF
                src1 = regs & 0xF
                self.registers[dst] = (~(self.registers[src1] | self.registers[src2])) & 0xFF
            case 0x1A: #XOR
                dst = (self.read_byte(self.pc + 1) >> 4) & 0xF
                self.pc += 1
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                src2 = (regs >> 4) & 0xF
                src1 = regs & 0xF
                self.registers[dst] = self.registers[src1] ^ self.registers[src2]
            case 0x1B: #XNOR
                dst = (self.read_byte(self.pc + 1) >> 4) & 0xF
                self.pc += 1
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                src2 = (regs >> 4) & 0xF
                src1 = regs & 0xF
                self.registers[dst] = (~(self.registers[src1] ^ self.registers[src2])) & 0xFF
            case 0x1C: #SHL - shift left
                dst = (self.read_byte(self.pc + 1) >> 4) & 0xF
                self.pc += 1
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                amount = (regs >> 4) & 0xF
                src = regs & 0xF
                self.registers[dst] = (self.registers[src] << self.registers[amount]) & 0xFF
            
            case 0x1D: #SHR - shift right
                dst = (self.read_byte(self.pc + 1) >> 4) & 0xF
                self.pc += 1
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                amount = (regs >> 4) & 0xF
                src = regs & 0xF
                self.registers[dst] = (self.registers[src] >> self.registers[amount]) & 0xFF
            case 0x20: #JMP
                low_byte = self.read_byte(self.pc + 1)
                self.pc += 1
                high_byte = self.read_byte(self.pc + 1)
                self.pc += 1
                addr = (high_byte << 8) | low_byte
                self.pc = addr
                return True
            case 0x21: #JSR
                low_byte = self.read_byte(self.pc + 1)
                self.pc += 1
                high_byte = self.read_byte(self.pc + 1)
                self.pc += 1
                addr = (high_byte << 8) | low_byte
                self.jsr(addr)
                return True
            case 0x22: #RTS
                self.rts()
            case 0x23: #BEQ
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                reg1 = (regs >> 4) & 0xF
                reg2 = regs & 0xF
                low_byte = self.read_byte(self.pc + 1)
                self.pc += 1
                high_byte = self.read_byte(self.pc + 1)
                self.pc += 1
                addr = (high_byte << 8) | low_byte
                if self.registers[reg1] == self.registers[reg2]:
                    self.pc = addr
                    return True
            case 0x24: #BNE
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                reg1 = (regs >> 4) & 0xF
                reg2 = regs & 0xF
                low_byte = self.read_byte(self.pc + 1)
                self.pc += 1
                high_byte = self.read_byte(self.pc + 1)
                self.pc += 1
                addr = (high_byte << 8) | low_byte
                if self.registers[reg1] != self.registers[reg2]:
                    self.pc = addr
                    return True
            case 0x25: #BGT
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                reg1 = (regs >> 4) & 0xF
                reg2 = regs & 0xF
                low_byte = self.read_byte(self.pc + 1)
                self.pc += 1
                high_byte = self.read_byte(self.pc + 1)
                self.pc += 1
                addr = (high_byte << 8) | low_byte
                if self.registers[reg1] > self.registers[reg2]:
                    self.pc = addr
                    return True
            case 0x26: #BLT
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                reg1 = (regs >> 4) & 0xF
                reg2 = regs & 0xF
                low_byte = self.read_byte(self.pc + 1)
                self.pc += 1
                high_byte = self.read_byte(self.pc + 1)
                self.pc += 1
                addr = (high_byte << 8) | low_byte
                if self.registers[reg1] < self.registers[reg2]:
                    self.pc = addr
                    return True
            case 0x27: #BGE
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                reg1 = (regs >> 4) & 0xF
                reg2 = regs & 0xF
                low_byte = self.read_byte(self.pc + 1)
                self.pc += 1
                high_byte = self.read_byte(self.pc + 1)
                self.pc += 1
                addr = (high_byte << 8) | low_byte
                if self.registers[reg1] >= self.registers[reg2]:
                    self.pc = addr
                    return True
            case 0x28: #BLE
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                reg1 = (regs >> 4) & 0xF
                reg2 = regs & 0xF
                low_byte = self.read_byte(self.pc + 1)
                self.pc += 1
                high_byte = self.read_byte(self.pc + 1)
                self.pc += 1
                addr = (high_byte << 8) | low_byte
                if self.registers[reg1] <= self.registers[reg2]:
                    self.pc = addr
                    return True
            case 0x29: #JMPI - Jump indirect through register pair
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                reg_high = (regs >> 4) & 0xF
                reg_low = regs & 0xF
                addr = (self.registers[reg_high] << 8) | self.registers[reg_low]
                self.pc = addr
                return True
            case 0xF0: #WPX
                regs = self.read_byte(self.pc + 1)
                self.pc += 1
                y_reg = (self.read_byte(self.pc + 1)>>4) & 0xF
                self.pc += 1
                col_reg = (regs >> 4) & 0xF
                x_reg = regs & 0xF
                addr = 0x1000 + (self.registers[y_reg]*64) + self.registers[x_reg]
                self.write_byte(addr, self.registers[col_reg])
            case 0xFF: #HLT
                for i in range(0x1000):
                    self.ram[i+0x1000] = 0
                reset_high = self.rom[0xDFFF]
                reset_low = self.rom[0xDFFE]
                self.pc = (reset_high << 8) | reset_low
                return True
            case _:
                print(f"Unknown opcode: {opcode:02X} at PC={self.pc:04X}. Halting.")
                return False
        self.pc += 1
        return True
    
    def run_program(self, display=None):
        reset_high = self.rom[0xDFFF]
        reset_low = self.rom[0xDFFE]
        self.pc = (reset_high << 8) | reset_low
        self.running = True
        self.fc = 0
        while self.running:
            opcode = self.read_byte(self.pc)
            self.running = self.exec_instruction(opcode)
            self.fc += 1
            if display and self.fc == 1000:
                display.update()
                self.fc = 0
                if not display.running:
                    self.running = False
        print(f"RAM[0x0000] (strobe) = 0x{self.ram[0]:02X}")
        print(f"RAM[0x1000] (first pixel) = 0x{self.ram[0x1000]:02X}")
        print(f"RAM[0x1001] (second pixel) = 0x{self.ram[0x1001]:02X}")
        print(f"Registers: R0=0x{self.registers[0]:02X}, R1=0x{self.registers[1]:02X}, R2=0x{self.registers[2]:02X}")
        # In run_program, after the while loop:
        if display:
            display.render_framebuffer()  # Force one final render

import pygame
import time

class Display:
    def __init__(self, cpu, scale=8):
        self.cpu = cpu
        self.scale = scale  # Each pixel becomes 8x8 on screen
        self.width = 64
        self.height = 64
        
        pygame.init()
        self.screen = pygame.display.set_mode((self.width * scale, self.height * scale))
        pygame.display.set_caption("CPU Display")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Pre-compute the color palette (2 bits per channel = 64 colors)
        self.palette = []
        for i in range(64):
            r = ((i >> 4) & 0x03) * 85  # 0, 85, 170, 255
            g = ((i >> 2) & 0x03) * 85
            b = (i & 0x03) * 85
            self.palette.append((r, g, b))
    
    def render_framebuffer(self):
        for y in range(self.height):
            for x in range(self.width):
                addr = 0x1000 + (y * self.width) + x
                pixel = self.cpu.read_byte(addr)
                color_index = pixel & 0x3F  # Extract 6-bit color
                color = self.palette[color_index]
                
                rect = (x * self.scale, y * self.scale, self.scale, self.scale)
                self.screen.fill(color, rect)
        
        pygame.display.flip()
    
    # In Display class, add to update():
    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.cpu.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    self.cpu.running = False
                elif event.key == pygame.K_RETURN:
                    self.cpu.serial_input_buffer.append(0x0A)  # LF
                elif event.key == pygame.K_BACKSPACE:
                    self.cpu.serial_input_buffer.append(0x08)
                elif event.unicode and ord(event.unicode) < 128:
                    self.cpu.serial_input_buffer.append(ord(event.unicode))
                # Arrow keys still for game input
                elif event.key == pygame.K_UP:
                    self.cpu.write_byte(0x0002, 0x01)
                elif event.key == pygame.K_DOWN:
                    self.cpu.write_byte(0x0002, 0x02)
                elif event.key == pygame.K_LEFT:
                    self.cpu.write_byte(0x0002, 0x03)
                elif event.key == pygame.K_RIGHT:
                    self.cpu.write_byte(0x0002, 0x04)
            elif event.type == pygame.KEYUP:
                self.cpu.write_byte(0x0002, 0x00)
        
        # Graphics strobe
        strobe = self.cpu.read_byte(0x0000)
        if strobe != 0:
            self.render_framebuffer()
            self.cpu.write_byte(0x0000, 0)
            self.cpu.write_byte(0x0001, 0x01)
        
        self.clock.tick(60)

def create_rom(program_bytes, start_addr=0x2000):
    """Create a 56KB ROM with program and reset vector"""
    rom = [0] * (56 * 1024)
    
    # Write program
    rom_offset = start_addr - 0x2000
    for i, byte in enumerate(program_bytes):
        rom[rom_offset + i] = byte
    
    # Set reset vector
    rom[0xFFFF - 0x2000] = (start_addr >> 8) & 0xFF
    rom[0xFFFE - 0x2000] = start_addr & 0xFF
    
    return rom

with open("program.asm", "r") as program:
    cpu = CPU()
    try:
        with open('persistent_rom.bin', 'rb') as f:
            saved_rom = list(f.read())
            if len(saved_rom) == 56*1024:
                cpu.rom = saved_rom
    except FileNotFoundError:
        assembler = Assembler()
        machine_code = assembler.assemble(program.read())
        print("\nLabels:")
        for label, addr in sorted(assembler.labels.items()):
            print(f"  {label}: 0x{addr:04X}")
        for i, byte in enumerate(machine_code):
            if i % 16 == 0:
                print(f"\n{i:04X}: ", end = "")
            print(f"{byte:02X} ", end = "")
        print("\n")
        cpu.rom = machine_code
        input("Press enter to continue...")
    display = Display(cpu)
    paste_data = input("Paste hex string (or press Enter to skip): ")
    if paste_data:
        for char in paste_data:
            cpu.serial_input_buffer.append(ord(char))
        cpu.serial_input_buffer.append(0x0A)  # Enter at the end
    cpu.run_program(display)
    
    # Keep window open for a few seconds after program halts
    input("Program halted. Press enter to end the session... ")
    
    pygame.quit()
    with open('persistent_rom.bin', 'wb') as f:
        f.write(bytes(cpu.rom))
