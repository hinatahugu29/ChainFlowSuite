(function() {
    if (window.sniperInitialized) return;
    window.sniperInitialized = true;

    const style = document.createElement('style');
    style.textContent = `
        .sniper-highlight {
            outline: 2px solid #00f2fe !important;
            outline-offset: -2px !important;
            background-color: rgba(0, 242, 254, 0.1) !important;
            transition: outline-color 0.2s, background-color 0.2s !important;
            cursor: crosshair !important;
            z-index: 2147483647 !important;
        }
        .sniper-selected {
            background-color: rgba(0, 242, 254, 0.3) !important;
        }
        [disabled], input, textarea, select {
            pointer-events: auto !important;
        }
        .sniper-highlight-struct {
            outline: 3px dashed #f5c2e7 !important;
            background-color: rgba(245, 194, 231, 0.1) !important;
        }
        .sniper-highlight-dom {
            outline: 3px solid #a6e3a1 !important;
            outline-offset: -3px !important;
            background-color: rgba(166, 227, 161, 0.15) !important;
            cursor: crosshair !important;
        }
        .sniper-highlight-batch {
            outline: 2px solid #fab387 !important;
            background-color: rgba(250, 179, 135, 0.3) !important;
        }
        .sniper-highlight-style {
            outline: 3px solid #b4befe !important;
            outline-offset: -3px !important;
            background-color: rgba(180, 190, 254, 0.15) !important;
            cursor: crosshair !important;
        }
        .sniper-zoom-indicator {
            position: fixed;
            bottom: 25px;
            right: 25px;
            background: rgba(30, 30, 46, 0.95);
            color: #cdd6f4;
            padding: 15px;
            border-radius: 14px;
            font-size: 13px;
            font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
            pointer-events: none;
            z-index: 2000000;
            border: 1px solid #45475a;
            box-shadow: 0 15px 40px rgba(0,0,0,0.6);
            display: none;
            backdrop-filter: blur(12px);
            transition: all 0.2s ease;
            max-width: 450px;
            line-height: 1.5;
        }
        .sniper-breadcrumb-container {
            margin-bottom: 8px;
            padding-bottom: 8px;
            border-bottom: 1px solid #313244;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .sniper-breadcrumb-item {
            color: #7f849c;
            display: inline-block;
        }
        .sniper-breadcrumb-item.active {
            color: #89b4fa;
            font-weight: bold;
        }
        .sniper-breadcrumb-separator {
            margin: 0 6px;
            color: #585b70;
        }
        .sniper-batch-preview {
            margin-top: 5px;
        }
        .sniper-batch-header {
            color: #fab387;
            font-weight: bold;
            font-size: 11px;
            text-transform: uppercase;
            margin-bottom: 5px;
            display: flex;
            justify-content: space-between;
        }
        .sniper-batch-list {
            max-height: 200px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .sniper-batch-item {
            background: rgba(49, 50, 68, 0.6);
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 11px;
            color: #a6adc8;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            border-left: 2px solid #fab387;
        }
        .sniper-struct-mode {
            color: #f5c2e7;
            font-weight: bold;
            font-size: 10px;
            margin-left: 10px;
        }
    `;
    (document.head || document.documentElement).appendChild(style);

    // HTMLエスケープ関数（XSS防止）
    function escapeHtml(str) {
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    const isInputType = (el) => el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA');

    const indicator = document.createElement('div');
    indicator.className = 'sniper-zoom-indicator';
    (document.body || document.documentElement).appendChild(indicator);

    let baseTarget = null;
    let targetStack = []; 
    let zoomIndex = 0; 
    let isSniperMode = false;
    let isStructMode = false;
    let isStyleMode = false;
    let isDomMode = false;
    let isBatchMode = false;
    let batchBucket = [];
    let lastHighlighted = null; // 前回のハイライト要素を保持（パフォーマンス最適化）

    // --- Style Snipe v2: 最適化済みCSSプロパティリスト ---
    // ショートハンドのみを使用し、ロングハンド（-top, -right等）は個別に必要な場合のみ追加
    const STYLE_PROPS = {
        // テキスト装飾（最重要：見た目の再現に直結）
        text: ['color', 'font-size', 'font-weight', 'font-family', 'font-style',
               'text-decoration', 'text-align', 'line-height', 'letter-spacing', 'white-space'],
        // 背景（サイズや位置の制御もフル解禁）
        bg: ['background-color', 'background-image', 'background-size', 'background-position', 'background-repeat'],
        // ボックスモデル（寸法限定許可を適用）
        box: ['width', 'height', 'min-width', 'min-height', 'max-width', 'padding', 'margin', 'border', 'border-top', 'border-right', 'border-bottom', 'border-left', 'border-radius'],
        // レイアウト（Flexbox / Float / CSS Grid 完全解禁）
        layout: ['display', 'flex', 'flex-direction', 'flex-wrap', 'flex-grow', 'flex-shrink', 'flex-basis', 'align-items', 'justify-content', 'gap',
                 'vertical-align', 'float', 'clear', 'grid-template-columns', 'grid-template-rows', 'grid-column', 'grid-row'],
        // 装飾（変形やフィルター効果を解禁しリッチ化）
        decoration: ['box-shadow', 'text-shadow', 'opacity', 'overflow', 'transform', 'filter', 'backdrop-filter'],
        // リスト（ul/ol/liのみ適用）
        list: ['list-style-type']
    };

    /**
     * isDefaultValue: 値がデフォルト（焼き付け不要）かどうかをパターンで判定
     * 完全一致ではなくパターンマッチにより、ブラウザ間の微妙な出力差を吸収
     */
    function isDefaultValue(prop, val) {
        if (!val || val === 'normal' || val === 'none' || val === 'auto') return true;

        // 透明背景
        if (prop === 'background-color' && /rgba\(\s*0,\s*0,\s*0,\s*0\s*\)/.test(val)) return true;
        if (prop === 'background-image' && val === 'none') return true;

        // ボーダーなし（"0px none ..." の各種パターン）
        if (/^border(-top|-right|-bottom|-left)?$/.test(prop) && /^0px\s+none/.test(val)) return true;

        // ゼロ値（margin: 0px, padding: 0px, border-radius: 0px 等）
        if (/^(margin|padding|border-radius|width|height|min-width|min-height)$/.test(prop) && /^0(px)?\b/.test(val)) return true;

        // テキスト系デフォルト
        if (prop === 'color' && val === 'rgb(0, 0, 0)') return true;
        if (prop === 'font-weight' && (val === '400' || val === 'normal')) return true;
        if (prop === 'font-style' && val === 'normal') return true;
        if (prop === 'text-decoration' && /^none/.test(val)) return true;
        if (prop === 'text-align' && (val === 'start' || val === 'left')) return true;
        if (prop === 'letter-spacing' && val === 'normal') return true;
        if (prop === 'white-space' && val === 'normal') return true;
        if (prop === 'line-height' && val === 'normal') return true;

        // レイアウトデフォルト
        if (prop === 'display' && (val === 'block' || val === 'inline')) return true;
        if (prop === 'flex-direction' && val === 'row') return true;
        if (prop === 'flex' && val === '0 1 auto') return true;
        if (prop === 'flex-grow' && val === '0') return true;
        if (prop === 'flex-shrink' && val === '1') return true;
        if (prop === 'flex-wrap' && val === 'nowrap') return true;
        if (prop === 'align-items' && (val === 'normal' || val === 'stretch')) return true;
        if (prop === 'justify-content' && (val === 'normal' || val === 'flex-start')) return true;
        if (prop === 'gap' && (val === 'normal' || val === '0px')) return true;
        if (prop === 'vertical-align' && val === 'baseline') return true;
        if (/^grid/.test(prop) && val === 'none') return true;

        // 装飾デフォルト
        if (prop === 'box-shadow' && val === 'none') return true;
        if (prop === 'text-shadow' && val === 'none') return true;
        if (prop === 'opacity' && val === '1') return true;
        if (prop === 'overflow' && val === 'visible') return true;
        if (prop === 'transform' && val === 'none') return true;
        if (prop === 'filter' && val === 'none') return true;
        if (prop === 'backdrop-filter' && val === 'none') return true;
        
        // 背景詳細デフォルト
        if (prop === 'background-size' && val === 'auto') return true;
        if (prop === 'background-position' && val === '0% 0%') return true;
        if (prop === 'background-repeat' && val === 'repeat') return true;

        // リスト
        if (prop === 'list-style-type' && (val === 'disc' || val === 'none')) return true;

        return false;
    }

    /**
     * cloneWithComputedStyle v2: CSS最適化強化版
     * 
     * 改善点:
     * 1. ショートハンド優先（padding-top等のロングハンドを完全排除）
     * 2. デフォルト値のパターンマッチ（ブラウザ差異を吸収）
     * 3. 固定px幅/高さを全要素で除去（Writer A4紙面適合）
     * 4. list-styleはul/ol/liのみに適用
     * 5. font-familyの正規化（長大なフォールバックチェーンを簡素化）
     */
    function cloneWithComputedStyle(element) {
        const baseUrl = window.location.href;

        function resolveUrl(url) {
            if (!url || url.startsWith('data:') || url.startsWith('blob:')) return url;
            try {
                return new URL(url, baseUrl).href;
            } catch(e) {
                return url;
            }
        }

        // font-family 簡素化: 長いフォント指定から先頭のみ抽出 + 汎用フォールバック
        function simplifyFontFamily(val) {
            if (!val) return val;
            const fonts = val.split(',').map(f => f.trim().replace(/^["']|["']$/g, ''));
            const generic = ['serif', 'sans-serif', 'monospace', 'cursive', 'fantasy', 'system-ui'];
            const primary = fonts[0] || 'sans-serif';
            const fallback = fonts.find(f => generic.includes(f)) || 'sans-serif';
            if (generic.includes(primary)) return primary;
            return `${primary}, ${fallback}`;
        }

        // rgba → rgb 変換: 白背景(255,255,255)に合成して不透明色にする
        // Writer等のリッチテキスト環境ではrgbaの透明度合成が正しく処理されないため
        function resolveRgba(val) {
            if (!val) return val;
            return val.replace(/rgba\(\s*(\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\s*\)/g,
                (match, r, g, b, a) => {
                    const alpha = parseFloat(a);
                    if (alpha >= 1) return `rgb(${r}, ${g}, ${b})`;
                    if (alpha <= 0) return 'transparent';
                    // 白背景(255)に合成: result = alpha * color + (1 - alpha) * 255
                    const rr = Math.round(alpha * parseInt(r) + (1 - alpha) * 255);
                    const gg = Math.round(alpha * parseInt(g) + (1 - alpha) * 255);
                    const bb = Math.round(alpha * parseInt(b) + (1 - alpha) * 255);
                    // 白に十分近い場合は透明扱い（Writerで微妙な色差が目立つのを防止）
                    if (rr >= 240 && gg >= 240 && bb >= 240) return 'transparent';
                    return `rgb(${rr}, ${gg}, ${bb})`;
                }
            );
        }

        // 継承されるプロパティのリスト
        const INHERITABLE_PROPS = [
            'color', 'font-size', 'font-weight', 'font-family', 'font-style',
            'text-align', 'line-height', 'letter-spacing', 'white-space',
            'list-style-type'
        ];

        function processNode(original, clone, isRoot, inheritedStyles = {}) {
            if (original.nodeType !== Node.ELEMENT_NODE) return;

            const tagName = original.tagName.toLowerCase();

            // 除去対象タグ
            if (tagName === 'script' || tagName === 'style' || tagName === 'link' || tagName === 'noscript') {
                clone.remove();
                return;
            }

            // Sniperのハイライトクラスを除去
            clone.classList.remove('sniper-highlight', 'sniper-highlight-struct',
                                  'sniper-highlight-batch', 'sniper-highlight-style');
            if (clone.classList.length === 0) clone.removeAttribute('class');

            let newInheritedStyles = { ...inheritedStyles };

            // ComputedStyleの取得と最適化された焼き付け
            try {
                const computed = window.getComputedStyle(original);
                let inlineStyles = [];
                const isListElement = /^(ul|ol|li)$/.test(tagName);

                // 必要なプロパティグループを収集
                const propGroups = ['text', 'bg', 'box', 'layout', 'decoration'];
                if (isListElement) propGroups.push('list');

                for (const group of propGroups) {
                    for (const prop of STYLE_PROPS[group]) {
                        let val = computed.getPropertyValue(prop);
                        if (!val || isDefaultValue(prop, val)) continue;

                        // rgba → rgb 変換
                        val = resolveRgba(val);
                        if (val === 'transparent' || isDefaultValue(prop, val)) continue;

                        // font-family は簡素化
                        if (prop === 'font-family') {
                            val = simplifyFontFamily(val);
                        }

                        // ★ 継承最適化: 親と全く同じ値なら省略
                        if (INHERITABLE_PROPS.includes(prop)) {
                            if (val === inheritedStyles[prop]) {
                                continue; // 親から継承されるため出力不要
                            }
                            // 子へ引き継ぎ
                            newInheritedStyles[prop] = val;
                        }

                        inlineStyles.push(`${prop}: ${val}`);
                    }
                }

                // position: absolute/fixed は解除
                const pos = computed.getPropertyValue('position');
                if (pos === 'absolute' || pos === 'fixed') {
                    inlineStyles.push('position: static');
                }

                if (inlineStyles.length > 0) {
                    clone.setAttribute('style', inlineStyles.join('; '));
                }
            } catch(e) {
                // pass
            }

            // URL系属性の絶対化とリンクの安全性
            if (tagName === 'img' && clone.hasAttribute('src')) {
                clone.setAttribute('src', resolveUrl(clone.getAttribute('src')));
            }
            if (tagName === 'a') {
                if (clone.hasAttribute('href')) {
                    clone.setAttribute('href', resolveUrl(clone.getAttribute('href')));
                }
                // ★ リンクの安全設計 (Writer上の利便性)
                clone.setAttribute('target', '_blank');
                clone.setAttribute('rel', 'noopener noreferrer');
            }
            if (clone.hasAttribute('srcset')) {
                // srcsetは複雑なので除去してsrcに寄せる
                clone.removeAttribute('srcset');
            }

            // 不要な属性を除去
            const removeAttrs = ['id', 'onclick', 'onload', 'onerror', 'onmouseover',
                                 'onmouseout', 'onfocus', 'onblur', 'data-file-width',
                                 'data-file-height', 'typeof', 'decoding'];
            for (const attr of removeAttrs) {
                clone.removeAttribute(attr);
            }

            // 子要素を再帰処理
            const origChildren = Array.from(original.children);
            const cloneChildren = Array.from(clone.children);
            for (let i = 0; i < origChildren.length && i < cloneChildren.length; i++) {
                processNode(origChildren[i], cloneChildren[i], false, newInheritedStyles);
            }

            // ★ 空要素のクリーンアップ（子を持たず、テキストもない、表示上意味のないspanやdivを除去）
            // isRootは除去しない
            if (!isRoot && /^(span|div|p|b|i|strong|em)$/.test(tagName)) {
                if (clone.childNodes.length === 0 && clone.textContent.trim() === "") {
                    clone.remove();
                }
            }
        }

        // Deep Clone
        const clone = element.cloneNode(true);
        processNode(element, clone, true, {});

        // Minify: Markdownのコードブロック化を防ぐため、改行と連続する空白を除去
        // ただし、<pre>タグの中身は元のフォーマット(改行やインデント)を維持する
        let finalHtml = clone.outerHTML;
        
        const preBlocks = [];
        finalHtml = finalHtml.replace(/<pre\b[^>]*>([\s\S]*?)<\/pre>/gi, (match) => {
            preBlocks.push(match);
            return `__PRE_BLOCK_${preBlocks.length - 1}__`;
        });
        
        // <pre>以外をミニファイ
        finalHtml = finalHtml.replace(/\n\s*/g, ' ').replace(/>\s+</g, '><').trim();
        
        // <pre>を復元
        preBlocks.forEach((block, idx) => {
            finalHtml = finalHtml.replace(`__PRE_BLOCK_${idx}__`, block);
        });
        
        // ★ Sモード防波堤：A4サイズ（Writer等）での破綻を防ぎつつ、スクロールバーを出さずに折り返させる
        const safeguardStyle = `
<style>
.sniper-style-wrapper * {
    max-width: 100% !important;
    height: auto !important;
    box-sizing: border-box !important;
    word-break: break-word !important;
    overflow-wrap: anywhere !important;
    overflow: visible !important;
}
.sniper-style-wrapper pre, .sniper-style-wrapper code {
    white-space: pre-wrap !important;
    overflow: visible !important;
}
</style>`;
        finalHtml = `${safeguardStyle}\n<div class="sniper-style-wrapper" style="clear: both; width: 100%;">${finalHtml}</div>`;
        
        return finalHtml;
    }

    function updateIndicator() {
        if (targetStack.length === 0 && !isBatchMode) {
            indicator.style.display = 'none';
            return;
        }
        
        let breadcrumbs = targetStack.map((el, idx) => {
            const tagName = escapeHtml(el.tagName.toLowerCase());
            const activeClass = (idx === zoomIndex) ? 'active' : '';
            return `<span class="sniper-breadcrumb-item ${activeClass}">${tagName}</span>`;
        }).join('<span class="sniper-breadcrumb-separator">/</span>');
        
        let modeIndicator = "";
        if (isStyleMode) {
            modeIndicator = `<span class="sniper-struct-mode" style="color: #b4befe;">[HOLD S: Style]</span>`;
        } else if (isDomMode) {
            modeIndicator = `<span class="sniper-struct-mode" style="color: #a6e3a1;">[HOLD D: DOM]</span>`;
        } else if (isSniperMode) {
            modeIndicator = isStructMode ? 
                `<span class="sniper-struct-mode">[HOLD Z: Struct]</span>` : 
                `<span class="sniper-struct-mode" style="color: #00f2fe;">[HOLD A: Direct]</span>`;
        }
        let breadcrumbHtml = `<div class="sniper-breadcrumb-container">${breadcrumbs}${modeIndicator}</div>`;
        
        let batchHtml = "";
        if (isBatchMode) {
            let itemsHtml = batchBucket.map(text => {
                let display = text.length > 50 ? text.substring(0, 50) + "..." : text;
                return `<div class="sniper-batch-item">${escapeHtml(display)}</div>`;
            }).join('');
            
            batchHtml = `
                <div class="sniper-batch-preview">
                    <div class="sniper-batch-header">
                        <span>Batch Collection</span>
                        <span>${batchBucket.length} items</span>
                    </div>
                    <div class="sniper-batch-list">${itemsHtml}</div>
                </div>
            `;
        }
        
        indicator.innerHTML = breadcrumbHtml + batchHtml;
        indicator.style.display = 'block';
        indicator.style.opacity = '1';
    }

    document.addEventListener('keydown', (e) => {
        // 入力欄でもスナイパーモードを起動できるようガードを外す (z/aの介入は抽出時にクリーンアップ)
        // if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        
        if (e.key.toLowerCase() === 'z') {
            if (!isSniperMode || !isStructMode) {
                isSniperMode = true;
                isStructMode = true;
                updateHighlight();
                updateIndicator();
            }
        }
        
        if (e.key.toLowerCase() === 'a') {
            if (!isSniperMode || isStructMode) {
                isSniperMode = true;
                isStructMode = false;
                updateHighlight();
                updateIndicator();
            }
        }
        
        if (e.key.toLowerCase() === 'c' && !e.ctrlKey && !e.metaKey) {
            if (!isBatchMode) {
                isBatchMode = true;
                batchBucket = [];
                updateHighlight();
                updateIndicator();
            }
        }

        if (e.key.toLowerCase() === 's' && !e.ctrlKey && !e.metaKey) {
            if (!isStyleMode) {
                isStyleMode = true;
                isSniperMode = false;
                isStructMode = false;
                isDomMode = false;
                updateHighlight();
                updateIndicator();
            }
        }

        if (e.key.toLowerCase() === 'd' && !e.ctrlKey && !e.metaKey) {
            if (!isDomMode) {
                isDomMode = true;
                isSniperMode = false;
                isStructMode = false;
                isStyleMode = false;
                updateHighlight();
                updateIndicator();
            }
        }
    }, true);

    document.addEventListener('keyup', (e) => {
        if (e.key.toLowerCase() === 'z' || e.key.toLowerCase() === 'a') {
            isSniperMode = false;
            isStructMode = false;
            updateHighlight();
            updateIndicator();
        }

        if (e.key.toLowerCase() === 's') {
            isStyleMode = false;
            updateHighlight();
            updateIndicator();
        }

        if (e.key.toLowerCase() === 'd') {
            isDomMode = false;
            updateHighlight();
            updateIndicator();
        }

        if (e.key.toLowerCase() === 'c') {
            if (isBatchMode) {
                if (batchBucket.length > 0) {
                    const combinedText = batchBucket.join('\n');
                    if (window.sniperBridge) {
                        window.sniperBridge.receive_text(combinedText);
                    }
                }
                isBatchMode = false;
                batchBucket = [];
                updateIndicator();
            }
        }
    }, true);

    function updateHighlight() {
        // 前回のハイライトだけをクリア（全要素走査を回避）
        if (lastHighlighted) {
            lastHighlighted.classList.remove('sniper-highlight', 'sniper-highlight-struct', 'sniper-highlight-batch', 'sniper-highlight-style', 'sniper-highlight-dom');
            lastHighlighted = null;
        }

        if (!isSniperMode && !isBatchMode && !isStyleMode && !isDomMode) return;

        let current = targetStack[zoomIndex];
        if (!current) return;

        if (isStyleMode) {
            current.classList.add('sniper-highlight-style');
            lastHighlighted = current;
        } else if (isDomMode) {
            current.classList.add('sniper-highlight-dom');
            lastHighlighted = current;
        } else if (isStructMode) {
            let struct = current.closest('table, ul, ol');
            if (struct && targetStack[zoomIndex] !== document.documentElement && targetStack[zoomIndex] !== document.body) {
                struct.classList.add('sniper-highlight-struct');
                lastHighlighted = struct;
            } else {
                current.classList.add('sniper-highlight');
                lastHighlighted = current;
            }
        } else {
            current.classList.add('sniper-highlight');
            lastHighlighted = current;
        }
    }

    document.addEventListener('mouseover', function(e) {
        // 座標からその地点にある全要素（深さ順）を取得する「貫通探索」
        const x = e.clientX;
        const y = e.clientY;
        const elementsAtPoint = document.elementsFromPoint(x, y);
        
        // 1. 最優先でInput/Textareaを探す
        let target = elementsAtPoint.find(el => el.tagName === 'INPUT' || el.tagName === 'TEXTAREA');
        
        // 2. 見つからなければ本来のe.targetを使用
        if (!target) {
            target = e.target;
        }

        if (baseTarget === target) return;
        
        baseTarget = target;
        targetStack = [baseTarget];
        zoomIndex = 0;
        updateHighlight();
        updateIndicator();
    }, true);

    document.addEventListener('wheel', function(e) {
        if (targetStack.length === 0 || (!isSniperMode && !isBatchMode && !isStyleMode && !isDomMode)) return;

        if (e.deltaY < 0) {
            let current = targetStack[zoomIndex];
            if (current.parentElement && current.parentElement !== document.documentElement) {
                if (zoomIndex + 1 < targetStack.length) {
                    zoomIndex++;
                } else {
                    targetStack.push(current.parentElement);
                    zoomIndex++;
                }
                e.preventDefault();
                updateHighlight();
                updateIndicator();
            }
        } 
        else if (e.deltaY > 0) {
            if (zoomIndex > 0) {
                zoomIndex--;
                e.preventDefault();
                updateHighlight();
                updateIndicator();
            }
        }
    }, { passive: false });

    function tableToMarkdown(table) {
        let markdown = "";
        let rows = table.querySelectorAll('tr');
        if (rows.length === 0) return "";

        Array.from(rows).forEach((row, rowIndex) => {
            let cols = row.querySelectorAll('td, th');
            let rowData = Array.from(cols).map(col => {
                let cellText = (col.innerText || col.textContent).trim();
                return cellText.replace(/\r?\n/g, " ").replace(/\|/g, "\\|");
            });
            markdown += "| " + rowData.join(" | ") + " |\n";
            
            if (rowIndex === 0) {
                let separator = Array.from(cols).map(() => "---");
                markdown += "| " + separator.join(" | ") + " |\n";
            }
        });
        return markdown.trim();
    }

    function listToMarkdown(list, depth = 0) {
        let markdown = "";
        let isOrdered = list.tagName.toLowerCase() === 'ol';
        let indent = "  ".repeat(depth);
        let count = 1;
        
        Array.from(list.children).forEach(li => {
            if (li.tagName.toLowerCase() !== 'li') return;
            
            let prefix = isOrdered ? `${count}. ` : "- ";
            
            // Get text without children lists to avoid duplication
            let ownText = "";
            Array.from(li.childNodes).forEach(node => {
                if (node.nodeType === Node.TEXT_NODE) ownText += node.textContent;
                else if (node.nodeType === Node.ELEMENT_NODE && !['UL', 'OL'].includes(node.tagName)) {
                    ownText += node.innerText || node.textContent;
                }
            });
            
            markdown += `${indent}${prefix}${ownText.trim()}\n`;
            
            // Nested lists
            let nested = li.querySelector('ul, ol');
            if (nested) {
                markdown += listToMarkdown(nested, depth + 1);
            }
            count++;
        });
        return markdown;
    }

    // --- 深層探索ユーティリティ ---
    function getAllElementsAtPoint(doc, x, y) {
        let elements = Array.from(doc.elementsFromPoint(x, y));
        let allElements = [...elements];

        for (const el of elements) {
            // 1. Iframe 貫通
            if (el.tagName === 'IFRAME') {
                try {
                    const iframeDoc = el.contentDocument || el.contentWindow.document;
                    if (iframeDoc) {
                        const rect = el.getBoundingClientRect();
                        const subElements = getAllElementsAtPoint(iframeDoc, x - rect.left, y - rect.top);
                        allElements = allElements.concat(subElements);
                    }
                } catch (e) {
                    console.warn("Cross-origin iframe access blocked.");
                }
            }
            
            // 2. Shadow DOM 貫通 (Web Components 対策)
            if (el.shadowRoot) {
                try {
                    const shadowElements = getAllElementsAtPoint(el.shadowRoot, x, y);
                    allElements = allElements.concat(shadowElements);
                } catch (e) {
                    // Ignore errors
                }
            }
        }
        return allElements;
    }

    /**
     * cloneWithoutStyles: 全てのスタイルやクラス、寸法を削ぎ落とし
     * セマンティックな純粋HTML構造(DOM)のみを出力する
     */
    function cloneWithoutStyles(element) {
        const baseUrl = window.location.href;

        function resolveUrl(url) {
            if (!url || url.startsWith('data:') || url.startsWith('blob:')) return url;
            try { return new URL(url, baseUrl).href; } catch(e) { return url; }
        }

        function processDomNode(original, clone) {
            if (original.nodeType !== Node.ELEMENT_NODE) return;
            const tagName = original.tagName.toLowerCase();

            if (tagName === 'script' || tagName === 'style' || tagName === 'link' || tagName === 'noscript') {
                clone.remove();
                return;
            }

            // ★ width/height 等の寸法属性を含め、純粋なHTMLタグに不要な情報をすべてパージ
            const strictlyAllowed = ['src', 'href', 'alt', 'title', 'type', 'value', 'placeholder', 'rowspan', 'colspan', 'scope'];
            Array.from(clone.attributes).forEach(attr => {
                if (!strictlyAllowed.includes(attr.name)) {
                    clone.removeAttribute(attr.name);
                }
            });

            if (tagName === 'img' && clone.hasAttribute('src')) {
                clone.setAttribute('src', resolveUrl(clone.getAttribute('src')));
            }
            if (tagName === 'a') {
                if (clone.hasAttribute('href')) {
                    clone.setAttribute('href', resolveUrl(clone.getAttribute('href')));
                }
                clone.setAttribute('target', '_blank');
                clone.setAttribute('rel', 'noopener noreferrer');
            }

            // Shadow DOM、Iframe 貫通はせず、表層の純粋DOMのみを処理
            const origChildren = Array.from(original.children);
            const cloneChildren = Array.from(clone.children);
            for (let i = 0; i < origChildren.length && i < cloneChildren.length; i++) {
                processDomNode(origChildren[i], cloneChildren[i]);
            }
        }

        const clone = element.cloneNode(true);
        processDomNode(element, clone);
        
        let finalHtml = clone.outerHTML;
        
        // <pre>を保護しつつミニファイ
        const preBlocks = [];
        finalHtml = finalHtml.replace(/<pre\b[^>]*>([\s\S]*?)<\/pre>/gi, (match) => {
            preBlocks.push(match);
            return `__PRE_BLOCK_${preBlocks.length - 1}__`;
        });
        
        finalHtml = finalHtml.replace(/\n\s*/g, ' ').replace(/>\s+</g, '><').trim();
        
        preBlocks.forEach((block, idx) => {
            finalHtml = finalHtml.replace(`__PRE_BLOCK_${idx}__`, block);
        });
        
        return finalHtml;
    }

    document.addEventListener('click', function(e) {
        if (!isSniperMode && !isBatchMode && !isStyleMode && !isDomMode) return; 

        e.preventDefault();
        e.stopPropagation();

        let targetElement = targetStack[zoomIndex];
        if (!targetElement) return;

        // --- DOM Snipe モード (D) ---
        if (isDomMode) {
            try {
                const html = cloneWithoutStyles(targetElement);
                if (html && window.sniperBridge && window.sniperBridge.receive_html) {
                    window.sniperBridge.receive_html(html);

                    const originalOutline = targetElement.style.outline;
                    targetElement.style.outline = '3px solid #a6e3a1';
                    setTimeout(() => {
                        targetElement.style.outline = originalOutline;
                    }, 400);
                }
            } catch(err) {
                console.error('DOM Snipe error:', err);
            }
            window.getSelection().removeAllRanges();
            return;
        }

        // --- Style Snipe モード (S) ---
        if (isStyleMode) {
            try {
                const html = cloneWithComputedStyle(targetElement);
                if (html && window.sniperBridge && window.sniperBridge.receive_html) {
                    window.sniperBridge.receive_html(html);

                    // 成功フィードバック（Lavender系で一瞬光る）
                    const originalOutline = targetElement.style.outline;
                    targetElement.style.outline = '3px solid #b4befe';
                    setTimeout(() => {
                        targetElement.style.outline = originalOutline;
                    }, 400);
                }
            } catch(err) {
                console.error('Style Snipe error:', err);
            }
            window.getSelection().removeAllRanges();
            return; // Sモードは独自処理で完結。既存のテキスト抽出には進まない
        }

        let text = window.getSelection().toString().trim();

        // 汎用データ・コレクター（ピンポイント狙撃 vs 範囲一括収集）
        const extractSmartText = (rootEl, collectAll = false) => {
            if (!rootEl) return "";
            
            let candidates = [];

            // 再帰的に候補を収集
            const scan = (el) => {
                if (!el) return;
                const tag = el.tagName.toLowerCase();
                const id = el.id || "";
                const cls = el.className || "";
                const isInput = (tag === 'input' || tag === 'textarea');
                const dataKeywords = /input|value|code|text|amt|val|data/i;
                const weight = dataKeywords.test(id + cls) ? 50 : 0;

                // --- 候補1: 入力欄 ---
                if (isInput) {
                    const val = (el.value || "").trim();
                    if (val && val.length > 0) {
                        candidates.push({ text: val, score: 100 + weight, el: el, isInput: true });
                    }
                }

                // --- 候補2: 表面のテキスト ---
                let inner = (el.innerText || el.textContent || "").trim();
                // コレクターモード時は、子要素へ再帰した後にこの要素自身を評価するか判断
                if (inner && inner.length > 0 && inner.length < 1000) {
                    let score = 30 + weight;
                    if (inner.endsWith('：') || inner.endsWith(':')) score -= 10;
                    if (/[0-9]/.test(inner)) score += 10;
                    candidates.push({ text: inner, score: score, el: el, isInput: false });
                }

                // 子要素へ (Shadow DOM含む)
                if (el.children && el.children.length > 0) {
                    Array.from(el.children).forEach(scan);
                }
                if (el.shadowRoot) scan(el.shadowRoot);
            };

            scan(rootEl);
            if (candidates.length === 0) return "";

            // --- A. ピンポイント狙撃モード (collectAll = false) ---
            if (!collectAll) {
                candidates.sort((a, b) => b.score - a.score);
                let best = candidates[0].text.replace(/[：:]\s*$/, "").trim();
                return best;
            }

            // --- B. スマート・コレクターモード (collectAll = true) ---
            // 1. スコアで最低限の足切り (意味のない要素を除外)
            let validCandidates = candidates.filter(c => c.score >= 30);
            
            // 2. 重複排除 (親要素のテキストの一部が子要素の入力値である場合など、中身を優先)
            // 具体的な要素（Inputや深い階層のもの）を優先的に拾い、重複を削る
            let results = [];
            let seenText = new Set();
            
            // 入力欄を最優先で確定
            validCandidates.filter(c => c.isInput).forEach(c => {
                const t = c.text;
                if (!seenText.has(t)) {
                    results.push(t);
                    seenText.add(t);
                }
            });

            // その他のテキストを、他と重ならない範囲で追加
            validCandidates.filter(c => !c.isInput).forEach(c => {
                const t = c.text.replace(/[：:]\s*$/, "").trim();
                // 既に取得済みの入力値がこのテキストに含まれている、またはその逆ならスキップ（重複回避）
                let isDuplicate = false;
                for (let seen of seenText) {
                    if (seen.includes(t) || t.includes(seen)) {
                        isDuplicate = true; break;
                    }
                }
                if (!isDuplicate && t.length > 0) {
                    results.push(t);
                    seenText.add(t);
                }
            });

            return results.join('\n');
        };

        if (!text) {
            // ズームアウト(zoomIndex > 0)している場合は「全収集」、そうでなければ「ピンポイント」
            const isCollection = (zoomIndex > 0);
            let candidateText = extractSmartText(targetElement, isCollection);

            if (!candidateText || candidateText.length === 0) {
                const elementsAtPoint = getAllElementsAtPoint(document, e.clientX, e.clientY);
                for (const el of elementsAtPoint) {
                    let t = extractSmartText(el, isCollection);
                    if (t) {
                        candidateText = t;
                        targetElement = el;
                        break;
                    }
                }
            }
            text = candidateText;
        }
        
        if (!targetElement) return;

        // --- 特殊処理: 構造抽出モード (Z) ---
        if (isStructMode && (!text || text === targetElement.innerText)) {
            let struct = targetElement.closest('table, ul, ol');
            if (struct) {
                const tag = struct.tagName.toLowerCase();
                text = (tag === 'table') ? tableToMarkdown(struct) : listToMarkdown(struct);
                targetElement = struct;
            }
        }

        // --- スナイパーキーによる不要な入力のクリーンアップ (z, a) ---
        if (text && isInputType(targetElement)) {
            const sniperKey = isStructMode ? 'z' : 'a';
            if (text.endsWith(sniperKey)) {
                text = text.slice(0, -1);
                targetElement.value = text;
            }
        }
        
        if (text) {
            text = text.trim();
            
            if (isBatchMode) {
                batchBucket.push(text);
                updateIndicator();
                
                targetElement.classList.add('sniper-highlight-batch');
                setTimeout(() => {
                    targetElement.classList.remove('sniper-highlight-batch');
                }, 200);
            } else {
                if (window.sniperBridge) {
                    window.sniperBridge.receive_text(text);
                    
                    const originalOutline = targetElement.style.outline;
                    targetElement.style.outline = "2px solid #a6e3a1"; 
                    setTimeout(() => {
                        targetElement.style.outline = originalOutline;
                    }, 300);
                }
            }
            window.getSelection().removeAllRanges();
        }
    }, true);

    function initWebChannel() {
        if (typeof QWebChannel !== 'undefined' && typeof qt !== 'undefined' && qt.webChannelTransport) {
            new QWebChannel(qt.webChannelTransport, function(channel) {
                window.sniperBridge = channel.objects.sniperBridge;
                console.log("SniperBridge initialized.");
            });
        } else {
            // まだ qt が定義されていない場合は少し待ってリトライ
            setTimeout(initWebChannel, 100);
        }
    }

    initWebChannel();
})();
