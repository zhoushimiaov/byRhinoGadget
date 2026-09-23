# -*- coding: utf-8 -*-
import os
import re
import json
import subprocess
import fitz

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
MD_FILE = os.path.join(ROOT_DIR, "byRhinoGadget橙皮书.md")
HELP_DIR = os.path.join(ROOT_DIR, "help_pages")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
COVER_BG = "assets/cover_bg_nograin.png"
OUTPUT_HTML = os.path.join(ROOT_DIR, "byRhinoGadget_Orange_Book_v2.html")
OUTPUT_PDF = os.path.join(ROOT_DIR, "byRhinoGadget_Orange_Book_v2.pdf")

# Load assets_data
with open(os.path.join(ASSETS_DIR, "assets_data.json"), encoding='utf-8') as f:
    assets_data = json.load(f)

commands_meta = assets_data.get('commands', {})
icon_map = assets_data.get('icon_map', {})

def get_page_info(page_file):
    filepath = os.path.join(HELP_DIR, page_file)
    if not os.path.exists(filepath):
        return None
    with open(filepath, encoding='utf-8', errors='ignore') as f:
        raw_html = f.read()

    icon_match = re.search(r'<p class=Body><span lang=EN-US><img[^>]+src=["\'](doc\.files/[^"\']+)["\']', raw_html)
    if not icon_match:
        icon_match = re.search(r'<img[^>]+width=43[^>]+src=["\'](doc\.files/[^"\']+)["\']', raw_html)
    icon_file = "assets/icons/" + os.path.basename(icon_match.group(1)) if icon_match else None

    see_also_idx = raw_html.find('See also')
    content_part = raw_html[:see_also_idx] if see_also_idx != -1 else raw_html
    see_also_part = raw_html[see_also_idx:] if see_also_idx != -1 else ""

    all_imgs = re.findall(r'src=["\'](doc\.files/[^"\']+)["\']', content_part)
    all_imgs = list(dict.fromkeys(all_imgs))
    
    step_imgs = []
    for img in all_imgs:
        base = os.path.basename(img)
        if icon_file and base in icon_file:
            continue
        img_path = "assets/images/" + base
        if os.path.exists(os.path.join(ROOT_DIR, img_path)):
            step_imgs.append(img_path)

    see_also_items = []
    if see_also_part:
        sa_matches = re.findall(r'<p class=SeeAlso>.*?<img[^>]+src=["\']doc\.files/([^"\']+)["\'].*?<a[^>]+href=["\']([^"\']+)["\']>([^<]+)</a>', see_also_part, re.DOTALL)
        for sa_img, sa_href, sa_name in sa_matches:
            see_also_items.append({
                "name": sa_name.strip(),
                "icon": "assets/icons/" + sa_img if os.path.exists(os.path.join(ASSETS_DIR, "icons", sa_img)) else "assets/images/" + sa_img
            })

    return {
        "icon": icon_file,
        "images": step_imgs,
        "see_also": see_also_items
    }

page_files = [f for f in os.listdir(HELP_DIR) if f.endswith('.html') and f not in ['command-list.html', 'byrhino-gadget.html']]
page_data_cache = {}
for pf in page_files:
    info = get_page_info(pf)
    if info:
        base_name = os.path.splitext(pf)[0].lower()
        page_data_cache[base_name] = info

def find_command_assets(cmd_name):
    clean = re.sub(r'[^a-zA-Z0-9]', '', cmd_name.split('/')[0]).lower()
    
    # 1. Direct match in icon_map
    if clean in icon_map:
        icon_file = icon_map[clean]['icon_file']
        pg = icon_map[clean].get('page', '')
        pg_base = os.path.splitext(pg)[0].lower()
        if pg_base in page_data_cache:
            data = page_data_cache[pg_base]
            return icon_file, data['images'], data['see_also']
        return icon_file, [], []

    # 2. Check page_data_cache directly
    if clean in page_data_cache:
        data = page_data_cache[clean]
        icon = data['icon']
        return icon, data['images'], data['see_also']

    # 3. Fallback search in icon_map
    for k, v in icon_map.items():
        if k in clean or clean in k:
            icon_file = v['icon_file']
            pg = v.get('page', '')
            pg_base = os.path.splitext(pg)[0].lower()
            if pg_base in page_data_cache:
                data = page_data_cache[pg_base]
                return icon_file, data['images'], data['see_also']
            return icon_file, [], []

    # 4. Fallback search in commands_meta
    for k, v in commands_meta.items():
        if k in clean or clean in k:
            return v.get('icon'), v.get('illustrations', []), []

    return None, [], []

def make_clickable_links(text):
    def replace_url(m):
        url = m.group(0)
        return f'<a href="{url}" target="_blank">{url}</a>'
    
    text = re.sub(r'(?<!href=["\'])(https?://[a-zA-Z0-9\./_\-]+[a-zA-Z0-9/_])', replace_url, text)
    text = re.sub(r'(?<![/\w])(means\.group)(?![\w/])', r'<a href="https://means.group" target="_blank">means.group</a>', text)
    text = re.sub(r'(?<![/\w])(www\.byrhino3d\.com)(?![\w/])', r'<a href="https://www.byrhino3d.com" target="_blank">www.byrhino3d.com</a>', text)
    text = re.sub(r'(?<![/\w])(byrhino3d\.com)(?![\w/])', r'<a href="https://www.byrhino3d.com" target="_blank">byrhino3d.com</a>', text)
    return text

def pangu_spacing(text):
    text = re.sub(r'([\u4e00-\u9fa5])([a-zA-Z0-9`"\(])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z0-9`"\)])([\u4e00-\u9fa5])', r'\1 \2', text)
    return text

def format_table(table_text, cmd_page_map=None):
    if cmd_page_map is None:
        cmd_page_map = {}
        
    lines = [l.strip() for l in table_text.strip().split('\n') if l.strip()]
    if len(lines) < 2:
        return table_text

    header_cells = [c.strip() for c in lines[0].strip('|').split('|')]
    is_matrix_table = any('命令' in c for c in header_cells)
    
    html_out = ['<table class="specs-table">']
    html_out.append('<thead><tr>')
    for h in header_cells:
        h_clean = re.sub(r'`([^`]+)`', r'<code>\1</code>', h)
        html_out.append(f'<th>{pangu_spacing(h_clean)}</th>')
    if is_matrix_table and len(header_cells) == 2:
        html_out.append('<th>页码 (Page)</th>')
    html_out.append('</tr></thead>')
    html_out.append('<tbody>')

    for r in lines[2:]:
        cells = [c.strip() for c in r.strip('|').split('|')]
        html_out.append('<tr>')
        matched_cmd_clean = None
        for idx, cell in enumerate(cells):
            cell_html = re.sub(r'`([^`]+)`', r'<code>\1</code>', cell)
            cell_html = re.sub(r'\*\*([^\*]+)\*\*', r'<strong>\1</strong>', cell_html)
            cell_html = make_clickable_links(cell_html)
            
            # If cell has a command name in code block, prefix with mini icon and make clickable pill
            cmd_match = re.search(r'<code>([a-zA-Z0-9_/]+)</code>', cell_html)
            if idx == 0 and cmd_match:
                cmd_raw = cmd_match.group(1).split('/')[0].strip()
                clean_id = re.sub(r'[^a-zA-Z0-9]', '', cmd_raw).lower()
                matched_cmd_clean = clean_id
                t_icon, _, _ = find_command_assets(cmd_raw)
                icon_tag = f'<img src="{t_icon}" class="table-cmd-icon">' if t_icon and os.path.exists(os.path.join(ROOT_DIR, t_icon)) else '<div class="table-cmd-icon-empty"></div>'
                cell_html = f'<a href="#cmd-{clean_id}" class="table-cmd-pill">{icon_tag}<span class="table-cmd-code">{cmd_raw}</span></a>'
            
            html_out.append(f'<td>{pangu_spacing(cell_html)}</td>')
        
        if is_matrix_table and len(cells) == 2:
            if matched_cmd_clean and matched_cmd_clean in cmd_page_map:
                p_val = f"{cmd_page_map[matched_cmd_clean]:02d}"
                page_link = f'<a href="#cmd-{matched_cmd_clean}" class="table-page-link">P. {p_val}</a>'
            else:
                page_link = f'<a href="#cmd-{matched_cmd_clean}" class="table-page-link">P. --</a>' if matched_cmd_clean else '<span class="table-page-link">--</span>'
            html_out.append(f'<td class="td-page">{page_link}</td>')
            
        html_out.append('</tr>')
    html_out.extend(['</tbody>', '</table>'])
    return '\n'.join(html_out)

def format_text_block(text):
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*([^\*]+)\*\*', r'<strong>\1</strong>', text)
    text = make_clickable_links(text)
    text = pangu_spacing(text)
    return text

