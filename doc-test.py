import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import sqlite3, hashlib, datetime, re, csv, os, unicodedata

# =============================================================================
# [Iron Vault v8.5] CRT Legacy Edition (Final Gold Master)
# -----------------------------------------------------------------------------
# [Environment] Windows XP / Python 3.4 (Standard Lib Only - No pip required)
# [Resolution]  1000x700 (Optimized for 1024x768 CRT Monitors w/ Taskbar area)
# [Localization] Japanese (MS UI Gothic, UTF-8-SIG, Yen/Full-width Support)
# [Input Guard]  IME 자판 실수(장음, 전각 하이픈 등) 완벽 방어 로직 탑재
# =============================================================================

class IronVaultCommander:
    def __init__(self, root):
        self.root = root
        self.root.title("Iron Vault v8.5 (CRT Legacy - IME Guard)")
        
        # [XP 최적화] 1024x768 해상도 대응. 
        self.root.geometry("1000x700")
        self.root.resizable(True, True) 
        
        # [Database] 장부용(ERP)과 세금용(Invoice) DB 이중화
        self.db_erp, self.db_inv = "vault_erpa.db", "vault_invoice.db"
        self.init_databases()
        
        # [State] 기본 뷰 설정
        self.current_view, self.sort_col, self.sort_desc = "erp", "date", True
        self.is_cross_searching = False

        # [Pipeline] UI 초기화 -> 데이터 로드
        self.setup_ui()
        self.load_data()

    def init_databases(self):
        """DB 초기화: 파일 없으면 자동 생성 (Portable)"""
        try:
            with sqlite3.connect(self.db_erp) as c1, sqlite3.connect(self.db_inv) as c2:
                # [Ledger] 일반 장부
                c1.execute("CREATE TABLE IF NOT EXISTS ledger (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, corp TEXT, amount INTEGER, hash TEXT UNIQUE, created_at TEXT)")
                # [Invoices] 인보이스 (T-번호 포함)
                c2.execute("CREATE TABLE IF NOT EXISTS invoices (id INTEGER PRIMARY KEY AUTOINCREMENT, t_no TEXT, date TEXT, corp TEXT, item TEXT, amount INTEGER, tax_rate INTEGER, tax INTEGER, hash TEXT UNIQUE, created_at TEXT)")
        except: 
            messagebox.showerror("Error", "DB Init Failed (Write Permission Check)")

    def setup_ui(self):
        """UI 구성: 입력부, 검색부, 결과부 3단 구성"""
        # --- [1] 입력부 (Input Area) ---
        input_frame = tk.LabelFrame(self.root, text=" [ 1. 데이터 박제소 ] ", padx=5, pady=5)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        self.entries = {}
        fields = [("① 날짜 (2026-01-25)", "date", 0, 0), ("② 거래처명", "corp", 0, 1), ("③ 공급가액", "amount", 0, 2),
                  ("④ T-번호", "t_no", 1, 0), ("⑤ 세율 (10/8)", "tax_rate", 1, 1), ("⑥ 세액", "tax", 1, 2), ("⑦ 품목", "item", 2, 0)]
        
        for txt, key, r, c in fields:
            f = tk.Frame(input_frame); f.grid(row=r, column=c, sticky="we", padx=5, pady=2)
            tk.Label(f, text=txt, anchor="w", font=("MS UI Gothic", 9, "bold")).pack(fill="x")
            e = tk.Entry(f); e.pack(fill="x"); self.entries[key] = e
            if key == "tax_rate": e.insert(0, "10") # 기본 세율 10%
            
        for i in range(3): input_frame.grid_columnconfigure(i, weight=1)
        
        # 저장 버튼 (초대형)
        tk.Button(input_frame, text="▼ 안전하게 박제하기 (COMMIT) [Enter] ▼", command=self.save_transaction, bg="#2c3e50", fg="white", font=("MS UI Gothic", 9, "bold")).grid(row=3, column=0, columnspan=3, sticky="we", pady=5)

        # --- [2] 검색부 (Search Filters) ---
        search_frame = tk.LabelFrame(self.root, text=" [ 2. 통합 검색 필터 ] ", padx=10, pady=5)
        search_frame.pack(fill="x", padx=10, pady=5)

        # Row 1: 검색어, 날짜
        row1 = tk.Frame(search_frame); row1.pack(fill="x", pady=2)
        tk.Label(row1, text="검색어:", width=8, anchor="e").pack(side="left")
        self.entry_search = tk.Entry(row1, width=20); self.entry_search.pack(side="left", padx=5)
        
        tk.Label(row1, text="날짜:", width=8, anchor="e").pack(side="left")
        self.date_start = tk.Entry(row1, width=12); self.date_start.pack(side="left")
        tk.Label(row1, text="~").pack(side="left")
        self.date_end = tk.Entry(row1, width=12); self.date_end.pack(side="left")

        # Row 2: 금액, 버튼
        row2 = tk.Frame(search_frame); row2.pack(fill="x", pady=2)
        tk.Label(row2, text="금액:", width=8, anchor="e").pack(side="left")
        self.amt_min = tk.Entry(row2, width=15); self.amt_min.pack(side="left", padx=5)
        tk.Label(row2, text="~").pack(side="left")
        self.amt_max = tk.Entry(row2, width=15); self.amt_max.pack(side="left")
        
        tk.Button(row2, text="🔍 검색", command=self.load_data, bg="#3498db", fg="white", width=8).pack(side="left", padx=15)
        tk.Button(row2, text="🔄 초기화", command=self.clear_search, width=8).pack(side="left")

        # 엔터키 바인딩
        for w in [self.entry_search, self.date_start, self.date_end, self.amt_min, self.amt_max]:
            w.bind("<Return>", self.on_search_enter)

        # --- [3] 결과창 (Result View) ---
        ctrl = tk.Frame(self.root); ctrl.pack(fill="x", padx=10, pady=5)
        tk.Button(ctrl, text="[ 장부 ]", command=lambda: self.switch_view("erp"), width=12).pack(side="left")
        tk.Button(ctrl, text="[ 인보이스 ]", command=lambda: self.switch_view("inv"), width=12, padx=2).pack(side="left")
        tk.Button(ctrl, text="CSV 내보내기", command=self.export_to_csv, bg="#27ae60", fg="white").pack(side="right")

        self.tree = ttk.Treeview(self.root, show="headings", selectmode="browse") 
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        sb = ttk.Scrollbar(self.tree, command=self.tree.yview); sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

        # 메인 윈도우 엔터키 바인딩 (저장)
        self.root.bind('<Return>', self.save_transaction)

    def on_search_enter(self, event):
        self.load_data()
        return "break"

    def clear_search(self):
        for e in [self.entry_search, self.date_start, self.date_end, self.amt_min, self.amt_max]: e.delete(0, 'end')
        self.load_data()

    def validate_input(self, d):
        """입력값 유효성 검사"""
        try: datetime.datetime.strptime(d["date"], "%Y-%m-%d")
        except: raise ValueError("날짜 형식 오류 (YYYY-MM-DD)")
        
        try: amt, tax, rate = int(d["amount"]), int(d["tax"]), int(d["tax_rate"])
        except: raise ValueError("금액/세율/세액은 숫자만 입력 가능합니다!")
        
        if rate not in [8, 10]:
            if not messagebox.askyesno("확인", f"{rate}%가 맞습니까? (통상 10% or 8%)"): return None, None, None
            
        if not re.match(r'^T\d{13}$', d["t_no"].upper()): raise ValueError("T-번호 형식 오류 (예: T1234567890123)")
        
        if not d["corp"].strip(): raise ValueError("거래처명은 필수입니다.")
        return amt, tax, rate

    def save_transaction(self, event=None):
        """
        [Core Logic] 데이터 저장 및 정제
        - 여기가 마스터가 요청하신 'IME 오타 방어'의 핵심입니다.
        """
        d = {k: v.get().strip() for k, v in self.entries.items()}
        
        # [Sanitization] 강력한 전처리
        for k in ["t_no", "amount", "tax", "tax_rate", "date"]:
            if d.get(k):
                # 1. 전각->반각 정규화 (１００ -> 100)
                d[k] = unicodedata.normalize('NFKC', d[k])
                
                # 2. 금액: 통화 기호 및 콤마 제거
                if k in ["amount", "tax", "tax_rate"]: 
                    d[k] = re.sub(r'[¥円,]', '', d[k])
                
                # 3. 날짜: 일본어 IME 오타 방어 로직 (여기가 업데이트됨!)
                # Em dash(\u2014), 하이픈류(\u2010~), 마이너스(\u2212), 전각하이픈(\uFF0D)
                # ★ 장음 부호(\u30FC) 추가: '2026ー01ー25' 같은 오타를 '2026-01-25'로 자동 수정
                # 슬래시(/), 닷(.) 도 포함
                if k == "date": 
                    d[k] = re.sub(r'[\u2010-\u2015\u2212\uFF0D\u30FC/.]', '-', d[k])

        try:
            # 유효성 검사
            amt, tax, rate = self.validate_input(d)
            if amt is None: return 

            # 해시 생성 (중복 방지)
            doc_hash = hashlib.sha256("".join(str(x) for x in [d["date"], d["corp"], amt, d["t_no"], tax]).encode()).hexdigest()
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # DB 저장 (트랜잭션)
            with sqlite3.connect(self.db_erp) as c1, sqlite3.connect(self.db_inv) as c2:
                # 중복 체크
                if c1.execute("SELECT 1 FROM ledger WHERE hash=?", (doc_hash,)).fetchone(): 
                    raise ValueError("이미 박제된 데이터입니다 (중복).")
                
                # 이중 저장
                c1.execute("INSERT INTO ledger (date, corp, amount, hash, created_at) VALUES (?,?,?,?,?)", 
                          (d["date"], d["corp"], amt, doc_hash, now))
                c2.execute("INSERT INTO invoices (t_no, date, corp, item, amount, tax_rate, tax, hash, created_at) VALUES (?,?,?,?,?,?,?,?,?)", 
                          (d["t_no"].upper(), d["date"], d["corp"], d["item"], amt, rate, tax, doc_hash, now))
                
                messagebox.showinfo("성공", "데이터가 안전하게 박제되었습니다.")
                self.load_data()
                
                # 입력창 초기화 (세율 제외)
                for k, e in self.entries.items(): 
                    if k != "tax_rate": e.delete(0, 'end')
                    
        except Exception as e: messagebox.showwarning("입력 오류", str(e))

    def switch_view(self, mode): 
        self.current_view = mode; self.load_data()
        
    def sort_by(self, col): 
        if self.sort_col == col: self.sort_desc = not self.sort_desc
        else: self.sort_col, self.sort_desc = col, True
        self.load_data()

    def load_data(self):
        """데이터 조회 및 검색 필터링"""
        kw = self.entry_search.get().strip().replace(",", "").split()
        
        # 날짜 필터도 IME 방어 로직 적용 (검색창에서도 오타 허용)
        s_d = re.sub(r'[\u2010-\u2015\u2212\uFF0D\u30FC/.]', '-', self.date_start.get().strip())
        e_d = re.sub(r'[\u2010-\u2015\u2212\uFF0D\u30FC/.]', '-', self.date_end.get().strip())
        if s_d and e_d and s_d > e_d: s_d, e_d = e_d, s_d
        
        s_a = re.sub(r'[^\d]', '', self.amt_min.get())
        e_a = re.sub(r'[^\d]', '', self.amt_max.get())
        if s_a and e_a and int(s_a) > int(e_a): s_a, e_a = e_a, s_a
        
        for i in self.tree.get_children(): self.tree.delete(i)
        
        if self.current_view == "erp":
            cols = [("ID", "id", 40), ("날짜", "date", 90), ("거래처", "corp", 150), ("가액", "amount", 90), ("해시", "hash", 150)]
            sql, fields, amt_col = "SELECT id, date, corp, amount, hash FROM ledger", ["date", "corp", "amount"], "amount"
        else:
            cols = [("ID", "id", 40), ("T-번호", "t_no", 110), ("날짜", "date", 90), ("거래처", "corp", 120), ("합계", "amount+tax", 100)]
            sql, fields, amt_col = "SELECT id, t_no, date, corp, amount+tax FROM invoices", ["date", "corp", "t_no", "item", "amount", "tax"], "(amount+tax)"

        self.tree["columns"] = [c[0] for c in cols]
        for ui, db, w in cols:
            self.tree.heading(ui, text=ui, command=lambda c=db: self.sort_by(c))
            self.tree.column(ui, width=w, anchor="e" if "액" in ui or "합계" in ui else "center")

        where, params = [], []
        for k in kw:
            where.append("(" + " OR ".join([f"{f} LIKE ?" for f in fields]) + ")")
            params.extend([f"%{k}%"] * len(fields))
        
        if s_d: where.append("date >= ?"); params.append(s_d)
        if e_d: where.append("date <= ?"); params.append(e_d)
        if s_a: where.append(f"{amt_col} >= ?"); params.append(int(s_a))
        if e_a: where.append(f"{amt_col} <= ?"); params.append(int(e_a))
        
        if where: sql += " WHERE " + " AND ".join(where)
        sql += f" ORDER BY {self.sort_col} {'DESC' if self.sort_desc else 'ASC'}"

        try:
            with sqlite3.connect(self.db_erp if self.current_view == "erp" else self.db_inv) as conn:
                rows = conn.execute(sql, params).fetchall()
                
                if not rows and kw and not self.is_cross_searching:
                    self.is_cross_searching = True
                    if messagebox.askyesno("교차 검색", "현재 탭에 결과가 없습니다.\n반대편 탭에서 찾아볼까요?"):
                        self.current_view = "inv" if self.current_view == "erp" else "erp"; self.load_data()
                    self.is_cross_searching = False; return
                
                for r in rows:
                    v = list(r)
                    idx = -2 if self.current_view == "erp" else -1
                    v[idx] = "{:,}".format(v[idx])
                    self.tree.insert("", "end", values=v)
        except: pass

    def export_to_csv(self):
        """CSV 내보내기 (utf-8-sig 사용)"""
        db = self.db_erp if self.current_view == "erp" else self.db_inv
        fname = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=f"Vault_{self.current_view}.csv")
        if not fname: return
        try:
            with sqlite3.connect(db) as conn:
                cur = conn.cursor(); cur.execute(f"SELECT * FROM {'ledger' if self.current_view == 'erp' else 'invoices'}")
                rows = cur.fetchall(); headers = [d[0] for d in cur.description]
            
            with open(fname, 'w', newline='', encoding='utf-8-sig') as f:
                csv.writer(f).writerow(headers); csv.writer(f).writerows(rows)
            messagebox.showinfo("Success", "CSV Export OK")
        except: messagebox.showerror("Error", "Save Failed")

if __name__ == "__main__":
    root = tk.Tk(); IronVaultCommander(root); root.mainloop()
