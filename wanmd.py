#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WanMD - スタンドアロン マークダウンエディタ
依存: pip install pywebview
実行: python wanmd.py
"""

import os
import sys

try:
    import webview
except ImportError:
    print("エラー: pywebview が見つかりません。")
    print("インストール: pip install pywebview")
    sys.exit(1)


class Api:
    """JS から呼び出されるファイル操作 API"""

    def __init__(self):
        self._window = None

    def open_file(self):
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=("Markdown (*.md;*.markdown;*.txt)", "All files (*.*)")
        )
        if not result:
            return None
        try:
            with open(result[0], "r", encoding="utf-8") as f:
                return {"content": f.read(), "filename": os.path.basename(result[0])}
        except Exception as e:
            return {"error": str(e)}

    def save_markdown(self, content, default_name):
        base = default_name.rsplit(".", 1)[0] if "." in default_name else default_name
        result = self._window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=base + ".md",
            file_types=("Markdown (*.md)",)
        )
        if not result:
            return None
        path = result[0] if isinstance(result, (list, tuple)) else result
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"saved": True, "filename": os.path.basename(path)}
        except Exception as e:
            return {"error": str(e)}

    def save_html(self, content, default_name):
        base = default_name.rsplit(".", 1)[0] if "." in default_name else default_name
        result = self._window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=base + ".html",
            file_types=("HTML (*.html)",)
        )
        if not result:
            return None
        path = result[0] if isinstance(result, (list, tuple)) else result
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"saved": True}
        except Exception as e:
            return {"error": str(e)}


HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WanMD - マークダウンエディタ</title>
  <link id="prism-theme-light" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/prismjs@1/themes/prism.min.css">
  <link id="prism-theme-dark" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/prismjs@1/themes/prism-okaidia.min.css" disabled>
  <script src="https://cdn.jsdelivr.net/npm/markdown-it@14/dist/markdown-it.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1/prism.min.js" data-manual></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-markup.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-css.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-javascript.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-typescript.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-python.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-bash.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-json.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-yaml.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-java.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-csharp.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-go.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-rust.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-sql.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-powershell.min.js"></script>
  <style>
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
:root{
  --font-sans:"Segoe UI","Hiragino Kaku Gothic ProN","Meiryo",sans-serif;
  --font-mono:"Cascadia Code","Consolas","Fira Code","Source Han Code JP",monospace;
  --transition-speed:0.25s;
  --header-height:52px;
  --footer-height:28px;
}
[data-theme="dark"]{
  --bg-primary:#0d1117;--bg-secondary:#161b22;--bg-tertiary:#1c2333;
  --bg-hover:#21262d;--bg-editor:#0d1117;--bg-preview:#0d1117;
  --bg-header:rgba(13,17,23,0.85);--bg-footer:#010409;
  --bg-pane-header:#161b22;--bg-toc:#161b22;--bg-input:#0d1117;
  --border-primary:#30363d;--border-subtle:#21262d;
  --text-primary:#e6edf3;--text-secondary:#8b949e;--text-muted:#6e7681;
  --text-link:#58a6ff;--accent-primary:#58a6ff;
  --accent-gradient-start:#7c3aed;--accent-gradient-end:#2563eb;
  --scrollbar-track:#161b22;--scrollbar-thumb:#30363d;--scrollbar-hover:#484f58;
  --shadow-elevated:0 8px 24px rgba(0,0,0,0.4);--shadow-subtle:0 1px 3px rgba(0,0,0,0.3);
  --line-number-bg:#161b22;--line-number-color:#484f58;
  --resize-handle:#30363d;--resize-handle-hover:#58a6ff;
  --btn-hover-bg:rgba(88,166,255,0.12);--btn-active-bg:rgba(88,166,255,0.2);
  --md-bg:#0d1117;--md-text:#e6edf3;--md-heading:#e6edf3;--md-link:#58a6ff;
  --md-code-bg:#161b22;--md-code-text:#e6edf3;
  --md-blockquote-border:#3b82f6;--md-blockquote-text:#8b949e;
  --md-table-border:#30363d;--md-table-stripe:#161b22;--md-hr:#21262d;
  --md-kbd-bg:#161b22;--md-kbd-border:#30363d;--md-mark-bg:rgba(210,153,34,0.3);
}
[data-theme="light"]{
  --bg-primary:#ffffff;--bg-secondary:#f6f8fa;--bg-tertiary:#eef1f5;
  --bg-hover:#ebeef2;--bg-editor:#ffffff;--bg-preview:#ffffff;
  --bg-header:rgba(255,255,255,0.88);--bg-footer:#f0f2f5;
  --bg-pane-header:#f6f8fa;--bg-toc:#f6f8fa;--bg-input:#ffffff;
  --border-primary:#d0d7de;--border-subtle:#e7ecf0;
  --text-primary:#1f2328;--text-secondary:#656d76;--text-muted:#8c959f;
  --text-link:#0969da;--accent-primary:#0969da;
  --accent-gradient-start:#7c3aed;--accent-gradient-end:#0969da;
  --scrollbar-track:#f0f2f5;--scrollbar-thumb:#c9cfd6;--scrollbar-hover:#afb8c1;
  --shadow-elevated:0 8px 24px rgba(140,149,159,0.2);--shadow-subtle:0 1px 3px rgba(140,149,159,0.12);
  --line-number-bg:#f6f8fa;--line-number-color:#8c959f;
  --resize-handle:#d0d7de;--resize-handle-hover:#0969da;
  --btn-hover-bg:rgba(9,105,218,0.08);--btn-active-bg:rgba(9,105,218,0.15);
  --md-bg:#ffffff;--md-text:#1f2328;--md-heading:#1f2328;--md-link:#0969da;
  --md-code-bg:#f6f8fa;--md-code-text:#1f2328;
  --md-blockquote-border:#0969da;--md-blockquote-text:#656d76;
  --md-table-border:#d0d7de;--md-table-stripe:#f6f8fa;--md-hr:#d8dee4;
  --md-kbd-bg:#f6f8fa;--md-kbd-border:#d0d7de;--md-mark-bg:rgba(255,220,73,0.4);
}
html,body{height:100%;overflow:hidden;font-family:var(--font-sans);background:var(--bg-primary);color:var(--text-primary);transition:background var(--transition-speed),color var(--transition-speed)}
::-webkit-scrollbar{width:8px;height:8px}
::-webkit-scrollbar-track{background:var(--scrollbar-track)}
::-webkit-scrollbar-thumb{background:var(--scrollbar-thumb);border-radius:4px}
::-webkit-scrollbar-thumb:hover{background:var(--scrollbar-hover)}
#app-header{display:flex;align-items:center;justify-content:space-between;height:var(--header-height);padding:0 12px;background:var(--bg-header);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid var(--border-primary);z-index:100;gap:8px}
.header-left{display:flex;align-items:center;flex-shrink:0}
.app-logo{display:flex;align-items:center;gap:6px;font-size:16px;font-weight:700;letter-spacing:-0.5px;user-select:none}
.logo-icon{font-size:20px;background:linear-gradient(135deg,var(--accent-gradient-start),var(--accent-gradient-end));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;animation:logo-pulse 3s ease-in-out infinite}
@keyframes logo-pulse{0%,100%{opacity:1;filter:brightness(1)}50%{opacity:0.8;filter:brightness(1.3)}}
.logo-text{background:linear-gradient(135deg,var(--accent-gradient-start),var(--accent-gradient-end));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.toolbar{display:flex;align-items:center;gap:2px;padding:4px 8px;background:var(--bg-secondary);border:1px solid var(--border-subtle);border-radius:8px;flex-shrink:1;overflow-x:auto}
.toolbar-group{display:flex;align-items:center;gap:1px}
.toolbar-divider{width:1px;height:20px;background:var(--border-primary);margin:0 4px;flex-shrink:0}
.tool-btn{display:flex;align-items:center;justify-content:center;width:30px;height:30px;border:none;border-radius:6px;background:transparent;color:var(--text-secondary);font-family:var(--font-sans);font-size:12px;font-weight:600;cursor:pointer;transition:all 0.15s;flex-shrink:0}
.tool-btn:hover{background:var(--btn-hover-bg);color:var(--text-primary);transform:translateY(-1px)}
.tool-btn:active{background:var(--btn-active-bg);transform:translateY(0)}
.header-right{display:flex;align-items:center;gap:4px;flex-shrink:0}
.file-controls,.view-controls{display:flex;align-items:center;gap:2px}
.ctrl-btn{display:flex;align-items:center;gap:4px;padding:4px 8px;border:none;border-radius:6px;background:transparent;color:var(--text-secondary);font-family:var(--font-sans);font-size:12px;cursor:pointer;transition:all 0.15s;white-space:nowrap}
.ctrl-btn:hover{background:var(--btn-hover-bg);color:var(--text-primary)}
.ctrl-btn.active{background:var(--btn-active-bg);color:var(--accent-primary)}
.ctrl-icon{font-size:14px;line-height:1}
.ctrl-label{font-size:11px;font-weight:500}
#app-main{display:flex;height:calc(100vh - var(--header-height) - var(--footer-height));overflow:hidden}
.pane{display:flex;flex-direction:column;overflow:hidden;transition:flex 0.3s ease}
#editor-pane{flex:1;min-width:0;border-right:1px solid var(--border-primary)}
#preview-pane{flex:1;min-width:0}
.pane-header{display:flex;align-items:center;justify-content:space-between;height:32px;padding:0 12px;background:var(--bg-pane-header);border-bottom:1px solid var(--border-subtle);flex-shrink:0}
.pane-title{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;color:var(--text-muted)}
.pane-info{font-size:11px;color:var(--text-muted);font-family:var(--font-mono)}
.editor-wrapper{display:flex;flex:1;overflow:hidden}
.line-numbers{width:48px;padding:12px 8px 12px 0;background:var(--line-number-bg);color:var(--line-number-color);font-family:var(--font-mono);font-size:13px;line-height:1.6;text-align:right;overflow:hidden;user-select:none;flex-shrink:0;border-right:1px solid var(--border-subtle)}
#editor{flex:1;padding:12px 16px;border:none;outline:none;resize:none;background:var(--bg-editor);color:var(--text-primary);font-family:var(--font-mono);font-size:13px;line-height:1.6;tab-size:2;-moz-tab-size:2;white-space:pre-wrap;word-wrap:break-word;overflow-y:auto;overflow-x:hidden}
#editor::placeholder{color:var(--text-muted)}
.resize-handle{width:4px;cursor:col-resize;background:var(--resize-handle);transition:background 0.2s;flex-shrink:0;position:relative}
.resize-handle:hover,.resize-handle.dragging{background:var(--resize-handle-hover)}
.resize-handle::after{content:"";position:absolute;top:50%;left:-4px;width:12px;height:40px;transform:translateY(-50%);cursor:col-resize}
.preview-wrapper{display:flex;flex:1;overflow:hidden}
.preview-content{flex:1;padding:24px 32px;overflow-y:auto;overflow-x:hidden;background:var(--bg-preview)}
.toc-toggle{padding:2px 8px;border:1px solid var(--border-subtle);border-radius:4px;background:transparent;color:var(--text-muted);font-size:11px;cursor:pointer;transition:all 0.15s}
.toc-toggle:hover{background:var(--btn-hover-bg);color:var(--text-primary)}
.toc-toggle.active{background:var(--btn-active-bg);color:var(--accent-primary);border-color:var(--accent-primary)}
.toc-sidebar{width:0;overflow:hidden;transition:width 0.3s ease;border-right:none;background:var(--bg-toc);flex-shrink:0}
.toc-sidebar.open{width:240px;border-right:1px solid var(--border-subtle);overflow-y:auto}
.toc-header{padding:12px 16px 8px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--text-muted)}
.toc-content{padding:0 8px 12px}
.toc-content a{display:block;padding:4px 8px;margin:1px 0;font-size:12px;color:var(--text-secondary);text-decoration:none;border-radius:4px;transition:all 0.15s;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.toc-content a:hover{background:var(--btn-hover-bg);color:var(--text-primary)}
.toc-content a.toc-h1{padding-left:8px;font-weight:600}
.toc-content a.toc-h2{padding-left:20px}
.toc-content a.toc-h3{padding-left:32px;font-size:11px}
.toc-content a.toc-h4{padding-left:44px;font-size:11px}
.toc-content a.toc-h5{padding-left:56px;font-size:11px}
.toc-content a.toc-h6{padding-left:68px;font-size:11px}
.markdown-body{color:var(--md-text);font-family:var(--font-sans);font-size:15px;line-height:1.7;word-wrap:break-word}
.markdown-body h1,.markdown-body h2,.markdown-body h3,.markdown-body h4,.markdown-body h5,.markdown-body h6{color:var(--md-heading);font-weight:600;margin-top:24px;margin-bottom:16px;line-height:1.25}
.markdown-body h1{font-size:2em;padding-bottom:0.3em;border-bottom:1px solid var(--border-primary)}
.markdown-body h2{font-size:1.5em;padding-bottom:0.3em;border-bottom:1px solid var(--border-primary)}
.markdown-body h3{font-size:1.25em}
.markdown-body h4{font-size:1em}
.markdown-body h5{font-size:0.875em}
.markdown-body h6{font-size:0.85em;color:var(--text-muted)}
.markdown-body p{margin-top:0;margin-bottom:16px}
.markdown-body a{color:var(--md-link);text-decoration:none;transition:opacity 0.15s}
.markdown-body a:hover{text-decoration:underline;opacity:0.85}
.markdown-body code{padding:0.2em 0.4em;background:var(--md-code-bg);color:var(--md-code-text);border-radius:6px;font-family:var(--font-mono);font-size:85%}
.markdown-body pre{padding:16px;overflow:auto;font-size:85%;line-height:1.5;background:var(--md-code-bg);border-radius:8px;margin-bottom:16px;border:1px solid var(--border-subtle)}
.markdown-body pre code{padding:0;background:transparent;border-radius:0;font-size:100%}
.markdown-body blockquote{padding:8px 16px;margin:0 0 16px;border-left:4px solid var(--md-blockquote-border);color:var(--md-blockquote-text);background:var(--md-code-bg);border-radius:0 8px 8px 0}
.markdown-body blockquote>:first-child{margin-top:0}
.markdown-body blockquote>:last-child{margin-bottom:0}
.markdown-body ul,.markdown-body ol{padding-left:2em;margin-bottom:16px}
.markdown-body li{margin-top:4px}
.markdown-body li+li{margin-top:4px}
.markdown-body input[type="checkbox"]{margin-right:6px;vertical-align:middle;accent-color:var(--accent-primary)}
.markdown-body table{border-collapse:collapse;width:100%;margin-bottom:16px;overflow:auto}
.markdown-body table th,.markdown-body table td{padding:8px 13px;border:1px solid var(--md-table-border)}
.markdown-body table th{font-weight:600;background:var(--md-table-stripe)}
.markdown-body table tr:nth-child(2n){background:var(--md-table-stripe)}
.markdown-body hr{height:2px;padding:0;margin:24px 0;background:var(--md-hr);border:0;border-radius:1px}
.markdown-body img{max-width:100%;border-radius:8px;margin:8px 0}
.markdown-body strong{font-weight:600}
.markdown-body em{font-style:italic}
.markdown-body del{text-decoration:line-through;color:var(--text-muted)}
.markdown-body mark{background:var(--md-mark-bg);padding:0.1em 0.3em;border-radius:3px}
.markdown-body kbd{display:inline-block;padding:3px 6px;font-family:var(--font-mono);font-size:11px;line-height:1;color:var(--text-primary);background:var(--md-kbd-bg);border:1px solid var(--md-kbd-border);border-radius:4px;box-shadow:inset 0 -1px 0 var(--md-kbd-border)}
#app-footer{display:flex;align-items:center;justify-content:space-between;height:var(--footer-height);padding:0 12px;background:var(--bg-footer);border-top:1px solid var(--border-primary);font-size:11px;color:var(--text-muted);font-family:var(--font-mono)}
.status-left,.status-right{display:flex;align-items:center;gap:8px}
.status-divider{color:var(--border-primary)}
body.view-editor #preview-pane,body.view-editor .resize-handle{display:none}
body.view-editor #editor-pane{flex:1;border-right:none}
body.view-preview #editor-pane,body.view-preview .resize-handle{display:none}
body.view-preview #preview-pane{flex:1}
.drop-overlay{display:none;position:fixed;inset:0;background:rgba(88,166,255,0.08);border:3px dashed var(--accent-primary);z-index:1000;pointer-events:none;align-items:center;justify-content:center}
.drop-overlay.active{display:flex}
.drop-overlay-text{padding:16px 32px;background:var(--bg-secondary);border:1px solid var(--accent-primary);border-radius:12px;color:var(--accent-primary);font-size:16px;font-weight:600;box-shadow:var(--shadow-elevated)}
#app-header,#app-footer,.pane-header,.line-numbers,#editor,.preview-content,.toc-sidebar,.toolbar,.tool-btn,.ctrl-btn{transition:background var(--transition-speed),color var(--transition-speed),border-color var(--transition-speed)}
@media(max-width:768px){.ctrl-label{display:none}.toolbar-group{gap:0}.toolbar{padding:2px 4px}.tool-btn{width:28px;height:28px;font-size:11px}.toc-sidebar.open{width:200px}}
@media(max-width:600px){#app-main{flex-direction:column}#editor-pane{border-right:none;border-bottom:1px solid var(--border-primary)}.resize-handle{width:auto;height:4px;cursor:row-resize}}
@media print{#app-header,#app-footer,#editor-pane,.resize-handle,.toc-sidebar,.pane-header{display:none !important}#preview-pane{flex:1}.preview-content{padding:0}.markdown-body pre{white-space:pre-wrap;word-wrap:break-word}}
  </style>
</head>
<body data-theme="dark">

  <header id="app-header">
    <div class="header-left">
      <h1 class="app-logo">
        <span class="logo-icon">&#10022;</span>
        <span class="logo-text">WanMD</span>
      </h1>
    </div>
    <div class="toolbar" id="toolbar">
      <div class="toolbar-group">
        <button class="tool-btn" data-action="heading1" title="見出し1 (Ctrl+1)">H1</button>
        <button class="tool-btn" data-action="heading2" title="見出し2 (Ctrl+2)">H2</button>
        <button class="tool-btn" data-action="heading3" title="見出し3 (Ctrl+3)">H3</button>
      </div>
      <div class="toolbar-divider"></div>
      <div class="toolbar-group">
        <button class="tool-btn" data-action="bold" title="太字 (Ctrl+B)"><b>B</b></button>
        <button class="tool-btn" data-action="italic" title="斜体 (Ctrl+I)"><i>I</i></button>
        <button class="tool-btn" data-action="strikethrough" title="打消線 (Ctrl+D)"><s>S</s></button>
        <button class="tool-btn" data-action="code" title="コード (Ctrl+`)">&#10216;&#10217;</button>
      </div>
      <div class="toolbar-divider"></div>
      <div class="toolbar-group">
        <button class="tool-btn" data-action="unordered-list" title="箇条書き">&#9776;</button>
        <button class="tool-btn" data-action="ordered-list" title="番号付きリスト">1.</button>
        <button class="tool-btn" data-action="task-list" title="タスクリスト">&#9745;</button>
        <button class="tool-btn" data-action="blockquote" title="引用">&#10077;</button>
      </div>
      <div class="toolbar-divider"></div>
      <div class="toolbar-group">
        <button class="tool-btn" data-action="link" title="リンク (Ctrl+K)">&#128279;</button>
        <button class="tool-btn" data-action="image" title="画像">&#128444;</button>
        <button class="tool-btn" data-action="table" title="テーブル">&#9638;</button>
        <button class="tool-btn" data-action="horizontal-rule" title="水平線">&#8213;</button>
        <button class="tool-btn" data-action="codeblock" title="コードブロック">&#65371;&#65373;</button>
      </div>
    </div>
    <div class="header-right">
      <div class="file-controls">
        <button class="ctrl-btn" id="btn-open" title="ファイルを開く (Ctrl+O)">
          <span class="ctrl-icon">&#128194;</span>
          <span class="ctrl-label">開く</span>
        </button>
        <button class="ctrl-btn" id="btn-save-md" title="Markdownとして保存 (Ctrl+S)">
          <span class="ctrl-icon">&#128190;</span>
          <span class="ctrl-label">.md保存</span>
        </button>
        <button class="ctrl-btn" id="btn-save-html" title="HTMLとして出力">
          <span class="ctrl-icon">&#127760;</span>
          <span class="ctrl-label">.html出力</span>
        </button>
      </div>
      <div class="toolbar-divider"></div>
      <div class="view-controls">
        <button class="ctrl-btn" id="btn-view-editor" title="エディタのみ表示"><span class="ctrl-icon">&#9999;</span></button>
        <button class="ctrl-btn active" id="btn-view-split" title="分割表示"><span class="ctrl-icon">&#9647;</span></button>
        <button class="ctrl-btn" id="btn-view-preview" title="プレビューのみ表示"><span class="ctrl-icon">&#128065;</span></button>
      </div>
      <div class="toolbar-divider"></div>
      <button class="ctrl-btn" id="btn-theme" title="テーマ切替">
        <span class="ctrl-icon" id="theme-icon">&#127769;</span>
      </button>
    </div>
  </header>

  <main id="app-main">
    <div class="pane" id="editor-pane">
      <div class="pane-header">
        <span class="pane-title">エディタ</span>
        <span class="pane-info" id="editor-info">行: 0 | 文字: 0</span>
      </div>
      <div class="editor-wrapper">
        <div class="line-numbers" id="line-numbers"></div>
        <textarea id="editor" spellcheck="false" placeholder="ここにMarkdownを入力..."># WanMD へようこそ！

**WanMD** はワンさん専用の軽量マークダウンエディタです。

## 特徴

- リアルタイムプレビュー
- ダーク/ライトテーマ
- ファイルの読み込み・保存
- シンタックスハイライト
- 目次の自動生成

## コードブロック

```javascript
function greet(name) {
  return `こんにちは、${name}さん！`;
}
console.log(greet('ワン'));
```

## テーブル

| 機能 | 状態 |
|:-----|:----:|
| リアルタイムプレビュー | ✅ |
| テーマ切替 | ✅ |
| ファイル操作 | ✅ |
| 目次生成 | ✅ |

## タスクリスト

- [x] エディタの作成
- [x] プレビューの実装
- [ ] さらに機能追加

> **ヒント**: ツールバーのボタンを使うと、Markdown記法を簡単に挿入できます！
</textarea>
      </div>
    </div>
    <div class="resize-handle" id="resize-handle"></div>
    <div class="pane" id="preview-pane">
      <div class="pane-header">
        <span class="pane-title">プレビュー</span>
        <button class="toc-toggle" id="btn-toc" title="目次の表示/非表示">&#128209; 目次</button>
      </div>
      <div class="preview-wrapper">
        <aside class="toc-sidebar" id="toc-sidebar">
          <div class="toc-header">目次</div>
          <nav class="toc-content" id="toc-content"></nav>
        </aside>
        <div class="preview-content markdown-body" id="preview"></div>
      </div>
    </div>
  </main>

  <footer id="app-footer">
    <div class="status-left">
      <span id="status-filename">新規ドキュメント</span>
    </div>
    <div class="status-right">
      <span id="status-wordcount">0 文字</span>
      <span class="status-divider">|</span>
      <span id="status-linecount">0 行</span>
      <span class="status-divider">|</span>
      <span id="status-saved">未保存</span>
    </div>
  </footer>

  <script>
(() => {
  const md = window.markdownit({
    html: true,
    linkify: true,
    typographer: true,
    breaks: true,
    highlight: (code, lang) => {
      if (lang && Prism.languages[lang]) {
        const h = Prism.highlight(code, Prism.languages[lang], lang);
        return `<pre class="language-${lang}"><code class="language-${lang}">${h}</code></pre>`;
      }
      return `<pre class="language-none"><code>${escHtml(code)}</code></pre>`;
    }
  });
  enableTaskLists(md);

  const el = {
    editor:        document.getElementById('editor'),
    preview:       document.getElementById('preview'),
    lineNumbers:   document.getElementById('line-numbers'),
    editorInfo:    document.getElementById('editor-info'),
    tocContent:    document.getElementById('toc-content'),
    tocSidebar:    document.getElementById('toc-sidebar'),
    btnToc:        document.getElementById('btn-toc'),
    btnTheme:      document.getElementById('btn-theme'),
    themeIcon:     document.getElementById('theme-icon'),
    btnOpen:       document.getElementById('btn-open'),
    btnSaveMd:     document.getElementById('btn-save-md'),
    btnSaveHtml:   document.getElementById('btn-save-html'),
    btnViewEditor: document.getElementById('btn-view-editor'),
    btnViewSplit:  document.getElementById('btn-view-split'),
    btnViewPreview:document.getElementById('btn-view-preview'),
    resizeHandle:  document.getElementById('resize-handle'),
    editorPane:    document.getElementById('editor-pane'),
    previewPane:   document.getElementById('preview-pane'),
    statusFilename:document.getElementById('status-filename'),
    statusWordcount:document.getElementById('status-wordcount'),
    statusLinecount:document.getElementById('status-linecount'),
    statusSaved:   document.getElementById('status-saved'),
    prismLight:    document.getElementById('prism-theme-light'),
    prismDark:     document.getElementById('prism-theme-dark'),
  };

  const state = {
    filename: '新規ドキュメント',
    isDirty: false,
    view: 'split',
    tocVisible: false,
    theme: localStorage.getItem('wanmd-theme') || 'dark',
    timer: null,
    isResizing: false,
  };

  /* --- テーマ --- */
  function applyTheme(name) {
    document.body.setAttribute('data-theme', name);
    state.theme = name;
    localStorage.setItem('wanmd-theme', name);
    if (name === 'dark') {
      el.prismLight.disabled = true;
      el.prismDark.disabled = false;
      el.themeIcon.textContent = '🌙';
    } else {
      el.prismLight.disabled = false;
      el.prismDark.disabled = true;
      el.themeIcon.textContent = '☀️';
    }
    requestAnimationFrame(renderPreview);
  }

  /* --- レンダリング --- */
  function renderPreview() {
    el.preview.innerHTML = md.render(el.editor.value);
    updateToc();
    updateStatus();
  }

  function debouncedRender() {
    clearTimeout(state.timer);
    state.timer = setTimeout(() => {
      renderPreview();
      if (!state.isDirty) {
        state.isDirty = true;
        el.statusSaved.textContent = '未保存 ●';
        el.statusSaved.style.color = 'var(--accent-primary)';
      }
    }, 50);
  }

  /* --- 行番号 --- */
  function updateLineNumbers() {
    const lines = el.editor.value.split('\n').length;
    const frag = document.createDocumentFragment();
    el.lineNumbers.textContent = '';
    for (let i = 1; i <= lines; i++) {
      const d = document.createElement('div');
      d.textContent = i;
      frag.appendChild(d);
    }
    el.lineNumbers.appendChild(frag);
    el.editorInfo.textContent = `行: ${lines} | 文字: ${el.editor.value.length}`;
  }

  /* --- 目次 --- */
  function updateToc() {
    const headings = el.preview.querySelectorAll('h1,h2,h3,h4,h5,h6');
    const frag = document.createDocumentFragment();
    headings.forEach((h, i) => {
      h.id = `h-${i}`;
      const a = document.createElement('a');
      a.href = `#h-${i}`;
      a.textContent = h.textContent;
      a.className = `toc-${h.tagName.toLowerCase()}`;
      a.addEventListener('click', e => { e.preventDefault(); h.scrollIntoView({behavior:'smooth'}); });
      frag.appendChild(a);
    });
    el.tocContent.textContent = '';
    el.tocContent.appendChild(frag);
  }

  /* --- ステータス --- */
  function updateStatus() {
    const t = el.editor.value;
    el.statusWordcount.textContent = `${t.length} 文字`;
    el.statusLinecount.textContent = `${t.split('\n').length} 行`;
  }

  /* --- ツールバー --- */
  const actions = {
    heading1:       { pre:'# ',    suf:'',      ph:'見出し1' },
    heading2:       { pre:'## ',   suf:'',      ph:'見出し2' },
    heading3:       { pre:'### ',  suf:'',      ph:'見出し3' },
    bold:           { pre:'**',    suf:'**',    ph:'太字テキスト' },
    italic:         { pre:'*',     suf:'*',     ph:'斜体テキスト' },
    strikethrough:  { pre:'~~',    suf:'~~',    ph:'打消線テキスト' },
    code:           { pre:'`',     suf:'`',     ph:'コード' },
    link:           { pre:'[',     suf:'](url)',ph:'リンクテキスト' },
    image:          { pre:'![',    suf:'](url)',ph:'画像の説明' },
    blockquote:     { pre:'> ',    suf:'',      ph:'引用テキスト' },
    'horizontal-rule':{ pre:'\n---\n',suf:'',  ph:'' },
    'unordered-list':{ pre:'- ',   suf:'',      ph:'リスト項目' },
    'ordered-list': { pre:'1. ',   suf:'',      ph:'リスト項目' },
    'task-list':    { pre:'- [ ] ',suf:'',      ph:'タスク項目' },
    codeblock:      { pre:'```\n', suf:'\n```', ph:'コードをここに' },
    table:          { pre:'\n| 列1 | 列2 | 列3 |\n|:-----|:----:|-----:|\n| ', suf:' | データ | データ |\n', ph:'データ' },
  };
  const lineActions = new Set(['heading1','heading2','heading3','blockquote','unordered-list','ordered-list','task-list']);

  function insertMarkdown(name) {
    const a = actions[name];
    if (!a) return;
    const ta = el.editor;
    const s = ta.selectionStart, e = ta.selectionEnd;
    const sel = ta.value.substring(s, e);
    const txt = sel || a.ph;
    let ins, cur;
    if (lineActions.has(name) && sel) {
      ins = sel.split('\n').map(l => a.pre + l).join('\n');
      cur = s + ins.length;
    } else {
      ins = a.pre + txt + a.suf;
      cur = s + a.pre.length + txt.length;
    }
    ta.setRangeText(ins, s, e, 'end');
    ta.selectionStart = ta.selectionEnd = cur;
    ta.focus();
    debouncedRender();
    updateLineNumbers();
  }

  /* --- ファイル操作（pywebview API） --- */
  async function openFile() {
    const r = await window.pywebview.api.open_file();
    if (r && r.content !== undefined) {
      el.editor.value = r.content;
      state.filename = r.filename;
      state.isDirty = false;
      el.statusFilename.textContent = r.filename;
      el.statusSaved.textContent = '保存済';
      el.statusSaved.style.color = '';
      renderPreview();
      updateLineNumbers();
    }
  }

  async function saveAsMarkdown() {
    const r = await window.pywebview.api.save_markdown(el.editor.value, state.filename);
    if (r && r.saved) {
      state.filename = r.filename;
      el.statusFilename.textContent = r.filename;
      markSaved();
    }
  }

  async function saveAsHtml() {
    const styles = getExportStyles();
    const html = `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escHtml(state.filename)}</title>
  <style>${styles}</style>
</head>
<body><div class="markdown-body">${el.preview.innerHTML}</div></body>
</html>`;
    await window.pywebview.api.save_html(html, state.filename);
  }

  function markSaved() {
    state.isDirty = false;
    el.statusSaved.textContent = '保存済 ✓';
    el.statusSaved.style.color = '#2ea043';
  }

  function getExportStyles() {
    const d = state.theme === 'dark';
    return `body{font-family:'Segoe UI','Hiragino Kaku Gothic ProN','Meiryo',sans-serif;max-width:900px;margin:0 auto;padding:32px;background:${d?'#0d1117':'#fff'};color:${d?'#e6edf3':'#1f2328'}}.markdown-body{line-height:1.7;font-size:15px}.markdown-body h1,.markdown-body h2{border-bottom:1px solid ${d?'#30363d':'#d0d7de'};padding-bottom:.3em}.markdown-body h1{font-size:2em}.markdown-body h2{font-size:1.5em}.markdown-body h3{font-size:1.25em}.markdown-body code{padding:.2em .4em;background:${d?'#161b22':'#f6f8fa'};border-radius:6px;font-family:Consolas,monospace;font-size:85%}.markdown-body pre{padding:16px;background:${d?'#161b22':'#f6f8fa'};border-radius:8px;overflow:auto}.markdown-body pre code{padding:0;background:transparent}.markdown-body blockquote{padding:8px 16px;border-left:4px solid ${d?'#3b82f6':'#0969da'};color:${d?'#8b949e':'#656d76'}}.markdown-body table{border-collapse:collapse;width:100%}.markdown-body th,.markdown-body td{padding:8px 13px;border:1px solid ${d?'#30363d':'#d0d7de'}}.markdown-body th{background:${d?'#161b22':'#f6f8fa'}}.markdown-body a{color:${d?'#58a6ff':'#0969da'};text-decoration:none}.markdown-body hr{height:2px;background:${d?'#21262d':'#d8dee4'};border:0;margin:24px 0}.markdown-body img{max-width:100%;border-radius:8px}`;
  }

  /* --- ドラッグ&ドロップ --- */
  function setupDragDrop() {
    const ov = document.createElement('div');
    ov.className = 'drop-overlay';
    ov.innerHTML = '<div class="drop-overlay-text">&#128196; ファイルをドロップして読み込む</div>';
    document.body.appendChild(ov);
    let cnt = 0;
    document.addEventListener('dragenter', e => { e.preventDefault(); cnt++; ov.classList.add('active'); });
    document.addEventListener('dragleave', e => { e.preventDefault(); if (--cnt <= 0) { cnt = 0; ov.classList.remove('active'); } });
    document.addEventListener('dragover', e => e.preventDefault());
    document.addEventListener('drop', e => {
      e.preventDefault(); cnt = 0; ov.classList.remove('active');
      const f = e.dataTransfer.files[0];
      if (f) loadDrop(f);
    });
  }

  function loadDrop(file) {
    const r = new FileReader();
    r.onload = e => {
      el.editor.value = e.target.result;
      state.filename = file.name;
      state.isDirty = false;
      el.statusFilename.textContent = file.name;
      el.statusSaved.textContent = '保存済';
      el.statusSaved.style.color = '';
      renderPreview();
      updateLineNumbers();
    };
    r.readAsText(file);
  }

  /* --- 表示モード --- */
  function setView(mode) {
    state.view = mode;
    document.body.classList.remove('view-editor','view-split','view-preview');
    if (mode !== 'split') document.body.classList.add(`view-${mode}`);
    el.btnViewEditor.classList.toggle('active', mode === 'editor');
    el.btnViewSplit.classList.toggle('active', mode === 'split');
    el.btnViewPreview.classList.toggle('active', mode === 'preview');
    if (mode !== 'editor') renderPreview();
  }

  /* --- スクロール同期 --- */
  function setupScrollSync() {
    let syncing = false;
    el.editor.addEventListener('scroll', () => {
      if (syncing) return;
      syncing = true;
      const ratio = el.editor.scrollTop / (el.editor.scrollHeight - el.editor.clientHeight);
      el.preview.scrollTop = ratio * (el.preview.scrollHeight - el.preview.clientHeight);
      el.lineNumbers.scrollTop = el.editor.scrollTop;
      requestAnimationFrame(() => { syncing = false; });
    });
  }

  /* --- ペインリサイズ --- */
  function setupResize() {
    el.resizeHandle.addEventListener('mousedown', e => {
      e.preventDefault();
      state.isResizing = true;
      el.resizeHandle.classList.add('dragging');
      document.body.style.cssText += 'cursor:col-resize;user-select:none';
      const onMove = me => {
        const rect = document.getElementById('app-main').getBoundingClientRect();
        const w = Math.max(200, Math.min(rect.width - 200, me.clientX - rect.left));
        el.editorPane.style.flex = `0 0 ${w}px`;
        el.previewPane.style.flex = `0 0 ${rect.width - w - 4}px`;
      };
      const onUp = () => {
        state.isResizing = false;
        el.resizeHandle.classList.remove('dragging');
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
      };
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    });
  }

  /* --- キーボードショートカット --- */
  function setupKeys() {
    document.addEventListener('keydown', e => {
      const c = e.ctrlKey || e.metaKey;
      if (c) {
        const map = { b:'bold', i:'italic', d:'strikethrough', k:'link', '`':'code', 1:'heading1', 2:'heading2', 3:'heading3' };
        if (map[e.key]) { e.preventDefault(); insertMarkdown(map[e.key]); return; }
        if (e.key === 's') { e.preventDefault(); saveAsMarkdown(); return; }
        if (e.key === 'o') { e.preventDefault(); openFile(); return; }
      }
      if (e.key === 'Tab' && document.activeElement === el.editor) {
        e.preventDefault();
        const s = el.editor.selectionStart, ee = el.editor.selectionEnd;
        el.editor.setRangeText('  ', s, ee, 'end');
        debouncedRender(); updateLineNumbers();
      }
    });
  }

  /* --- タスクリスト --- */
  function enableTaskLists(mdInstance) {
    const def = mdInstance.renderer.rules.list_item_open ||
      ((t, i, o, e, s) => s.renderToken(t, i, o));
    mdInstance.renderer.rules.list_item_open = (t, i, o, e, s) => {
      const ct = t[i + 2];
      if (ct && ct.content) {
        for (const [pat, checked] of [['[ ] ', false], ['[x] ', true], ['[X] ', true]]) {
          if (ct.content.startsWith(pat)) {
            ct.content = ct.content.slice(4);
            if (ct.children && ct.children[0]) ct.children[0].content = ct.children[0].content.slice(4);
            return `<li style="list-style:none;margin-left:-1.5em"><input type="checkbox"${checked?' checked':''} disabled> `;
          }
        }
      }
      return def(t, i, o, e, s);
    };
  }

  /* --- ユーティリティ --- */
  function escHtml(s) {
    return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  /* --- イベント登録 --- */
  function setupEvents() {
    el.editor.addEventListener('input', () => { debouncedRender(); updateLineNumbers(); });
    document.getElementById('toolbar').addEventListener('click', e => {
      const b = e.target.closest('.tool-btn');
      if (b) insertMarkdown(b.dataset.action);
    });
    el.btnOpen.addEventListener('click', openFile);
    el.btnSaveMd.addEventListener('click', saveAsMarkdown);
    el.btnSaveHtml.addEventListener('click', saveAsHtml);
    el.btnTheme.addEventListener('click', () => applyTheme(state.theme === 'dark' ? 'light' : 'dark'));
    el.btnViewEditor.addEventListener('click', () => setView('editor'));
    el.btnViewSplit.addEventListener('click', () => setView('split'));
    el.btnViewPreview.addEventListener('click', () => setView('preview'));
    el.btnToc.addEventListener('click', () => {
      state.tocVisible = !state.tocVisible;
      el.tocSidebar.classList.toggle('open', state.tocVisible);
      el.btnToc.classList.toggle('active', state.tocVisible);
    });
    window.addEventListener('beforeunload', e => { if (state.isDirty) { e.preventDefault(); e.returnValue = ''; } });
  }

  /* --- 初期化 --- */
  function init() {
    applyTheme(state.theme);
    renderPreview();
    updateLineNumbers();
    setupEvents();
    setupScrollSync();
    setupResize();
    setupDragDrop();
    setupKeys();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
  </script>
</body>
</html>"""


def main():
    api = Api()
    window = webview.create_window(
        "WanMD - マークダウンエディタ",
        html=HTML,
        js_api=api,
        width=1280,
        height=800,
        min_size=(800, 600),
    )
    api._window = window
    webview.start()


if __name__ == "__main__":
    main()
