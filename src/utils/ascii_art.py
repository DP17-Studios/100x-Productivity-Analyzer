#!/usr/bin/env python3
"""
ASCII Art Renderer - Creates ASCII-only visual elements for console output
"""

from typing import List, Dict, Any
import textwrap

class ASCIIRenderer:
    """Renders ASCII-only visual elements for console output"""
    
    def __init__(self):
        # ASCII box drawing characters (compatible with all systems)
        self.box_chars = {
            'horizontal': '-',
            'vertical': '|',
            'top_left': '+',
            'top_right': '+',
            'bottom_left': '+',
            'bottom_right': '+',
            'cross': '+'
        }
        
        # Progress bar characters
        self.progress_chars = {
            'filled': '#',
            'empty': '-',
            'left': '[',
            'right': ']'
        }
    
    def create_title(self, text: str, width: int = 80) -> str:
        """Create a centered title with ASCII border"""
        text = text.upper()
        text_len = len(text)
        
        if text_len >= width - 4:
            # Text too long, wrap it
            return text
        
        padding = (width - text_len - 4) // 2
        border_line = self.box_chars['horizontal'] * width
        
        title_line = (
            self.box_chars['vertical'] + 
            ' ' * padding + 
            text + 
            ' ' * (width - text_len - padding - 2) +
            self.box_chars['vertical']
        )
        
        return f"{border_line}\n{title_line}\n{border_line}"
    
    def create_box(self, content: str, title: str = "", width: int = 60) -> str:
        """Create a box around content with optional title"""
        lines = content.split('\n')
        max_content_width = max(len(line) for line in lines) if lines else 0
        box_width = max(width, max_content_width + 4, len(title) + 4)
        
        # Top border
        top_border = self.box_chars['top_left'] + self.box_chars['horizontal'] * (box_width - 2) + self.box_chars['top_right']
        
        # Bottom border
        bottom_border = self.box_chars['bottom_left'] + self.box_chars['horizontal'] * (box_width - 2) + self.box_chars['bottom_right']
        
        result = [top_border]
        
        # Title if provided
        if title:
            title_padding = (box_width - len(title) - 2) // 2
            title_line = (
                self.box_chars['vertical'] + 
                ' ' * title_padding +
                title +
                ' ' * (box_width - len(title) - title_padding - 2) +
                self.box_chars['vertical']
            )
            result.append(title_line)
            
            # Separator line
            separator = (
                self.box_chars['vertical'] +
                self.box_chars['horizontal'] * (box_width - 2) +
                self.box_chars['vertical']
            )
            result.append(separator)
        
        # Content lines
        for line in lines:
            content_line = (
                self.box_chars['vertical'] +
                ' ' + 
                line.ljust(box_width - 3) +
                self.box_chars['vertical']
            )
            result.append(content_line)
        
        result.append(bottom_border)
        
        return '\n'.join(result)
    
    def create_table(self, headers: List[str], rows: List[List[str]], title: str = "") -> str:
        """Create an ASCII table"""
        if not headers or not rows:
            return "No data to display"
        
        # Calculate column widths
        col_widths = [len(header) for header in headers]
        
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Add padding
        col_widths = [w + 2 for w in col_widths]
        table_width = sum(col_widths) + len(headers) + 1
        
        result = []
        
        # Title
        if title:
            result.append(self.create_title(title, table_width))
            result.append("")
        
        # Top border
        top_border = self.box_chars['top_left']
        for i, width in enumerate(col_widths):
            top_border += self.box_chars['horizontal'] * width
            if i < len(col_widths) - 1:
                top_border += self.box_chars['cross']
        top_border += self.box_chars['top_right']
        result.append(top_border)
        
        # Header row
        header_row = self.box_chars['vertical']
        for i, (header, width) in enumerate(zip(headers, col_widths)):
            header_row += f" {header.ljust(width-1)}"
            if i < len(headers) - 1:
                header_row += self.box_chars['vertical']
        header_row += self.box_chars['vertical']
        result.append(header_row)
        
        # Header separator
        header_sep = self.box_chars['cross']
        for i, width in enumerate(col_widths):
            header_sep += self.box_chars['horizontal'] * width
            if i < len(col_widths) - 1:
                header_sep += self.box_chars['cross']
        header_sep += self.box_chars['cross']
        result.append(header_sep)
        
        # Data rows
        for row in rows:
            data_row = self.box_chars['vertical']
            for i, (cell, width) in enumerate(zip(row, col_widths)):
                data_row += f" {str(cell).ljust(width-1)}"
                if i < len(row) - 1:
                    data_row += self.box_chars['vertical']
            data_row += self.box_chars['vertical']
            result.append(data_row)
        
        # Bottom border
        bottom_border = self.box_chars['bottom_left']
        for i, width in enumerate(col_widths):
            bottom_border += self.box_chars['horizontal'] * width
            if i < len(col_widths) - 1:
                bottom_border += self.box_chars['cross']
        bottom_border += self.box_chars['bottom_right']
        result.append(bottom_border)
        
        return '\n'.join(result)
    
    def create_progress_bar(self, value: float, max_value: float = 100, width: int = 40, label: str = "") -> str:
        """Create an ASCII progress bar"""
        if max_value == 0:
            percentage = 0
        else:
            percentage = min(100, max(0, (value / max_value) * 100))
        
        filled_width = int((percentage / 100) * width)
        empty_width = width - filled_width
        
        bar = (
            self.progress_chars['left'] +
            self.progress_chars['filled'] * filled_width +
            self.progress_chars['empty'] * empty_width +
            self.progress_chars['right']
        )
        
        if label:
            return f"{label}: {bar} {percentage:.1f}%"
        else:
            return f"{bar} {percentage:.1f}%"
    
    def create_banner(self, text: str, char: str = '=', width: int = 80) -> str:
        """Create a simple banner"""
        if len(text) >= width - 4:
            return char * width + '\n' + text + '\n' + char * width
        
        padding = (width - len(text) - 2) // 2
        banner_line = char + ' ' * padding + text + ' ' * (width - len(text) - padding - 1) + char
        border = char * width
        
        return f"{border}\n{banner_line}\n{border}"
    
    def create_metric_display(self, metrics: Dict[str, Any], title: str = "METRICS") -> str:
        """Create a display for key metrics"""
        content_lines = []
        
        for key, value in metrics.items():
            # Format the key (replace underscores with spaces and title case)
            formatted_key = key.replace('_', ' ').title()
            
            # Format the value
            if isinstance(value, float):
                formatted_value = f"{value:.2f}"
            elif isinstance(value, int):
                formatted_value = f"{value:,}"
            else:
                formatted_value = str(value)
            
            content_lines.append(f"{formatted_key}: {formatted_value}")
        
        content = '\n'.join(content_lines)
        return self.create_box(content, title)
    
    def create_ranking_display(self, rankings: List[Dict[str, Any]], title: str = "RANKINGS") -> str:
        """Create a ranking display with medals/numbers"""
        content_lines = []
        
        rank_symbols = ['1st', '2nd', '3rd']
        
        for i, item in enumerate(rankings[:10]):  # Show top 10
            rank = rank_symbols[i] if i < 3 else f"{i+1}th"
            
            name = item.get('name', item.get('engineer', 'Unknown'))
            score = item.get('score', item.get('total_score', 0))
            
            if isinstance(score, float):
                score_str = f"{score:.1f}"
            else:
                score_str = str(score)
            
            line = f"{rank:>4} | {name:<20} | {score_str:>6}"
            content_lines.append(line)
        
        # Add header
        header = "Rank | Name                 | Score"
        separator = "-" * len(header)
        
        content = f"{header}\n{separator}\n" + '\n'.join(content_lines)
        
        return self.create_box(content, title)
    
    def wrap_text(self, text: str, width: int = 70) -> str:
        """Wrap text to specified width"""
        return '\n'.join(textwrap.wrap(text, width=width))