def format_regular_markdown(text, cmd_page_map=None):
    lines = text.split('\n')
    out = []
    i = 0
    in_list = False
    list_type = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            if in_list:
                out.append(f'</{list_type}>')
                in_list = False
            i += 1
            continue

        if stripped.startswith('|') and '|' in stripped[1:]:
            if in_list:
                out.append(f'</{list_type}>')
                in_list = False
            tbl_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                tbl_lines.append(lines[i])
                i += 1
            out.append(format_table('\n'.join(tbl_lines), cmd_page_map))
            continue

        if stripped.startswith('#### '):
            if in_list:
                out.append(f'</{list_type}>')
                in_list = False
            h_text = format_text_block(stripped[5:].strip())
            out.append(f'<h4 class="sub-section-h4">{h_text}</h4>')
            i += 1
            continue

        if stripped.startswith('### '):
            if in_list:
                out.append(f'</{list_type}>')
                in_list = False
            h_text = format_text_block(stripped[4:].strip())
            out.append(f'<h3 class="section-h3">{h_text}</h3>')
            i += 1
            continue

        m_num = re.match(r'^(\d+)\.\s+(.*)$', stripped)
        if m_num:
            if not in_list or list_type != 'ol':
                if in_list:
                    out.append(f'</{list_type}>')
                out.append('<ol class="styled-ordered-list">')
                in_list = True
                list_type = 'ol'
            out.append(f'<li>{format_text_block(m_num.group(2))}</li>')
            i += 1
            continue

        m_bullet = re.match(r'^[\-\*]\s+(.*)$', stripped)
        if m_bullet:
            if not in_list or list_type != 'ul':
                if in_list:
                    out.append(f'</{list_type}>')
                out.append('<ul class="styled-bullet-list">')
                in_list = True
                list_type = 'ul'
            out.append(f'<li>{format_text_block(m_bullet.group(1))}</li>')
            i += 1
            continue

        if in_list:
            out.append(f'</{list_type}>')
            in_list = False

        if stripped.startswith('> '):
            quote_text = format_text_block(stripped[2:].strip())
            out.append(f'<blockquote class="styled-quote">{quote_text}</blockquote>')
            i += 1
            continue

        out.append(f'<p class="para">{format_text_block(stripped)}</p>')
        i += 1

    if in_list:
        out.append(f'</{list_type}>')

    return '\n'.join(out)

def parse_command_section(num_str, title_str, body_text, category_str):
    if '—' in title_str:
        parts = [p.strip() for p in title_str.split('—')]
    elif ' - ' in title_str:
        parts = [p.strip() for p in title_str.split(' - ')]
    elif '|' in title_str:
        parts = [p.strip() for p in title_str.split('|')]
    else:
        parts = [title_str.strip()]
        
    eng_name = parts[0].strip()
    cn_name = parts[1].strip() if len(parts) > 1 else ""
    primary_cmd = eng_name.split('/')[0].strip()
    clean_id = re.sub(r'[^a-zA-Z0-9]', '', primary_cmd).lower()

    icon_path, images, see_also = find_command_assets(primary_cmd)

    card_html = [f'<div class="command-card" id="cmd-{clean_id}" data-cmd="{primary_cmd}">']
    card_html.append('<div class="cmd-header">')
    card_html.append('<div class="cmd-title-group">')

    if icon_path and os.path.exists(os.path.join(ROOT_DIR, icon_path)):
        card_html.append(f'<div class="cmd-icon-box"><img src="{icon_path}" alt="{primary_cmd}" class="cmd-icon"></div>')
    else:
        card_html.append('<div class="cmd-icon-box"><div class="cmd-icon-placeholder"></div></div>')

    card_html.append('<div class="cmd-names">')
    card_html.append(f'<div class="cmd-title-main"><span class="cmd-eng-name">{eng_name}</span> <span class="cmd-num-badge">#{num_str}</span></div>')
    if cn_name:
        card_html.append(f'<div class="cmd-cn-name">{cn_name}</div>')
    card_html.append('</div>')
    card_html.append('</div>')

    card_html.append(f'<span class="cmd-cat-badge">{category_str}</span>')
    card_html.append('</div>')

    lines = body_text.split('\n')
    sec_buffers = {"intro": [], "func": [], "steps": [], "options": [], "notes": []}
    current_sec = "intro"

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue

        if stripped.startswith('- **功能定义**') or stripped.startswith('- 功能定义') or stripped.startswith('**功能定义**'):
            current_sec = "func"
            val = re.sub(r'^(\-\s*)?(\*\*)?功能定义(\*\*)?[:：]?', '', stripped).strip()
            if val:
                sec_buffers["func"].append(val)
            i += 1
            continue
        elif stripped.startswith('- **操作步骤**') or stripped.startswith('- 操作步骤') or stripped.startswith('**操作步骤**'):
            current_sec = "steps"
            i += 1
            continue
        elif stripped.startswith('- **参数选项**') or stripped.startswith('- 参数选项') or stripped.startswith('**参数选项**'):
            current_sec = "options"
            i += 1
            continue
        elif stripped.startswith('- **核心要点**') or stripped.startswith('- 核心要点') or stripped.startswith('**核心要点**'):
            current_sec = "notes"
            i += 1
            continue
        elif stripped.startswith('- **图解范例**') or stripped.startswith('**图解范例**') or stripped.startswith('- **典型工作流**'):
            current_sec = "intro"
            i += 1
            continue

        sec_buffers[current_sec].append(stripped)
        i += 1

    func_content = ' '.join(sec_buffers["func"]).strip()
    if func_content:
        card_html.append(f'<div class="cmd-section"><span class="sec-label">功能定义 / FUNCTION</span><p class="cmd-desc">{format_text_block(func_content)}</p></div>')
    elif sec_buffers["intro"]:
        intro_content = '\n'.join(sec_buffers["intro"]).strip()
        if '<table' in intro_content or intro_content.startswith('|'):
            card_html.append(f'<div class="cmd-section">{format_regular_markdown(intro_content)}</div>')
        else:
            card_html.append(f'<div class="cmd-section"><p class="cmd-desc">{format_text_block(intro_content)}</p></div>')

    if sec_buffers["steps"]:
        card_html.append('<div class="cmd-section"><span class="sec-label">操作步骤 / STEPS</span><ol class="cmd-steps-list">')
        for step in sec_buffers["steps"]:
            clean_step = re.sub(r'^\d+\.\s*', '', step).strip()
            clean_step = re.sub(r'^[\-\*]\s*', '', clean_step).strip()
            if clean_step:
                card_html.append(f'<li>{format_text_block(clean_step)}</li>')
        card_html.append('</ol></div>')

    if sec_buffers["options"]:
        card_html.append('<div class="cmd-section"><span class="sec-label">参数选项 / OPTIONS</span>')
        card_html.append('<ul class="cmd-options-list">')
        for opt in sec_buffers["options"]:
            clean_opt = re.sub(r'^[\-\*]\s*', '', opt).strip()
            if clean_opt:
                card_html.append(f'<li>{format_text_block(clean_opt)}</li>')
        card_html.append('</ul></div>')

    if sec_buffers["notes"]:
        card_html.append('<div class="cmd-notes-box">')
        card_html.append('<div class="notes-header">NOTE · 核心要点</div>')
        card_html.append('<div class="notes-body">')
        for note in sec_buffers["notes"]:
            clean_note = re.sub(r'^[\-\*]\s*', '', note).strip()
            if clean_note:
                card_html.append(f'<p>▷ {format_text_block(clean_note)}</p>')
        card_html.append('</div></div>')

    if images:
        card_html.append('<div class="cmd-figures">')
        clean_steps = []
        for s in sec_buffers["steps"]:
            cs = re.sub(r'^\d+[\.\、\:]\s*', '', s).strip()
            cs = re.sub(r'^[\-\*]\s*', '', cs).strip()
            cs = cs.replace('**', '').replace('`', '')
            if cs:
                clean_steps.append(cs)

        def get_img_caption(idx, total):
            if idx < len(clean_steps):
                step_text = clean_steps[idx]
                step_short = step_text.split('；')[0].split(';')[0].split('，后')[0]
                if len(step_short) > 28:
                    step_short = step_short[:28] + '...'
                return f'<span class="fig-badge">步骤 {idx+1}</span> <span class="fig-cap-text">{step_short}</span>'
            else:
                if total == 1:
                    return f'<span class="fig-badge">操作演示</span> <span class="fig-cap-text">{primary_cmd} 操作流程</span>'
                else:
                    return f'<span class="fig-badge">效果范例</span> <span class="fig-cap-text">{primary_cmd} 输出展示</span>'

        if len(images) == 1:
            card_html.append('<div class="figure-grid figure-grid-1">')
            cap = get_img_caption(0, 1)
            card_html.append(f'<div class="figure-item"><img src="{images[0]}" alt="{primary_cmd} 图解" class="figure-img figure-img-lg"><div class="figure-sub-caption">{cap}</div></div>')
            card_html.append('</div>')
        elif len(images) == 2:
            card_html.append('<div class="figure-grid figure-grid-2">')
            for idx, img in enumerate(images):
                cap = get_img_caption(idx, 2)
                card_html.append(f'<div class="figure-item"><img src="{img}" alt="{primary_cmd} 图解" class="figure-img"><div class="figure-sub-caption">{cap}</div></div>')
            card_html.append('</div>')
        else:
            card_html.append('<div class="figure-grid figure-grid-multi">')
            for idx, img in enumerate(images):
                cap = get_img_caption(idx, len(images))
                card_html.append(f'<div class="figure-item"><img src="{img}" alt="{primary_cmd} 图解" class="figure-img"><div class="figure-sub-caption">{cap}</div></div>')
            card_html.append('</div>')
        
        card_html.append(f'<div class="figure-caption">FIG. {num_str} / {primary_cmd} — 官方操作流程与模型范例图解</div>')
        card_html.append('</div>')

    if see_also:
        card_html.append('<div class="cmd-seealso">')
        card_html.append('<span class="seealso-label">SEE ALSO · 关联命令:</span>')
        card_html.append('<div class="seealso-tags">')
        for sa in see_also:
            sa_name = sa["name"]
            sa_clean = re.sub(r'[^a-zA-Z0-9]', '', sa_name.split('/')[0]).lower()
            card_html.append(f'<a href="#cmd-{sa_clean}" class="seealso-tag">{sa_name}</a>')
        card_html.append('</div></div>')

    card_html.append('</div>\n')
    return '\n'.join(card_html), primary_cmd, eng_name, cn_name, clean_id

