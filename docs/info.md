<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works
This will be a 4 bit FFT Engine.

This is the google doc detailing the arch, timing diagrams, etc
``https://docs.google.com/document/d/13jseVi1bMsw91EZKD1t0jHazFGBT2K84RPKfIGI_DeA/edit?tab=t.0#heading=h.6vw8kxunlpo9``

## How to test (Post silicon)
Switches: The PCB has 8 input switches. Switch 0 will be used to control the input; turning it on once will indicate the loading of the first 2 8-bit samples using the input and bidirectional pins, while switching it on a second time will indicate the loading of the other 2 8-bit samples. Switch 1 will be used to control the output; turning it on once will indicate the output of the first 2 frequency groups, while turning it on a second time will indicate the output of the next 2 frequency groups.

7 Segment display: The display will be used to show the user the current mode of operation: 
1: Input/Load the first 2 samples
2: Input/Load the next 2 samples
C: Calculating FFT
3: Output/Read the first 2 frequency groups
4: Output/Read the next 2 frequency groups

## External hardware
7 segment display, switches