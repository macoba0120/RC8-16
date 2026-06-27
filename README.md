# RC8-16

## Overview

This project contains a full CPU. Along with it are:  
	- an assembler  
	- a ROM that persists and can be overwritten  
	- a monitor program, inspired by Wozmon  
	- a new programming language (only for the ISA the CPU uses)  

## The CPU's specifications

The CPU is simple, having 8-bit data and 16-bit addresses. It has 16 registers, plus the stack pointer and the program counter. It has 36 instructions, split into 4 groups:  
	- 0x0X (where X is any digit): Data movement (all kinds of loads and stores)  
	- 0x1X: Arithmetic operations (addition, subtraction, modulos, bitwise ORs, you name it)  
	- 0x2X: Flow control (jump, jump to subroutine, branches)  
	- 0xFX: Special (write pixel, halt)  

## The assembler

It is also pretty simple. The last section of this README details about it and the assembly.  

## The custom programming language

This one...  
  
is still simple. It's something between C and assembly, hence the name ACCL (Assembly-C Combined Language). Full testing to be done.

## The ROM

There is a file named persistent_rom.bin in this project. This is the ROM of the CPU, loaded upon boot. It contains:  
	- A monitor program inspired by Wozmon  
	- Snake game  
	- A Fibonacci sequence printer  
	- A visual memory viewer (literally shows the memory)  

## The assembly

TBD
