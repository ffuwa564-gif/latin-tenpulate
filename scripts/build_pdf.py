#!/usr/bin/env python3
"""Build a complete, searchable Latin 1000 PDF from data/latin_1000.csv.

Requires: reportlab, pymupdf, fonts-dejavu-core.
Exactly 1000 ranked rows must be present; verification fails on any omission.
"""
from collections import Counter, defaultdict
from pathlib import Path
import csv, html, json, re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
import fitz

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data/latin_1000.csv"
OUT = BASE / "output/latin_1000_semantic_templates.pdf"
MANIFEST = BASE / "output/manifest.json"
TEMPLATES = [
("REF","参照・指示","誰・何・どの対象を指しているか","ego / hic"),
("LOGIC","接続・論理","追加・逆接・理由・条件をどうつなぐか","et / sed"),
("FPOS","方向を示す機能語","起点・目標・基準点と必要な格","ad / ex"),
("SPACE","場所・空間","内外・高低・位置や領域の関係","locus / urbs"),
("MOVE","移動・方向","誰がどこへ、どの向きに動くか","ire / venire"),
("TRANSFER","取得・授受","何を誰から誰へ移すか","dare / accipere"),
("CREATE","生成・変化","何を作り、何を変えるか","facere / creare"),
("DIRECT","命令・働きかけ","誰に何をさせるか","iubere / cogere"),
("PERCEIVE","知覚・観察","何をどう知覚するか","videre / aspicere"),
("THINK","知識・思考","何を知り、何を考えるか","scire / cognoscere"),
("SPEAK","発話・表現","誰に何を伝え、表すか","dicere / narrare"),
("STATE","存在・状態","何があり、どんな状態か","esse / vivere"),
("EMOTION","感情・欲求","何を愛し、恐れ、望むか","amare / timere"),
("CONFLICT","対立・危険","どんな衝突・危害・抵抗があるか","pugnare / vincere"),
("SOCIAL","社会・制度","人・権力・規範・商業の関係","rex / lex"),
("PERSON","人物・身体","どの役割・身体部分を指すか","manus / mater"),
("NATURE","自然・物質","自然物・素材・生物の違い","aqua / terra"),
("TIME","時間・順序","いつ・どれほど・前後どちらか","annus / tempus"),
("QUANTITY","数量・尺度","数・量・尺度・比較の基準","multus / unus"),
("QUALITY","性質・評価","どんな性質で、何と対比されるか","bonus / malus"),
("DEGREE","程度・様態","強さ・方法・確かさを修飾する","bene / valde"),
("ACTION","一般行為","行為者・対象・結果を区別する","agere / colere"),
("ENTITY","その他の概念・物","個別の具体物・抽象概念を対比する","res / nomen"),
]
KEYS = {x[0] for x in TEMPLATES}
def category(r):
    p=r["Part of Speech"].split(":")[0];g=r["Semantic Group"]
    def has(*gset):return g in gset
    if p=="Conjunction":return "LOGIC"
    if p=="Preposition":return "FPOS" if g=="Place" else "LOGIC"
    if p=="Pronoun":return "REF"
    if p=="Adverb":
        if g=="Pronouns/Interrogatives":return "REF"
        if g=="Conjunctions/Adverbs":return "LOGIC"
        if has("Time","Lengths of Time"):return "TIME"
        if has("Place","Travel","Motion","Geography"):return "SPACE"
        if g=="Measurement":return "QUANTITY"
        return "DEGREE"
    if p=="Verb":
        if has("Motion","Travel","Geography","Place"):return "MOVE"
        if has("Verbs of Transport","Business/Money"):return "TRANSFER"
        if g=="Making/Doing":return "CREATE"
        if g=="Vision":return "PERCEIVE"
        if g=="Education/Knowledge":return "THINK"
        if has("Speech/Oratory","Writing/Poetry"):return "SPEAK"
        if has("Emotions","Love"):return "EMOTION"
        if has("War and Peace","Violence","Athletics"):return "CONFLICT"
        if has("Life and Being","Time","Lengths of Time"):return "STATE"
        if g=="Verbs of Compelling/Directing":return "DIRECT"
        if has("Justice","Religion","Social Life"):return "SOCIAL"
        return "ACTION"
    if p=="Noun":
        if has("People","The Body","The Household"):return "PERSON"
        if has("Air and Fire","Earth and Water","Animals/Plants"):return "NATURE"
        if has("The House","The City","Geography","Place","Travel"):return "SPACE"
        if g=="Measurement":return "QUANTITY"
        if has("Time","Lengths of Time"):return "TIME"
        if has("Emotions","Love"):return "EMOTION"
        if has("Education/Knowledge","Writing/Poetry","Speech/Oratory"):return "THINK"
        if has("Business/Money","Justice","Religion","War and Peace","Social Life"):return "SOCIAL"
        if g=="Life and Being":return "STATE"
        if has("Violence","Athletics"):return "CONFLICT"
        return "ENTITY"
    if p=="Adjective":
        if g=="Measurement":return "QUANTITY"
        if has("Time","Lengths of Time"):return "TIME"
        if has("Place","Geography","Travel"):return "SPACE"
        if has("Emotions","Love"):return "EMOTION"
        if g=="Pronouns/Interrogatives":return "REF"
        if has("Vision","Air and Fire","Earth and Water","Animals/Plants"):return "NATURE"
        if has("Justice","Social Life","War and Peace"):return "SOCIAL"
        return "QUALITY"
    return "ENTITY"
