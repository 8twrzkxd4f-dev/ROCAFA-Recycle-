from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/documents/圓形雙傘回收系統規格表.docx'
OUT.parent.mkdir(parents=True, exist_ok=True)
doc = Document()
sec = doc.sections[0]
sec.page_width = Inches(8.5)
sec.page_height = Inches(11)
sec.top_margin = sec.bottom_margin = Inches(.65)
sec.left_margin = sec.right_margin = Inches(.7)
for name in ['Normal', 'Title', 'Subtitle', 'Heading 1', 'Heading 2']:
    st = doc.styles[name]
    st.font.name = 'Arial Unicode MS'
    st.font.color.rgb = RGBColor(0,0,0)
    st.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), 'Arial Unicode MS')
    for attr in ['asciiTheme','hAnsiTheme','eastAsiaTheme','cstheme']:
        st.element.get_or_add_rPr().rFonts.attrib.pop(qn('w:'+attr),None)
    ppr=st.element.find(qn('w:pPr'))
    if ppr is not None:
        for border in list(ppr.findall(qn('w:pBdr'))): ppr.remove(border)
doc.styles['Normal'].font.size = Pt(11)
doc.styles['Normal'].paragraph_format.space_after = Pt(6)
doc.styles['Normal'].paragraph_format.line_spacing = Pt(15)
doc.styles['Title'].font.size = Pt(22)
doc.styles['Title'].paragraph_format.line_spacing = Pt(29)
doc.styles['Title'].paragraph_format.space_after = Pt(8)
doc.styles['Heading 1'].font.size = Pt(14)
doc.styles['Heading 1'].paragraph_format.line_spacing = Pt(19)
doc.styles['Heading 1'].paragraph_format.space_before = Pt(10)
doc.styles['Heading 1'].paragraph_format.space_after = Pt(6)

def para(s, style=None):
    return doc.add_paragraph(s, style)

def table(headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for c,w in zip(t.columns,widths): c.width = Inches(w)
    for c,s in zip(t.rows[0].cells,headers): c.text=s
    pr=t.rows[0]._tr.get_or_add_trPr()
    repeat=OxmlElement('w:tblHeader'); pr.append(repeat)
    for row in rows:
        for c,s in zip(t.add_row().cells,row): c.text=s
    for i,row in enumerate(t.rows):
        trpr=row._tr.get_or_add_trPr()
        trpr.append(OxmlElement('w:cantSplit'))
        for j,c in enumerate(row.cells):
            c.width=Inches(widths[j]); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tcpr=c._tc.get_or_add_tcPr()
            borders=OxmlElement('w:tcBorders')
            for side in ['top','left','bottom','right']:
                b=OxmlElement('w:'+side);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'D9D9D9');borders.append(b)
            tcpr.append(borders)
            mar=OxmlElement('w:tcMar')
            for side in ['top','bottom','left','right']:
                a=OxmlElement('w:'+side);a.set(qn('w:w'),'75');a.set(qn('w:type'),'dxa');mar.append(a)
            tcpr.append(mar)
            shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'DCE6F1' if i==0 else ('F4F6F8' if i%2==0 else 'FFFFFF'));tcpr.append(shade)
            for p in c.paragraphs:
                p.paragraph_format.space_after=Pt(1)
                p.paragraph_format.space_before=Pt(1)
                p.paragraph_format.line_spacing=Pt(14)
                for r in p.runs:
                    r.font.size=Pt(10.5);r.bold=(i==0)
    return t

