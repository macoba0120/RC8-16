# RC8-16

## Overview

This project contains a full CPU. Along with it are:  
	- an assembler  
	- a ROM that persists and can be overwritten  
	- a monitor program, inspired by Wozmon  
	- a new programming language (only for the ISA the CPU uses)  
	- a pygame screen (addresses 0x1000-0x1FFF), also provides inputs (and serial input)

## The CPU's specifications

The CPU is simple, having 8-bit data and 16-bit addresses. It has 16 registers, plus the stack pointer and the program counter. It has 36 instructions, split into 4 groups:  
	- 0x0X (where X is any digit): Data movement (all kinds of loads and stores)  
	- 0x1X: Arithmetic operations (addition, subtraction, modulos, bitwise ORs, you name it)  
	- 0x2X: Flow control (jump, jump to subroutine, branches)  
	- 0xFX: Special (write pixel, halt)  

## The assembler

It is also pretty simple. The last section of this README details about it and the assembly, and also has a guide.  

## The custom programming language

This one...  
  
is still simple. It's something between C and assembly, hence the name ACCL (Assembly-C Combined Language). Full testing to be done.

## The ROM

There is a file named persistent_rom.bin in this project. This is the ROM of the CPU, loaded upon boot. It contains:  
	- A monitor program inspired by Wozmon (0x0000-0x03FF) (don't overwrite, boots into this!)  
	- Snake (0x0400-0x07FF)  
	- A Fibonacci sequence printer (0x0800-0x08FF)  
	- A visual memory viewer (literally shows the memory on screen) (0x0900-0x09FF) 

## The assembler/assembly programming guide

The assembler is used by running it in a terminal and writing the output to persistent_rom.bin using write.py. When running without arguments, it prints the intended usage and crashes. The assembly has many instructions, but here are the most often used ones:  
	- LDI (register), (value to load) - load immediate  
	- LDZP (register), (zero page address) - load zero page  
	- STZP (register), (zero page address) - store zero page  
	- ADD/SUB/DIV/MOD/AND/OR/XOR (destination register), (source 1), (source 2) - do an arithmetic operation on the source registers and put the result in the destination register  
	- MUL (destination high), (destination low), (source 1), (source 2) - multiply the two sources together and store the high byte in the destination high register and the low byte in the destination low register.  
	- WPX (color), (x), (y) - write a pixel to the framebuffer  
	- NOT (destination), (source) - do a bitwise NOT on the source register and store it in the destination register  
	- HLT - halt  
Registers are R0-R15. There are a few built-in memory-mapped registers, they are:  
	- 0x00: Strobe (reads 0, writing causes the framebuffer to appear on screen)  
	- 0x01: Screen ready (writing 0 clears it, read starts outputting 1 at the end of each frame)  
	- 0x02: Arrow input (up = 1, down = 2, left = 3, right = 4, released = 0)  
	- 0x03: Random register  
	- 0x04: Serial status (bit 0 = data ready flag, bit 1 = ready to transmit flag)
	- 0x05: Serial data (write prints a letter to the terminal, read reads the last input)