rows=list(csv.DictReader(DATA.open(encoding="utf-8-sig",newline="")))
assert len(rows)==1000, f"Expected 1000, got {len(rows)}"
for row in rows:
    row["rank"]=int(row["Frequency Rank"])
    row["category"]=category(row)
    assert row["Headword"].strip() and row["Definition"].strip()
assert sorted(r["rank"] for r in rows)==list(range(1,1001))
assert {r["category"] for r in rows}==KEYS
assert {r["First Element"] for r in rows if r["rank"]>997}=={"gemma","vitrum","puellula"}
groups=defaultdict(list)
for row in rows:groups[row["category"]].append(row)
counts=Counter(r["category"] for r in rows)
OUT.parent.mkdir(parents=True,exist_ok=True)
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
REG="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
assert Path(REG).exists() and Path(BOLD).exists()
pdfmetrics.registerFont(TTFont("latin",REG))
pdfmetrics.registerFont(TTFont("latin-bold",BOLD))
jp="HeiseiKakuGo-W5"; w,h=A4; lx=43;rx=w-43
navy=HexColor("#17253b");teal=HexColor("#387d82")
ink=HexColor("#26364c");mute=HexColor("#677687")
line=HexColor("#e1e5e8");pale=HexColor("#f0f6f5")
def drawjp(c,x,y,t,size=10,color=ink):
    c.setFillColor(color);c.setFont(jp,size);c.drawString(x,y,t)
def draw(c,x,y,t,size=10,color=ink,bold=False):
    c.setFillColor(color);c.setFont("latin-bold" if bold else "latin",size);c.drawString(x,y,t)
def pagehead(c,n,label=""):
    c.setFillColorRGB(1,1,1);c.rect(0,0,w,h,fill=1,stroke=0)
    c.setFillColor(teal);c.rect(0,h-9,w,9,fill=1,stroke=0)
    draw(c,lx,h-36,"L A T I N   1 0 0 0",8,teal,True)
    if label:drawjp(c,207,h-36,label,8.4,mute)
    c.setStrokeColor(line);c.line(lx,37,rx,37)
    draw(c,lx,22,"DCC Latin Core Vocabulary  |  semantic-template edition",7,mute)
    draw(c,rx-21,22,f"{n:02d}",9,ink,True)
c=canvas.Canvas(str(OUT),pagesize=A4,pageCompression=1,invariant=1)
c.setTitle("Latin 1000: 23 Semantic Templates - Complete Vocabulary")
c.setAuthor("Latin Template Study Project / Dickinson College Commentaries data")
page=1;pagehead(c,page)
c.setFillColor(navy);c.rect(lx,h-355,rx-lx,267,fill=1,stroke=0)
draw(c,lx+25,h-167,"LATIN",38,HexColor("#ffffff"),True)
draw(c,lx+25,h-215,"1,000 WORDS",29,HexColor("#ffffff"),True)
drawjp(c,lx+25,h-273,"意味テンプレートで学ぶラテン語基本語彙",13,HexColor("#ffffff"))
draw(c,lx+25,h-302,"23 semantic templates / Complete 1,000-entry index",8,HexColor("#d6eeea"))
drawjp(c,lx,h-393,"すべての単語を掲載",17,navy)
for k,t in enumerate([
"品詞と意味分野を手掛かりに、1,000語を23種類の意味構造へ分類。",
"各項目には見出し語・英語語義・通し番号を掲載。",
"997語: Dickinson College Commentaries の基本語彙。",
"追加3語: gemma, vitrum, puellula（第998～1000番）。",
"注意: 分類は学習用の暫定分類。意味を確定する文法規則ではない。",
]):drawjp(c,lx,h-422-k*25,t,9,mute)
draw(c,lx,h-563,"https://dcc.dickinson.edu/latin-core-list1",8,mute)
c.showPage();page+=1
pagehead(c,page)
drawjp(c,lx,h-80,"23個の意味テンプレート",17,navy)
drawjp(c,lx,h-104,"それぞれの分類が持つ共通の問いを考えながら覚える。",9,mute)
y=h-144
for i,(key,title,frame,example) in enumerate(TEMPLATES,1):
    if y<77:
        c.showPage();page+=1;pagehead(c,page);y=h-80
    draw(c,lx,y,f"T{i:02d}",9,teal,True)
    drawjp(c,lx+52,y,title,10.5,navy)
    draw(c,rx-55,y,f"{counts[key]} words",8,mute)
    drawjp(c,lx+52,y-14,frame,7.8,mute)
    c.setStrokeColor(line);c.line(lx,y-19,rx,y-19)
    y-=29
