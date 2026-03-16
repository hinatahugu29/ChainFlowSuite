import json
import logging
import re
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PySide6.QtGui import QPageLayout, QPageSize
from PySide6.QtCore import QUrl, QTimer, QThread, Signal, Slot, QObject, Qt, QMarginsF
from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.tasklists import tasklists_plugin
from mdit_py_plugins.container import container_plugin
from mdit_py_plugins.texmath import texmath_plugin
from mdit_py_plugins.anchors import anchors_plugin

# JSコンソールをPythonログに転送
class DebugWebPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        logging.getLogger(__name__).debug(f"JS Console: {message} (line {lineNumber})")

# 背景レンダリング
class RenderWorker(QObject):
    finished = Signal(str)
    def __init__(self, md_parser):
        super().__init__()
        self.md = md_parser
    @Slot(str)
    def render(self, text):
        try:
            # 入力時の円マークをバックスラッシュに統一し、Windowsの改行を正規化
            text = text.replace('¥', '\\').replace('￥', '\\').replace('\r\n', '\n')
            
            # --- 変数埋め込み機能 (Front Matter Variable Embedding) ---
            # フロントマター (--- ... ---) の抽出
            front_matter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
            if front_matter_match:
                fm_content = front_matter_match.group(1)
                variables = {}
                for line in fm_content.split('\n'):
                    if ':' in line:
                        k, v = line.split(':', 1)
                        variables[k.strip()] = v.strip()
                
                body = text[front_matter_match.end():]
                # {{key}} を値に置換
                for k, v in variables.items():
                    if k:
                        body = body.replace(f'{{{{{k}}}}}', v)
                
                # レンダリング用に合体 (フロントマター自体は残してパースさせる)
                text = text[:front_matter_match.end()] + body
            # -------------------------------------------------------

            # Markdownレンダリング
            html = self.md.render(text).strip() if text.strip() else ""
            
            # 手動の \ -> \\ 置換は廃止（json.dumpsに任せる）
            self.finished.emit(html)
        except Exception as e:
            self.finished.emit(f"<div style='color:red'>Render Error: {e}</div>")