doc.add_paragraph('圓形雙傘回收系統規格表','Title')
para('未來飛行員有個太空夢  ｜  2026 年 10 月 6 日  ｜  版本 0.1')
para('本設計採用 2.12 m² 導引傘及 6.05 m² 主傘，供回收系統選材、收納設計與設計審查使用。下降性能已完成理想模型估算；傘具製作尺寸、開傘瞬態載荷與分階段充氣機構仍須確認。')
doc.add_paragraph('1 傘具初步規格','Heading 1')
table(['規格項目','主傘','導引傘／阻力傘'],[
('主要功能','降低落海速度','穩定箭體及降低主傘開啟前速度'),
('傘型','圓形平面傘，中央洩氣孔','圓形平面傘，中央洩氣孔'),
('名目參考面積','6.05 m²','2.12 m²'),
('名目平面直徑','2.78 m','1.64 m'),
('初步傘片數','12 片','8 片'),
('初步洩氣孔直徑','140 mm','80 mm'),
('傘布','高強度防撕裂尼龍','高強度防撕裂尼龍'),
('傘布選材條件','布重、透氣率及強度待確認','布重、透氣率及強度待確認'),
('傘面補強','傘緣、接縫與傘繩接點設補強帶','傘緣、接縫與傘繩接點設補強帶'),
('傘繩數量','12 條','8 條'),
('初步傘繩有效長度','3.3–3.6 m','2.0–2.1 m'),
('傘繩與吊帶','具破斷強度資料的低伸長纖維繩／織帶','具破斷強度資料的低伸長纖維繩／織帶'),
('模擬阻力係數','0.80，待實測校正','0.75，待實測校正'),
('開傘觸發條件','下降至 450 m AGL','最高點後 0.5 s'),
('展開方式','傘袋控制出繩；分階段充氣待驗證','直接展開；低動壓充氣待驗證'),
('預估下降速度','海平面約 8.03 m/s','450 m 高度約 14.32 m/s'),
('收納與連接','獨立收納區；吊帶及額定連接件接至承力點','獨立收納區；吊帶及額定連接件接至承力點'),
('可視性','橘色或螢光色搭配對比色','與主傘採不同顏色'),
], [1.45,2.825,2.825])

doc.add_page_break()
doc.add_paragraph('2 系統介面與計算條件','Heading 1')
table(['項目','設計基準或狀態'],[
('回收質量','19.471 kg，由 28.471 kg 減去燃料 9 kg；須以實際燃燒後質量更新。'),
('回收構型','假設各分離段保持繫留並共同回收；若分別回收，須重新分配傘具與質量。'),
('飛行高度','最高點約 3361 m；主傘高度採距地面 450 m。模擬假設射場接近海平面。'),
('主傘開啟速度','目標 ≤15 m/s；現有理想模型預估 14.32 m/s。'),
('主傘全開等效阻力','450 m 高度、速度 14.32 m/s 時約 0.58 kN；此值不是開傘瞬態峰值。'),
('開傘峰值載荷','尚未驗證；須計入充氣時間、繩索拉直衝擊及導引傘持續承力狀態。'),
('承力安全係數','依原報告，金屬 >1.5、非金屬／複合材料 >2.0；套用於確認後的設計載荷。'),
('收納介面','箭身內徑約 148 mm；可用艙長、傘袋外徑及打包體積待實際量測。'),
('起飛質量限制','總質量 <28.5 kg；報告現值 28.471 kg，餘量僅 29 g。更換傘具後須重算。'),
('落點條件','需重算 5 m/s 風速下落點；加大導引傘會增加下降時間與漂移。'),
], [1.55,5.55])
doc.add_paragraph('3 製作與驗證注意事項','Heading 1')
para('直徑為依名目圓面積換算的平面尺寸，不等於充氣後直徑。正式裁片需加入縫份、補強帶及洩氣孔配置；阻力係數必須與相同參考面積定義配對使用。')
para('導引傘在本文件中指 drogue chute，負責穩定及減速；若需用小傘拉出主傘，應另行設計 pilot chute 與抽傘介面。')
para('先前討論的 4 kN 測試載荷、30–40% 分階段充氣及解除時間均未定案。需依實測開傘峰值、結構安全係數與材料強度制定驗證載荷；繩結、縫製、潮濕及磨耗造成的強度折減也須納入。')
para('下一步量測完整回收狀態的實際質量，確認傘具打包尺寸，再依序完成承力路徑分析、充氣與載荷測試，以及航電觸發整合驗證。')
doc.add_paragraph('4 資料依據','Heading 1')
para('未來飛行員有個太空夢_一次審查報告.pdf：PDF 第 2、4、5、7、9、10 頁的箭體規格、模擬參數、任務剖面及系統需求。初步傘具幾何、材料與繩長為本次設計建議。')
para('下降速度與等效阻力引用本次討論的單軸變密度下降估算，模型未涵蓋傘面充氣動力學、風場、箭體氣動力及雙傘相互干擾，故不作為飛行驗證通過證明。')
doc.core_properties.title='圓形雙傘回收系統規格表'
doc.core_properties.subject='主傘與導引傘初步規格及驗證條件'
doc.save(OUT)
print(OUT)