c.showPage();page+=1
pagehead(c,page)
drawjp(c,lx,h-80,"学習の流れと限界",17,navy)
steps=[
("01 まず構造を見る","同じ意味テンプレートに入る語の共通点を言語化する。"),
("02 差分を比べる","似た2語を比べ、対象・方向・強さ・結果の違いを説明する。"),
("03 語義と照合する","英語語義を読み、予測できなかった意味を記録する。"),
("04 例文で確かめる","格支配・多義・慣用表現を辞書や古典本文で確認する。"),
]
y=h-140
for title,desc in steps:
    c.setFillColor(pale);c.roundRect(lx,y-55,rx-lx,70,7,stroke=0,fill=1)
    drawjp(c,lx+13,y-10,title,12,navy)
    drawjp(c,lx+13,y-32,desc,9,ink)
    y-=95
drawjp(c,lx,240,"注意事項",13,navy)
notes=[
"・23分類は元の意味分野と品詞によるヒューリスティックな分類。",
"・見出し語の多義性や細かいニュアンスまでは分類が保証しない。",
"・重複する見出し要素は同音異義語として別語義のことがある。",
"・番号は元データの頻度順位（998～1000のみ補助番号）。",
"・訳語は元CSVの英語語義を保持している。",
]
for i,t in enumerate(notes):drawjp(c,lx,207-i*23,t,8.5,mute)
c.showPage();page+=1
latin_style=ParagraphStyle("head",fontName="latin-bold",fontSize=10.1,leading=14.4,textColor=ink)
gloss_style=ParagraphStyle("gloss",fontName="latin",fontSize=8.5,leading=12.4,textColor=mute)
pages={}
for idx,(key,title,frame,example) in enumerate(TEMPLATES,1):
    chapter=f"T{idx:02d}  |  {title}";pages[key]=page;pagehead(c,page,chapter)
    anchor=f"T{idx:02d}";c.bookmarkPage(anchor);c.addOutlineEntry(f"T{idx:02d} {title} ({counts[key]} words)",anchor,0,False)
    draw(c,lx,h-76,f"TEMPLATE {idx:02d}",8.5,teal,True)
    drawjp(c,lx,h-109,title,19,navy)
    drawjp(c,lx,h-134,frame,9,mute)
    draw(c,lx,h-154,f"{counts[key]} words / example: {example}",8.5,teal)
    y=h-181
    for r in sorted(groups[key],key=lambda r:r["rank"]):
        ph=Paragraph(html.escape(r["Headword"]),latin_style)
        pg=Paragraph(html.escape(r["Definition"]),gloss_style)
        avail=rx-lx-69
        _,hh=ph.wrap(avail,800);_,hg=pg.wrap(avail,800)
        box=max(41,hh+hg+13)
        if y-box<55:
            c.showPage();page+=1;pagehead(c,page,chapter)
            draw(c,lx,h-76,f"TEMPLATE {idx:02d} / CONTINUED",8.5,teal,True)
            drawjp(c,lx,h-96,title,12,navy);y=h-120
        if r["rank"]>997:
            c.setFillColor(pale);c.rect(lx,y-box,rx-lx,box,fill=1,stroke=0)
        draw(c,lx+3,y-16,f'[{r["rank"]:04d}]',8.4,teal,True)
        ph.drawOn(c,lx+63,y-7-hh);pg.drawOn(c,lx+63,y-9-hh-hg)
        c.setStrokeColor(line);c.setLineWidth(.37);c.line(lx,y-box,rx,y-box)
        y-=box+3
    c.showPage();page+=1
c.save()
doc=fitz.open(str(OUT));alltext="\n".join(x.get_text() for x in doc)
numbers=[int(s) for s in re.findall(r"(?m)^\[(\d{4})\]\s*$",alltext)]
assert len(numbers)==1000, f"PDF yielded {len(numbers)} numbered rows, not 1000"
assert sorted(numbers)==list(range(1,1001)),"PDF contains missing or duplicate entry labels"
for lemma in ("gemma","vitrum","puellula","sum esse","petō"):
    assert lemma in alltext,f"missing lemma {lemma!r}"
meta={
 "entries":1000,"dcc_entries":997,
 "extra_words":[{"rank":r["rank"],"lemma":r["First Element"]} for r in rows if r["rank"]>997],
 "templates":[{"code":f"T{i:02d}","name_ja":title,"count":counts[key],"first_pdf_page":pages[key]} for i,(key,title,_,_) in enumerate(TEMPLATES,1)],
 "verification":{"pdf_pages":len(doc),"extractable_latin_entries":len(numbers),"unique_entry_ids":len(set(numbers))},
 "source":"https://dcc.dickinson.edu/latin-core-list1",
 "gloss_language":"English (original source)",
 "classification_method":"educational heuristic, not exhaustive semantic analysis"
}
MANIFEST.write_text(json.dumps(meta,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(f"VERIFIED: 1000 unique numbered entries across {len(doc)} PDF pages")
