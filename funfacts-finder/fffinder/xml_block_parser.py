from bs4 import BeautifulSoup
import re
from typing import List

class XMLBlockParser:
    """Robust parser to extract XML/HTML blocks from unstructured text using BeautifulSoup"""
    
    def __init__(self):
        pass
    
    def extract_xml_blocks(self, text: str) -> List[str]:
        """
        Extract complete XML blocks from unstructured text.
        Returns list of clean, well-formatted XML strings.
        """
        blocks = []
        
        # Find potential XML blocks using regex
        # Look for opening tags and try to find complete structures
        opening_tags = re.finditer(r'<([a-zA-Z][a-zA-Z0-9]*)[^>]*>', text)
        
        for match in opening_tags:
            tag_name = match.group(1)
            start_pos = match.start()
            
            # Find the matching closing tag
            closing_pattern = f'</{tag_name}>'
            rest_of_text = text[match.end():]
            
            # Find the position of the closing tag, accounting for nested tags
            tag_count = 1
            pos = 0
            
            while pos < len(rest_of_text) and tag_count > 0:
                # Look for opening or closing tags of the same type
                next_open = rest_of_text.find(f'<{tag_name}', pos)
                next_close = rest_of_text.find(closing_pattern, pos)
                
                if next_close == -1:  # No closing tag found
                    break
                
                # Check if there's an opening tag before the next closing tag
                if next_open != -1 and next_open < next_close:
                    # Make sure it's actually an opening tag, not just a substring
                    if pos == next_open or rest_of_text[next_open-1] == '<':
                        tag_count += 1
                    pos = next_open + len(tag_name) + 1
                else:
                    tag_count -= 1
                    if tag_count == 0:
                        end_pos = match.end() + next_close + len(closing_pattern)
                        potential_block = text[start_pos:end_pos]
                        
                        # Try to parse and clean with BeautifulSoup
                        try:
                            # Use lxml-xml parser but strip the XML declaration
                            soup = BeautifulSoup(potential_block, 'lxml-xml')
                            if soup.find():  # If it found any tags
                                prettified = soup.prettify()
                                # Remove XML declaration if present
                                if prettified.startswith('<?xml'):
                                    lines = prettified.split('\n')
                                    prettified = '\n'.join(lines[1:]).strip()
                                blocks.append(prettified)
                        except Exception:
                            # Fallback: just validate and use original with basic formatting
                            try:
                                BeautifulSoup(potential_block, 'html.parser')  # Just validate
                                # Add basic indentation manually while preserving case
                                formatted = self._format_xml_preserve_case(potential_block)
                                blocks.append(formatted)
                            except Exception:
                                continue
                        break
                    else:
                        pos = next_close + len(closing_pattern)
        
        # Remove duplicates and nested blocks
        return self._remove_nested_blocks(blocks)
    
    def _format_xml_preserve_case(self, xml_text: str) -> str:
        """Format XML with proper indentation while preserving original casing"""
        lines = xml_text.split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
                
            # Decrease indent for closing tags
            if stripped.startswith('</'):
                indent_level -= 1
            
            # Add the line with proper indentation
            formatted_lines.append('  ' * indent_level + stripped)
            
            # Increase indent for opening tags (but not self-closing or closing tags)
            if stripped.startswith('<') and not stripped.startswith('</') and not stripped.endswith('/>') and not stripped.startswith('<!--'):
                indent_level += 1
        
        return '\n'.join(formatted_lines)

    def _remove_nested_blocks(self, blocks: List[str]) -> List[str]:
        """Remove blocks that are completely contained within other blocks"""
        filtered = []
        
        for i, block in enumerate(blocks):
            is_nested = False
            block_clean = re.sub(r'\s+', ' ', block).strip()
            
            for j, other_block in enumerate(blocks):
                if i != j:
                    other_clean = re.sub(r'\s+', ' ', other_block).strip()
                    if len(block_clean) < len(other_clean) and block_clean in other_clean:
                        is_nested = True
                        break
            
            if not is_nested:
                filtered.append(block)
        
        return filtered
    
    def extract_raw_blocks(self, text: str) -> List[str]:
        """Extract blocks without prettifying (preserves original formatting)"""
        blocks = []
        
        # Simple regex approach for when you want to preserve original formatting
        pattern = r'(<[a-zA-Z][^>]*>.*?</[a-zA-Z][^>]*>)'
        matches = re.findall(pattern, text, re.DOTALL)
        
        validated_blocks = []
        for match in matches:
            try:
                # Just validate it's parseable
                BeautifulSoup(match, 'html.parser')
                validated_blocks.append(match)
            except Exception:
                continue
        
        return self._remove_nested_blocks(validated_blocks)

# Simple usage function
def extract_xml_from_text(text: str, prettify: bool = True) -> List[str]:
    """
    Simple function to extract XML blocks from text.
    
    Args:
        text: The unstructured text containing XML blocks
        prettify: Whether to format the XML nicely (default: True)
    
    Returns:
        List of XML block strings
    """
    parser = XMLBlockParser()
    
    if prettify:
        return parser.extract_xml_blocks(text)
    else:
        return parser.extract_raw_blocks(text)

# Demo
if __name__ == "__main__":
    sample_text = '''
    Here is some random text before the code block.
    
    <VideoContainer width="1080" height="1920">
     <!--extremely attention grabbing first scene)-->
    <Scene name="intro">
    <Visual transition="fadeIn 0.2s">
    <!-- This is supposed to be a image that will be generated, so what goes in is the prompt -->
    <GeneratedImage class="absolute top-0 left-0 w-full h-full" aspect="9/16" model="gpt-image">
     image of a catchy person with extreme expression
    </GeneratedImage>
    <TextContainer class="absolute" y="center" x="center">
    <SubtitleText ref="v01" />
    </TextContainer>
    </Visual>
    <VoiceOver id="v01">
    <VOFragment>Stub extremely catchy voiceover</VOFragment>
    <VOFragment>Each fragment is small</VOFragment>
    </VoiceOver>
    </Scene>
    </VideoContainer>
    
    And here is some more text after the code block.
    '''
    
    # Extract and print
    xml_blocks = extract_xml_from_text(sample_text)
    
    print(f"Found {len(xml_blocks)} XML blocks:")
    for i, block in enumerate(xml_blocks):
        print(f"\n--- Block {i+1} ---")
        print(block)