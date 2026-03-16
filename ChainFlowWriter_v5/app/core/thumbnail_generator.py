import os
from PySide6.QtCore import Qt, QObject, Signal, QTimer
from PySide6.QtGui import QImage, QPainter, QTextDocument, QFont
from markdown_it import MarkdownIt

class ThumbnailGenerator(QObject):
    thumbnail_ready = Signal(str) # Emits the filename of the generated thumbnail
    generation_failed = Signal(str)

    def __init__(self, output_dir):
        super().__init__()
        self.output_dir = output_dir
        self.queue = []
        self.is_processing = False
        
        # Setup Markdown parser for thumbnail rendering
        # This ensures Markdown snippets aren't rendered as raw text.
        self.md = MarkdownIt('commonmark', {'breaks': True, 'html': True})
        
    def generate_thumbnail(self, content, filename):
        """Adds a request to the generation queue."""
        self.queue.append((content, filename))
        self._process_queue()
        
    def _process_queue(self):
        if self.is_processing or not self.queue:
            return
            
        self.is_processing = True
        content, filename = self.queue.pop(0)
        
        # We use QTextDocument instead of QWebEngineView for thumbnails.
        # Why? QTextDocument is synchronous, lighter, and doesn't suffer from 
        # Chromium's "off-screen optimization" which often causes blank captures on Windows.
        try:
            # 1. Convert Markdown/Snippet to HTML
            html_body = self.md.render(content)
            full_html = self._wrap_in_shell(html_body)
            
            # 2. Setup a fixed-size canvas
            # We use 600x450 (4:3) for a slightly tighter thumbnail than 800x600
            canvas_size = (600, 450)
            img = QImage(canvas_size[0], canvas_size[1], QImage.Format_RGB32)
            img.fill(Qt.white)
            
            # 3. Render HTML using QTextDocument
            doc = QTextDocument()
            # Use a slightly larger default font for better readability in thumbnails
            doc.setDefaultFont(QFont("Segoe UI", 12)) 
            doc.setHtml(full_html)
            doc.setTextWidth(canvas_size[0])
            
            painter = QPainter(img)
            doc.drawContents(painter)
            painter.end()
            
            # 4. Scale down to a consistent thumbnail size
            thumb = img.scaledToWidth(250, Qt.SmoothTransformation)
            
            # 5. Save to disk
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir, exist_ok=True)
                
            out_path = os.path.join(self.output_dir, filename)
            thumb.save(out_path, "PNG")
            
            self.thumbnail_ready.emit(filename)
            
        except Exception as e:
            print(f"Thumbnail Error: {e}")
            self.generation_failed.emit(str(e))
        finally:
            self.is_processing = False
            # Process next item in the next event loop cycle
            QTimer.singleShot(10, self._process_queue)
            
    def _wrap_in_shell(self, html_body):
        # Simplified CSS optimized for QTextDocument (limited subset compared to full CSS)
        return f"""
        <html>
        <head>
            <style>
                body {{ 
                    font-family: 'Segoe UI', sans-serif; 
                    padding: 20px; 
                    color: #333; 
                    background-color: white;
                }}
                h1, h2, h3 {{ color: #0E639C; margin-top: 5px; }}
                table {{ 
                    border-collapse: collapse; 
                    width: 100%; 
                    margin: 10px 0; 
                    border: 1px solid #ccc; 
                }}
                th {{ background-color: #f5f5f5; border: 1px solid #ccc; padding: 6px; text-align: left; }}
                td {{ border: 1px solid #ccc; padding: 6px; }}
                blockquote {{ 
                    border-left: 5px solid #0E639C; 
                    background-color: #f8f8f8;
                    padding: 10px; 
                    margin: 10px 0;
                    color: #555;
                }}
                .info {{ 
                    background-color: #e8f4fd; 
                    border: 1px solid #2196f3; 
                    padding: 10px; 
                    margin: 10px 0; 
                }}
                .warning {{ 
                    background-color: #fff3e0; 
                    border: 1px solid #ff9800; 
                    padding: 10px; 
                    margin: 10px 0; 
                }}
                pre, code {{
                    background-color: #f0f0f0;
                    font-family: 'Consolas', monospace;
                }}
            </style>
        </head>
        <body>
            {html_body}
        </body>
        </html>
        """

