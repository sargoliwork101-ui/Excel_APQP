"""Prototype dual PFMEA/Control Plan workflow using shared product profiles."""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Dict
from PyQt6 import QtCore, QtWidgets
from .core.config import MergeSettings, TEMPLATES_DIR, OUTPUT_DIR
from .core.excel_reader import analyze_workbook
from .core.excel_merger import merge_pfmea
from .core import profile_manager as pm

CP_DEFAULTS = MergeSettings(header_rows=9, data_start_row=10,
    sheet_name="برنامه کنترل  ", history_sheet="تغییرات")

class DualWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("PFMEA + CP — APQP"); self.resize(1200, 760)
        self.pfmea_files: Dict[str,str] = {}; self.cp_files: Dict[str,str] = {}
        self.rows = {}; self.profile = None
        root=QtWidgets.QWidget(); self.setCentralWidget(root); lay=QtWidgets.QVBoxLayout(root)
        top=QtWidgets.QGridLayout(); lay.addLayout(top)
        self.pfmea_template=QtWidgets.QLineEdit(str(next(TEMPLATES_DIR.glob("PFMEA*.xlsx"), ""))); self.pfmea_template.setReadOnly(True)
        self.cp_template=QtWidgets.QLineEdit(str(next(TEMPLATES_DIR.glob("CP*.xlsx"), ""))); self.cp_template.setReadOnly(True)
        for i,(label,edit) in enumerate((("PFMEA Template",self.pfmea_template),("CP Template",self.cp_template))):
            top.addWidget(QtWidgets.QLabel(label),i,0); top.addWidget(edit,i,1)
            b=QtWidgets.QPushButton("Browse"); b.clicked.connect(lambda _,e=edit:self.pick_template(e)); top.addWidget(b,i,2)
        self.profile=QtWidgets.QComboBox(); self.profile.addItem(""); self.profile.addItems(pm.list_profiles()); self.profile.currentTextChanged.connect(self.load_profile)
        top.addWidget(QtWidgets.QLabel("Shared profile"),2,0); top.addWidget(self.profile,2,1)
        bar=QtWidgets.QHBoxLayout(); lay.addLayout(bar)
        for text,kind in (("Add PFMEA folder","pfmea"),("Add CP folder","cp")):
            b=QtWidgets.QPushButton(text); b.clicked.connect(lambda _,k=kind:self.add_folder(k)); bar.addWidget(b)
        self.info=QtWidgets.QLabel("Each row has independent PFMEA and CP selection."); bar.addWidget(self.info,1)
        self.table=QtWidgets.QTableWidget(0,7); self.table.setHorizontalHeaderLabels(["Use PFMEA","Use CP","OPC","Station","Failure modes","PFMEA file","CP file"]); self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows); lay.addWidget(self.table,1)
        out=QtWidgets.QHBoxLayout(); lay.addLayout(out); self.output=QtWidgets.QLineEdit(str(OUTPUT_DIR/"Merged")); out.addWidget(self.output,1); self.merge=QtWidgets.QPushButton("Merge selected"); self.merge.clicked.connect(self.merge_selected); out.addWidget(self.merge)
        self.statusBar().showMessage("Ready")
    def pick_template(self,e):
        p,_=QtWidgets.QFileDialog.getOpenFileName(self,"Template",str(TEMPLATES_DIR),"Excel (*.xlsx *.xlsm)")
        if p:e.setText(p)
    def add_folder(self,kind):
        folder=QtWidgets.QFileDialog.getExistingDirectory(self,"Folder",str(Path.home()))
        if not folder:return
        target=self.pfmea_files if kind=="pfmea" else self.cp_files
        for p in list(Path(folder).glob("*.xlsx"))+list(Path(folder).glob("*.xlsm")):
            if p.name.startswith("~$"):continue
            # Analyze with the matching template defaults and match by OPC.
            settings=MergeSettings() if kind=="pfmea" else CP_DEFAULTS
            a=analyze_workbook(p,settings)
            for block in a.stations: target[str(block.opc_code)]=str(p)
        self.rebuild()
    def load_profile(self,name):
        self.profile=pm.load_profile(name) if name else None; self.rebuild()
    def rebuild(self):
        codes=set(self.pfmea_files)|set(self.cp_files)
        if self.profile: codes={s.opc for s in self.profile.stations}|codes
        order={s.opc:i for i,s in enumerate(self.profile.stations)} if self.profile else {}
        codes=sorted(codes,key=lambda x:order.get(x,10000)); self.table.setRowCount(0)
        for code in codes:
            r=self.table.rowCount(); self.table.insertRow(r)
            pe=next((s.pfmea_enabled if s.pfmea_enabled is not None else s.enabled for s in self.profile.stations if s.opc==code), True) if self.profile else bool(code in self.pfmea_files)
            ce=next((s.cp_enabled if s.cp_enabled is not None else s.enabled for s in self.profile.stations if s.opc==code), True) if self.profile else bool(code in self.cp_files)
            for col,val in ((0,pe),(1,ce)):
                item=QtWidgets.QTableWidgetItem(); item.setFlags(QtCore.Qt.ItemFlag.ItemIsUserCheckable|QtCore.Qt.ItemFlag.ItemIsEnabled); item.setCheckState(QtCore.Qt.CheckState.Checked if val else QtCore.Qt.CheckState.Unchecked); self.table.setItem(r,col,item)
            self.table.setItem(r,2,QtWidgets.QTableWidgetItem(code)); self.table.setItem(r,3,QtWidgets.QTableWidgetItem(code))
            self.table.setItem(r,4,QtWidgets.QTableWidgetItem("")); self.table.setItem(r,5,QtWidgets.QTableWidgetItem(Path(self.pfmea_files.get(code,"missing")).name)); self.table.setItem(r,6,QtWidgets.QTableWidgetItem(Path(self.cp_files.get(code,"missing")).name))
    def merge_selected(self):
        jobs=[]; out=Path(self.output.text()); out.parent.mkdir(parents=True,exist_ok=True)
        for r in range(self.table.rowCount()):
            code=self.table.item(r,2).text(); pe=self.table.item(r,0).checkState()==QtCore.Qt.CheckState.Checked; ce=self.table.item(r,1).checkState()==QtCore.Qt.CheckState.Checked
            if pe and code in self.pfmea_files: jobs.append(("pfmea",code))
            if ce and code in self.cp_files: jobs.append(("cp",code))
        if any(kind=="pfmea" for kind,_ in jobs):
            selections=[]
            for _,code in jobs:
                if _=="pfmea":
                    a=analyze_workbook(self.pfmea_files[code],MergeSettings())
                    selections += [(self.pfmea_files[code],b) for b in a.stations]
            merge_pfmea(self.pfmea_template.text(),selections,str(out.with_name(out.stem+"_PFMEA.xlsx")),MergeSettings())
        if any(kind=="cp" for kind,_ in jobs):
            selections=[]
            for _,code in jobs:
                if _=="cp":
                    a=analyze_workbook(self.cp_files[code],CP_DEFAULTS)
                    selections += [(self.cp_files[code],b) for b in a.stations]
            merge_pfmea(self.cp_template.text(),selections,str(out.with_name(out.stem+"_CP.xlsx")),CP_DEFAULTS,rewrite_pfmea_formulas=False)
        self.statusBar().showMessage("Merge completed")

def main():
    app=QtWidgets.QApplication(sys.argv); from .ui.style import apply_dark_theme; apply_dark_theme(app); w=DualWindow(); w.show(); return app.exec()
if __name__=="__main__": sys.exit(main())