def fix_appendix_a_terms(text):
    term_map = [
        ("개체(Object)", "Object (개체)"),
        ("커브(Curve) / 서피스(Surface)", "Curve (커브) / Surface (서피스)"),
        ("폴리서피스(Polysurface)", "Polysurface (폴리서피스)"),
        ("솔리드(Solid)", "Solid (솔리드)"),
        ("제어점(Control Point / CV)", "Control Point (제어점 / CV)"),
        ("차수(Degree)", "Degree (차수)"),
        ("스팬(Span)", "Span (스팬)"),
        ("매듭점(Knot)", "Knot (매듭점)"),
        ("킹크(Kink)", "Kink (킹크)"),
        ("아이소팜(Isoparm)", "Isoparm (아이소팜)"),
        ("심(Seam)", "Seam (심)"),
        ("차집합(Difference)", "Difference (차집합)"),
        ("합집합(Union)", "Union (합집합)"),
        ("교집합(Intersection)", "Intersection (교집합)"),
        ("필렛(Fillet)", "Fillet (필렛)"),
        ("챔퍼(Chamfer)", "Chamfer (챔퍼)"),
        ("G0 / G1 / G2 연속성(Continuity)", "G0 / G1 / G2 Continuity (연속성)"),
        ("흐름(Flow)", "Flow (흐름)"),
        ("블렌드(Blend)", "Blend (블렌드)"),
        ("로프트(Loft)", "Loft (로프트)"),
        ("스윕(Sweep)", "Sweep (스윕)"),
        ("오프셋(Offset)", "Offset (오프셋)"),
        ("트림(Trim)", "Trim (트림)"),
        ("스플릿(Split)", "Split (스플릿)"),
        ("바운딩 박스(Bounding Box)", "Bounding Box (바운딩 박스)"),
        ("클리핑 평면(Clipping Plane)", "Clipping Plane (클리핑 평면)"),
        ("블록(Block)", "Block (블록)"),
        ("그룹(Group)", "Group (그룹)"),
        ("메시(Mesh)", "Mesh (메시)"),
        ("렌더메시(Render Mesh)", "Render Mesh (렌더메시)"),
        ("워크세션(Worksession)", "Worksession (워크세션)"),
        ("공차(Tolerance)", "Tolerance (공차)"),
        ("음각/양각", "Engrave / Emboss (음각/양각)"),
        ("분해뷰(Exploded View)", "Exploded View (분해뷰)"),
        ("3면도(Third Angle)", "Third Angle (3면도)"),
        ("씸(Seam)", "Seam (씸)"),
        ("돌출(Extrusion)", "Extrusion (돌출)"),
        ("—(LookAt)", "LookAt (카메라 추적)"),
        ("Detail View", "Detail View (디테일 뷰)"),
        ("BoundingBox", "BoundingBox (바운딩박스)")
    ]
    for k, v in term_map:
        text = text.replace(k, v)
    return text

