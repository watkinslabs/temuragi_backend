import re
from bs4 import BeautifulSoup, Comment
from typing import Dict, List, Tuple, Optional


class HTMLCompressor:
    """Clean and reorganize HTML template output by consolidating CSS and JS"""
    __depends_on__=[]
    
    def __init__(self):
        self.css_parts = []
        self.js_parts = []
        self.external_css = []
        self.external_js = []
        
    def extract_inline_styles(self, soup: BeautifulSoup) -> None:
        """Extract all inline style attributes and convert to CSS rules"""
        elements_with_style = soup.find_all(style=True)
        for idx, elem in enumerate(elements_with_style):
            style_content = elem.get('style', '').strip()
            if style_content:
                # Generate unique class for this element
                class_name = f"inline_style_{idx}"
                existing_classes = elem.get('class', [])
                if isinstance(existing_classes, str):
                    existing_classes = existing_classes.split()
                existing_classes.append(class_name)
                elem['class'] = ' '.join(existing_classes)
                
                # Create CSS rule
                css_rule = f".{class_name} {{ {style_content} }}"
                self.css_parts.append(('inline_style', css_rule))
                
                # Remove inline style
                del elem['style']

    def extract_css(self, soup: BeautifulSoup) -> None:
        """Extract all CSS from style tags and link tags"""
        # Extract <style> tags
        style_tags = soup.find_all('style')
        for tag in style_tags:
            css_content = tag.string or ''
            if css_content.strip():
                self.css_parts.append(('style_tag', css_content))
            tag.decompose()
        
        # Try different ways to find stylesheet links
        link_tags = []
        for link in soup.find_all('link'):
            rel = link.get('rel', [])
            # Handle rel as list or string
            if isinstance(rel, list):
                if 'stylesheet' in rel:
                    link_tags.append(link)
            elif isinstance(rel, str):
                if 'stylesheet' in rel:
                    link_tags.append(link)
        
        # Extract without using decompose
        for tag in link_tags:
            href = tag.get('href', '')
            if href:
                self.external_css.append(href)
            # Try extract() instead of decompose()
            parent = tag.parent
            tag.extract()
            # Ensure we're not breaking the tree
            if parent:
                parent.smooth()

    def extract_inline_js(self, soup: BeautifulSoup) -> None:
        """Extract inline JavaScript from event handlers"""
        # Common event handlers
        event_handlers = [
            'onclick', 'onload', 'onchange', 'onsubmit', 'onmouseover',
            'onmouseout', 'onkeyup', 'onkeydown', 'onfocus', 'onblur',
            'ondblclick', 'onmousedown', 'onmouseup', 'onmousemove',
            'onkeypress', 'onerror', 'onresize', 'onscroll'
        ]
        
        for handler in event_handlers:
            elements_with_handler = soup.find_all(attrs={handler: True})
            for elem in elements_with_handler:
                js_content = elem.get(handler, '').strip()
                if js_content:
                    # Generate unique function name
                    func_name = f"{handler}_{id(elem)}"
                    
                    # Wrap in function and bind to element
                    js_function = f"""
// Inline {handler} handler
function {func_name}(event) {{
    {js_content}
}}
document.addEventListener('DOMContentLoaded', function() {{
    var elem = document.querySelector('[data-handler-id="{func_name}"]');
    if (elem) {{
        elem.addEventListener('{handler[2:]}', {func_name});
    }}
}});
"""
                    self.js_parts.append(('inline_handler', js_function))
                    
                    # Add data attribute for binding
                    elem['data-handler-id'] = func_name
                    
                    # Remove inline handler
                    del elem[handler]
    
    
    def minify_css_content(self, css: str) -> str:
        """Basic CSS minification"""
        try:
            from csscompressor import compress
            return compress(css)
        except ImportError:
            # Fallback to basic minification
            # Remove comments
            css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
            # Remove unnecessary whitespace
            css = re.sub(r'\s+', ' ', css)
            css = re.sub(r'\s*([{}:;,])\s*', r'\1', css)
            return css.strip()
    
    def minify_js_content(self, js: str) -> str:
        """Basic JavaScript minification"""
        try:
            from jsmin import jsmin
            return jsmin(js)
        except ImportError:
            # Fallback to basic minification
            # Remove single-line comments
            js = re.sub(r'//.*?$', '', js, flags=re.MULTILINE)
            # Remove multi-line comments
            js = re.sub(r'/\*.*?\*/', '', js, flags=re.DOTALL)
            # Remove unnecessary whitespace
            js = re.sub(r'\s+', ' ', js)
            js = re.sub(r'\s*([{}();,=+\-*/])\s*', r'\1', js)
            return js.strip()
    
    def build_consolidated_css(self, minify: bool = False) -> str:
        """Build consolidated CSS block"""
        css_blocks = []
        
        # Add external CSS references first
        for href in self.external_css:
            css_blocks.append(f'@import url("{href}");')
        
        # Add all CSS content in order
        for source, content in self.css_parts:
            if content.strip():
                if minify:
                    content = self.minify_css_content(content)
                else:
                    css_blocks.append(f"/* Source: {source} */")
                css_blocks.append(content)
        
        separator = '' if minify else '\n\n'
        combined_css = separator.join(css_blocks)
        
        return combined_css
    
    def build_consolidated_js(self, minify: bool = False) -> str:
        """Build consolidated JavaScript block"""
        js_blocks = []
        
        # Only consolidate inline JS content
        for source, content in self.js_parts:
            if content.strip():
                if minify:
                    content = self.minify_js_content(content)
                else:
                    js_blocks.append(f"// Source: {source}")
                js_blocks.append(content)
        
        separator = '' if minify else '\n\n'
        combined_js = separator.join(js_blocks)
        
        return combined_js
    
    def extract_javascript(self, soup: BeautifulSoup) -> None:
        """Extract all JavaScript from script tags"""
        script_tags = soup.find_all('script')
        for tag in script_tags:
            src = tag.get('src', '')
            if src:
                # Store as dictionary with tag attributes to recreate later
                tag_attrs = dict(tag.attrs)
                self.external_js.append(tag_attrs)
                tag.decompose()
            else:
                js_content = tag.string or ''
                if js_content.strip():
                    self.js_parts.append(('script_tag', js_content))
                tag.decompose()

    def fix_unclosed_tags(self, html_content: str) -> str:
        """Fix unclosed self-closing tags like <link>, <meta>, <img>, etc."""
        # List of tags that should be self-closing
        self_closing_tags = ['link', 'meta', 'img', 'br', 'hr', 'input', 'area', 'base', 'col', 'embed', 'source', 'track', 'wbr']
        
        for tag in self_closing_tags:
            # Pattern: <tag ...> followed by anything that's not whitespace/newline and not another tag
            # If we find content between the tag and the next tag, close it
            pattern = rf'(<{tag}\b[^>]*>)(\s*[^\s<]+)'
            
            def replace_func(match):
                tag_part = match.group(1)
                content_after = match.group(2)
                
                # If the tag already ends with />, leave it alone
                if tag_part.rstrip().endswith('/>'):
                    return match.group(0)
                
                # If there's non-whitespace content after the tag, close it
                if content_after.strip():
                    # Remove any trailing > and add />
                    closed_tag = tag_part[:-1] + ' />'
                    return closed_tag + content_after
                else:
                    return match.group(0)
            
            html_content = re.sub(pattern, replace_func, html_content, flags=re.IGNORECASE)
        
        return html_content

    def fix_self_closing_tags(self, html_content: str) -> str:
        """Convert self-closing tags to regular open/close pairs"""
        # Tags that are commonly self-closing but can be regular tags
        void_elements = ['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr']
        
        for tag in void_elements:
            # Pattern to match self-closing tags: <tag ... />
            pattern = rf'<{tag}\b([^>]*?)\s*/>'
            # Replace with open and close tags: <tag ...></tag>
            replacement = rf'<{tag}\1></{tag}>'
            html_content = re.sub(pattern, replacement, html_content, flags=re.IGNORECASE)
        
        return html_content

    def clean_html(self, 
            html_content: str,
            consolidate_css: bool = True,
            consolidate_js: bool = True,
            minify_css: bool = False,
            minify_js: bool = False,
            minify_html: bool = False) -> str:
        """
        Main function to clean and reorganize HTML
        """
        # Early return if no options are enabled
        if not any([consolidate_css, consolidate_js, minify_css, minify_js, minify_html]):
            return html_content
        
        # Reset state
        self.css_parts = []
        self.js_parts = []
        self.external_css = []
        self.external_js = []
        
        # Fix unclosed tags before parsing
        html_content = self.fix_unclosed_tags(html_content)
        html_content = self.fix_self_closing_tags(html_content)
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Detect if this is a fragment (no html or body tags)
        is_fragment = not soup.find('html') and not soup.find('body')
        
        # Extract CSS if consolidating
        if consolidate_css:
            self.extract_inline_styles(soup)
            self.extract_css(soup)
        elif minify_css:
            # Minify CSS in place without consolidating
            style_tags = soup.find_all('style')
            for tag in style_tags:
                if tag.string:
                    tag.string = self.minify_css_content(tag.string)
            
            # Minify inline styles
            elements_with_style = soup.find_all(style=True)
            for elem in elements_with_style:
                style_content = elem.get('style', '').strip()
                if style_content:
                    elem['style'] = self.minify_css_content(f"dummy{{{style_content}}}")[5:-1]
        
        # Extract JS if consolidating
        if consolidate_js:
            self.extract_inline_js(soup)
            self.extract_javascript(soup)
        elif minify_js:
            # Minify JS in place without consolidating
            script_tags = soup.find_all('script')
            for tag in script_tags:
                if not tag.get('src') and tag.string:
                    tag.string = self.minify_js_content(tag.string)
            
            # Minify inline event handlers
            event_handlers = [
                'onclick', 'onload', 'onchange', 'onsubmit', 'onmouseover',
                'onmouseout', 'onkeyup', 'onkeydown', 'onfocus', 'onblur',
                'ondblclick', 'onmousedown', 'onmouseup', 'onmousemove',
                'onkeypress', 'onerror', 'onresize', 'onscroll'
            ]
            for handler in event_handlers:
                elements_with_handler = soup.find_all(attrs={handler: True})
                for elem in elements_with_handler:
                    js_content = elem.get(handler, '').strip()
                    if js_content:
                        elem[handler] = self.minify_js_content(js_content)
        
        # Add consolidated CSS
        if consolidate_css:
            consolidated_css = self.build_consolidated_css(minify_css)
            if consolidated_css.strip():
                if is_fragment:
                    # For fragments, just add style tag at the beginning
                    style_tag = soup.new_tag('style')
                    style_tag.string = consolidated_css
                    soup.insert(0, style_tag)
                else:
                    # For full HTML, find or create head
                    head = soup.find('head')
                    if not head:
                        head = soup.new_tag('head')
                        html_tag = soup.find('html')
                        if html_tag:
                            html_tag.insert(0, head)
                        else:
                            soup.insert(0, head)
                    
                    # Add consolidated CSS
                    style_tag = soup.new_tag('style')
                    style_tag.string = consolidated_css
                    head.append(style_tag)
        
        # Add consolidated JS
        if consolidate_js:
            if is_fragment:
                # For fragments, append scripts at the end without creating body
                # Re-add all external scripts
                for script_attrs in self.external_js:
                    script_tag = soup.new_tag('script', attrs=script_attrs)
                    soup.append(script_tag)
                
                # Then add consolidated inline JS
                consolidated_js = self.build_consolidated_js(minify_js)
                if consolidated_js.strip():
                    script_tag = soup.new_tag('script')
                    script_tag.string = consolidated_js
                    soup.append(script_tag)
            else:
                # For full HTML, find or create body
                body = soup.find('body')
                if not body:
                    body = soup.new_tag('body')
                    html_tag = soup.find('html')
                    if html_tag:
                        html_tag.append(body)
                    else:
                        soup.append(body)
                
                # Re-add all external scripts at end of body
                for script_attrs in self.external_js:
                    script_tag = soup.new_tag('script', attrs=script_attrs)
                    body.append(script_tag)
                
                # Then add consolidated inline JS
                consolidated_js = self.build_consolidated_js(minify_js)
                if consolidated_js.strip():
                    script_tag = soup.new_tag('script')
                    script_tag.string = consolidated_js
                    body.append(script_tag)
        
        # Return prettified or minified HTML
        if minify_html:
            return str(soup)
        else:
            return soup.prettify()
        
def clean_template_output(html_content: str,
                         consolidate_css: bool = True,
                         consolidate_js: bool = True,
                         minify_css: bool = False,
                         minify_js: bool = False,
                         minify_html: bool = False) -> str:
    """
    Clean and reorganize HTML template output
    
    Args:
        html_content: HTML string from template renderer
        consolidate_css: Whether to consolidate CSS into head
        consolidate_js: Whether to consolidate JS into body
        minify_css: Whether to minify CSS content
        minify_js: Whether to minify JavaScript content
        minify_html: Whether to minify the output HTML
        
    Returns:
        Cleaned HTML with optional consolidation and minification
    """
    cleaner = HTMLCompressor()
    return cleaner.clean_html(html_content, 
                             consolidate_css=consolidate_css,
                             consolidate_js=consolidate_js,
                             minify_css=minify_css,
                             minify_js=minify_js,
                             minify_html=minify_html)