class PreviewPane(QWidget):
    render_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.current_text = ""
        self._margins = (25, 25, 25, 25) # T, R, B, L
        self._typo = ('"Yu Mincho", "MS Mincho", serif', 1.6, 10, True, "Bordered (Default)")
        self._page_width, self._page_height = "210mm", "297mm"
        self._page_size, self._orientation = "A4", "Portrait"
        self._decor = {"show_page_num": False, "header": "", "footer": ""}
        self._is_initialized = False
        self._show_guides = True
        
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._do_update_preview)
        
        # MarkdownIt設定
        self.md = (MarkdownIt('commonmark', {'breaks': True, 'html': True})
                   .use(front_matter_plugin).use(footnote_plugin).use(tasklists_plugin)
                   .use(texmath_plugin, delimiters='dollars').use(anchors_plugin)
                   .enable('table').enable('strikethrough'))

        # Mermaid等のカスタムフェンス
        def custom_fence(tokens, idx, options, env, *args):
            token = tokens[idx]
            info = token.info.strip()
            
            if info == "mermaid": 
                return f'<div class="mermaid">{token.content.strip()}</div>'
                
            # mathブロックも直接KaTeXで描画させるための器を作る
            if info in ["math", "latex", "tex"]:
                # json.dumpsを使うため、ここでの手動エスケープも不要
                return f'<div class="math-display" style="display:none;">{token.content.strip()}</div>'
                
            orig = self.md.renderer.rules.get("fence_original", self.md.renderer.rules["fence"])
            return orig(tokens, idx, options, env, *args)
            
        def render_stamp(self_md, tokens, idx, options, env):
            token = tokens[idx]
            if token.nesting == 1:
                info = token.info.strip()[5:].strip()
                blend = "multiply" if "normal" not in info else "normal"
                style = f'style="{info.replace("normal","")}"' if info else ""
                return f'<div class="stamp {blend}" {style}>'
            return '</div>'

        self.md.renderer.rules["fence_original"] = self.md.renderer.rules["fence"]
        self.md.renderer.rules["fence"] = custom_fence
        self.md.validateLink = lambda url: True
        
        for n in ["center", "right", "left", "large", "small", "info", "warning", "no-print"]: 
            self.md.use(container_plugin, name=n)
        self.md.use(container_plugin, name="stamp", render=render_stamp)
        
        # スレッド開始
        self.render_thread = QThread()
        self.worker = RenderWorker(self.md)
        self.worker.moveToThread(self.render_thread)
        self.render_thread.start()
        self.worker.finished.connect(self._update_web_view)
        self.render_requested.connect(self.worker.render)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QLabel("LIVE PREVIEW")
        header.setStyleSheet("background-color: #2D2D30; color: #8F8F8F; padding: 10px 15px; font-weight: bold; font-size: 11px;")
        header.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout.addWidget(header)

        self.web_view = QWebEngineView()
        self.web_view.setPage(DebugWebPage(self.web_view))
        self.web_view.setStyleSheet("background-color: #333333;")
        self.web_view.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        self.web_view.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        layout.addWidget(self.web_view, 1)
        
        self.web_view.loadFinished.connect(self._on_load_finished)
        self._load_shell()
        
    def _on_load_finished(self, ok):
        self._is_initialized = True
        self._inject_dynamic_styles()
        self._sync_decor_to_js()
        if self._show_guides:
             self.web_view.page().runJavaScript("setTimeout(() => { if (window.toggleGuides) window.toggleGuides(true); }, 100);")
        if self.current_text:
             self.update_preview()
            
    def _load_shell(self):
        full_html = r"""<!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;700&family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">
            
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
            <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/mermaid@9.4.3/dist/mermaid.min.js"></script>
            
            <script>
                mermaid.initialize({ startOnLoad: false, theme: 'default', securityLevel: 'loose' });
                window._updateTimer = null;
                
                window.scheduleUpdateOverlays = function() {
                    if (window._updateTimer) clearTimeout(window._updateTimer);
                    window._updateTimer = setTimeout(window.updateOverlays, 30);
                };
                
                window.refreshContent = function(html) {
                    const paper = document.getElementById('paper-content');
                    if (!paper) return;
                    
                    if (!html || html.trim() === "") {
                        paper.innerHTML = "<div style='color: #ccc; text-align: center; margin-top: 40%; font-size: 14pt;' class='placeholder'>Write something to preview...</div>";
                        window.updateOverlays();
                        return;
                    }

                    // オフスクリーンバッファ
                    const buffer = document.createElement('div');
                    buffer.innerHTML = html;

                    // 円マークをバックスラッシュに正規化
                    const cleanMath = (text) => {
                        return text.replace(/[¥￥]/g, '\\').trim();
                    };

                    // ヘルパー：HTML要素内の「純粋なテキスト」を抽出（<br>などは改行に置換）
                    const extractMathText = (el) => {
                        let text = el.innerHTML
                            .replace(/<br\s*\/?>/gi, '\\n')
                            .replace(/<[^>]+>/g, '') // 他のタグを除去
                            .replace(/&nbsp;/g, ' ')
                            .replace(/&amp;/g, '&')
                            .replace(/&lt;/g, '<')
                            .replace(/&gt;/g, '>')
                            .replace(/&quot;/g, '"')
                            .replace(/&#39;/g, "'");
                        // 前後の $$ を削り、cleanMathを適用
                        return cleanMath(text.replace(/^\\$\\$|\\$\\$$/g, ''));
                    };

                    // 1. パーサーが出力した <eqn> (ブロック) と <eq> (インライン) の処理
                    buffer.querySelectorAll('eqn, eq').forEach(el => {
                        const isBlock = el.tagName.toLowerCase() === 'eqn';
                        const math = cleanMath(el.textContent);
                        if (!math) return;
                        try {
                            katex.render(math, el, { displayMode: isBlock, throwOnError: false });
                            if (isBlock) {
                                el.style.display = 'block';
                                el.style.textAlign = 'center';
                                el.style.margin = '1.2em 0';
                            }
                        } catch(e) { console.error("KaTeX Error:", e); }
                    });

                    // 2. カスタムフェンスで作成した .math-display の処理
                    buffer.querySelectorAll('.math-display').forEach(el => {
                        const math = cleanMath(el.textContent);
                        if (!math) return;
                        el.style.display = 'block'; // 表示を戻す
                        try {
                            katex.render(math, el, { displayMode: true, throwOnError: false });
                            el.style.textAlign = 'center';
                            el.style.margin = '1.2em 0';
                        } catch(e) { console.error("KaTeX Error:", e); }
                    });

                    // 3. 【最終手段】パース漏れの $$...$$ をテキストノードから探して強引に置換
                    const walkTextNodes = (node) => {
                        if (node.nodeType === 3) { // Text Node
                            const text = node.nodeValue;
                            if (text.includes('$$')) {
                                const parts = text.split(/(\\$\\$[\\s\\S]+?\\$\\$)/g);
                                if (parts.length > 1) {
                                    const fragment = document.createDocumentFragment();
                                    parts.forEach(part => {
                                        if (part.startsWith('$$') && part.endsWith('$$')) {
                                            const math = cleanMath(part.slice(2, -2));
                                            const span = document.createElement('span');
                                            try {
                                                katex.render(math, span, { displayMode: true, throwOnError: false });
                                                span.style.display = 'block';
                                                span.style.textAlign = 'center';
                                                span.style.margin = '1.2em 0';
                                            } catch(e) { 
                                                console.error("KaTeX walkTextNodes Error:", e);
                                                span.textContent = part; 
                                            }
                                            fragment.appendChild(span);
                                        } else if (part.length > 0) {
                                            fragment.appendChild(document.createTextNode(part));
                                        }
                                    });
                                    node.parentNode.replaceChild(fragment, node);
                                }
                            }
                        } else {
                            for (let i = 0; i < node.childNodes.length; i++) {
                                walkTextNodes(node.childNodes[i]);
                            }
                        }
                    };
                    walkTextNodes(buffer);

                    // スクロール位置保持
                    const scrollTop = window.scrollY || document.documentElement.scrollTop;
                    paper.replaceChildren(...buffer.childNodes);
                    
                    // Mermaid
                    const mermaidNodes = paper.querySelectorAll('.mermaid');
                    if (mermaidNodes.length > 0) {
                        try { mermaid.init(undefined, mermaidNodes); } 
                        catch(e) { console.error("Mermaid error:", e); }
                    }

                    window.updateOverlays();
                    window.scrollTo(0, scrollTop);
                    paper.querySelectorAll('img').forEach(img => img.onload = img.onerror = window.scheduleUpdateOverlays);
                };

                window.toggleGuides = function(show) { document.body.classList.toggle('show-guides', show); };
                window.updateDecor = function(decor) { window.currentDecor = decor; window.scheduleUpdateOverlays(); };

                window.updateOverlays = function() {
                    const paper = document.getElementById('paper-content');
                    const container = document.getElementById('overlay-container');
                    const helper = document.getElementById('dpi-helper');
                    if (!paper || !container || !helper) return;

                    const decor = window.currentDecor || {};
                    let pxPerMm = helper.offsetWidth / 100;
                    if (!pxPerMm || pxPerMm < 1) pxPerMm = 96 / 25.4;
                    const paperWidthPx = paper.offsetWidth;
                    const pageHeightPx = (decor.page_height_mm || 297) * pxPerMm;
                    
                    const marginTopPx = (decor.margin_top || 0) * pxPerMm;
                    const marginBottomPx = (decor.margin_bottom || 0) * pxPerMm;
                    const marginLeftPx = (decor.margin_left || 0) * pxPerMm;
                    const marginRightPx = (decor.margin_right || 0) * pxPerMm;
                    const contentHeightPx = pageHeightPx - marginTopPx - marginBottomPx;

                    paper.querySelectorAll('.js-page-break-spacer').forEach(el => el.remove());
                    
                    const avoidElements = Array.from(paper.children);
                    const paperTop = paper.getBoundingClientRect().top;

                    avoidElements.forEach(el => {
                        const rect = el.getBoundingClientRect();
                        const distTop = rect.top - paperTop;
                        if (distTop < 0) return;

                        const currentPage = Math.floor(distTop / pageHeightPx);
                        const contentBottomY = currentPage * pageHeightPx + marginTopPx + contentHeightPx;
                        
                        let isForceBreak = false;
                        if (el.nodeType === 1) {
                            const compStyle = window.getComputedStyle(el);
                            if (compStyle.pageBreakBefore === 'always' || compStyle.breakBefore === 'page') {
                                isForceBreak = true;
                            } else if (el.querySelector) {
                                const child = el.querySelector('[style*="page-break-before: always"],[style*="page-break-before:always"],[style*="break-before: page"], .page-break');
                                if (child) isForceBreak = true;
                            }
                        }

                        let shouldBreak = false;
                        if (isForceBreak) {
                            const offsetInPage = distTop - (currentPage * pageHeightPx + marginTopPx);
                            if (offsetInPage > 10) shouldBreak = true;
                        } else if (distTop + rect.height > contentBottomY && rect.height <= contentHeightPx) {
                            shouldBreak = true;
                        }

                        if (shouldBreak) {
                            const nextContentStartY = (currentPage + 1) * pageHeightPx + marginTopPx;
                            const gap = nextContentStartY - distTop;
                            const spacer = document.createElement('div');
                            spacer.className = 'js-page-break-spacer';
                            spacer.style.height = gap + 'px';
                            spacer.style.width = '100%';
                            spacer.style.clear = 'both';
                            el.parentNode.insertBefore(spacer, el);
                        }
                    });

                    const isPlaceholder = paper.querySelector('.placeholder') !== null;
                    const numPages = isPlaceholder ? 1 : Math.max(1, Math.ceil((paper.offsetHeight - 2) / pageHeightPx));
                    
                    const tempFragment = document.createDocumentFragment();
                    for (let i = 0; i < numPages; i++) {
                        const pageTop = i * pageHeightPx;
                        const decorLayer = document.createElement('div');
                        decorLayer.className = 'print-decor';
                        decorLayer.style.cssText = `position:absolute; top:${pageTop}px; width:100%; height:${pageHeightPx}px; box-sizing:border-box; pointer-events:none;`;
                        if (decor.header) {
                            const h = document.createElement('div');
                            h.style.cssText = `position:absolute; top:${marginTopPx/2}px; left:${marginLeftPx}px; transform:translateY(-50%);`;
                            h.innerText = decor.header; decorLayer.appendChild(h);
                        }
                        if (decor.footer || decor.show_page_num) {
                            const f = document.createElement('div');
                            f.style.cssText = `position:absolute; bottom:${marginBottomPx/2}px; left:50%; transform:translate(-50%, 50%);`;
                            f.innerText = decor.footer || (decor.show_page_num ? (i+1) : "");
                            decorLayer.appendChild(f);
                        }
                        tempFragment.appendChild(decorLayer);
                        
                        if (i < numPages - 1) {
                            const line = document.createElement('div');
                            line.className = 'screen-guide-line';
                            line.style.top = (pageTop + pageHeightPx) + 'px';
                            tempFragment.appendChild(line);
                        }
                        const limit = document.createElement('div');
                        limit.className = 'screen-guide-bottom-limit';
                        limit.style.top = (pageTop + pageHeightPx - marginBottomPx) + 'px';
                        tempFragment.appendChild(limit);
                        const marginBox = document.createElement('div');
                        marginBox.className = 'screen-guide-margin';
                        marginBox.style.cssText = `position:absolute; top:${pageTop + marginTopPx}px; left:${marginLeftPx}px; width:${paperWidthPx - marginLeftPx - marginRightPx}px; height:${contentHeightPx}px;`;
                        tempFragment.appendChild(marginBox);
                    }

                    container.style.width = paperWidthPx + 'px';
                    container.style.height = (numPages * pageHeightPx) + 'px';
                    paper.style.minHeight = (numPages * pageHeightPx) + 'px';
                    
                    container.innerHTML = '';
                    container.appendChild(tempFragment);
                };
            </script>
            <style>
                html, body { background-color: #252526; margin: 0; padding: 0; }
                body { display: flex; justify-content: center; padding: 40px 20px 200px 20px; }
                .paper {
                    background: white; width: var(--page-width); box-sizing: border-box;
                    padding: var(--margin-top) var(--margin-right) var(--margin-bottom) var(--margin-left);
                    box-shadow: 0 10px 30px rgba(0,0,0,0.5); font-family: var(--font-family);
                    position: relative; z-index: 1; display: flow-root; 
                    line-height: var(--line-height); font-size: var(--base-size);
                }
                #overlay-container { position: absolute; top: 0; left: 50%; transform: translateX(-50%); pointer-events: none; z-index: 10; }
                .screen-guide-line, .screen-guide-margin, .screen-guide-bottom-limit { display: none; }
                body.show-guides .screen-guide-line, body.show-guides .screen-guide-margin, body.show-guides .screen-guide-bottom-limit { display: block; }
                .screen-guide-line { width: 100%; height: 0; border-top: 1px dashed #4bbaff; position: absolute; }
                .screen-guide-bottom-limit { width: 100%; height: 1px; border-top: 1px dotted rgba(255, 0, 0, 0.4); position: absolute; z-index: 11; }
                .screen-guide-margin { border: 1px dashed rgba(75, 186, 255, 0.2); box-sizing: border-box; }
                .print-decor { font-size: 9pt; color: #777; }
                .center { text-align: center; } .right { text-align: right; } .left { text-align: left; }
                .large { font-size: 1.5em; font-weight: bold; } .small { font-size: 0.85em; }
                .stamp { position: absolute; right: 40mm; margin-top: -15mm; z-index: 100; }
                .stamp img { width: 20mm; mix-blend-mode: multiply; }
                .no-print { display: none !important; }
                
                .info { background-color: #f0f8ff; border-left: 5px solid #2196f3; padding: 10pt 15pt; margin: 10pt 0; color: #0d47a1; }
                .warning { background-color: #fffdf0; border-left: 5px solid #ff9800; padding: 10pt 15pt; margin: 10pt 0; color: #e65100; }
                .info p, .warning p { margin: 0; padding: 0; }
                
                table { border-collapse: collapse; width: 100%; margin: 10pt 0; }
                th, td { border: var(--table-border); padding: 6pt; text-align: left; }
                th { background-color: rgba(0,0,0,0.03); font-weight: bold; }
                
                u { text-underline-offset: 3px; }
                @media print {
                    @page { margin: 0 !important; size: var(--page-width) var(--page-height); }
                    html, body {
                        background-color: white !important; margin: 0 !important; padding: 0 !important;
                        display: block !important; width: var(--page-width) !important;
                    }
                    .paper { box-shadow: none !important; margin: 0 !important; width: 100% !important; height: auto !important; }
                    .screen-guide-line, .screen-guide-margin, .screen-guide-bottom-limit, .screen-guide-label, .screen-guide-margin-label { display: none !important; }
                    .js-page-break-spacer { display: block !important; visibility: hidden !important; }
                    #overlay-container { display: block !important; width: 100% !important; left: 0 !important; transform: none !important; }
                }
            </style>
        </head>
        <body>
            <div id="dpi-helper" style="width: 100mm; height: 0; position: absolute; visibility: hidden;"></div>
            <div class="paper-container" style="position: relative;">
                <div id="paper-content" class="paper"></div>
                <div id="overlay-container"></div>
            </div>
        </body>
        </html>
        """
        self.web_view.setHtml(full_html, QUrl("file:///"))
        
    def _inject_dynamic_styles(self):
        if not self._is_initialized: return
        css = f":root {{ --page-width: {self._page_width}; --page-height: {self._page_height}; --margin-top: {self._margins[0]}mm; --margin-right: {self._margins[1]}mm; --margin-bottom: {self._margins[2]}mm; --margin-left: {self._margins[3]}mm; --font-family: {self._typo[0]}; --line-height: {self._typo[1]}; --base-size: {self._typo[2]}pt; --table-border: {'1px solid #ccc' if 'Bordered' in self._typo[4] else 'none'}; }}"
        print_css = f"@media print {{ .paper {{ padding: {self._margins[0]}mm {self._margins[1]}mm {self._margins[2]}mm {self._margins[3]}mm !important; box-sizing: border-box !important; width: {self._page_width} !important; height: auto !important; }} }}"
        self.web_view.page().runJavaScript(f"var s=document.getElementById('dyn-style')||document.createElement('style');s.id='dyn-style';s.innerHTML=`{css} {print_css}`;if(!s.parentNode)document.head.appendChild(s);window.scheduleUpdateOverlays();")

    def _sync_decor_to_js(self):
        if not self._is_initialized: return
        ctx = self._decor.copy()
        ctx.update({"margin_top": self._margins[0], "margin_bottom": self._margins[2], "margin_left": self._margins[3], "margin_right": self._margins[1], "page_height_mm": float(self._page_height.replace('mm',''))})
        self.web_view.page().runJavaScript(f"updateDecor({json.dumps(ctx)});")

    def export_pdf(self, path):
        sz = QPageSize.A4
        if "B5" in self._page_size: sz = QPageSize.B5
        elif "A5" in self._page_size: sz = QPageSize.A5
        elif "Letter" in self._page_size: sz = QPageSize.Letter
        page_layout = QPageLayout(QPageSize(sz), QPageLayout.Landscape if "Landscape" in self._orientation else QPageLayout.Portrait, QMarginsF(0,0,0,0))
        page_layout.setUnits(QPageLayout.Unit.Millimeter)
        self.web_view.page().printToPdf(path, page_layout)

    def update_margins(self, t, r, b, l): 
        self._margins = (t, r, b, l); self._inject_dynamic_styles(); self._sync_decor_to_js()
    def update_typography(self, f, l, b, h=True, t="Bordered"):
        if "Serif" in f: f = f'{f}, "Noto Serif JP", serif'
        elif "Sans" in f: f = f'{f}, "Noto Sans JP", sans-serif'
        self._typo = (f, l, b, h, t); self._inject_dynamic_styles(); self._sync_decor_to_js()
    def update_page_size(self, s, o): 
        self._page_size = s; self._orientation = o
        # 用紙サイズに合わせた寸法設定
        dims = {"A4": ("210mm","297mm"), "B5": ("182mm","257mm"), "A5": ("148mm","210mm"), "Letter": ("215.9mm","279.4mm")}
        w, h = dims.get(next((k for k in dims if k in s), "A4"))
        self._page_width, self._page_height = (h, w) if o == "Landscape" else (w, h)
        self._sync_decor_to_js(); self._inject_dynamic_styles()
    def update_page_decor(self, d): self._decor = d; self._sync_decor_to_js()
    def update_preview(self, text=None):
        if text is not None: self.current_text = text
        self._update_timer.start(300)
    def _do_update_preview(self): self.render_requested.emit(self.current_text)
    @Slot(str)
    def _update_web_view(self, html): self.web_view.page().runJavaScript(f"refreshContent({json.dumps(html)});")
    def set_guides_visible(self, v): self._show_guides = v; self.web_view.page().runJavaScript(f"window.toggleGuides({json.dumps(v)});")
