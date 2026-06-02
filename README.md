# WidgetAI

WidgetAI is a floating desktop widget that lets users send prompts to ChatGPT, Claude, or Perplexity and read the responses directly inside a compact Apple-style interface.

It is designed to remove browser friction: no tab switching, no manual copy-pasting, and no need to manage multiple AI websites separately.

---

## Overview

WidgetAI starts as a compact, wide desktop widget inspired by Apple’s medium widget layout, then expands into a larger panel when a response is available. The visible interface stays minimal, while the actual AI interaction runs through a hidden embedded browser powered by Qt WebEngine.

The result is a lightweight desktop workflow for querying multiple AI providers from one persistent floating widget.

---

## Features

- **Floating always-on-top widget**: stays visible above other windows for fast access while working.
- **Compact-to-expanded layout**: rests in a medium-style format and expands automatically when a response arrives.
- **Unified AI access**: supports ChatGPT, Claude, and Perplexity through one consistent command interface.
- **Inline response display**: answers are shown directly inside the widget in a read-only output panel.
- **Background browser automation**: prompts are sent through a hidden Qt WebEngine worker window, keeping the user-facing UI clean.
- **Command history support**: recent prompts can be viewed from inside the widget.

---

## Usage

Enter a slash command followed by a prompt, then press Enter.

```text
/chatgpt explain how sorting algorithms work
/claude write a cover letter for a software engineering role
/perplexity what is the latest news about the James Webb telescope

---

## Note

The project is under construction, more features yet to come.

##TODO: 

proper message output for tables etc. History chat per model and use history function a memory or a history list if model usage goes down. Model usage limit.