def build_html(ch_page_map=None, cmd_page_map=None):
    if ch_page_map is None:
        ch_page_map = {}
    if cmd_page_map is None:
        cmd_page_map = {}

    print("Reading Markdown...")
    with open(MD_FILE, encoding='utf-8') as f:
        full_md = f.read()

    raw_chapters = re.split(r'\n(?=## )', full_md)
    print(f"Parsed {len(raw_chapters)} top-level sections.")

    all_commands_index = []
    rendered_chapters_html = []

    chapter_bilingual = {
        "第一章 概述": ("第一章 · 插件概述", "CHAPTER 01 · OVERVIEW"),
        "第二章 设计理念与交互约定": ("第二章 · 设计理念与交互约定", "CHAPTER 02 · DESIGN PHILOSOPHY & INTERACTION"),
        "第三章 命令体系总览": ("第三章 · 命令体系总览矩阵", "CHAPTER 03 · GLOBAL COMMAND MATRIX"),
        "第四章 控制点编辑(Point Edit)": ("第四章 · 控制点编辑", "CHAPTER 04 · POINT EDIT"),
        "第五章 曲线(Curve)": ("第五章 · 曲线工具", "CHAPTER 05 · CURVE TOOLS"),
        "第六章 曲面(Surface)": ("第六章 · 曲面工具", "CHAPTER 06 · SURFACE TOOLS"),
        "第七章 实体(Solid)": ("第七章 · 实体建模", "CHAPTER 07 · SOLID MODELING"),
        "第八章 标注与出图(Annotation)": ("第八章 · 标注与出图", "CHAPTER 08 · ANNOTATION & LAYOUT"),
        "第九章 文件管理(File)": ("第九章 · 文件与图层管理", "CHAPTER 09 · FILE & LAYER MANAGEMENT"),
        "第十章 变换(Transform)": ("第十章 · 空间变换", "CHAPTER 10 · TRANSFORM TOOLS"),
        "第十一章 建模(Modeling)": ("第十一章 · 建模与造型细节", "CHAPTER 11 · MODELING & DETAILS"),
        "第十二章 显示与设置(Display, Settings)": ("第十二章 · 视口显示与环境设置", "CHAPTER 12 · DISPLAY & SETTINGS"),
        "第十三章 分析(Analyze)": ("第十三章 · 物理分析与测算", "CHAPTER 13 · PHYSICAL ANALYSIS"),
        "第十四章 帮助(Help)": ("第十四章 · 官方技术支持与帮助", "CHAPTER 14 · HELP & SUPPORT"),
        "第十五章 典型工作流": ("第十五章 · 六大典型高阶工作流", "CHAPTER 15 · TYPICAL WORKFLOWS"),
        "附录 A 术语对照表": ("附录 A · 核心术语与参数对照表", "APPENDIX A · GLOSSARY OF TERMS"),
        "附录 B 相关资源": ("附录 B · 官方技术资源与生态", "APPENDIX B · RESOURCES & ECOSYSTEM")
    }

    ch_slug_map = {}

    for raw_ch in raw_chapters:
        lines = raw_ch.strip().split('\n')
        if not lines:
            continue
        first_line = lines[0].strip()

        if first_line.startswith('# byRhino Gadget 橙皮书') or first_line.startswith('## 目录'):
            continue

        ch_title_match = re.match(r'^##\s+(.+)$', first_line)
        if not ch_title_match:
            continue
        ch_raw_title = ch_title_match.group(1).strip()
        
        bi_title = chapter_bilingual.get(ch_raw_title, (ch_raw_title, ch_raw_title))
        cn_ch_title, en_ch_title = bi_title
        ch_slug = "ch-" + re.sub(r'[^a-zA-Z0-9]+', '-', en_ch_title.lower()).strip('-')
        ch_slug_map[cn_ch_title.split('·')[0].strip()] = ch_slug

        ch_content = '\n'.join(lines[1:]).strip()

        if '附录 A' in cn_ch_title:
            ch_content = fix_appendix_a_terms(ch_content)

        ch_html = [f'<div class="chapter-container" id="{ch_slug}">']
        ch_html.append('<div class="chapter-header">')
        ch_html.append(f'<div class="chapter-title-en">{en_ch_title}</div>')
        ch_html.append(f'<h2 class="chapter-title-cn">{cn_ch_title}</h2>')
        ch_html.append('<div class="chapter-divider-bar"></div>')
        ch_html.append('</div>')

        is_command_chapter = any(f'CHAPTER {i:02d}' in en_ch_title for i in range(4, 15))
        cat_badge = en_ch_title.split('·')[-1].strip() if '·' in en_ch_title else ""

        if is_command_chapter:
            parts = re.split(r'\n(?=###\s+\d+\.\d+\s+)', '\n' + ch_content)
            if parts[0].strip():
                ch_html.append(f'<div class="chapter-intro">{format_regular_markdown(parts[0].strip(), cmd_page_map)}</div>')
            
            for cmd_block in parts[1:]:
                m = re.match(r'^\s*###\s+(\d+\.\d+)\s+([^\n]+)\n(.*)$', cmd_block, re.DOTALL)
                if m:
                    c_num = m.group(1).strip()
                    c_title = m.group(2).strip()
                    c_body = m.group(3).strip()
                    card_markup, p_cmd, e_name, c_name, c_clean = parse_command_section(c_num, c_title, c_body, cat_badge)
                    ch_html.append(card_markup)
                    
                    t_icon, _, _ = find_command_assets(p_cmd)
                    all_commands_index.append({
                        "num": c_num,
                        "primary_cmd": p_cmd,
                        "clean_id": c_clean,
                        "eng_name": e_name,
                        "cn_name": c_name,
                        "cat": cat_badge,
                        "icon": t_icon,
                        "anchor": f"cmd-{c_clean}"
                    })
                else:
                    ch_html.append(format_regular_markdown(cmd_block, cmd_page_map))
        else:
            ch_html.append(format_regular_markdown(ch_content, cmd_page_map))

        ch_html.append('</div>\n')
        rendered_chapters_html.append('\n'.join(ch_html))

    print(f"Parsed {len(all_commands_index)} commands into index pool.")

    # Build Appendix C: Alphabetical Index
    all_commands_index.sort(key=lambda x: x["primary_cmd"].upper())

    appendix_c_html = [
        '<div class="chapter-container" id="appendix-index">',
        '<div class="chapter-header">',
        '<div class="chapter-title-en">APPENDIX C · ALPHABETICAL COMMAND INDEX</div>',
        '<h2 class="chapter-title-cn">附录 C · 英文命令字母序（A–Z）全书双向检索索引</h2>',
        '<div class="chapter-divider-bar"></div>',
        '</div>',
        '<div class="index-intro-text">',
        '本索引按英文字母 A–Z 升序收录插件全部核心命令。每个命令条目均配有官方高辨识度工具栏图标、功能分类、规范中文译名，并标注全书物理印制页码，支持点击直达正文。',
        '</div>'
    ]

    current_letter = ""
    for c in all_commands_index:
        first_char = c["primary_cmd"][0].upper()
        if first_char != current_letter:
            if current_letter != "":
                appendix_c_html.append('</div></div>')
            current_letter = first_char
            appendix_c_html.append(f'<div class="index-letter-group">')
            appendix_c_html.append(f'<div class="index-letter-header">{current_letter}</div>')
            appendix_c_html.append('<div class="index-cards-grid">')

        icon_tag = f'<img src="{c["icon"]}" class="index-cmd-icon">' if c['icon'] and os.path.exists(os.path.join(ROOT_DIR, c['icon'])) else '<div class="index-cmd-icon-empty"></div>'
        p_val = f"{cmd_page_map[c['clean_id']]:02d}" if c['clean_id'] in cmd_page_map else "--"
        
        appendix_c_html.append(
            f'<a href="#{c["anchor"]}" class="index-command-card">'
            f'<div class="index-card-left">'
            f'{icon_tag}'
            f'<div class="index-cmd-text">'
            f'<div class="index-cmd-name">{c["primary_cmd"]}</div>'
            f'<div class="index-cmd-cn">{c["cn_name"]}</div>'
            f'</div>'
            f'</div>'
            f'<div class="index-card-right">'
            f'<span class="index-cmd-cat">{c["cat"]}</span>'
            f'<span class="index-page-badge">P. {p_val}</span>'
            f'</div>'
            f'</a>'
        )

    if current_letter != "":
        appendix_c_html.append('</div></div>')
    appendix_c_html.append('</div>\n')

    # Build TOC Items using pure ASCII chapter codes
    toc_items = [
        ("第一章 · 插件概述", "OVERVIEW & BACKGROUND", "ch-chapter-01-overview", "ch-01"),
        ("第二章 · 设计理念与交互约定", "DESIGN PHILOSOPHY & INTERACTION", "ch-chapter-02-design-philosophy-interaction", "ch-02"),
        ("第三章 · 全局命令体系总览矩阵", "GLOBAL COMMAND MATRIX", "ch-chapter-03-global-command-matrix", "ch-03"),
        ("第四章 · 控制点编辑 (11 条)", "POINT EDIT TOOLS", "ch-chapter-04-point-edit", "ch-04"),
        ("第五章 · 曲线工具 (17 条)", "CURVE TOOLS", "ch-chapter-05-curve-tools", "ch-05"),
        ("第六章 · 曲面工具 (3 条)", "SURFACE TOOLS", "ch-chapter-06-surface-tools", "ch-06"),
        ("第七章 · 实体建模 (5 条)", "SOLID MODELING", "ch-chapter-07-solid-modeling", "ch-07"),
        ("第八章 · 标注与出图 (12 条)", "ANNOTATION & LAYOUT", "ch-chapter-08-annotation-layout", "ch-08"),
        ("第九章 · 文件与图层管理 (6 条)", "FILE & LAYER MANAGEMENT", "ch-chapter-09-file-layer-management", "ch-09"),
        ("第十章 · 空间变换 (14 条)", "TRANSFORM TOOLS", "ch-chapter-10-transform-tools", "ch-10"),
        ("第十一章 · 建模与造型细节 (19 条)", "MODELING & DETAILS", "ch-chapter-11-modeling-details", "ch-11"),
        ("第十二章 · 视口显示与环境设置 (19 条)", "DISPLAY & SETTINGS", "ch-chapter-12-display-settings", "ch-12"),
        ("第十三章 · 物理分析与测算 (8 条)", "PHYSICAL ANALYSIS", "ch-chapter-13-physical-analysis", "ch-13"),
        ("第十四章 · 官方技术支持与帮助 (2 条)", "HELP & SUPPORT", "ch-chapter-14-help-support", "ch-14"),
        ("第十五章 · 六大典型高阶工作流", "TYPICAL WORKFLOWS", "ch-chapter-15-typical-workflows", "ch-15"),
        ("附录 A · 核心术语与参数对照表", "APPENDIX A · GLOSSARY OF TERMS", "ch-appendix-a-glossary-of-terms", "app-a"),
        ("附录 B · 官方技术资源与生态", "APPENDIX B · RESOURCES & ECOSYSTEM", "ch-appendix-b-resources-ecosystem", "app-b"),
        ("附录 C · 英文命令字母序（A–Z）索引", "APPENDIX C · ALPHABETICAL INDEX", "appendix-index", "app-c")
    ]

    toc_rows_html = []
    for cn_t, en_t, slug, ch_key in toc_items:
        p_val = f"{ch_page_map[ch_key]:02d}" if ch_key in ch_page_map else "--"
        toc_rows_html.append(f'''
        <a href="#{slug}" class="toc-item">
            <div class="toc-item-left">
                <span class="toc-item-cn">{cn_t}</span>
                <span class="toc-item-en">{en_t}</span>
            </div>
            <div class="toc-dots"></div>
            <span class="toc-page-num">P. {p_val}</span>
        </a>
        ''')

    # Construct the full HTML document
    full_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>byRhino Gadget · 橙皮书完全参考手册</title>
    <style>
        @page {{
            size: A4 portrait;
            margin: 18mm 16mm 18mm 16mm;
            @top-left {{
                content: "byRhino Gadget 橙皮书 · 完全参考手册";
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
                font-size: 7.5pt;
                font-weight: 500;
                color: #64748B;
                border-bottom: 0.5pt solid #CBD5E1;
                padding-bottom: 4px;
            }}
            @top-right {{
                content: "PlusPlastic 官方效能插件";
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
                font-size: 7.5pt;
                font-weight: 500;
                color: #64748B;
                border-bottom: 0.5pt solid #CBD5E1;
                padding-bottom: 4px;
            }}
            @bottom-left {{
                content: "PlusPlastic © 2023 · 中文版 edit by 有物建筑 MeansGroup";
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
                font-size: 7.5pt;
                color: #94A3B8;
                border-top: 0.5pt solid #E2E8F0;
                padding-top: 4px;
            }}
            @bottom-right {{
                content: counter(page);
                font-family: 'JetBrains Mono', Consolas, 'Courier New', monospace;
                font-size: 8.5pt;
                font-weight: 700;
                color: #0F172A;
                border-top: 0.5pt solid #E2E8F0;
                padding-top: 4px;
            }}
        }}

        @page :first {{
            size: A4 portrait;
            margin: 0;
            @top-left {{ content: none; border: none; }}
            @top-right {{ content: none; border: none; }}
            @bottom-left {{ content: none; border: none; }}
            @bottom-right {{ content: none; border: none; }}
        }}

        @page colophon_page {{
            size: A4 portrait;
            margin: 0;
            @top-left {{ content: none; border: none; }}
            @top-right {{ content: none; border: none; }}
            @bottom-left {{ content: none; border: none; }}
            @bottom-right {{ content: none; border: none; }}
        }}

        :root {{
            --primary: #0F172A;
            --accent: #EA580C;
            --accent-light: #FFF7ED;
            --accent-border: #FED7AA;
            --text-dark: #1E293B;
            --text-muted: #64748B;
            --bg-light: #F8FAFC;
            --border-subtle: #E2E8F0;
            --border-strong: #CBD5E1;
        }}

        * {{
            box-sizing: border-box;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}

        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
            font-size: 9.5pt;
            line-height: 1.55;
            color: var(--text-dark);
            background-color: #FFFFFF;
        }}

        /* ==================== COVER PAGE (FULL-PAGE TRANSLUCENT VELLUM) ==================== */
        .cover-page {{
            width: 210mm;
            height: 297mm;
            max-height: 297mm;
            position: relative;
            page-break-after: always;
            break-after: page;
            background-image: linear-gradient(rgba(255, 255, 255, 0.78), rgba(255, 255, 255, 0.78)), url('{COVER_BG}');
            background-size: cover;
            background-position: center center;
            background-repeat: no-repeat;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 26mm 22mm 22mm 22mm;
            box-sizing: border-box;
        }}

        .cover-body {{
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: flex-start;
            padding: 10px 0;
        }}

        .cover-eyebrow {{
            font-family: Montserrat, -apple-system, sans-serif;
            font-size: 15pt;
            font-weight: 800;
            letter-spacing: 4px;
            text-transform: uppercase;
            color: #0A0A0A;
            margin-bottom: 12px;
        }}

        .cover-title-chinese {{
            font-size: 56pt;
            font-weight: 900;
            line-height: 1.05;
            letter-spacing: -2px;
            color: #0A0A0A;
            margin: 0 0 16px 0;
        }}

        .cover-subtitle-bilingual {{
            display: flex;
            align-items: baseline;
            gap: 12px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
            margin-bottom: 20px;
        }}

        .cover-sub-cn {{
            font-size: 14pt;
            font-weight: 800;
            color: #FF5500;
        }}

        .cover-sub-sep {{
            color: #94A3B8;
            font-weight: 300;
        }}

        .cover-sub-en {{
            font-family: Montserrat, sans-serif;
            font-size: 11pt;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
            color: #475569;
        }}

        .cover-accent-line {{
            width: 140px;
            height: 5px;
            background-color: #0A0A0A;
            margin: 0 0 24px 0;
        }}

        .cover-intro-text {{
            font-size: 9.5pt;
            line-height: 1.7;
            color: #334155;
            margin: 0 0 24px 0;
            max-width: 90%;
        }}

        .cover-graphic-wrap {{
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 10px 0 20px 0;
        }}

        .cover-svg-wireframe {{
            max-width: 330px;
            height: auto;
        }}

        .cover-footer-editorial {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            border-top: 1px solid rgba(10, 10, 10, 0.25);
            padding-top: 16px;
            font-size: 8.5pt;
            color: #64748B;
        }}

        .cover-footer-left strong, .cover-footer-right strong {{
            color: #0A0A0A;
            font-size: 9pt;
        }}

        .cover-footer-right a, .cover-footer-left a {{
            color: #FF5500;
            text-decoration: none;
            font-weight: 600;
        }}

        /* ==================== COLOPHON (BACK COVER) ==================== */
        .colophon-page {{
            page: colophon_page;
            width: 210mm;
            height: 297mm;
            max-height: 297mm;
            position: relative;
            page-break-before: always;
            break-before: page;
            background-image: linear-gradient(rgba(255, 255, 255, 0.78), rgba(255, 255, 255, 0.78)), url('{COVER_BG}');
            background-size: cover;
            background-position: center center;
            background-repeat: no-repeat;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            padding: 30mm 24mm;
            box-sizing: border-box;
            border-top: 12px solid #0A0A0A;
        }}

        .colophon-box {{
            border: 1px solid rgba(10, 10, 10, 0.2);
            padding: 32px;
            background: rgba(255, 255, 255, 0.7);
        }}

        .colophon-kicker {{
            font-family: Montserrat, monospace;
            font-size: 8pt;
            font-weight: 800;
            letter-spacing: 2px;
            color: #FF5500;
            margin-bottom: 6px;
        }}

        .colophon-title {{
            font-family: Montserrat, 'Segoe UI', Arial, sans-serif;
            font-size: 24pt;
            font-weight: 900;
            color: #0A0A0A;
            margin: 0 0 4px 0;
            letter-spacing: -0.5px;
        }}

        .colophon-sub {{
            font-size: 11pt;
            font-weight: 700;
            color: #475569;
            margin-bottom: 14px;
        }}

        .colophon-divider {{
            width: 60px;
            height: 3px;
            background: #0A0A0A;
            margin-bottom: 20px;
        }}

        .colophon-block {{
            margin-bottom: 14px;
        }}

        .colophon-label {{
            font-size: 7.5pt;
            font-weight: 800;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            color: #94A3B8;
            margin-bottom: 3px;
        }}

        .colophon-val {{
            font-size: 8.5pt;
            line-height: 1.6;
            color: #1E293B;
            font-weight: 500;
        }}

        .colophon-link a {{
            font-size: 8.5pt;
            font-weight: 700;
            color: #FF5500;
            text-decoration: none;
        }}

        .colophon-legal {{
            border-top: 1px solid rgba(10, 10, 10, 0.15);
            padding-top: 12px;
            margin-top: 16px;
            font-size: 7.5pt;
            color: #64748B;
            line-height: 1.6;
        }}

        /* Book Wrapper */
        .book-wrapper {{
            padding: 0;
        }}

        /* Preface Page */
        .preface-container {{
            page-break-after: always;
            break-after: page;
            padding: 10px 0 20px 0;
        }}

        .preface-header {{
            margin-bottom: 24px;
            border-bottom: 2px solid #0F172A;
            padding-bottom: 12px;
        }}

        .preface-kicker {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 8.5pt;
            font-weight: 800;
            letter-spacing: 2px;
            color: var(--accent);
            margin-bottom: 4px;
        }}

        .preface-title {{
            font-family: 'Noto Serif SC', 'Source Han Serif SC', SimSun, serif;
            font-size: 22pt;
            font-weight: 700;
            color: #0F172A;
            margin: 0;
        }}

        .preface-body {{
            font-family: 'Noto Serif SC', 'Source Han Serif SC', SimSun, serif;
            font-size: 10.5pt;
            line-height: 1.8;
            color: #334155;
        }}

        .preface-body p {{
            margin-bottom: 14px;
            text-align: justify;
        }}

        .project-facts-card {{
            margin-top: 32px;
            background: #F8FAFC;
            border: 1.5px solid #CBD5E1;
            border-radius: 8px;
            padding: 18px 22px;
        }}

        .facts-kicker {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 8pt;
            font-weight: 800;
            letter-spacing: 1.5px;
            color: #0F172A;
            border-bottom: 1px solid #CBD5E1;
            padding-bottom: 6px;
            margin-bottom: 12px;
        }}

        .facts-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px 20px;
            font-size: 8.5pt;
        }}

        .fact-item {{
            display: flex;
            flex-direction: column;
        }}

        .fact-k {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 7.5pt;
            color: #64748B;
            font-weight: 700;
        }}

        .fact-v {{
            font-weight: 600;
            color: #0F172A;
        }}

        /* Table of Contents */
        .toc-container {{
            page-break-after: always;
            break-after: page;
            padding: 10px 0 20px 0;
        }}

        .toc-header {{
            margin-bottom: 24px;
            border-bottom: 2px solid #0F172A;
            padding-bottom: 12px;
        }}

        .toc-kicker {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 8.5pt;
            font-weight: 800;
            letter-spacing: 2px;
            color: var(--accent);
            margin-bottom: 4px;
        }}

        .toc-title {{
            font-family: Montserrat, 'Segoe UI', Arial, sans-serif;
            font-size: 22pt;
            font-weight: 900;
            color: #0F172A;
            margin: 0;
        }}

        .toc-list {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}

        .toc-item {{
            display: flex;
            align-items: baseline;
            text-decoration: none !important;
            color: inherit !important;
            padding: 4px 6px;
            border-radius: 4px;
            transition: background 0.15s ease;
        }}

        .toc-item:hover {{
            background: #F1F5F9;
        }}

        .toc-item-left {{
            display: flex;
            align-items: baseline;
            gap: 10px;
            flex-shrink: 0;
        }}

        .toc-item-cn {{
            font-weight: 700;
            font-size: 9.5pt;
            color: #0F172A;
        }}

        .toc-item-en {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 7.5pt;
            color: #64748B;
            font-weight: 600;
        }}

        .toc-dots {{
            flex-grow: 1;
            border-bottom: 1px dotted #CBD5E1;
            margin: 0 10px;
            height: 1px;
            align-self: center;
        }}

        .toc-page-num {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-weight: 800;
            font-size: 9.5pt;
            color: var(--accent);
            flex-shrink: 0;
        }}

        /* Chapter Containers */
        .chapter-container {{
            margin-bottom: 30px;
            page-break-before: always;
            break-before: page;
        }}

        .chapter-header {{
            margin-bottom: 22px;
            border-bottom: 2px solid #0F172A;
            padding-bottom: 10px;
        }}

        .chapter-title-en {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 8.5pt;
            font-weight: 800;
            letter-spacing: 2px;
            color: var(--accent);
            text-transform: uppercase;
            margin-bottom: 4px;
        }}

        .chapter-title-cn {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
            font-size: 18pt;
            font-weight: 800;
            color: #0F172A;
            margin: 0;
        }}

        .chapter-divider-bar {{
            display: none;
        }}

        /* Command Cards */
        .command-card {{
            background: #FFFFFF;
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            padding: 18px 20px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
            page-break-inside: avoid;
            break-inside: avoid;
        }}

        .cmd-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1.5px solid var(--border-subtle);
            padding-bottom: 12px;
            margin-bottom: 14px;
        }}

        .cmd-title-group {{
            display: flex;
            align-items: center;
            gap: 14px;
        }}

        .cmd-icon-box {{
            width: 48px;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #FFFFFF;
            border: 1.5px solid var(--border-strong);
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.06);
            flex-shrink: 0;
        }}

        .cmd-icon {{
            width: 36px;
            height: 36px;
            object-fit: contain;
            image-rendering: -webkit-optimize-contrast;
            image-rendering: pixelated;
        }}

        .cmd-icon-placeholder {{
            width: 32px;
            height: 32px;
            background: #F1F5F9;
            border-radius: 4px;
        }}

        .cmd-names {{
            display: flex;
            flex-direction: column;
            gap: 2px;
        }}

        .cmd-title-main {{
            display: flex;
            align-items: baseline;
            gap: 8px;
        }}

        .cmd-eng-name {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 13pt;
            font-weight: 800;
            color: #0F172A;
            letter-spacing: -0.3px;
        }}

        .cmd-num-badge {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 8.5pt;
            font-weight: 700;
            color: var(--accent);
            background: var(--accent-light);
            border: 1px solid var(--accent-border);
            padding: 1px 6px;
            border-radius: 4px;
        }}

        .cmd-cn-name {{
            font-size: 10.5pt;
            font-weight: 700;
            color: #475569;
        }}

        .cmd-cat-badge {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 7.5pt;
            font-weight: 800;
            color: #0F172A;
            background: #F1F5F9;
            border: 1px solid #CBD5E1;
            padding: 4px 9px;
            border-radius: 4px;
            letter-spacing: 0.5px;
            flex-shrink: 0;
        }}

        .cmd-section {{
            margin-bottom: 12px;
        }}

        .sec-label {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 7.5pt;
            font-weight: 800;
            letter-spacing: 1px;
            color: #64748B;
            text-transform: uppercase;
            display: block;
            margin-bottom: 4px;
        }}

        .cmd-desc {{
            font-size: 9.5pt;
            line-height: 1.6;
            color: #1E293B;
            margin: 0;
        }}

        .cmd-steps-list {{
            margin: 4px 0 0 0;
            padding-left: 18px;
            font-size: 9pt;
            line-height: 1.55;
            color: #334155;
        }}

        .cmd-steps-list li {{
            margin-bottom: 4px;
        }}

        .cmd-options-list {{
            margin: 4px 0 0 0;
            padding-left: 18px;
            font-size: 9pt;
            line-height: 1.55;
            color: #334155;
        }}

        .cmd-options-list li {{
            margin-bottom: 4px;
        }}

        /* Notes Box */
        .cmd-notes-box {{
            background: #FFFBEB;
            border-left: 3.5px solid #F59E0B;
            border-radius: 0 6px 6px 0;
            padding: 10px 14px;
            margin: 12px 0;
        }}

        .notes-header {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 8pt;
            font-weight: 800;
            color: #B45309;
            margin-bottom: 4px;
        }}

        .notes-body p {{
            margin: 2px 0;
            font-size: 8.5pt;
            line-height: 1.5;
            color: #78350F;
        }}

        /* Figures Grid */
        .cmd-figures {{
            margin: 16px 0 10px 0;
            border-top: 1px solid var(--border-subtle);
            padding-top: 14px;
            page-break-inside: avoid;
            break-inside: avoid;
        }}

        .figure-grid {{
            display: grid;
            gap: 12px;
            width: 100%;
            margin-bottom: 8px;
        }}

        .figure-grid-1 {{
            grid-template-columns: 1fr;
        }}

        .figure-grid-2 {{
            grid-template-columns: 1fr 1fr;
        }}

        .figure-grid-multi {{
            grid-template-columns: 1fr 1fr;
        }}

        .figure-item {{
            display: flex;
            align-items: center;
            justify-content: center;
            background: #FAFAFA;
            border: 1px solid var(--border-subtle);
            border-radius: 6px;
            padding: 8px;
        }}

        .figure-img {{
            max-width: 100%;
            max-height: 270px;
            object-fit: contain;
            border-radius: 4px;
            background: #FFFFFF;
        }}

        .figure-img-lg {{
            max-height: 380px;
        }}

        .figure-caption {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 8pt;
            font-weight: 600;
            color: #64748B;
            text-align: center;
            margin-top: 6px;
        }}

        /* See Also */
        .cmd-seealso {{
            display: flex;
            align-items: center;
            gap: 10px;
            border-top: 1px dashed var(--border-subtle);
            padding-top: 10px;
            margin-top: 12px;
            font-size: 8.5pt;
        }}

        .seealso-label {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 7.5pt;
            font-weight: 800;
            color: #64748B;
        }}

        .seealso-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}

        .seealso-tag {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 8pt;
            font-weight: 700;
            color: #0F172A !important;
            text-decoration: none !important;
            background: #F1F5F9;
            border: 1px solid #CBD5E1;
            padding: 2px 7px;
            border-radius: 4px;
            transition: all 0.15s ease;
        }}

        .seealso-tag:hover {{
            background: var(--accent-light);
            border-color: var(--accent);
            color: var(--accent) !important;
        }}

        /* Tables & Matrix */
        .specs-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 8.5pt;
            margin: 14px 0 20px 0;
            page-break-inside: auto;
        }}

        .specs-table thead {{
            display: table-header-group;
        }}

        .specs-table tr {{
            page-break-inside: avoid;
            break-inside: avoid;
        }}

        .specs-table th {{
            background: #0F172A;
            color: #FFFFFF;
            font-weight: 700;
            text-align: left;
            padding: 8px 12px;
            border: 1px solid #0F172A;
            font-size: 8pt;
            letter-spacing: 0.5px;
        }}

        .specs-table td {{
            padding: 8px 12px;
            border: 1px solid var(--border-subtle);
            line-height: 1.5;
            vertical-align: middle;
        }}

        .specs-table tr:nth-child(even) {{
            background-color: #F8FAFC;
        }}

        /* Table Command Pill */
        .table-cmd-pill {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            text-decoration: none !important;
            background: #FFFFFF;
            border: 1.5px solid var(--border-strong);
            border-radius: 6px;
            padding: 4px 10px;
            color: #0F172A !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
            transition: all 0.15s ease;
        }}

        .table-cmd-pill:hover {{
            border-color: var(--accent);
            background: var(--accent-light);
            color: var(--accent) !important;
        }}

        .table-cmd-icon {{
            width: 28px;
            height: 28px;
            object-fit: contain;
            image-rendering: -webkit-optimize-contrast;
            image-rendering: pixelated;
            background: #F8FAFC;
            border: 1px solid var(--border-subtle);
            border-radius: 4px;
            padding: 2px;
            flex-shrink: 0;
        }}

        .table-cmd-icon-empty {{
            width: 28px;
            height: 28px;
            background: #F1F5F9;
            border-radius: 4px;
            flex-shrink: 0;
        }}

        .table-cmd-code {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-weight: 700;
            font-size: 9.5pt;
            letter-spacing: -0.2px;
        }}

        .table-page-link {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 8.5pt;
            font-weight: 800;
            color: var(--accent) !important;
            text-decoration: none !important;
            background: var(--accent-light);
            border: 1px solid var(--accent-border);
            padding: 3px 8px;
            border-radius: 4px;
            display: inline-block;
            white-space: nowrap;
        }}

        .table-page-link:hover {{
            background: var(--accent);
            color: #FFFFFF !important;
        }}

        .td-page {{
            text-align: center;
            width: 80px;
        }}

        /* Appendix C Alphabetical Index */
        .index-intro-text {{
            font-size: 9.5pt;
            color: #475569;
            margin-bottom: 20px;
            line-height: 1.6;
        }}

        .index-letter-group {{
            margin-bottom: 24px;
            page-break-inside: avoid;
            break-inside: avoid;
        }}

        .index-letter-header {{
            font-family: Montserrat, 'Segoe UI', Arial, sans-serif;
            font-size: 16pt;
            font-weight: 900;
            color: #0F172A;
            border-bottom: 2px solid #0F172A;
            padding-bottom: 4px;
            margin-bottom: 12px;
        }}

        .index-cards-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px 12px;
        }}

        .index-command-card {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #FFFFFF;
            border: 1px solid var(--border-subtle);
            border-radius: 6px;
            padding: 6px 10px;
            text-decoration: none !important;
            color: inherit !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
            transition: all 0.15s ease;
        }}

        .index-command-card:hover {{
            border-color: var(--accent);
            background: var(--accent-light);
        }}

        .index-card-left {{
            display: flex;
            align-items: center;
            gap: 8px;
            overflow: hidden;
        }}

        .index-cmd-icon {{
            width: 24px;
            height: 24px;
            object-fit: contain;
            image-rendering: -webkit-optimize-contrast;
            image-rendering: pixelated;
            background: #F8FAFC;
            border: 1px solid var(--border-subtle);
            border-radius: 4px;
            padding: 1px;
            flex-shrink: 0;
        }}

        .index-cmd-icon-empty {{
            width: 24px;
            height: 24px;
            background: #F1F5F9;
            border-radius: 4px;
            flex-shrink: 0;
        }}

        .index-cmd-text {{
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}

        .index-cmd-name {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 8.5pt;
            font-weight: 700;
            color: #0F172A;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .index-cmd-cn {{
            font-size: 7.5pt;
            color: #64748B;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .index-card-right {{
            display: flex;
            align-items: center;
            gap: 6px;
            flex-shrink: 0;
        }}

        .index-cmd-cat {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 6.5pt;
            font-weight: 700;
            color: #475569;
            background: #F1F5F9;
            padding: 2px 5px;
            border-radius: 3px;
        }}

        .index-page-badge {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 8pt;
            font-weight: 800;
            color: var(--accent);
            background: var(--accent-light);
            border: 1px solid var(--accent-border);
            padding: 2px 6px;
            border-radius: 4px;
        }}

        /* General Typography */
        code {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 8.5pt;
            background: #F1F5F9;
            border: 1px solid #E2E8F0;
            padding: 1px 4px;
            border-radius: 3px;
            color: #0F172A;
        }}

        a {{
            color: var(--accent);
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
        }}
    
        .figure-item {{
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 4px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}

        .figure-sub-caption {{
            font-size: 7.5pt;
            font-weight: 500;
            color: #334155;
            background: #F8FAFC;
            border-top: 1px solid #E2E8F0;
            padding: 3px 6px;
            display: flex;
            align-items: center;
            gap: 5px;
            line-height: 1.35;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .fig-badge {{
            display: inline-block;
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 6.5pt;
            font-weight: 800;
            color: #EA580C;
            background: #FFF7ED;
            border: 0.5pt solid #FDBA74;
            padding: 0px 4px;
            border-radius: 2px;
            flex-shrink: 0;
        }}

        .fig-cap-text {{
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

    </style>
</head>
<body>

<!-- Page 1: Full-Bleed Cover (Translucent Full-Page Vellum) -->
<div class="cover-page">
    <div class="cover-body">
        <div class="cover-eyebrow">BYRHINO GADGET</div>
        <h1 class="cover-title-chinese">橙皮书</h1>
        <div class="cover-subtitle-bilingual">
            <span class="cover-sub-cn">插件完全参考手册</span>
            <span class="cover-sub-sep">/</span>
            <span class="cover-sub-en">THE COMPLETE TECHNICAL REFERENCE MANUAL</span>
        </div>
        <div class="cover-accent-line"></div>

        <p class="cover-intro-text">
            韩国 PlusPlastic (플러스플라스틱) 官方效能插件 · 93 个权威专题 · 472 幅操作图解 · 116 条高频增强命令全维解构
        </p>

        <!-- Minimalist Architectural Geometric Wireframe SVG (Axon Cube) -->
        <div class="cover-graphic-wrap">
            <svg class="cover-svg-wireframe" width="330" height="230" viewBox="0 0 280 200" fill="none" xmlns="http://www.w3.org/2000/svg">
                <!-- Isometric Cube Wireframe with Subdivision Curves -->
                <polygon points="140,20 240,75 140,130 40,75" stroke="#0A0A0A" stroke-width="1.8" fill="none" />
                <polygon points="40,75 140,130 140,185 40,130" stroke="#0A0A0A" stroke-width="1.8" fill="none" />
                <polygon points="140,130 240,75 240,130 140,185" stroke="#0A0A0A" stroke-width="1.8" fill="none" />
                
                <!-- Internal Parametric Iso-curves -->
                <path d="M65,88 Q140,115 215,88" stroke="rgba(10,10,10,0.35)" stroke-width="1.2" stroke-dasharray="3 3" />
                <path d="M90,102 Q140,120 190,102" stroke="rgba(10,10,10,0.45)" stroke-width="1.2" />
                <path d="M115,116 Q140,125 165,116" stroke="rgba(10,10,10,0.55)" stroke-width="1.2" />
                
                <path d="M90,47 Q140,102 190,157" stroke="rgba(10,10,10,0.25)" stroke-width="1.2" stroke-dasharray="2 2" />
                <path d="M190,47 Q140,102 90,157" stroke="rgba(10,10,10,0.25)" stroke-width="1.2" stroke-dasharray="2 2" />

                <!-- Accent Anchor Points -->
                <circle cx="140" cy="20" r="3" fill="#0A0A0A" />
                <circle cx="240" cy="75" r="3" fill="#0A0A0A" />
                <circle cx="140" cy="130" r="3.5" fill="#FF5500" />
                <circle cx="40" cy="75" r="3" fill="#0A0A0A" />
                <circle cx="140" cy="185" r="3" fill="#0A0A0A" />
            </svg>
        </div>
    </div>

    <div class="cover-footer-editorial">
        <div class="cover-footer-left">
            <div><strong>PlusPlastic Co., Ltd.</strong> & <strong>byRhino3D</strong></div>
            <div>Rhino Authorized Partner & Training Center · <a href="https://www.byrhino3d.com" target="_blank">www.byrhino3d.com</a></div>
        </div>
        <div class="cover-footer-right" style="text-align: right;">
            <div><strong>中文版 edit by 有物建筑 MeansGroup</strong></div>
            <div><a href="https://means.group" target="_blank">means.group</a> · Edition 2026.09</div>
        </div>
    </div>
</div>

<div class="book-wrapper">

    <!-- Page 2: Standalone Preface -->
    <div class="preface-container" id="ch-preface">
        <div class="preface-header">
            <div class="preface-title-en" style="font-family: Montserrat, sans-serif; font-size: 10pt; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; color: #64748B; margin-bottom: 4px;">PREFACE · 序言</div>
            <h2 class="preface-title-cn" style="font-size: 24pt; font-weight: 800; color: #0A0A0A; margin: 0 0 14px 0;">设计工具的克制与效率重构</h2>
            <div class="chapter-divider-bar" style="width: 100%; height: 2px; background: #0A0A0A; margin-bottom: 22px;"></div>
        </div>

        <div class="preface-body" style="font-size: 9.5pt; line-height: 1.8; color: #222222;">
            <div class="preface-lead" style="font-size: 10.5pt; font-weight: 600; line-height: 1.8; color: #1E293B; border-left: 4px solid #0A0A0A; padding-left: 16px; margin: 0 0 20px 0; background: #F8FAFC; padding-top: 10px; padding-bottom: 10px;">
                byRhino Gadget 是韩国 PlusPlastic 团队在十余年一线工业设计与高阶教学培训中凝聚而成的效率结晶。它不试图替代 Rhino 原生命令，而是以克制、利落的工程直觉，打通那些「每次都要做、但又极为繁复」的工作流断点。
            </div>
            <p style="margin-bottom: 14px;">
                PlusPlastic 自 2005 年起担任 Rhino 官方授权代理店与培训中心，长期为设计院校、工业界及建筑工作室提供软体供应、技术支持与培训课程。团队本身亦承接产品与建筑领域的实际设计课题——设计师既是重度建模者，又是技术讲师。为了高效应对大量实际项目中的高频痛点，团队在内部积累了丰富的脚本工具与自制命令。byRhino Gadget 即为这些高频生产力工具的公开编译集。
            </p>
            <p style="margin-bottom: 14px;">
                设计社群习惯将具备权威性与完整体系的工具书称为「橙皮书」。本书基于官方帮助文档的全部 93 个专题页面、472 幅高清操作图解与完整技术参数重新编译制作，全面覆盖 11 大功能领域与全部 116 条命令。每条命令均按「功能定义 → 操作步骤 → 参数选项 → 核心要点 → 图解范例」的标准化版式呈现，并在第十五章系统提炼出六大典型工程工作流。
            </p>
            <p style="margin-bottom: 22px;">
                本书旨在成为每一位 Rhino 高阶设计师案头的权威参考书。
            </p>
        </div>

        <div class="project-facts-block" style="border: 1px solid #E2E8F0; background: #FAFAFA; padding: 18px 22px; margin-top: 10px;">
            <div class="facts-header" style="font-family: Montserrat, monospace; font-size: 8pt; font-weight: 800; letter-spacing: 1.5px; color: #475569; border-bottom: 1px solid #E2E8F0; padding-bottom: 8px; margin-bottom: 14px;">PROJECT FACTS · 项目信息与技术规约</div>
            <div class="facts-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px 24px;">
                <div class="fact-item">
                    <span class="fact-label" style="display: block; font-size: 7.5pt; font-weight: 700; color: #94A3B8; text-transform: uppercase;">DEVELOPER / 研发机构</span>
                    <span class="fact-value" style="font-size: 8.5pt; font-weight: 600; color: #0A0A0A;">PlusPlastic (플러스플라스틱)</span>
                </div>
                <div class="fact-item">
                    <span class="fact-label" style="display: block; font-size: 7.5pt; font-weight: 700; color: #94A3B8; text-transform: uppercase;">QUALIFICATION / 官方资质</span>
                    <span class="fact-value" style="font-size: 8.5pt; font-weight: 600; color: #0A0A0A;">Rhino 授权代理商 & 培训中心 (Since 2005)</span>
                </div>
                <div class="fact-item">
                    <span class="fact-label" style="display: block; font-size: 7.5pt; font-weight: 700; color: #94A3B8; text-transform: uppercase;">TARGET PLATFORM / 适用平台</span>
                    <span class="fact-value" style="font-size: 8.5pt; font-weight: 600; color: #0A0A0A;">Rhinoceros 7 & 8 for Windows</span>
                </div>
                <div class="fact-item">
                    <span class="fact-label" style="display: block; font-size: 7.5pt; font-weight: 700; color: #94A3B8; text-transform: uppercase;">SCOPE / 体系规模</span>
                    <span class="fact-value" style="font-size: 8.5pt; font-weight: 600; color: #0A0A0A;">11 大功能领域 · 116 条高频增强命令</span>
                </div>
                <div class="fact-item">
                    <span class="fact-label" style="display: block; font-size: 7.5pt; font-weight: 700; color: #94A3B8; text-transform: uppercase;">DOCUMENTATION / 官方源文档</span>
                    <span class="fact-value" style="font-size: 8.5pt; font-weight: 600;"><a href="https://www.byrhino3d.com/byRhinoGadget/help/index.html" target="_blank" style="color: #0A0A0A; text-decoration: underline;">byRhino3D 官方技术文档 (93 专题页)</a></span>
                </div>
                <div class="fact-item">
                    <span class="fact-label" style="display: block; font-size: 7.5pt; font-weight: 700; color: #94A3B8; text-transform: uppercase;">EDITORIAL & COMPILATION / 编译策划</span>
                    <span class="fact-value" style="font-size: 8.5pt; font-weight: 600; color: #0A0A0A;">by 有物建筑 · <a href="https://means.group" target="_blank" style="color: #FF5500; text-decoration: underline;">means.group</a></span>
                </div>
            </div>
        </div>
    </div>

    <!-- Page 3: Table of Contents -->
    <div class="toc-container" id="ch-toc">
        <div class="toc-header">
            <div class="toc-kicker">NAVIGATION & ROADMAP</div>
            <h2 class="toc-title">目录大纲与检索导航</h2>
        </div>
        <div class="toc-list">
            {''.join(toc_rows_html)}
        </div>
    </div>

    <!-- Chapters 1 to 15 + Appendices A & B -->
    {''.join(rendered_chapters_html)}

    <!-- Appendix C -->
    {''.join(appendix_c_html)}

</div>

<!-- Full-Bleed Colophon (Back Cover) -->
<div class="colophon-page">
    <div class="colophon-box">
        <div class="colophon-kicker">COLOPHON · 版权与出版说明</div>
        <h2 class="colophon-title">byRhino Gadget · 橙皮书</h2>
        <div class="colophon-sub">插件完全参考手册 / The Complete Technical Reference Manual</div>
        <div class="colophon-divider"></div>

        <div class="colophon-block">
            <div class="colophon-label">原文技术资料来源</div>
            <div class="colophon-val">byRhino Gadget 官方在线帮助文档 (93 个专题)</div>
        </div>
        <div class="colophon-block">
            <div class="colophon-label">原著研发机构</div>
            <div class="colophon-val">PlusPlastic Co., Ltd. (플러스플라스틱) © 2023 PlusPlastic. All rights reserved.</div>
            <div class="colophon-link"><a href="https://www.byrhino3d.com" target="_blank">www.byrhino3d.com</a></div>
        </div>
        <div class="colophon-block">
            <div class="colophon-label">版本规约</div>
            <div class="colophon-val">2026.09 典范参考版 · Rhinoceros 7 & 8 for Windows 全量 116 条命令图文并茂编录</div>
        </div>
        <div class="colophon-block">
            <div class="colophon-label">策划与编译机构</div>
            <div class="colophon-val">中文版 edit by 有物建筑 MeansGroup</div>
            <div class="colophon-link"><a href="https://means.group" target="_blank">means.group</a></div>
        </div>
        
        <div class="colophon-legal">
            byRhino 是 PlusPlastic 运营的设计软件专业平台。Rhinoceros 及 Rhino 标识为 Robert McNeel & Associates 的注册商标。
        </div>
    </div>
</div>

</body>
</html>
'''
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"Wrote HTML to {OUTPUT_HTML} ({len(full_html)/1024:.2f} KB)")
    return all_commands_index

def print_pdf(html_path, pdf_path):
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Users\shimi\AppData\Local\Microsoft\Edge\Application\msedge.exe"
    ]
    edge_exe = None
    for p in edge_paths:
        if os.path.exists(p):
            edge_exe = p
            break
            
    if not edge_exe:
        raise RuntimeError("Microsoft Edge executable not found!")

    cmd = [
        edge_exe,
        "--headless=new",
        "--disable-gpu",
        "--allow-file-access-from-files",
        "--no-margins",
        "--print-to-pdf-no-header",
        f"--print-to-pdf={pdf_path}",
        html_path
    ]
    print(f"Calling Edge Headless to print PDF...")
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    if res.returncode != 0:
        print("Edge error:", res.stderr)
    else:
        print(f"Successfully generated PDF: {pdf_path}")

def extract_real_pages(pdf_path, all_commands):
    print("Extracting physical page numbers with PyMuPDF...")
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"Total physical pages in PDF: {total_pages}")

    ch_page_map = {}
    cmd_page_map = {}

    ascii_chapters = [
        ('ch-01', 'CHAPTER 01'),
        ('ch-02', 'CHAPTER 02'),
        ('ch-03', 'CHAPTER 03'),
        ('ch-04', 'CHAPTER 04'),
        ('ch-05', 'CHAPTER 05'),
        ('ch-06', 'CHAPTER 06'),
        ('ch-07', 'CHAPTER 07'),
        ('ch-08', 'CHAPTER 08'),
        ('ch-09', 'CHAPTER 09'),
        ('ch-10', 'CHAPTER 10'),
        ('ch-11', 'CHAPTER 11'),
        ('ch-12', 'CHAPTER 12'),
        ('ch-13', 'CHAPTER 13'),
        ('ch-14', 'CHAPTER 14'),
        ('ch-15', 'CHAPTER 15'),
        ('app-a', 'APPENDIX A'),
        ('app-b', 'APPENDIX B'),
        ('app-c', 'APPENDIX C')
    ]

    for code, tag in ascii_chapters:
        tag_clean = tag.replace(' ', '').upper()
        for pno in range(3, total_pages):
            text_clean = re.sub(r'\s+', '', doc[pno].get_text()).upper()
            if tag_clean in text_clean:
                ch_page_map[code] = pno + 1
                print(f"  {code} ({tag}) -> Page {pno + 1}")
                break

    # For commands:
    for c in all_commands:
        num = c["num"]
        eng = c["primary_cmd"]
        clean = c["clean_id"]
        found_pno = None
        for pno in range(14, total_pages - 5): # command pages
            ptext = doc[pno].get_text()
            if eng in ptext and (f"#{num}" in ptext or num in ptext):
                found_pno = pno + 1
                break
        if found_pno:
            cmd_page_map[clean] = found_pno
        else:
            print(f"  Warning: command {eng} (#{num}) page not found")

    print(f"Mapped {len(ch_page_map)} chapters and {len(cmd_page_map)} / {len(all_commands)} commands to exact pages.")
    return ch_page_map, cmd_page_map

def main():
    print("=== PASS 1: Build initial HTML and PDF ===")
    all_cmds = build_html()
    print_pdf(OUTPUT_HTML, OUTPUT_PDF)

    print("\n=== ANALYZE: Extract Physical Page Numbers ===")
    ch_map, cmd_map = extract_real_pages(OUTPUT_PDF, all_cmds)

    print("\n=== PASS 2: Inject Physical Page Numbers and Recompile ===")
    build_html(ch_map, cmd_map)
    print_pdf(OUTPUT_HTML, OUTPUT_PDF)

    print("\n=== FINAL VERIFICATION WITH PyMuPDF ===")
    doc = fitz.open(OUTPUT_PDF)
    print(f"Final PDF Pages: {len(doc)}")
    
    total_links = 0
    link_kinds = {}
    for pno in range(len(doc)):
        links = doc[pno].get_links()
        total_links += len(links)
        for l in links:
            k = l.get('kind')
            link_kinds[k] = link_kinds.get(k, 0) + 1
            
    print(f"Total Link Annotations in PDF: {total_links}")
    print(f"Link Kinds: {link_kinds}")
    print("ALL DONE!")

if __name__ == "__main__":
    main()
